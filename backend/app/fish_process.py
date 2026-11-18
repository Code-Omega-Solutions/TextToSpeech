from __future__ import annotations

import logging
import os
import signal
import socket
import subprocess
import threading
import time
from collections.abc import Callable
from http.client import HTTPException
from typing import NoReturn, TypeVar
from urllib.parse import urlsplit

from app.config import Settings
from app.fish_speech import FishSpeechEngine
from app.memory import available_memory_bytes, process_group_resident_memory_bytes

_POLL_SECONDS = 0.25
_T = TypeVar("_T")
logger = logging.getLogger(__name__)


class FishResourceUnavailable(RuntimeError):
    """A safe reason code for yielding optional neural synthesis."""


def endpoint_in_use(origin: str | None, timeout: float) -> bool:
    if origin is None:
        raise FishResourceUnavailable("fish_unavailable")
    parsed = urlsplit(origin)
    if parsed.hostname is None:
        raise FishResourceUnavailable("fish_unavailable")
    try:
        with socket.create_connection(
            (parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)),
            timeout=timeout,
        ):
            return True
    except ConnectionRefusedError:
        return False
    except OSError:
        raise FishResourceUnavailable("fish_endpoint_unverified") from None


def terminate_owned_group(process: subprocess.Popen[bytes]) -> None:
    # start_new_session makes this child's PID its exclusively owned group ID.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait(timeout=0.5)
        return
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        process.wait(timeout=0.5)
        return
    process.wait(timeout=0.5)
    end = time.monotonic() + 0.5
    while True:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return
        if time.monotonic() >= end:
            raise OSError("owned worker group termination is unverified")
        time.sleep(0.01)


