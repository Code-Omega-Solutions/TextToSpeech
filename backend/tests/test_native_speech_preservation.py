from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisResult


def test_native_speech_remains_available_when_phonon_is_disabled(
    settings_factory, monkeypatch
):
    settings = settings_factory(
        phonon_enabled=False,
        phonon_server_url=None,
        phonon_approval=None,
    )
    app = create_app(settings)
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr(
        "app.services.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr(
        "app.routers.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr(
        "app.services.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"}
    )
    monkeypatch.setattr(
        "app.routers.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"}
    )
    monkeypatch.setattr(
        app.state.speech_service,
        "_synthesize_macos",
        lambda *_args: SynthesisResult(
            b"native audio", "audio/mpeg", "speech.mp3", actual_backend="macos-say"
        ),
    )

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    catalog = client.get("/v1/audio/engines", headers=headers)
    assert catalog.status_code == 200
    engines = {engine["id"]: engine for engine in catalog.json()["engines"]}
    assert engines["macos-say"]["available"] is True
    assert engines["phonon"]["available"] is False
    assert client.get("/readyz").status_code == 200

    response = client.post(
        "/v1/audio/speech",
        json={"input": "Hello there", "model": "macos-say", "language": "en-US"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.content == b"native audio"
    assert response.headers["x-speech-backend"] == "macos-say"
    assert response.headers["x-speech-fallback"] == "false"
