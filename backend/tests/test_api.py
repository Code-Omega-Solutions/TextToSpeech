import logging
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services import AudioTooLarge, SynthesisResult, SynthesisTimeout, SynthesisUnavailable


def client_for(settings):
    return TestClient(create_app(settings))


def test_missing_and_invalid_authentication_return_challenge(settings):
    client = client_for(settings)
    for headers in ({}, {"Authorization": "Bearer wrong"}):
        response = client.post("/v1/audio/speech", json={"input": "hello"}, headers=headers)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_authentication_rejects_before_synthesis(settings, monkeypatch):
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("external process attempted")),
    )
    response = client_for(settings).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
    )
    assert response.status_code == 401


def test_explicitly_disabled_auth_accepts_requests_without_bearer(settings_factory, monkeypatch):
    app = create_app(settings_factory(api_key=None, auth_enabled=False))
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(b"audio", "audio/mpeg", "speech.mp3"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
    )
    assert response.status_code == 200
    assert response.content == b"audio"


def test_validation_errors_are_safe_422(settings):
    client = client_for(settings)
    response = client.post(
        "/v1/audio/speech",
        json={"input": "private text must not leak", "language": "fr"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}
    assert "private text" not in response.text


def test_too_many_speech_segments_return_safe_422(settings):
    response = client_for(settings).post(
        "/v1/audio/speech",
        json={"input": "Sentence. " * 101, "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Speech input must contain no more than 100 sentence segments."
    }
    assert "Sentence." not in response.text


def test_success_returns_binary_audio_and_expected_headers(settings, monkeypatch):
    client = client_for(settings)
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: {"Anna", "Samantha", "Daniel"},
    )
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/ffmpeg")

    def fake_run(arguments, **_kwargs):
        if arguments[0] != settings.say_path:
            Path(arguments[-1]).write_bytes(b"\x00\x01audio")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr("app.services.subprocess.run", fake_run)
    response = client.post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en", "voice": "alloy"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 200
    assert response.content == b"\x00\x01audio"
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["content-disposition"] == 'inline; filename="speech.mp3"'
    assert response.headers["x-request-id"]


def test_runtime_errors_map_to_safe_http_statuses(settings, monkeypatch):
    client = client_for(settings)
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: {"Samantha"},
    )
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/ffmpeg")
    response = client.post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]

    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(AudioTooLarge()),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 413
    assert "size limit" in response.json()["detail"]


def test_timeout_maps_to_504(settings, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(SynthesisTimeout()),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 504


def test_capacity_is_rejected_before_dispatch(settings, monkeypatch):
    app = create_app(settings)
    assert app.state.speech_service.try_acquire()
    assert app.state.speech_service.try_acquire()
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(AssertionError("synthesis must not be dispatched")),
    )
    try:
        response = TestClient(app).post(
            "/v1/audio/speech",
            json={"input": "Hello there", "language": "en-US"},
            headers={"Authorization": "Bearer " + settings.api_key},
        )
    finally:
        app.state.speech_service.release_permit()
        app.state.speech_service.release_permit()
    assert response.status_code == 503


def test_liveness_has_no_executable_checks(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: (_ for _ in ()).throw(AssertionError()))
    response = client_for(settings).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_requires_only_german_and_us_english(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"})
    client = client_for(settings)
    assert client.get("/readyz").status_code == 200

    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna"})
    response = client.get("/readyz")
    assert response.status_code == 503
    assert "Required speech voices" in response.json()["detail"]


def test_missing_optional_uk_voice_does_not_block_readiness_or_request_behavior(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"})
    client = client_for(settings)
    assert client.get("/readyz").status_code == 200
    response = client.post(
        "/v1/audio/speech",
        json={"input": "Good morning", "language": "en-GB"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503


def test_readiness_checks_executables(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: None)
    response = client_for(settings).get("/readyz")
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_logs_and_errors_do_not_disclose_request_text_or_token(settings, caplog, monkeypatch):
    client = client_for(settings)
    private_text = "TOP-SECRET-REQUEST-TEXT"
    private_token = settings.api_key
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError(private_text)),
    )
    caplog.set_level(logging.INFO)
    response = client.post(
        "/v1/audio/speech",
        json={"input": private_text, "language": "en-US"},
        headers={"Authorization": f"Bearer {private_token}"},
    )
    assert response.status_code == 500
    assert private_text not in response.text
    assert private_text not in caplog.text
    assert private_token not in caplog.text
