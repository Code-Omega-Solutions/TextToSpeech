import json
from urllib.error import URLError

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisResult, SynthesisUnavailable
from phonon_test_support import FakeOpener, FakeResponse, MODEL_DIGESTS, phonon_settings, request_payload


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
    monkeypatch.setattr(service.phonon_engine, "is_available", lambda *_args: False)

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


def test_catalog_advertises_matching_installed_models(settings_factory):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener()
    app.state.speech_service.phonon_engine._opener = opener
    response = TestClient(app).get(
        "/v1/audio/engines",
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    phonon = next(item for item in response.json()["engines"] if item["id"] == "phonon")
    assert response.status_code == 200
    assert phonon["available"] is True
    assert set(phonon["languages"]) == {"en-US", "de-DE"}
    assert len(opener.tag_calls) == 1
    assert "sha256" not in response.text


@pytest.mark.parametrize(
    "tags",
    [
        URLError("unavailable"),
        FakeResponse(b'{"models":[]}', content_type="application/json"),
        FakeResponse(b'{"models":', content_type="application/json"),
        FakeResponse(
            json.dumps({"models": [
                {"name": "fixture-model-en", "digest": "a" * 64},
                {"name": "fixture-model-en", "digest": "c" * 64},
            ]}).encode(),
            content_type="application/json",
        ),
        FakeResponse(
            json.dumps({"models": [
                {"name": name, "digest": "c" * 64}
                for name in MODEL_DIGESTS
            ]}).encode(),
            content_type="application/json",
        ),
    ],
    ids=["service-offline", "missing-models", "malformed-metadata", "duplicate-name", "digest-mismatch"],
)
def test_catalog_and_speech_fail_closed_for_unavailable_or_changed_models(
    settings_factory, tags
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener(tags=tags)
    app.state.speech_service.phonon_engine._opener = opener
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.api_key}"}

    catalog = client.get("/v1/audio/engines", headers=headers)
    phonon = next(item for item in catalog.json()["engines"] if item["id"] == "phonon")
    assert catalog.status_code == 200
    assert phonon == {"id": "phonon", "available": False, "languages": [], "voices": {}}
    assert "sha256" not in catalog.text
    assert "fixture-model" not in catalog.text

    speech = client.post(
        "/v1/audio/speech",
        headers=headers,
        json={"input": "hello", "model": "phonon", "language": "en-US"},
    )
    assert speech.status_code == 503
    assert opener.calls == []


def test_only_language_with_matching_model_is_advertised_and_usable(settings_factory, monkeypatch):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    tags = FakeResponse(
        json.dumps({"models": [
            {"name": "fixture-model-en", "digest": "a" * 64},
            {"name": "fixture-model-de", "digest": "c" * 64},
        ]}).encode(),
        content_type="application/json",
    )
    opener = FakeOpener([FakeResponse(b"\x00\x00")], tags=tags)
    app.state.speech_service.phonon_engine._opener = opener
    monkeypatch.setattr(
        app.state.speech_service,
        "_transcode_wav",
        lambda *_args, **_kwargs: SynthesisResult(
            b"audio", "audio/wav", "speech.wav", actual_backend="phonon"
        ),
    )
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    catalog = client.get("/v1/audio/engines", headers=headers)
    phonon = next(item for item in catalog.json()["engines"] if item["id"] == "phonon")
    assert phonon["available"] is True
    assert phonon["languages"] == ["en-US"]
    assert list(phonon["voices"]) == ["en-US"]
    english = client.post(
        "/v1/audio/speech", headers=headers,
        json={"input": "hello", "model": "phonon", "language": "en-US"},
    )
    german = client.post(
        "/v1/audio/speech", headers=headers,
        json={"input": "hallo", "model": "phonon", "language": "de-DE"},
    )
    assert english.status_code == 200
    assert german.status_code == 503
    assert len(opener.calls) == 1
    assert request_payload(opener.calls[0][0])["model"] == "sha256-" + "a" * 64


def test_unsupported_ollama_version_is_unavailable(settings_factory):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener()

    def old_server(request, *, timeout):
        if request.full_url.endswith("/api/version"):
            return FakeResponse(b'{"version":"0.40.17"}', content_type="application/json")
        return opener(request, timeout=timeout)

    app.state.speech_service.phonon_engine._opener = old_server
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    catalog = client.get("/v1/audio/engines", headers=headers)
    phonon = next(item for item in catalog.json()["engines"] if item["id"] == "phonon")
    assert phonon["available"] is False
    assert client.post(
        "/v1/audio/speech", headers=headers,
        json={"input": "hello", "model": "phonon", "language": "en-US"},
    ).status_code == 503
    assert opener.tag_calls == []
    assert opener.calls == []


@pytest.mark.parametrize(
    ("status", "body"),
    [(404, b"{}"), (200, b"{}"), (200, b'{"capabilities":["completion"]}')],
)
def test_missing_or_non_speech_manifest_is_not_advertised(settings_factory, status, body):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener()

    def missing_manifest(request, *, timeout):
        if request.full_url.endswith("/api/show"):
            return FakeResponse(body, content_type="application/json", status=status)
        return opener(request, timeout=timeout)

    app.state.speech_service.phonon_engine._opener = missing_manifest
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    catalog = client.get("/v1/audio/engines", headers=headers)
    phonon = next(item for item in catalog.json()["engines"] if item["id"] == "phonon")
    assert phonon["available"] is False
    assert phonon["languages"] == []
    assert client.post(
        "/v1/audio/speech", headers=headers,
        json={"input": "hello", "model": "phonon", "language": "en-US"},
    ).status_code == 503
    assert opener.calls == []
