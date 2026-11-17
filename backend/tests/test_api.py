import logging
import asyncio
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.fish_speech import FishSpeechError
from app.services import (
    AudioTooLarge,
    SynthesisFailure,
    SynthesisResult,
    SynthesisTimeout,
    SynthesisUnavailable,
)


def client_for(settings):
    return TestClient(create_app(settings))


def send_asgi_body(app, body, *, content_length=None, chunk_size=4096):
    headers = [(b"content-type", b"application/json")]
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode("ascii")))
    chunks = [body[index : index + chunk_size] for index in range(0, len(body), chunk_size)]
    messages = [
        {
            "type": "http.request",
            "body": chunk,
            "more_body": index < len(chunks) - 1,
        }
        for index, chunk in enumerate(chunks)
    ] or [{"type": "http.request", "body": b"", "more_body": False}]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(message):
        sent.append(message)

    async def run():
        await app(
            {
                "type": "http",
                "asgi": {"version": "3.0", "spec_version": "2.3"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/v1/audio/speech",
                "raw_path": b"/v1/audio/speech",
                "query_string": b"",
                "headers": headers,
                "client": ("127.0.0.1", 12345),
                "server": ("127.0.0.1", 8000),
            },
            receive,
            send,
        )

    asyncio.run(run())
    return sent


def test_missing_and_invalid_authentication_return_challenge(settings):
    client = client_for(settings)
    for headers in ({}, {"Authorization": "Bearer wrong"}):
        response = client.post("/v1/audio/speech", json={"input": "hello"}, headers=headers)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_authentication_rejects_before_synthesis(settings, monkeypatch):
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("external process attempted")),
    )
    response = client_for(settings).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
    )
    assert response.status_code == 401


def test_explicitly_disabled_auth_accepts_requests_without_bearer(settings_factory, monkeypatch):
    app = create_app(settings_factory(api_key=None, auth_enabled=False))
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(b"audio", "audio/mpeg", "speech.mp3"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
    )
    assert response.status_code == 200
    assert response.content == b"audio"


