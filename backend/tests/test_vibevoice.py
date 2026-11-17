import io
import json
import os
import threading
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.vibevoice import VibeVoiceError, VibeVoiceWorker
from vibevoice_worker.worker import _create_decoder_only_tokenizer, main as worker_main, serve


_wav_buffer = io.BytesIO()
with wave.open(_wav_buffer, "wb") as _wav_file:
    _wav_file.setnchannels(1)
    _wav_file.setsampwidth(2)
    _wav_file.setframerate(24_000)
    _wav_file.writeframes(b"\x00\x00")
_WAV = _wav_buffer.getvalue()


class FakeProcess:
    def __init__(self, audio=_WAV):
        self.request = None
        self.audio = audio
        self.response = None
        self.returncode = None
        self.terminated = False
        self.closed = False
        self.terminated_event = threading.Event()
        self.stdin = self
        self.stdout = self

    def write(self, message):
        self.request = json.loads(message)

    def flush(self):
        request = self.request
        Path(request["output_path"]).write_bytes(self.audio)
        self.response = json.dumps(
            {"request_id": request["request_id"], "status": "ok"}
        ) + "\n"

    def readline(self):
        return self.response

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15
        self.terminated_event.set()

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9

    def close(self):
        self.closed = True


def make_worker(settings_factory, *, memory_probe=None, timeout_seconds=60, audio=_WAV):
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_timeout_seconds=timeout_seconds,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
        vibevoice_worker_python="/worker/bin/python",
        vibevoice_source_path="/approved/VibeVoice",
        vibevoice_model_path="/models/VibeVoice-Realtime-0.5B",
    )
    processes = []

    def process_factory(arguments, **kwargs):
        assert arguments[0] == "/worker/bin/python"
        assert kwargs["shell"] is False
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        assert kwargs["env"]["TRANSFORMERS_OFFLINE"] == "1"
        assert kwargs["env"]["TTS_VIBEVOICE_RESEARCH_ONLY"] == "true"
        assert "TTS_API_KEY" not in kwargs["env"]
        assert kwargs["env"]["TTS_MAX_OUTPUT_BYTES"] == str(settings.max_output_bytes)
        process = FakeProcess(audio)
        processes.append(process)
        return process

    worker = VibeVoiceWorker(
        settings,
        process_factory=process_factory,
        memory_probe=memory_probe or (lambda: 1000),
    )
    return worker, processes


def test_worker_reuses_one_process_and_bounds_protocol(monkeypatch, settings_factory):
    worker, processes = make_worker(settings_factory)
    results = [
        worker.synthesize("hello", "en-US", "en-Carter_man"),
        worker.synthesize("Guten Morgen", "de-DE", "de-Spk1_woman"),
    ]
    worker.stop()
    assert results == [_WAV, _WAV]
    assert len(processes) == 1
    assert processes[0].request["locale"] == "de-DE"
    assert processes[0].request["voice"] == "de-Spk1_woman"
    assert processes[0].terminated
    assert processes[0].closed


def test_worker_yields_below_reserve_and_does_not_reload_until_recovered(
    settings_factory,
):
    available = [1000]
    worker, processes = make_worker(settings_factory, memory_probe=lambda: available[0])
    assert worker.synthesize("hello", "en-US", "en-Carter_man") == _WAV
    available[0] = 49
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")
    assert len(processes) == 1
    assert processes[0].terminated
    available[0] = 150
    assert worker.synthesize("hello", "en-US", "en-Carter_man") == _WAV
    assert len(processes) == 2
    worker.stop()


def test_idle_worker_is_evicted_when_reserve_is_crossed(settings_factory):
    available = [1000]
    worker, processes = make_worker(settings_factory, memory_probe=lambda: available[0])
    assert worker.synthesize("hello", "en-US", "en-Carter_man") == _WAV
    available[0] = 49
    assert processes[0].terminated_event.wait(timeout=1)
    assert processes[0].terminated
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")
    assert len(processes) == 1
    worker.stop()


def test_worker_refuses_to_start_without_peak_budget(settings_factory):
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=None,
        higher_priority_memory_reserve_bytes=50,
        vibevoice_worker_python="/worker/bin/python",
    )
    worker = VibeVoiceWorker(settings, process_factory=lambda *_args, **_kwargs: pytest.fail())
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")


def test_worker_start_failure_is_safe(settings_factory):
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
        vibevoice_worker_python="/worker/bin/python",
        vibevoice_source_path="/approved/VibeVoice",
        vibevoice_model_path="/models/VibeVoice-Realtime-0.5B",
    )

    def fail_to_start(*_args, **_kwargs):
        raise OSError("private worker start error")

    worker = VibeVoiceWorker(
        settings, process_factory=fail_to_start, memory_probe=lambda: 1000
    )
    with pytest.raises(VibeVoiceError, match="worker unavailable") as error:
        worker.synthesize("hello", "en-US", "en-Carter_man")
    assert "private worker start error" not in str(error.value)


def test_worker_rejects_audio_above_output_limit(settings_factory, monkeypatch, tmp_path):
    oversized_buffer = io.BytesIO()
    with wave.open(oversized_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24_000)
        wav_file.writeframes(b"\x00\x00" * 524_300)
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
        vibevoice_worker_python="/worker/bin/python",
        vibevoice_source_path="/approved/VibeVoice",
        vibevoice_model_path="/models/VibeVoice-Realtime-0.5B",
        max_output_bytes=1_048_576,
    )
    process = FakeProcess(oversized_buffer.getvalue())
    monkeypatch.setattr("app.vibevoice.tempfile.tempdir", str(tmp_path))
    worker = VibeVoiceWorker(
        settings,
        process_factory=lambda *_args, **_kwargs: process,
        memory_probe=lambda: 1000,
    )
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")
    assert process.terminated
    assert list(tmp_path.iterdir()) == []


