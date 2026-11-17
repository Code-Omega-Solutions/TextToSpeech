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


def test_serving_does_not_construct_vibevoice_worker(settings, monkeypatch):
    prepare_macos_readiness(monkeypatch)
    monkeypatch.setattr(
        VibeVoiceWorker,
        "__init__",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("the serving application constructed VibeVoiceWorker")
        ),
    )

    app = create_app(settings)

    assert not hasattr(app.state.speech_service, "vibevoice_worker")
    with TestClient(app) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["x-vibevoice-status"] == "disabled"