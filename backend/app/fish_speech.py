from __future__ import annotations

import io
import json
import socket
import wave
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

import msgpack

from app.config import Settings


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

    def is_available(self) -> bool:
        if not self.settings.fish_enabled or not self.settings.fish_server_url:
            return False
        if not self.settings.fish_api_key:
            return False
        request = Request(
            f"{self.settings.fish_server_url}/v1/health",
            headers={"Authorization": f"Bearer {self.settings.fish_api_key}"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=min(3, self.settings.fish_request_timeout_seconds)) as response:
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