def test_worker_cleans_up_after_invalid_protocol_response(settings_factory):
    worker, processes = make_worker(settings_factory)

    def bad_flush():
        processes[0].response = "x" * (64 * 1024) + "\n"

    processes  # process is created lazily
    original_factory = worker._process_factory

    def process_factory(*args, **kwargs):
        process = original_factory(*args, **kwargs)
        process.flush = bad_flush
        return process

    worker._process_factory = process_factory
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")
    assert processes[0].terminated
    worker.stop()


def test_worker_times_out_and_terminates_process(settings_factory):
    worker, processes = make_worker(settings_factory, timeout_seconds=1)

    class BlockingProcess(FakeProcess):
        def flush(self):
            pass

        def readline(self):
            threading.Event().wait()
            return ""

    worker._process_factory = lambda *_args, **_kwargs: processes.append(BlockingProcess()) or processes[-1]
    with pytest.raises(VibeVoiceError):
        worker.synthesize("hello", "en-US", "en-Carter_man")
    assert processes[0].terminated


def test_worker_denies_concurrent_admission(settings_factory):
    worker, processes = make_worker(settings_factory)
    assert worker._lock.acquire(blocking=False)
    try:
        with pytest.raises(VibeVoiceError):
            worker.synthesize("hello", "en-US", "en-Carter_man")
    finally:
        worker._lock.release()
        worker.stop()
    assert processes == []


@pytest.mark.skipif(os.name != "posix", reason="uses POSIX output paths")
def test_worker_protocol_returns_only_safe_error_reasons():
    request = {
        "request_id": "a" * 32,
        "text": "private speech marker",
        "locale": "en-US",
        "voice": "en-Carter_man",
        "output_path": "/tmp/vibevoice-request-test/speech.wav",
    }

    class FailedEngine:
        def synthesize(self, _request):
            raise RuntimeError("private speech marker /private/model/path")

    output = io.BytesIO()
    serve(FailedEngine(), io.BytesIO((json.dumps(request) + "\n").encode()), output)
    response = json.loads(output.getvalue())
    assert response == {
        "request_id": "a" * 32,
        "status": "error",
        "reason": "generation_failed",
    }
    assert b"private speech marker" not in output.getvalue()
    assert b"/private/model/path" not in output.getvalue()


@pytest.mark.skipif(os.name != "posix", reason="uses POSIX output paths")
def test_worker_protocol_accepts_german_research_request():
    request = {
        "request_id": "a" * 32,
        "text": "Guten Morgen",
        "locale": "de-DE",
        "voice": "de-Spk1_woman",
        "output_path": "/tmp/vibevoice-request-test/speech.wav",
    }

    class Engine:
        def synthesize(self, _request):
            return None

    output = io.BytesIO()
    serve(Engine(), io.BytesIO((json.dumps(request) + "\n").encode()), output)
    response = json.loads(output.getvalue())
    assert response["status"] == "ok"


def test_worker_entrypoint_requires_research_only(monkeypatch):
    monkeypatch.delenv("TTS_VIBEVOICE_RESEARCH_ONLY", raising=False)
    monkeypatch.setattr(
        "vibevoice_worker.worker.VibeVoiceEngine",
        lambda *_args: pytest.fail("worker initialized without R&D-only mode"),
    )
    assert worker_main() == 2


def test_worker_protocol_rejects_oversized_lines_without_running_engine():
    class Engine:
        def synthesize(self, _request):
            pytest.fail("oversized protocol input reached synthesis")

    output = io.BytesIO()
    serve(Engine(), io.BytesIO(b"x" * (64 * 1024 + 8)), output)
    response = json.loads(output.getvalue().splitlines()[0])
    assert response["status"] == "error"
    assert response["reason"] == "invalid_request"


def test_worker_entrypoint_requires_research_only_mode(monkeypatch, tmp_path):
    source_path = tmp_path / "source"
    model_path = tmp_path / "model"
    source_path.mkdir()
    model_path.mkdir()
    monkeypatch.setenv("TTS_VIBEVOICE_SOURCE_PATH", str(source_path))
    monkeypatch.setenv("TTS_VIBEVOICE_MODEL_PATH", str(model_path))
    monkeypatch.delenv("TTS_VIBEVOICE_RESEARCH_ONLY", raising=False)
    monkeypatch.setattr(
        "vibevoice_worker.worker.VibeVoiceEngine",
        lambda *_args: pytest.fail("worker initialized without research-only mode"),
    )

    assert worker_main() == 2


def test_decoder_only_tokenizer_constructs_only_the_speech_decoder():
    class Module:
        def __init__(self):
            pass

    class Decoder:
        def __init__(self, config):
            self.config = config

    torch_stub = SimpleNamespace(nn=SimpleNamespace(Module=Module))
    config = SimpleNamespace(
        encoder_depths="1-2",
        decoder_depths="3-4",
        vae_dim=8,
        decoder_n_filters=16,
        decoder_ratios=[2, 2],
        conv_norm="none",
        pad_mode="zeros",
        conv_bias=True,
        layernorm_eps=1e-6,
        layernorm_elementwise_affine=True,
        mixer_layer="conv",
        layer_scale_init_value=0,
        disable_last_norm=False,
    )
    tokenizer = _create_decoder_only_tokenizer(torch_stub, config, Decoder)
    assert tokenizer.decoder.config.depths == [3, 4]
    assert tokenizer.decoder.config.dimension == 8
    assert not hasattr(tokenizer, "encoder")
