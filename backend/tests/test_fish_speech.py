import hashlib
import io
import json
import msgpack
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from app.fish_speech import (
    FishSpeechAudioTooLarge,
    FishSpeechEngine,
    FishSpeechError,
    load_qualified_reference_catalog,
)


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(b"\x00\x00" * 12)
    return output.getvalue()


class FishFixture:
    def __init__(self):
        self.payloads = []
        self.responses = {"/v1/health": (200, b'{"status":"ok"}', "application/json")}
        self.request_event = threading.Event()
        self.response_delay = 0
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                status, body, content_type = fixture.responses.get(
                    self.path, (404, b"not found", "text/plain")
                )
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                fixture.payloads.append(
                    (self.path, self.headers.get("Authorization"), self.headers.get("Content-Type"), body)
                )
                fixture.request_event.set()
                if fixture.response_delay:
                    time.sleep(fixture.response_delay)
                status, response, content_type = fixture.responses.get(
                    self.path, (404, b"not found", "text/plain")
                )
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                try:
                    self.wfile.write(response)
                except BrokenPipeError:
                    pass

            def log_message(self, _format, *_args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


@pytest.fixture
def fish_fixture():
    fixture = FishFixture()
    try:
        yield fixture
    finally:
        fixture.close()


def make_engine(settings_factory, base_url, **overrides):
    return FishSpeechEngine(
        settings_factory(
            fish_enabled=True,
            fish_server_url=base_url,
            fish_api_key="unit-test-fish-key",
            **overrides,
        )
    )


def test_availability_uses_authenticated_health_check(settings_factory, fish_fixture):
    engine = make_engine(settings_factory, fish_fixture.url)

    assert engine.is_available() is True
    path, authorization, content_type, payload = fish_fixture.payloads[0]
    assert path == "/v1/health"
    assert authorization == "Bearer unit-test-fish-key"
    assert payload == b""


def test_synthesis_sends_bounded_messagepack_request_and_validates_wav(
    settings_factory, fish_fixture
):
    audio = wav_bytes()
    fish_fixture.responses["/v1/tts?format=msgpack"] = (200, audio, "audio/wav")
    engine = make_engine(settings_factory, fish_fixture.url)

    result = engine.synthesize_wav("Guten Morgen", "de-reference")

    assert result == audio
    path, authorization, content_type, payload = fish_fixture.payloads[0]
    assert path == "/v1/tts?format=msgpack"
    assert authorization == "Bearer unit-test-fish-key"
    assert content_type == "application/msgpack"
    assert msgpack.unpackb(payload, raw=False) == {
        "text": "Guten Morgen",
        "format": "wav",
        "reference_id": "de-reference",
    }


def test_synthesis_omits_unspecified_reference(settings_factory, fish_fixture):
    fish_fixture.responses["/v1/tts?format=msgpack"] = (200, wav_bytes(), "audio/wav")
    engine = make_engine(settings_factory, fish_fixture.url)

    engine.synthesize_wav("Hello", None)

    payload = msgpack.unpackb(fish_fixture.payloads[0][3], raw=False)
    assert payload == {"text": "Hello", "format": "wav"}


def test_synthesis_refuses_oversized_audio(settings_factory, fish_fixture):
    settings = settings_factory(
        fish_enabled=True,
        fish_server_url=fish_fixture.url,
        fish_api_key="unit-test-fish-key",
        max_temp_bytes=128,
    )
    fish_fixture.responses["/v1/tts?format=msgpack"] = (200, b"x" * 129, "audio/wav")

    with pytest.raises(FishSpeechAudioTooLarge):
        FishSpeechEngine(settings).synthesize_wav("Hello", None)


def test_synthesis_rejects_non_audio_response(settings_factory, fish_fixture):
    fish_fixture.responses["/v1/tts?format=msgpack"] = (200, b"private error body", "application/json")

    with pytest.raises(FishSpeechError, match="audio type"):
        make_engine(settings_factory, fish_fixture.url).synthesize_wav("Hello", None)


def test_synthesis_does_not_follow_redirects(settings_factory, fish_fixture):
    fish_fixture.responses["/v1/tts?format=msgpack"] = (
        302,
        b"redirect",
        "text/plain",
    )

    with pytest.raises(FishSpeechError):
        make_engine(settings_factory, fish_fixture.url).synthesize_wav("Hello", None)

    assert fish_fixture.request_event.is_set()


def test_synthesis_timeout_is_bounded(settings_factory, fish_fixture):
    fish_fixture.response_delay = 0.1
    engine = make_engine(settings_factory, fish_fixture.url)

    with pytest.raises(Exception) as error:
        engine.synthesize_wav("Hello", None, timeout_seconds=0.01)

    assert type(error.value).__name__ == "FishSpeechTimeout"
    assert fish_fixture.request_event.is_set()


def test_cancelled_request_is_not_sent(settings_factory, fish_fixture):
    engine = make_engine(settings_factory, fish_fixture.url)
    cancelled = threading.Event()
    cancelled.set()

    with pytest.raises(FishSpeechError, match="cancelled"):
        engine.synthesize_wav("Hello", None, cancel_event=cancelled)

    assert fish_fixture.payloads == []


def test_reference_catalog_requires_all_exact_consent_records(tmp_path):
    records = []
    for language, gender, reference_id in (
        ("de-DE", "male", "de-male"),
        ("de-DE", "female", "de-female"),
        ("en-US", "male", "en-male"),
        ("en-US", "female", "en-female"),
    ):
        wav = tmp_path / f"{reference_id}.wav"
        transcript = tmp_path / f"{reference_id}.txt"
        wav.write_bytes(reference_id.encode("ascii"))
        transcript.write_text(f"Transcript for {reference_id}", encoding="utf-8")
        records.append(
            {
                "id": reference_id,
                "language": language,
                "gender": gender,
                "wav": str(wav),
                "transcript": str(transcript),
                "wav_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
                "transcript_sha256": hashlib.sha256(
                    transcript.read_bytes()
                ).hexdigest(),
                "source_url": "https://example.test/source",
                "source_revision": "source-revision",
                "source_license": "CC0",
                "terms_url": "https://example.test/terms",
                "terms_revision": "terms-revision",
                "consent_status": "speaker-consent",
                "speaker_category": "non-celebrity",
                "terms_status": "approved",
                "intended_use": "private-noncommercial",
            }
        )
    manifest = tmp_path / "references.json"
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )

    assert load_qualified_reference_catalog(str(manifest)) == {
        "de-DE": ("de-female", "de-male"),
        "en-US": ("en-female", "en-male"),
    }

    records.pop()
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )
    assert load_qualified_reference_catalog(str(manifest)) == {}