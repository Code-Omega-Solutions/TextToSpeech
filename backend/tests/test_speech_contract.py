import logging

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisFailure, SynthesisResult
from phonon_test_support import phonon_settings


@pytest.mark.parametrize(
    ("backend", "response_format", "language", "voice", "media_type"),
    [
        ("macos-say", "mp3", "en-US", None, "audio/mpeg"),
        ("macos-say", "wav", "de-DE", None, "audio/wav"),
        ("phonon", "mp3", "en-US", None, "audio/mpeg"),
        ("phonon", "wav", "de-DE", None, "audio/wav"),
    ],
)
def test_backends_preserve_binary_audio_contract(
    settings_factory, monkeypatch, backend, response_format, language, voice, media_type
):
    settings = (
        phonon_settings(settings_factory)
        if backend == "phonon"
        else settings_factory()
    )
    app = create_app(settings)
    audio = b"complete audio payload"
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(
            audio,
            media_type,
            f"speech.{response_format}",
            actual_backend=backend,
        ),
    )
    payload = {
        "input": "A complete bounded speech request.",
        "model": backend,
        "language": language,
        "response_format": response_format,
    }
    if voice is not None:
        payload["voice"] = voice
    response = TestClient(app).post(
        "/v1/audio/speech",
        json=payload,
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 200
    assert response.content == audio
    assert response.headers["content-type"] == media_type
    assert response.headers["content-disposition"] == (
        f'inline; filename="speech.{response_format}"'
    )
    assert response.headers["x-speech-backend"] == backend
    assert response.headers["x-speech-fallback"] == "false"
    assert "x-speech-fallback-reason" not in response.headers


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("private_internal_marker", "unknown"),
        (None, "unknown"),
    ],
)
def test_fallback_diagnostics_are_generic_and_safe(
    settings, monkeypatch, caplog, reason, expected
):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(
            b"audio fixture", "audio/wav", "speech.wav",
            fallback=True, failure_reason=reason,
        ),
    )
    with caplog.at_level(logging.INFO, logger="app.routers"):
        response = TestClient(app).post(
            "/v1/audio/speech",
            json={
                "input": "private text marker",
                "model": "macos-say",
                "language": "en-US",
            },
            headers={"Authorization": f"Bearer {settings.api_key}"},
        )
    assert response.status_code == 200
    assert response.headers["x-speech-backend"] == "macos-say"
    assert response.headers["x-speech-fallback"] == "true"
    assert response.headers["x-speech-fallback-reason"] == expected
    assert f"request_id={response.headers['x-request-id']}" in caplog.text
    assert "requested_backend=macos-say backend=macos-say fallback=true" in caplog.text
    assert f"reason={expected} status=200" in caplog.text
    assert "private text marker" not in caplog.text
    assert "private_internal_marker" not in caplog.text


def test_authentication_precedes_optional_backend_admission(settings_factory, monkeypatch):
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
    )
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "try_acquire",
        lambda: pytest.fail("unauthenticated request reached admission"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "private request text", "model": "vibevoice", "language": "en-US"},
    )
    assert response.status_code == 401
    assert "private request text" not in response.text


def test_synthesis_error_never_echoes_request_text(settings, monkeypatch, caplog):
    app = create_app(settings)
    private_text = "private speech content marker"
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(SynthesisFailure(private_text)),
    )
    with caplog.at_level(logging.ERROR):
        response = TestClient(app).post(
            "/v1/audio/speech",
            json={"input": private_text, "language": "en-US"},
            headers={"Authorization": f"Bearer {settings.api_key}"},
        )
    assert response.status_code == 500
    assert private_text not in response.text
    assert private_text not in caplog.text
