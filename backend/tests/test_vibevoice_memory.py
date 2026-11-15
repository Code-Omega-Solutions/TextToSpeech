import json
import threading

import pytest

from app.vibevoice import VibeVoiceError, VibeVoiceWorker


class WaitingProcess:
    def __init__(self):
        self.request = None
        self.returncode = None
        self.terminated = False
        self.released = threading.Event()
        self.stdin = self
        self.stdout = self

    def write(self, message):
        self.request = json.loads(message)

    def flush(self):
        pass

    def readline(self):
        self.released.wait()
        return ""

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15
        self.released.set()

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.returncode = -9
        self.released.set()


def test_reserve_crossing_during_generation_evicts_worker(settings_factory):
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
        vibevoice_worker_timeout_seconds=5,
        vibevoice_worker_python="/worker/bin/python",
        vibevoice_source_path="/approved/VibeVoice",
        vibevoice_model_path="/models/VibeVoice-Realtime-0.5B",
    )
    process = WaitingProcess()
    observations = iter([1000, 49])
    worker = VibeVoiceWorker(
        settings,
        process_factory=lambda *_args, **_kwargs: process,
        memory_probe=lambda: next(observations),
    )

    with pytest.raises(VibeVoiceError, match="memory reserve reached"):
        worker.synthesize("hello", "en-US", "en-Carter_man")

    assert process.terminated
    assert worker._yielded is True
    worker.stop()
