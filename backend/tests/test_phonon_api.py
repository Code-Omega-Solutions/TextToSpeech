from __future__ import annotations

import wave
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import SynthesisResult, SynthesisUnavailable
from phonon_test_support import FakeOpener, FakeResponse, MODEL_DIGESTS, phonon_settings, request_payload


def tiny_pcm_wav(pcm=b"\x00\x00\x01\x00"):
    output = BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(24_000)
        target.writeframes(pcm)
    return output.getvalue()


@pytest.mark.parametrize(
    ("language", "voice", "model"),
    [
        ("en-US", "fixture-en-voice", "fixture-model-en"),
        ("de-DE", "fixture-de-voice", "fixture-model-de"),
    ],
)
def test_public_api_uses_only_approved_language_voice_and_model(
    settings_factory, monkeypatch, language, voice, model
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener([FakeResponse(b"\x00\x00\x01\x00")])
    app.state.speech_service.phonon_engine._opener = opener
    complete_wav = tiny_pcm_wav()

    def transcode(wav_audio, speed, response_format, cancel_event, *, actual_backend, deadline=None):
        assert wav_audio.startswith(b"RIFF")
        assert speed == 1
        assert response_format == "wav"
        assert actual_backend == "phonon"
        return SynthesisResult(
            complete_wav,
            "audio/wav",
            "speech.wav",
            actual_backend=actual_backend,
        )

    monkeypatch.setattr(app.state.speech_service, "_transcode_wav", transcode)
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={
            "input": "A complete fixture request.",
            "model": "phonon",
            "language": language,
            "voice": voice,
            "response_format": "wav",
        },
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 200
    assert response.content == complete_wav
    assert response.headers["x-speech-backend"] == "phonon"
    assert response.headers["x-speech-fallback"] == "false"
    payload = request_payload(opener.calls[0][0])
    assert payload["model"] == MODEL_DIGESTS[model].replace("sha256:", "sha256-", 1)
    assert payload["voice"] == voice


def test_unapproved_voice_is_unavailable_without_endpoint_call(settings_factory):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener()
    app.state.speech_service.phonon_engine._opener = opener

    response = TestClient(app).post(
        "/v1/audio/speech",
        json={
            "input": "hello",
            "model": "phonon",
            "language": "en-US",
            "voice": "unreviewed-fixture-voice",
        },
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 503
    assert opener.calls == []


def test_speech_uses_approved_digest_if_tag_changes_after_discovery(
    settings_factory, monkeypatch
):
    settings = phonon_settings(settings_factory)
    app = create_app(settings)
    opener = FakeOpener([FakeResponse(b"\x00\x00")])
    tag_digest = "a" * 64

    def changing_service(request, *, timeout):
        nonlocal tag_digest
        response = opener(request, timeout=timeout)
        if request.full_url.endswith("/api/tags"):
            tag_digest = "c" * 64
        if request.full_url.endswith("/v1/audio/speech"):
            model = request_payload(request)["model"]
            used_digest = tag_digest if model == "fixture-model-en" else model.removeprefix("sha256-")
            assert used_digest == "a" * 64
        return response

    app.state.speech_service.phonon_engine._opener = changing_service
    monkeypatch.setattr(
        app.state.speech_service,
        "_transcode_wav",
        lambda *_args, **_kwargs: SynthesisResult(
            b"audio", "audio/wav", "speech.wav", actual_backend="phonon"
        ),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "hello", "model": "phonon", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 200
