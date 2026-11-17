from __future__ import annotations

import hashlib
import io
import json
import socket
import wave
from pathlib import Path
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import msgpack

from app.config import Settings


_REFERENCE_PROFILES = {
    ("de-DE", "male"): "de-male",
    ("de-DE", "female"): "de-female",
    ("en-US", "male"): "en-male",
    ("en-US", "female"): "en-female",
}


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_qualified_reference_catalog(path: str | None) -> dict[str, tuple[str, ...]]:
    """Load exactly four locally pinned, consented reference records.

    Invalid or incomplete manifests intentionally collapse to an empty catalog
    so an unqualified voice can never become publicly discoverable.
    """

    if not path:
        return {}
    try:
        manifest_path = Path(path).expanduser().resolve()
        if manifest_path.is_symlink() or not manifest_path.is_file():
            return {}
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            return {}
        records = document.get("references")
        if document.get("status") != "approved" or not isinstance(records, list):
            return {}
        if len(records) != len(_REFERENCE_PROFILES):
            return {}
        catalog: dict[str, list[str]] = {"de-DE": [], "en-US": []}
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                return {}
            language = str(record.get("language", ""))
            gender = str(record.get("gender", ""))
            reference_id = _REFERENCE_PROFILES.get((language, gender))
            if (
                reference_id is None
                or record.get("id") != reference_id
                or reference_id in seen
                or record.get("consent_status") != "speaker-consent"
                or record.get("speaker_category") != "non-celebrity"
                or record.get("terms_status") != "approved"
                or record.get("intended_use") != "private-noncommercial"
                or not str(record.get("source_revision", "")).strip()
                or not str(record.get("terms_revision", "")).strip()
                or not str(record.get("source_url", "")).startswith("https://")
                or not str(record.get("terms_url", "")).startswith("https://")
                or not str(record.get("source_license", "")).strip()
            ):
                return {}
            wav = Path(str(record.get("wav", ""))).expanduser().resolve()
            transcript = Path(str(record.get("transcript", ""))).expanduser().resolve()
            wav_hash = str(record.get("wav_sha256", ""))
            transcript_hash = str(record.get("transcript_sha256", ""))
            if (
                wav.is_symlink()
                or transcript.is_symlink()
                or not wav.is_file()
                or not transcript.is_file()
                or len(wav_hash) != 64
                or len(transcript_hash) != 64
                or any(character not in "0123456789abcdef" for character in wav_hash)
                or any(character not in "0123456789abcdef" for character in transcript_hash)
                or _file_sha256(wav) != wav_hash
                or _file_sha256(transcript) != transcript_hash
            ):
                return {}
            seen.add(reference_id)
            catalog[language].append(reference_id)
        if seen != set(_REFERENCE_PROFILES.values()):
            return {}
        return {language: tuple(sorted(voices)) for language, voices in catalog.items()}
    except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError):
        return {}


class FishSpeechError(RuntimeError):
    """The optional Fish Speech service cannot safely serve the request."""


class FishSpeechTimeout(FishSpeechError):
    """The Fish Speech request exceeded its configured deadline."""


class FishSpeechAudioTooLarge(FishSpeechError):
    """Fish Speech returned audio beyond the configured temporary limit."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class FishSpeechEngine:
    def __init__(self, settings: Settings, opener=None) -> None:
        self.settings = settings
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect()).open

    def is_available(self, timeout_seconds: float | None = None) -> bool:
        if not self.settings.fish_enabled or not self.settings.fish_server_url:
            return False
        if not self.settings.fish_api_key:
            return False
        request = Request(
            f"{self.settings.fish_server_url}/v1/health",
            data=b"",
            headers={"Authorization": f"Bearer {self.settings.fish_api_key}"},
            method="POST",
        )
        try:
            timeout = min(3, self.settings.fish_request_timeout_seconds)
            if timeout_seconds is not None:
                timeout = max(0.001, min(timeout, timeout_seconds))
            with self._opener(request, timeout=timeout) as response:
                if response.status != 200:
                    return False
                body = response.read(4097)
            if len(body) > 4096:
                return False
            data = json.loads(body)
            return isinstance(data, dict) and data.get("status") == "ok"
        except (HTTPError, URLError, OSError, ValueError, TimeoutError):
            return False

    def synthesize_wav(
        self,
        text: str,
        voice: str | None,
        cancel_event: Event | None = None,
        timeout_seconds: float | None = None,
    ) -> bytes:
        if cancel_event is not None and cancel_event.is_set():
            raise FishSpeechError("request cancelled")
        if not self.settings.fish_enabled or not self.settings.fish_server_url:
            raise FishSpeechError("engine disabled")
        if not self.settings.fish_api_key:
            raise FishSpeechError("engine credential unavailable")

        payload: dict[str, object] = {"text": text, "format": "wav"}
        if voice is not None:
            payload["reference_id"] = voice
        body = msgpack.packb(payload, use_bin_type=True)
        request = Request(
            f"{self.settings.fish_server_url}/v1/tts?format=msgpack",
            data=body,
            headers={
                "Authorization": f"Bearer {self.settings.fish_api_key}",
                "Accept": "audio/wav",
                "Content-Type": "application/msgpack",
            },
            method="POST",
        )

        try:
            with self._opener(
                request,
                timeout=timeout_seconds or self.settings.fish_request_timeout_seconds,
            ) as response:
                content_type = response.headers.get_content_type()
                audio = response.read(self.settings.max_temp_bytes + 1)
        except HTTPError as error:
            error.close()
            raise FishSpeechError("upstream request failed") from None
        except (socket.timeout, TimeoutError) as error:
            raise FishSpeechTimeout from error
        except (URLError, OSError) as error:
            if isinstance(getattr(error, "reason", None), (socket.timeout, TimeoutError)):
                raise FishSpeechTimeout from None
            raise FishSpeechError("upstream unavailable") from None

        if cancel_event is not None and cancel_event.is_set():
            raise FishSpeechError("request cancelled")
        if len(audio) > self.settings.max_temp_bytes:
            raise FishSpeechAudioTooLarge
        if content_type != "audio/wav":
            raise FishSpeechError("upstream returned an unsupported audio type")

        try:
            with wave.open(io.BytesIO(audio), "rb") as wav_file:
                if wav_file.getnchannels() < 1 or wav_file.getframerate() < 1:
                    raise FishSpeechError("upstream returned invalid audio")
        except (wave.Error, EOFError) as error:
            raise FishSpeechError("upstream returned invalid audio") from error

        return audio