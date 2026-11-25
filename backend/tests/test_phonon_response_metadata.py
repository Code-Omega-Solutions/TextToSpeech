from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisResult
from phonon_test_support import FakeOpener, FakeResponse, phonon_settings


def test_response_names_the_actual_phonon_engine(settings_factory, monkeypatch):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    app.state.speech_service.phonon_engine._opener = FakeOpener(
        [FakeResponse(b"\x00\x00")]
    )
    monkeypatch.setattr(
        app.state.speech_service,
        "_transcode_wav",
        lambda _wav, _speed, _format, _cancel, *, actual_backend, deadline=None:
            SynthesisResult(b"audio", "audio/mpeg", "speech.mp3", actual_backend=actual_backend),
    )

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "hello", "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 200
    assert response.headers["x-speech-backend"] == "phonon"
    assert response.headers["x-speech-fallback"] == "false"
