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


def reference_record(language, gender, reference_id):
    dataset_id = (
        "cmu5mc2sn00s5mi07udtq2864"
        if language == "de-DE"
        else "cmu5nqn1h00vwmi07b4dbk085"
    )
    return {
        "id": reference_id,
        "language": language,
        "gender": gender,
        "dataset_id": dataset_id,
        "dataset_release": "sps-corpus-5.0-2026-09-11",
        "source_url": f"https://mozilladatacollective.com/datasets/{dataset_id}",
        "source_revision": "sps-corpus-5.0-2026-09-11",
        "source_license": "CC0-1.0",
        "terms_url": "https://example.test/terms",
        "terms_revision": "accepted-dataset-agreement",
        "permission_basis": "dataset-terms-accepted",
        "terms_status": "approved",
        "intended_use": "private-noncommercial",
    }


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
        "use_memory_cache": "on",
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
    source_root = tmp_path / "fish-source"
    source_root.mkdir()
    records = []
    for language, gender, reference_id in (
        ("de-DE", "male", "de-male"),
        ("de-DE", "female", "de-female"),
        ("en-US", "male", "en-male"),
        ("en-US", "female", "en-female"),
    ):
        reference_dir = source_root / "references" / reference_id
        reference_dir.mkdir(parents=True)
        wav = reference_dir / f"{reference_id}.wav"
        transcript = reference_dir / f"{reference_id}.lab"
        wav.write_bytes(wav_bytes())
        transcript.write_text(f"Transcript for {reference_id}", encoding="utf-8")
        records.append(
            {
                **reference_record(language, gender, reference_id),
                "audio_path": f"references/{reference_id}/{reference_id}.wav",
                "lab_path": f"references/{reference_id}/{reference_id}.lab",
                "audio_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
                "lab_sha256": hashlib.sha256(
                    transcript.read_bytes()
                ).hexdigest(),
            }
        )
    manifest = tmp_path / "references.json"
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )

    extra_dir = source_root / "references" / "unapproved"
    extra_dir.mkdir()
    (extra_dir / "unapproved.wav").write_bytes(wav_bytes())

    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {}

    (extra_dir / "unapproved.wav").unlink()
    extra_dir.rmdir()

    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {
        "de-DE": ("de-female", "de-male"),
        "en-US": ("en-female", "en-male"),
    }

    records[0]["permission_basis"] = "speaker-consent"
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )
    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {}
    records[0]["permission_basis"] = "dataset-terms-accepted"
    records[0]["dataset_id"] = "unreviewed-dataset"
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )
    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {}

    records.pop()
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )
    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {}


def test_reference_catalog_rejects_paths_not_consumed_by_fish(tmp_path):
    source_root = tmp_path / "fish-source"
    reference_dir = source_root / "references" / "de-male"
    reference_dir.mkdir(parents=True)
    wav = reference_dir / "de-male.wav"
    lab = reference_dir / "de-male.lab"
    wav.write_bytes(wav_bytes())
    lab.write_text("Guten Morgen", encoding="utf-8")
    records = [
        {
            **reference_record("de-DE", "male", "de-male"),
            "audio_path": str(wav),
            "lab_path": str(lab),
            "audio_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
            "lab_sha256": hashlib.sha256(lab.read_bytes()).hexdigest(),
        }
    ]
    manifest = tmp_path / "references.json"
    manifest.write_text(json.dumps({"status": "approved", "references": records}), encoding="utf-8")

    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {}


def test_reference_catalog_rejects_extra_files_fish_would_load(tmp_path):
    source_root = tmp_path / "fish-source"
    reference_dir = source_root / "references" / "de-male"
    reference_dir.mkdir(parents=True)
    wav = reference_dir / "de-male.wav"
    lab = reference_dir / "de-male.lab"
    extra = reference_dir / "second.wav"
    wav.write_bytes(wav_bytes())
    lab.write_text("Guten Morgen", encoding="utf-8")
    extra.write_bytes(wav_bytes())
    record = {
        **reference_record("de-DE", "male", "de-male"),
        "audio_path": "references/de-male/de-male.wav",
        "lab_path": "references/de-male/de-male.lab",
        "audio_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
        "lab_sha256": hashlib.sha256(lab.read_bytes()).hexdigest(),
    }
    manifest = tmp_path / "references.json"
    manifest.write_text(
        json.dumps({"status": "approved", "references": [record]}), encoding="utf-8"
    )

    assert load_qualified_reference_catalog(str(manifest), str(source_root)) == {}