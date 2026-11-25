import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_authenticated_engine_discovery_does_not_advertise_fish(settings):
    response = TestClient(create_app(settings)).get(
        "/v1/audio/engines",
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 200
    engine_ids = {engine["id"] for engine in response.json()["engines"]}
    assert "fish-speech" not in engine_ids
    assert {"macos-say", "phonon"} <= engine_ids


def test_retired_fish_selection_is_unavailable_without_default_fallback(
    settings_factory, monkeypatch
):
    settings = settings_factory(default_backend="phonon", phonon_enabled=False)
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "try_acquire",
        lambda: pytest.fail("retired Fish request reached synthesis admission"),
    )
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: pytest.fail("retired Fish request fell back to the default"),
    )

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "model": "fish-speech", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Speech synthesis is unavailable."}


def test_baseline_readiness_does_not_require_fish_or_phonon(
    settings_factory, monkeypatch
):
    settings = settings_factory(phonon_enabled=False)
    app = create_app(settings)
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr(
        "app.routers.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr(
        "app.routers.available_voices",
        lambda *_args, **_kwargs: {"Anna", "Samantha"},
    )
    monkeypatch.setattr(
        app.state.speech_service.phonon_engine,
        "is_available",
        lambda: pytest.fail("baseline readiness probed Phonon"),
    )

    response = TestClient(app).get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