class FishProcess:
    def __init__(self, settings: Settings, engine: FishSpeechEngine):
        self.settings = settings
        self.engine = engine
        self._request_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._process: subprocess.Popen[bytes] | None = None
        self._monitor: threading.Thread | None = None
        self._preload_thread: threading.Thread | None = None
        self._closed = threading.Event()
        self._last_used = 0.0
        self._restart_after = 0.0
        self._reason = "fish_unavailable"
        self._cleanup_failed = False
        self._active_deadline: float | None = None
        self._cancel_event: threading.Event | None = None

    def start_preload(self) -> None:
        if not self.settings.fish_preload:
            return
        with self._state_lock:
            if self._closed.is_set() or self._preload_thread is not None:
                return
            # Reserve the neural slot before serving requests, without claiming native capacity.
            if not self._request_lock.acquire(blocking=False):
                logger.info("fish preload skipped reason=fish_busy")
                return
            thread = threading.Thread(target=self._preload, name="fish-preload", daemon=True)
            try:
                thread.start()
            except RuntimeError:
                self._request_lock.release()
                self._stop("fish_preload_start_failed")
                logger.warning("fish preload failed reason=fish_preload_start_failed")
            else:
                self._preload_thread = thread

    def _preload(self) -> None:
        started = time.monotonic()
        logger.info("fish preload started")
        try:
            self._run_locked(
                lambda: None,
                deadline=started + self.settings.fish_request_timeout_seconds,
                cancel_event=None,
                preload=True,
            )
        except FishResourceUnavailable as exc:
            if str(exc) == "fish_shutdown":
                logger.info("fish preload cancelled reason=fish_shutdown")
            else:
                logger.warning("fish preload failed reason=%s", exc)
        except (HTTPException, OSError, RuntimeError, ValueError):
            logger.warning("fish preload failed reason=fish_preload_aborted")
        else:
            logger.info("fish preload ready duration_ms=%d", round((time.monotonic() - started) * 1000))

    def run(
        self,
        callback: Callable[[], _T],
        *,
        deadline: float,
        cancel_event: threading.Event | None = None,
    ) -> _T:
        if not self._request_lock.acquire(blocking=False):
            raise FishResourceUnavailable("fish_busy")
        return self._run_locked(callback, deadline=deadline, cancel_event=cancel_event)

    def _run_locked(
        self,
        callback: Callable[[], _T],
        *,
        deadline: float,
        cancel_event: threading.Event | None,
        preload: bool = False,
    ) -> _T:
        try:
            with self._state_lock:
                self._check_request(deadline, cancel_event)
                self._active_deadline = deadline
                self._cancel_event = cancel_event
                self._ensure_started(deadline)
            while True:
                with self._state_lock:
                    self._check_request(deadline, cancel_event)
                    self._check_resources()
                    if self._process is None:
                        raise FishResourceUnavailable(self._reason)
                if self.engine.is_available(timeout_seconds=min(0.25, deadline - time.monotonic())):
                    with self._state_lock:
                        self._check_request(deadline, cancel_event)
                        if self._process is None:
                            raise FishResourceUnavailable(self._reason)
                    break
                self._closed.wait(min(_POLL_SECONDS, max(0, deadline - time.monotonic())))
            result = callback()
            with self._state_lock:
                self._check_request(deadline, cancel_event)
                self._check_resources()
                if self._process is None:
                    raise FishResourceUnavailable(self._reason)
            return result
        except Exception as exc:
            # Keep the original error for the caller, including a monitor's stop reason.
            with self._state_lock:
                if not (self._closed.is_set() or self._cleanup_failed) and (
                    self._process is not None or (preload and time.monotonic() >= self._restart_after)
                ):
                    reason = "fish_request_aborted"
                    if preload:
                        reason = (
                            str(exc) if isinstance(exc, FishResourceUnavailable)
                            else "fish_preload_aborted"
                        )
                    self._stop(reason)
            raise
        finally:
            with self._state_lock:
                self._last_used = time.monotonic()
                self._active_deadline = None
                self._cancel_event = None
            self._request_lock.release()

    def close(self) -> None:
        self._closed.set()
        with self._state_lock:
            self._stop("fish_shutdown")
        for thread, role in ((self._preload_thread, "preload"), (self._monitor, "monitor")):
            if thread is not None:
                thread.join(timeout=8)
                if thread.is_alive():
                    logger.error("fish worker %s shutdown is unverified", role)

    def _check_request(self, deadline: float, cancel_event: threading.Event | None) -> None:
        if self._closed.is_set():
            raise FishResourceUnavailable("fish_shutdown")
        if cancel_event is not None and cancel_event.is_set():
            raise FishResourceUnavailable("fish_cancelled")
        if time.monotonic() >= deadline:
            raise FishResourceUnavailable("fish_timeout")
        if self._cleanup_failed:
            raise FishResourceUnavailable("fish_cleanup_failed")

    def _ensure_started(self, deadline: float) -> None:
        if self._process is not None:
            self._check_resources()
            if self._process is None:
                raise FishResourceUnavailable(self._reason)
            return
        if time.monotonic() < self._restart_after:
            raise FishResourceUnavailable("fish_cooldown")
        if not self.settings.fish_enabled or not self.settings.fish_worker_command:
            raise FishResourceUnavailable("fish_unavailable")
        if os.name != "posix":
            raise FishResourceUnavailable("fish_platform_unqualified")
        self._check_resources(starting=True)
        if endpoint_in_use(
            self.settings.fish_server_url, min(0.25, max(0.001, deadline - time.monotonic()))
        ):
            raise FishResourceUnavailable("fish_external_service")
        self._check_request(deadline, self._cancel_event)
        environment = {
            key: value for key, value in os.environ.items()
            if key not in {
                "TTS_API_KEY", "TTS_API_KEY_FILE", "TTS_OPERATOR_TOKEN",
                "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN",
            }
        }
        environment.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        try:
            self._process = subprocess.Popen(
                ["/usr/bin/nice", "-n", "19", *self.settings.fish_worker_command],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, shell=False, start_new_session=True,
                env=environment,
            )
        except OSError:
            self._deny("fish_start_failed")
        self._last_used = time.monotonic()
        if self._monitor is None:
            monitor = threading.Thread(target=self._watch, daemon=True)
            monitor.start()
            self._monitor = monitor

    def _check_resources(self, *, starting: bool = False) -> None:
        try:
            available = available_memory_bytes()
            resident = (
                process_group_resident_memory_bytes(self._process)
                if self._process is not None else 0
            )
            if type(available) is not int or available < 0:
                raise ValueError("invalid available memory")
            if type(resident) is not int or resident < 0:
                raise ValueError("invalid worker memory")
        except (OSError, ValueError, subprocess.SubprocessError):
            self._deny("fish_memory_unreadable")
        required = self.settings.fish_memory_reserve_bytes
        if starting:
            startup = self.settings.fish_startup_memory_bytes
            required += (
                self.settings.fish_worker_peak_memory_bytes if startup is None else startup
            )
        if available < required:
            self._deny("fish_memory_reserve")
        if resident > self.settings.fish_worker_peak_memory_bytes:
            self._deny("fish_worker_budget")
        if self._process is not None and self._process.poll() is not None:
            self._deny("fish_worker_exited")

    def _deny(self, reason: str) -> NoReturn:
        self._stop(reason)
        raise FishResourceUnavailable(self._reason)

    def _stop(self, reason: str) -> None:
        self._reason = reason
        self._restart_after = time.monotonic() + self.settings.fish_cooldown_seconds
        if self._process is None:
            return
        try:
            terminate_owned_group(self._process)
        except (OSError, subprocess.SubprocessError):
            self._cleanup_failed = True
            self._reason = "fish_cleanup_failed"
            logger.error("fish worker termination is unverified; neural restart disabled")
        else:
            self._process = None
            logger.info("fish worker stopped reason=%s", reason)

    def _watch(self) -> None:
        while not self._closed.wait(_POLL_SECONDS):
            with self._state_lock:
                if self._process is None or self._cleanup_failed:
                    continue
                try:
                    self._check_resources()
                    if self._active_deadline is not None:
                        self._check_request(self._active_deadline, self._cancel_event)
                    elif not self.settings.fish_preload and (
                        time.monotonic() - self._last_used >= self.settings.fish_idle_timeout_seconds
                    ):
                        self._stop("fish_idle")
                except FishResourceUnavailable as exc:
                    if self._process is not None and not self._cleanup_failed:
                        self._stop(str(exc))
