from __future__ import annotations

import json

from app.config import PhononApproval


def approved_phonon_profile() -> PhononApproval:
    return PhononApproval(
        models_by_language={
            "en-US": "fixture-model-en",
            "de-DE": "fixture-model-de",
        },
        voices_by_language={
            "en-US": ("fixture-en-voice",),
            "de-DE": ("fixture-de-voice",),
        },
        default_voices_by_language={
            "en-US": "fixture-en-voice",
            "de-DE": "fixture-de-voice",
        },
    )


def phonon_settings(settings_factory, **overrides):
    values = {
        "phonon_enabled": True,
        "phonon_server_url": "http://127.0.0.1:11434",
        "phonon_approval": approved_phonon_profile(),
    }
    values.update(overrides)
    return settings_factory(**values)


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        content_type: str = "audio/pcm",
        status: int = 200,
        on_read=None,
    ):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.on_read = on_read
        self.offset = 0
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def close(self):
        self.closed = True

    def read(self, size=-1):
        if self.on_read is not None:
            self.on_read()
        if size < 0:
            size = len(self.body)
        end = min(self.offset + size, len(self.body))
        chunk = self.body[self.offset:end]
        self.offset = end
        return chunk


class FakeOpener:
    def __init__(self, responses=()):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, request, *, timeout):
        self.calls.append((request, timeout))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def request_payload(request) -> dict[str, object]:
    return json.loads(request.data.decode("utf-8"))
