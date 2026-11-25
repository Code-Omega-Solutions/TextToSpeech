from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisResult
from phonon_test_support import FakeOpener, FakeResponse, phonon_settings


def test_public_response_is_complete_and_does_not_claim_client_streaming(
    settings_factory, monkeypatch
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    app.state.speech_service.phonon_engine._opener = FakeOpener(
        [FakeResponse(b"\x00\x00")]
    )
    audio = b"entire completed response"
    monkeypatch.setattr(
        app.state.speech_service,
        "_transcode_wav",
        lambda _wav, _speed, _format, _cancel, *, actual_backend, deadline=None:
            SynthesisResult(audio, "audio/wav", "speech.wav", actual_backend=actual_backend),
    )

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "hello", "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 200
    assert response.content == audio
    assert response.headers["content-length"] == str(len(audio))
    assert "transfer-encoding" not in response.headers
