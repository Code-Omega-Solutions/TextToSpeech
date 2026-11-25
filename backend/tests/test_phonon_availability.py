from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisUnavailable
from phonon_test_support import phonon_settings


def test_unavailable_phonon_selection_never_falls_back_to_native(
    settings_factory, monkeypatch
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    service = app.state.speech_service
    calls = []
    service.phonon_engine._opener = lambda *_args, **_kwargs: calls.append("phonon")
    monkeypatch.setattr(
        service,
        "_synthesize_macos",
        lambda *_args, **_kwargs: calls.append("native"),
    )
    monkeypatch.setattr(service.phonon_engine, "is_available", lambda: False)

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "hello", "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 503
    assert calls == []


def test_missing_model_or_voice_is_unavailable(settings_factory):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    service = app.state.speech_service
    service.phonon_engine.settings = settings_factory(
        phonon_enabled=True,
        phonon_server_url=settings.phonon_server_url,
        phonon_approval=None,
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "hello", "model": "phonon", "language": "de-DE"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503
