from fastapi.testclient import TestClient

from app.main import create_app
from app.vibevoice import VibeVoiceWorker


def prepare_macos_readiness(monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr(
        "app.routers.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr(
        "app.routers.available_voices",
        lambda *_args, **_kwargs: {"Anna", "Samantha"},
    )


def test_readiness_keeps_macos_baseline_when_optional_engines_are_disabled(settings, monkeypatch):
    prepare_macos_readiness(monkeypatch)
    app = create_app(settings)
    response = TestClient(app).get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["x-vibevoice-status"] == "disabled"
    assert response.headers["x-fish-speech-status"] == "disabled"


def test_unavailable_fish_service_does_not_block_macos_readiness(settings_factory, monkeypatch):
    prepare_macos_readiness(monkeypatch)
    monkeypatch.setattr("app.services.FishSpeechEngine.is_available", lambda _self: False)
    settings = settings_factory(
        fish_enabled=True,
        fish_server_url="http://127.0.0.1:8080",
        fish_api_key="unit-test-fish-key",
    )
    response = TestClient(create_app(settings)).get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["x-fish-speech-status"] == "unavailable"


def test_serving_application_never_constructs_vibevoice_worker(settings, monkeypatch):
    prepare_macos_readiness(monkeypatch)
    monkeypatch.setattr(
        VibeVoiceWorker,
        "__init__",
        lambda *_args, **_kwargs: pytest.fail("serving app constructed VibeVoice worker"),
    )
    app = create_app(settings)

    with TestClient(app) as client:
        assert client.get("/readyz").status_code == 200
    assert not hasattr(app.state.speech_service, "vibevoice_worker")
