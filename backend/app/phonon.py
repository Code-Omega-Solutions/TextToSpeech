from __future__ import annotations

import json
import re
import socket
import time
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from app.config import Settings


_PCM_CONTENT_TYPES = {"audio/pcm", "application/octet-stream"}
_PCM_READ_CHUNK_BYTES = 64 * 1024
_INSTALLED_MODELS_MAX_BYTES = 1024 * 1024
_MAX_SEGMENTS = 100
_MODEL_INPUT_CHARACTERS = 4096
_WAV_HEADER_BYTES = 44


class PhononError(Exception):
    """Base class for sanitized Phonon failures."""


class PhononUnavailable(PhononError):
    """Phonon or its approved model/voice is unavailable."""


class PhononTimeout(PhononError):
    """A bounded Phonon request exceeded its deadline."""


class PhononAudioTooLarge(PhononError):
    """Phonon returned more PCM than the configured temporary limit."""


class PhononFailure(PhononError):
    """A Phonon request was cancelled or returned invalid audio."""


class PhononSegmentLimitExceeded(PhononError):
    """An input would require more segments than the service permits."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def split_text(text: str, max_characters: int = _MODEL_INPUT_CHARACTERS) -> list[str]:
    if not text or max_characters < 1:
        raise PhononUnavailable
    segments: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_characters, len(text))
        if end < len(text):
            boundary = next(
                (
                    index
                    for index in range(end - 1, start + max_characters // 2, -1)
                    if text[index].isspace()
                ),
                None,
            )
            if boundary is not None:
                end = boundary + 1
        segments.append(text[start:end])
        if len(segments) > _MAX_SEGMENTS:
            raise PhononSegmentLimitExceeded
        start = end
    return segments


class PhononEngine:
    def __init__(self, settings: Settings, opener=None) -> None:
        self.settings = settings
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect()).open

    def is_configured(self) -> bool:
        approval = self.settings.phonon_approval
        return bool(
            self.settings.phonon_enabled
            and self.settings.phonon_server_url
            and approval is not None
            and all(
                approval.models_by_language.get(language)
                and approval.model_digests_by_language.get(language)
                and approval.voices_by_language.get(language)
                and approval.default_voices_by_language.get(language)
                in approval.voices_by_language.get(language, ())
                for language in ("en-US", "de-DE")
            )
        )

    def is_available(self, language: str | None = None, deadline: float | None = None) -> bool:
        catalog = self.voice_catalog(deadline, language)
        return bool(catalog) if language is None else language in catalog

    def voice_catalog(
        self, deadline: float | None = None, language: str | None = None
    ) -> dict[str, tuple[str, ...]]:
        if not self.is_configured():
            return {}
        try:
            installed = self.installed_model_digests(deadline)
        except PhononUnavailable:
            return {}
        approval = self.settings.phonon_approval
        voices = {}
        for locale, tag in approval.models_by_language.items():
            if language is not None and locale != language:
                continue
            digest = approval.model_digests_by_language[locale]
            if installed.get(tag) != digest:
                continue
            try:
                manifest = self._read_json(
                    "/api/show", deadline,
                    {"model": digest.replace("sha256:", "sha256-", 1)},
                )
            except PhononUnavailable:
                continue
            capabilities = manifest.get("capabilities") if isinstance(manifest, dict) else None
            if isinstance(capabilities, list) and "speech" in capabilities:
                voices[locale] = approval.voices_by_language[locale]
        return voices

    def installed_model_digests(self, deadline: float | None = None) -> dict[str, str]:
        version = self._read_json("/api/version", deadline)
        version_string = version.get("version") if isinstance(version, dict) else None
        if not isinstance(version_string, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version_string):
            raise PhononUnavailable
        if tuple(int(part) for part in version_string.split(".")) < (0, 40, 18):
            raise PhononUnavailable
        document = self._read_json("/api/tags", deadline)
        if not isinstance(document, dict) or not isinstance(document.get("models"), list):
            raise PhononUnavailable
        identities: dict[str, str] = {}
        for item in document["models"]:
            if not isinstance(item, dict):
                raise PhononUnavailable
            name, digest = item.get("name"), item.get("digest")
            if not isinstance(name, str) or not name.strip() or not isinstance(digest, str):
                raise PhononUnavailable
            if name in identities:
                raise PhononUnavailable
            identities[name] = "sha256:" + digest.removeprefix("sha256:")
        return identities

    def _read_json(
        self, path: str, deadline: float | None, payload: dict[str, str] | None = None
    ) -> object:
        if not self.settings.phonon_server_url:
            raise PhononUnavailable
        request = Request(
            f"{self.settings.phonon_server_url}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        timeout = min(3, self.settings.phonon_request_timeout_seconds)
        if deadline is not None:
            timeout = min(timeout, self._remaining(deadline))
        try:
            with self._opener(
                request,
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    raise PhononUnavailable
                if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise PhononUnavailable
                body = response.read(_INSTALLED_MODELS_MAX_BYTES + 1)
        except HTTPError as exc:
            exc.close()
            raise PhononUnavailable from None
        except (URLError, OSError, ValueError, TimeoutError):
            raise PhononUnavailable from None
        if len(body) > _INSTALLED_MODELS_MAX_BYTES:
            raise PhononUnavailable
        try:
            return json.loads(body)
        except (TypeError, ValueError):
            raise PhononUnavailable from None

    def synthesize_pcm(
        self,
        text: str,
        language: str,
        voice: str | None,
        cancel_event: Event | None = None,
        deadline: float | None = None,
    ) -> bytes:
        if cancel_event is not None and cancel_event.is_set():
            raise PhononFailure
        started = time.monotonic()
        operation_deadline = min(
            deadline or started + self.settings.request_timeout_seconds,
            started + self.settings.phonon_request_timeout_seconds,
        )
        if not self.is_available(language, operation_deadline):
            raise PhononUnavailable
        approval = self.settings.phonon_approval
        digest = approval.model_digests_by_language.get(language)
        voices = approval.voices_by_language.get(language, ())
        selected_voice = voice or approval.default_voices_by_language.get(language)
        if not digest or selected_voice not in voices:
            raise PhononUnavailable
        maximum_pcm_bytes = max(0, self.settings.max_temp_bytes - _WAV_HEADER_BYTES)
        pcm_parts: list[bytes] = []
        total_bytes = 0
        for segment in split_text(text):
            remaining = maximum_pcm_bytes - total_bytes
            if remaining <= 0:
                raise PhononAudioTooLarge
            pcm = self._request_pcm(
                digest.replace("sha256:", "sha256-", 1),
                segment,
                selected_voice,
                remaining,
                cancel_event,
                operation_deadline,
            )
            total_bytes += len(pcm)
            if total_bytes > maximum_pcm_bytes:
                raise PhononAudioTooLarge
            pcm_parts.append(pcm)
        if not total_bytes or total_bytes % 2:
            raise PhononUnavailable
        return b"".join(pcm_parts)

    def _request_pcm(
        self,
        model: str,
        text: str,
        voice: str,
        maximum_bytes: int,
        cancel_event: Event | None,
        deadline: float,
    ) -> bytes:
        if cancel_event is not None and cancel_event.is_set():
            raise PhononFailure
        payload = json.dumps(
            {
                "model": model,
                "input": text,
                "voice": voice,
                "response_format": "pcm",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            f"{self.settings.phonon_server_url}/v1/audio/speech",
            data=payload,
            headers={
                "Accept": "audio/pcm",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self._remaining(deadline)) as response:
                if response.status != 200:
                    raise PhononUnavailable
                content_type = response.headers.get("Content-Type", "")
                if content_type.split(";", 1)[0].strip().lower() not in _PCM_CONTENT_TYPES:
                    raise PhononUnavailable
                declared_length = response.headers.get("Content-Length")
                if declared_length is not None:
                    try:
                        if int(declared_length) > maximum_bytes:
                            raise PhononAudioTooLarge
                    except ValueError:
                        raise PhononUnavailable from None
                chunks: list[bytes] = []
                received = 0
                while True:
                    if cancel_event is not None and cancel_event.is_set():
                        raise PhononFailure
                    self._remaining(deadline)
                    chunk = response.read(min(_PCM_READ_CHUNK_BYTES, maximum_bytes - received + 1))
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > maximum_bytes:
                        raise PhononAudioTooLarge
                    chunks.append(chunk)
                if declared_length is not None and received != int(declared_length):
                    raise PhononUnavailable
                pcm = b"".join(chunks)
        except HTTPError as exc:
            exc.close()
            raise PhononUnavailable from None
        except (socket.timeout, TimeoutError):
            raise PhononTimeout from None
        except URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise PhononTimeout from None
            raise PhononUnavailable from None
        except OSError:
            raise PhononUnavailable from None
        if not pcm or len(pcm) % 2:
            raise PhononUnavailable
        return pcm

    @staticmethod
    def _remaining(deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise PhononTimeout
        return remaining
