from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import AudioTooLarge, SynthesisResult
from phonon_test_support import FakeOpener, FakeResponse, phonon_settings


@pytest.mark.parametrize(
    ("response_format", "media_type", "filename"),
    [("wav", "audio/wav", "speech.wav"), ("mp3", "audio/mpeg", "speech.mp3")],
)
def test_long_text_and_existing_controls_are_preserved(
    settings_factory, monkeypatch, response_format, media_type, filename
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener([FakeResponse(b"\x00\x00"), FakeResponse(b"\x00\x00")])
    app.state.speech_service.phonon_engine._opener = opener
    requested = []

    def transcode(wav_audio, speed, output_format, cancel_event, *, actual_backend, deadline=None):
        requested.append((speed, output_format, actual_backend))
        return SynthesisResult(
            b"complete audio",
            media_type,
            filename,
            actual_backend=actual_backend,
        )

    monkeypatch.setattr(app.state.speech_service, "_transcode_wav", transcode)
    text = "A" * 6000
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={
            "input": text,
            "model": "phonon",
            "language": "en-US",
            "voice": "fixture-en-voice",
            "speed": 1.5,
            "response_format": response_format,
        },
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 200
    assert response.content == b"complete audio"
    assert response.headers["content-type"] == media_type
    assert response.headers["content-disposition"] == f'inline; filename="{filename}"'
    assert requested == [(1.5, response_format, "phonon")]


def test_authentication_rejects_before_phonon_transport(settings_factory):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener()
    app.state.speech_service.phonon_engine._opener = opener

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "private text", "model": "phonon", "language": "en-US"},
    )

    assert response.status_code == 401
    assert opener.calls == []


def test_generated_output_limit_remains_enforced(settings_factory, monkeypatch):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    app.state.speech_service.phonon_engine._opener = FakeOpener(
        [FakeResponse(b"\x00\x00")]
    )
    monkeypatch.setattr(
        app.state.speech_service,
        "_transcode_wav",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AudioTooLarge),
    )

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "hello", "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 413
