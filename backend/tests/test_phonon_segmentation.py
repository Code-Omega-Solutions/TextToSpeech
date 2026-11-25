from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisResult
from phonon_test_support import FakeOpener, FakeResponse, phonon_settings, request_payload


def test_long_request_is_segmented_without_omission_in_order(settings_factory, monkeypatch):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener([FakeResponse(b"\x00\x00") for _ in range(3)])
    app.state.speech_service.phonon_engine._opener = opener

    def transcode(_wav_audio, _speed, _format, _cancel, *, actual_backend, deadline=None):
        return SynthesisResult(b"complete", "audio/wav", "speech.wav", actual_backend=actual_backend)

    monkeypatch.setattr(app.state.speech_service, "_transcode_wav", transcode)
    text = "  \n" + "ordered segment " * 299 + "ordered segment \t"
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": text, "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    sent = [request_payload(request) for request, _timeout in opener.calls]
    segments = [str(payload["input"]) for payload in sent]
    assert response.status_code == 200
    assert len(segments) > 1
    assert all(len(segment) <= 4096 for segment in segments)
    assert "".join(segments) == text
    assert response.content == b"complete"
