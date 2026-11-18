import os
import signal
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from app import fish_process
from app.fish_process import FishProcess, FishResourceUnavailable
from app.memory import process_group_resident_memory_bytes


class Process:
    pid = 12345

    def __init__(self):
        self.terminated = threading.Event()

    def poll(self):
        return 0 if self.terminated.is_set() else None


@pytest.fixture
def worker(settings_factory, monkeypatch):
    monkeypatch.setattr(fish_process.os, "name", "posix")
    settings = settings_factory(
        fish_enabled=True, fish_opportunistic=True,
        fish_worker_command=("/approved/launcher",),
        fish_worker_peak_memory_bytes=100, fish_memory_reserve_bytes=50,
    )
    observations = {"available": 1000, "resident": 20, "ready": True, "external": False}
    starts = []

    def start(*args, **kwargs):
        process = Process()
        starts.append((process, args, kwargs))
        return process

    class Engine:
        def is_available(self, timeout_seconds=None):
            return observations["external"] or (
                any(not process.terminated.is_set() for process, *_ in starts)
                and observations["ready"]
            )

    def available():
        value = observations["available"]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(fish_process, "_POLL_SECONDS", 0.01)
    monkeypatch.setattr(fish_process.subprocess, "Popen", start)
    monkeypatch.setattr(fish_process, "available_memory_bytes", available)
    monkeypatch.setattr(
        fish_process, "endpoint_in_use", lambda *_args: observations["external"]
    )
    monkeypatch.setattr(
        fish_process, "process_group_resident_memory_bytes",
        lambda _process: observations["resident"],
    )
    monkeypatch.setattr(
        fish_process, "terminate_owned_group",
        lambda process: process.terminated.set(),
    )
    managed = FishProcess(settings, Engine())
    yield managed, observations, starts
    managed.close()


def run(managed, callback=lambda: b"audio", cancel=None, seconds=2):
    return managed.run(callback, deadline=time.monotonic() + seconds, cancel_event=cancel)


@pytest.mark.parametrize("available", [149, -1, None, OSError("probe unavailable")])
def test_invalid_or_insufficient_start_headroom_never_launches(worker, available):
    managed, observations, starts = worker
    observations["available"] = available
    with pytest.raises(FishResourceUnavailable):
        run(managed)
    assert starts == []


def test_worker_is_lazy_low_priority_offline_and_reused(worker, monkeypatch):
    managed, _observations, starts = worker
    monkeypatch.setenv("TTS_API_KEY", "synthetic-private-key")
    assert not starts
    assert run(managed) == b"audio"
    assert run(managed) == b"audio"
    assert len(starts) == 1
    _process, args, kwargs = starts[0]
    assert args[0][:3] == ["/usr/bin/nice", "-n", "19"]
    assert kwargs["start_new_session"] is True
    assert kwargs["shell"] is False
    assert "TTS_API_KEY" not in kwargs["env"]
    assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"


def test_exact_budget_and_reserve_boundaries_are_admitted(worker, monkeypatch):
    managed, observations, starts = worker
    observations["available"] = 150
    observations["resident"] = 100
    assert run(managed) == b"audio"
    observations["available"] = 50
    assert run(managed) == b"audio"
    observations["available"] = 49
    with pytest.raises(FishResourceUnavailable, match="reserve"):
        run(managed)
    assert starts[0][0].terminated.is_set()
    observations["available"] = 150
    monkeypatch.setattr(managed, "_restart_after", time.monotonic() - 1)
    assert run(managed) == b"audio"
    assert len(starts) == 2


@pytest.mark.parametrize("available", [74, 75])
def test_opt_in_startup_allowance_retains_runtime_reserve_and_ceiling(worker, available):
    managed, observations, starts = worker
    managed.settings = replace(managed.settings, fish_startup_memory_bytes=25)
    observations["available"] = available
    if available < 75:
        with pytest.raises(FishResourceUnavailable, match="reserve"):
            run(managed)
        assert not starts
        return
    assert run(managed) == b"audio"
    observations.update(available=50, resident=100)
    assert run(managed) == b"audio"
    observations["resident"] = 101
    with pytest.raises(FishResourceUnavailable, match="budget"):
        run(managed)
    assert starts[0][0].terminated.is_set()


def test_aggressive_startup_still_yields_when_reserve_is_breached(worker):
    managed, observations, starts = worker
    managed.settings = replace(managed.settings, fish_startup_memory_bytes=25)
    observations["available"] = 75
    assert run(managed) == b"audio"
    observations["available"] = 49
    with pytest.raises(FishResourceUnavailable, match="reserve"):
        run(managed)
    assert starts[0][0].terminated.is_set()


