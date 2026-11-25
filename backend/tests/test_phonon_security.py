from fastapi.testclient import TestClient

from app.main import create_app
from phonon_test_support import FakeOpener, phonon_settings


def test_authentication_is_required_before_unauthenticated_ollama_service(
    settings_factory,
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener()
    app.state.speech_service.phonon_engine._opener = opener
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "private text", "model": "phonon", "language": "en-US"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert opener.calls == []
