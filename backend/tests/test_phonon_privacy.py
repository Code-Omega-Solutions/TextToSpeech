import logging
from urllib.error import URLError

from fastapi.testclient import TestClient

from app.main import create_app
from phonon_test_support import FakeOpener, phonon_settings


def test_upstream_errors_and_logs_hide_text_credentials_and_endpoint(
    settings_factory, caplog
):
    secret_endpoint = "http://127.0.0.1:11434/private-endpoint-marker"
    settings = phonon_settings(settings_factory, phonon_server_url="http://127.0.0.1:11434")
    app = create_app(settings)
    app.state.speech_service.phonon_engine._opener = FakeOpener(
        [URLError(secret_endpoint)]
    )
    private_text = "private speech marker"
    caplog.set_level(logging.INFO)

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": private_text, "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    logs = caplog.text
    assert response.status_code == 503
    assert private_text not in response.text + logs
    assert settings.api_key not in logs
    assert secret_endpoint not in response.text + logs