@pytest.mark.parametrize("phase", ["loading", "active", "idle"])
@pytest.mark.parametrize("failure", ["reserve", "resident", "probe"])
def test_pressure_in_every_phase_stops_owned_worker_and_cools_down(worker, phase, failure):
    managed, observations, starts = worker
    if phase == "loading":
        observations["ready"] = False

    def breach():
        if failure == "reserve":
            observations["available"] = 49
        elif failure == "resident":
            observations["resident"] = 101
        else:
            observations["available"] = OSError("unreadable")

    with ThreadPoolExecutor(max_workers=1) as pool:
        if phase == "idle":
            run(managed)
            breach()
        else:
            def callback():
                breach()
                assert starts[0][0].terminated.wait(1)
                return b"discard partial audio"
            future = pool.submit(run, managed, callback)
            if phase == "loading":
                end = time.monotonic() + 1
                while not starts and time.monotonic() < end:
                    time.sleep(0.005)
                assert starts
                breach()
        assert starts[0][0].terminated.wait(1)
        if phase != "idle":
            with pytest.raises(FishResourceUnavailable):
                future.result(timeout=2)
    observations["available"] = 1000
    observations["resident"] = 20
    with pytest.raises(FishResourceUnavailable, match="cooldown"):
        run(managed)
    assert len(starts) == 1


def test_busy_neural_request_does_not_wait(worker):
    managed, _observations, starts = worker
    active, release = threading.Event(), threading.Event()

    def callback():
        active.set()
        assert release.wait(1)
        return b"audio"

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run, managed, callback)
        assert active.wait(1)
        try:
            with pytest.raises(FishResourceUnavailable, match="busy"):
                run(managed)
            assert not starts[0][0].terminated.is_set()
        finally:
            release.set()
        assert future.result(timeout=2) == b"audio"


@pytest.mark.parametrize("cause", ["cancel", "deadline", "idle", "shutdown"])
def test_abort_idle_and_shutdown_release_owned_worker(worker, monkeypatch, cause):
    managed, _observations, starts = worker
    cancel = threading.Event()
    if cause in {"idle", "shutdown"}:
        run(managed)
        if cause == "idle":
            monkeypatch.setattr(managed, "_last_used", time.monotonic() - 31)
        else:
            managed.close()
        assert starts[0][0].terminated.wait(1)
    else:
        def callback():
            if cause == "cancel":
                cancel.set()
            assert starts[0][0].terminated.wait(1)
            return b"discard"
        with pytest.raises(FishResourceUnavailable):
            run(managed, callback, cancel, seconds=0.1 if cause == "deadline" else 2)
        assert starts[0][0].terminated.is_set()


def test_external_listener_is_never_adopted_or_terminated(worker):
    managed, observations, starts = worker
    observations["external"] = True
    with pytest.raises(FishResourceUnavailable, match="external"):
        run(managed)
    assert not starts


def test_unverified_termination_quarantines_worker(worker, monkeypatch):
    managed, observations, starts = worker
    run(managed)

    def cannot_stop(_process):
        raise OSError("cannot verify cleanup")

    monkeypatch.setattr(fish_process, "terminate_owned_group", cannot_stop)
    observations["available"] = 49
    with pytest.raises(FishResourceUnavailable):
        run(managed)
    observations["available"] = 1000
    monkeypatch.setattr(managed, "_restart_after", 0)
    with pytest.raises(FishResourceUnavailable, match="cleanup"):
        run(managed)
    assert len(starts) == 1


@pytest.mark.skipif(os.name != "posix", reason="owned POSIX session cleanup")
@pytest.mark.parametrize("ignore_term", [False, True])
def test_real_owned_session_is_terminated_and_reaped(ignore_term):
    script = (
        "import signal,time;"
        f"signal.signal(signal.SIGTERM, {'signal.SIG_IGN' if ignore_term else 'signal.SIG_DFL'});"
        "print('ready',flush=True);time.sleep(10)"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script], start_new_session=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    assert process.stdout is not None
    try:
        assert process.stdout.readline() == b"ready\n"
        fish_process.terminate_owned_group(process)
        assert process.poll() is not None
        with pytest.raises(ProcessLookupError):
            os.killpg(process.pid, 0)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)
        process.stdout.close()


def test_worker_budget_counts_group_members_but_not_unrelated_processes(monkeypatch):
    monkeypatch.setattr(
        "app.memory.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [], 0, "98765 9999\n12345 20\n12345 30\n", ""
        ),
    )
    assert process_group_resident_memory_bytes(Process()) == 50 * 1024


def test_existing_listener_is_rejected_without_waiting_for_http_health():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
        assert fish_process.endpoint_in_use(origin, 0.1)


def test_uncertain_endpoint_probe_does_not_authorize_worker_start(monkeypatch):
    def timeout(*_args, **_kwargs):
        raise TimeoutError
    monkeypatch.setattr(fish_process.socket, "create_connection", timeout)
    with pytest.raises(FishResourceUnavailable, match="endpoint_unverified"):
        fish_process.endpoint_in_use("http://127.0.0.1:8000", 0.1)