def test_validation_errors_are_safe_422(settings):
    client = client_for(settings)
    response = client.post(
        "/v1/audio/speech",
        json={"input": "private text must not leak", "language": "fr"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}
    assert "private text" not in response.text


def test_too_many_speech_segments_return_safe_422(settings):
    response = client_for(settings).post(
        "/v1/audio/speech",
        json={"input": "Sentence. " * 101, "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Speech input must contain no more than 100 sentence segments."
    }
    assert "Sentence." not in response.text


def test_success_returns_binary_audio_and_expected_headers(settings, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(b"\x00\x01audio", "audio/mpeg", "speech.mp3"),
    )
    client = TestClient(app)
    response = client.post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en", "voice": "alloy"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 200
    assert response.content == b"\x00\x01audio"
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["content-disposition"] == 'inline; filename="speech.mp3"'
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-request-id"]


def test_response_reports_actual_backend(settings_factory, monkeypatch):
    settings = settings_factory(
        fish_enabled=True,
        fish_server_url="http://127.0.0.1:8080",
        fish_api_key="unit-test-fish-key",
    )
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(
            b"audio", "audio/wav", "speech.wav", actual_backend="fish-speech"
        ),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "model": "fish-speech", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 200
    assert response.headers["x-speech-backend"] == "fish-speech"
    assert response.headers["x-speech-fallback"] == "false"


def test_fish_failure_returns_unavailable_without_silent_macos_fallback(
    settings_factory, monkeypatch
):
    settings = settings_factory(
        fish_enabled=True,
        fish_server_url="http://127.0.0.1:8080",
        fish_api_key="unit-test-fish-key",
    )
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service.fish_speech,
        "synthesize_wav",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FishSpeechError("fixture failure")),
    )
    monkeypatch.setattr(
        app.state.speech_service,
        "_synthesize_macos",
        lambda *_args, **_kwargs: pytest.fail("Fish failure silently fell back to macOS"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "model": "fish-speech", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech synthesis is unavailable."}


def test_legacy_vibevoice_selector_is_safe_unavailable_without_admission(settings, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "try_acquire",
        lambda: pytest.fail("legacy VibeVoice request reached synthesis admission"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "model": "vibevoice", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech synthesis is unavailable."}


@pytest.mark.parametrize(
    ("model", "language", "voice"),
    [
        ("fish-speech", "de", "neural-reference"),
        ("fish-speech", "en", "neural-reference"),
        ("vibevoice", "de", "de-Spk0_man"),
        ("vibevoice", "en", "en-Carter_man"),
    ],
)
def test_optional_fallback_is_authenticated_language_only_and_observable(
    settings_factory, monkeypatch, caplog, model, language, voice
):
    settings = settings_factory(fish_opportunistic=True)
    app = create_app(settings)
    calls = []

    def native(*args, **kwargs):
        calls.append(args)
        assert kwargs["deadline"] <= time.monotonic() + settings.request_timeout_seconds
        return SynthesisResult(b"native audio", "audio/wav", "speech.wav")

    monkeypatch.setattr(app.state.speech_service, "_synthesize_macos", native)
    with TestClient(app) as client:
        body = {
            "input": "synthetic speech marker", "model": model,
            "language": language, "voice": voice, "response_format": "wav",
        }
        assert client.post("/v1/audio/speech", json=body).status_code == 401
        assert calls == []
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/v1/audio/speech", json=body,
                headers={"Authorization": f"Bearer {settings.api_key}"},
            )
        assert response.status_code == 200
        assert calls[0][1] == {"de": "de-DE", "en": "en-US"}[language]
        assert calls[0][5] is None
        assert response.content == b"native audio"
        assert response.headers["x-speech-backend"] == "macos-say"
        assert response.headers["x-speech-fallback"] == "true"
        body["model"] = "unknown"
        assert client.post(
            "/v1/audio/speech", json=body,
            headers={"Authorization": f"Bearer {settings.api_key}"},
        ).status_code == 422
        assert len(calls) == 1
    assert "synthetic speech marker" not in caplog.text
    assert settings.api_key not in caplog.text


def test_application_shutdown_closes_managed_worker(settings_factory, monkeypatch):
    app = create_app(settings_factory(fish_opportunistic=True))
    closed = []
    monkeypatch.setattr(app.state.speech_service.fish_process, "close", lambda: closed.append(True))
    with TestClient(app):
        assert not closed
    assert closed == [True]


def test_invalid_vibevoice_voice_is_rejected_before_capacity(settings_factory, monkeypatch):
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
    )
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "try_acquire",
        lambda: pytest.fail("invalid voice reached synthesis admission"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={
            "input": "Hello there",
            "model": "vibevoice",
            "language": "en-US",
            "voice": "de-Spk1_woman",
        },
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request."}


def test_configured_backend_and_explicit_override_reach_service(settings_factory, monkeypatch):
    settings = settings_factory(
        default_backend="fish-speech",
        fish_enabled=True,
        fish_server_url="http://127.0.0.1:8080",
        fish_api_key="unit-test-fish-key",
    )
    app = create_app(settings)
    calls = []

    def synthesize(*args):
        calls.append(args)
        return SynthesisResult(b"audio", "audio/mpeg", "speech.mp3")

    monkeypatch.setattr(app.state.speech_service, "synthesize_reserved", synthesize)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    for model in (None, "macos-say"):
        payload = {"input": "Hello there", "language": "en-US"}
        if model is not None:
            payload["model"] = model
        response = client.post("/v1/audio/speech", json=payload, headers=headers)
        assert response.status_code == 200
    assert [call[-2:] for call in calls] == [("fish-speech", None), ("macos-say", None)]


def test_legacy_vibevoice_override_returns_unavailable_before_synthesis(settings, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: pytest.fail("disabled backend reached synthesis"),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "model": "vibevoice", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Speech synthesis is unavailable."}


def test_unsupported_detected_language_synthesizes_with_en_us(settings_factory, monkeypatch):
    settings = settings_factory(default_language="de-DE")
    app = create_app(settings)
    calls = []
    monkeypatch.setattr("app.language.langid.classify", lambda _text: ("fr", 0.9))

    def synthesize(text, language, speed, response_format, cancel_event, backend, voice):
        calls.append((language, backend, voice))
        return SynthesisResult(b"fixture-audio", "audio/mpeg", "speech.mp3")

    monkeypatch.setattr(app.state.speech_service, "synthesize_reserved", synthesize)
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "A synthetic example of speech synthesis for testing."},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 200
    assert response.content == b"fixture-audio"
    assert response.headers["content-type"] == "audio/mpeg"
    assert calls == [("en-US", "macos-say", None)]


def test_speech_body_limit_accepts_exact_32_kib(settings, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: SynthesisResult(b"fixture-audio", "audio/mpeg", "speech.mp3"),
    )
    payload = b'{"input":"' + b"a" * 5000 + b'","language":"en-US"}'
    body = b" " * (32 * 1024 - len(payload)) + payload
    response = TestClient(app).post(
        "/v1/audio/speech",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}",
        },
    )
    assert len(body) == 32 * 1024
    assert response.status_code == 200
    assert response.content == b"fixture-audio"


@pytest.mark.parametrize("declared_length", [None, 1])
def test_speech_body_limit_rejects_chunked_and_underreported_bodies(
    settings, monkeypatch, declared_length
):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(AssertionError("oversized request reached synthesis")),
    )
    payload = b'{"input":"' + b"a" * 5000 + b'","language":"en-US"}'
    body = b" " * (32 * 1024 + 1 - len(payload)) + payload
    sent = send_asgi_body(app, body, content_length=declared_length)
    response_start = next(message for message in sent if message["type"] == "http.response.start")
    response_body = next(message for message in sent if message["type"] == "http.response.body")
    assert response_start["status"] == 413
    assert b"32 KiB" in response_body["body"]
    assert b"a" * 16 not in response_body["body"]


def test_backend_exposes_only_documented_routes(settings):
    client = client_for(settings)
    assert client.get("/api/unknown").status_code == 404
    assert client.get("/v1/audio/speech").status_code == 405
    assert client.post("/healthz").status_code == 405


def test_runtime_errors_map_to_safe_http_statuses(settings, monkeypatch):
    client = client_for(settings)
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: {"Samantha"},
    )
    monkeypatch.setattr("app.services.shutil.which", lambda _path: None)
    response = client.post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]

    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(AudioTooLarge()),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 413
    assert "size limit" in response.json()["detail"]


def test_timeout_maps_to_504(settings, monkeypatch):
    app = create_app(settings)
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(SynthesisTimeout()),
    )
    response = TestClient(app).post(
        "/v1/audio/speech",
        json={"input": "Hello there", "language": "en-US"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 504


def test_capacity_is_rejected_before_dispatch(settings, monkeypatch):
    app = create_app(settings)
    assert app.state.speech_service.try_acquire()
    assert app.state.speech_service.try_acquire()
    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        lambda *_args: (_ for _ in ()).throw(AssertionError("synthesis must not be dispatched")),
    )
    try:
        response = TestClient(app).post(
            "/v1/audio/speech",
            json={"input": "Hello there", "language": "en-US"},
            headers={"Authorization": "Bearer " + settings.api_key},
        )
    finally:
        app.state.speech_service.release_permit()
        app.state.speech_service.release_permit()
    assert response.status_code == 503


def test_request_cancellation_terminates_work_and_releases_capacity(settings, monkeypatch):
    app = create_app(settings)
    started = threading.Event()
    cancelled = threading.Event()

    def wait_for_cancellation(*arguments):
        cancel_event = arguments[4]
        started.set()
        while not cancel_event.is_set():
            time.sleep(0.005)
        cancelled.set()
        raise SynthesisFailure

    monkeypatch.setattr(
        app.state.speech_service,
        "synthesize_reserved",
        wait_for_cancellation,
    )

    async def cancel_request():
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )
        request = asyncio.create_task(
            client.post(
                "/v1/audio/speech",
                json={"input": "Hello there", "language": "en-US"},
                headers={"Authorization": f"Bearer {settings.api_key}"},
            )
        )
        while not started.is_set():
            await asyncio.sleep(0.005)
        request.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request
        await client.aclose()

    asyncio.run(cancel_request())
    assert cancelled.wait(timeout=1)
    assert app.state.speech_service.try_acquire()
    app.state.speech_service.release_permit()


def test_liveness_has_no_executable_checks(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: (_ for _ in ()).throw(AssertionError()))
    response = client_for(settings).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_requires_only_german_and_us_english(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr(
        "app.routers.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"})
    client = client_for(settings)
    assert client.get("/readyz").status_code == 200

    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna"})
    response = client.get("/readyz")
    assert response.status_code == 503
    assert "Required speech voices" in response.json()["detail"]


def test_missing_optional_uk_voice_does_not_block_readiness_or_request_behavior(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr(
        "app.routers.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"})
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: {"Anna", "Samantha"},
    )
    client = client_for(settings)
    assert client.get("/readyz").status_code == 200
    response = client.post(
        "/v1/audio/speech",
        json={"input": "Good morning", "language": "en-GB"},
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )
    assert response.status_code == 503


def test_readiness_checks_executables(settings, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: None)
    response = client_for(settings).get("/readyz")
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]


def test_readiness_requires_both_audio_codecs_and_authentication(settings, settings_factory, monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr("app.routers.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha"})
    monkeypatch.setattr("app.routers.available_codecs", lambda *_args, **_kwargs: {"libmp3lame"})
    response = client_for(settings).get("/readyz")
    assert response.status_code == 503
    assert "codecs" in response.json()["detail"]

    missing_key = settings_factory(api_key=None, auth_enabled=True)
    response = client_for(missing_key).get("/readyz")
    assert response.status_code == 503
    assert "Authentication" in response.json()["detail"]


def test_logs_and_errors_do_not_disclose_request_text_or_token(settings, caplog, monkeypatch):
    client = client_for(settings)
    private_text = "TOP-SECRET-REQUEST-TEXT"
    private_token = settings.api_key
    monkeypatch.setattr(
        "app.services.available_voices",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError(private_text)),
    )
    caplog.set_level(logging.INFO)
    response = client.post(
        "/v1/audio/speech?private_query=TOP-SECRET-QUERY",
        json={"input": private_text, "language": "en-US"},
        headers={"Authorization": f"Bearer {private_token}"},
    )
    assert response.status_code == 500
    application_logs = "\n".join(
        record.getMessage() for record in caplog.records if record.name.startswith("app.")
    )
    assert private_text not in response.text
    assert private_text not in application_logs
    assert private_token not in application_logs
    assert "TOP-SECRET-QUERY" not in application_logs
