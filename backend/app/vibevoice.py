from __future__ import annotations

import json
import os
import platform
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import wave
from pathlib import Path
from typing import Any, Callable

from app.config import Settings

_MAX_REQUEST_LINE_BYTES = 64 * 1024
_MAX_RESPONSE_LINE_BYTES = 4 * 1024
_POLL_INTERVAL_SECONDS = 0.05


class VibeVoiceError(RuntimeError):
    """The optional VibeVoice worker cannot safely serve the request."""


class VibeVoiceWorker:
    def __init__(
        self,
        settings: Settings,
        *,
        process_factory: Callable[..., Any] | None = None,
        memory_probe: Callable[[], int] | None = None,
    ) -> None:
        self.settings = settings
        self._process_factory = process_factory or subprocess.Popen
        self._memory_probe = memory_probe or available_memory_bytes
        self._lock = threading.Lock()
        self._process_lock = threading.Lock()
        self._process: Any | None = None
        self._yielded = False
        self._monitor_stop = threading.Event()

    def synthesize(
        self,
        text: str,
        locale: str,
        voice: str,
        cancel_event: threading.Event | None = None,
    ) -> bytes:
        if not self.settings.vibevoice_enabled:
            raise VibeVoiceError("disabled")
        if not self._lock.acquire(blocking=False):
            raise VibeVoiceError("busy")
        try:
            self._check_admission()
            return self._request(text, locale, voice, cancel_event)
        finally:
            self._lock.release()

    def stop(self) -> None:
        self._monitor_stop.set()
        with self._process_lock:
            process = self._process
            self._process = None
            if process is not None:
                self._terminate(process)

    @property
    def status(self) -> str:
        if not self.settings.vibevoice_enabled:
            return "disabled"
        if self._yielded:
            return "yielded"
        with self._process_lock:
            if self._process is not None and self._process.poll() is None:
                return "ready"
        worker_python = self.settings.vibevoice_worker_python
        source_path = self.settings.vibevoice_source_path
        model_path = self.settings.vibevoice_model_path
        if not worker_python or not source_path or not model_path:
            return "unavailable"
        if (
            not Path(worker_python).is_file()
            or not os.access(worker_python, os.X_OK)
            or not Path(source_path).is_dir()
            or not Path(model_path).is_dir()
        ):
            return "unavailable"
        return "not_loaded"

    def _check_admission(self) -> None:
        peak_budget = self.settings.vibevoice_worker_peak_memory_bytes
        reserve = self.settings.higher_priority_memory_reserve_bytes
        if peak_budget is None or reserve is None:
            raise VibeVoiceError("memory budget unavailable")
        try:
            available = self._memory_probe()
        except (OSError, ValueError, subprocess.SubprocessError):
            self.stop()
            raise VibeVoiceError("memory probe unavailable") from None
        if type(available) is not int or available < 0:
            self.stop()
            raise VibeVoiceError("memory probe unavailable")
        if available < reserve:
            self._yielded = True
            self.stop()
            raise VibeVoiceError("memory reserve reached")
        if available < peak_budget + reserve:
            self.stop()
            raise VibeVoiceError("worker memory budget unavailable")
        self._yielded = False

    def _request(
        self,
        text: str,
        locale: str,
        voice: str,
        cancel_event: threading.Event | None,
    ) -> bytes:
        worker_python = self.settings.vibevoice_worker_python
        source_path = self.settings.vibevoice_source_path
        model_path = self.settings.vibevoice_model_path
        if not worker_python or not source_path or not model_path:
            raise VibeVoiceError("worker configuration unavailable")

        deadline = time.monotonic() + min(
            self.settings.vibevoice_worker_timeout_seconds,
            self.settings.request_timeout_seconds,
        )
        with tempfile.TemporaryDirectory(prefix="vibevoice-request-") as temp_dir:
            output_path = Path(temp_dir) / "speech.wav"
            request_id = uuid.uuid4().hex
            request = {
                "request_id": request_id,
                "text": text,
                "locale": locale,
                "voice": voice,
                "output_path": str(output_path),
            }
            message = json.dumps(request, ensure_ascii=True, separators=(",", ":")) + "\n"
            if len(message.encode("utf-8")) > _MAX_REQUEST_LINE_BYTES:
                raise VibeVoiceError("request exceeds worker protocol limit")

            process = self._ensure_process(worker_python, source_path, model_path)
            try:
                if process.poll() is not None or process.stdin is None or process.stdout is None:
                    raise VibeVoiceError("worker unavailable")
                process.stdin.write(message)
                process.stdin.flush()
                response_line = self._read_response(process, deadline, cancel_event)
                response = json.loads(response_line)
                if not isinstance(response, dict) or response.get("request_id") != request_id:
                    raise VibeVoiceError("invalid worker response")
                if response.get("status") != "ok":
                    raise VibeVoiceError("worker synthesis failed")
                return self._read_wav(output_path)
            except VibeVoiceError:
                self.stop()
                raise
            except (OSError, ValueError, TypeError, json.JSONDecodeError, wave.Error):
                self.stop()
                raise VibeVoiceError("worker protocol failed") from None

    def _ensure_process(self, worker_python: str, source_path: str, model_path: str) -> Any:
        with self._process_lock:
            if self._process is not None and self._process.poll() is None:
                return self._process
            self._process = None
            worker_script = Path(__file__).resolve().parents[1] / "vibevoice_worker" / "worker.py"
            environment = os.environ.copy()
            for name in ("TTS_API_KEY", "TTS_API_KEY_FILE", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"):
                environment.pop(name, None)
            environment.update(
                {
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "HF_DATASETS_OFFLINE": "1",
                    "TTS_VIBEVOICE_SOURCE_PATH": source_path,
                    "TTS_VIBEVOICE_MODEL_PATH": model_path,
                    "TTS_MAX_OUTPUT_BYTES": str(
                        min(self.settings.max_output_bytes, self.settings.max_temp_bytes)
                    ),
                }
            )
            try:
                process = self._process_factory(
                    [worker_python, str(worker_script)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                    shell=False,
                    env=environment,
                )
            except OSError:
                raise VibeVoiceError("worker unavailable") from None
            if process.stdin is None or process.stdout is None:
                self._terminate(process)
                raise VibeVoiceError("worker streams unavailable")
            self._process = process
            self._monitor_stop = threading.Event()
            threading.Thread(target=self._monitor_reserve, daemon=True).start()
            return process

    def _monitor_reserve(self) -> None:
        reserve = self.settings.higher_priority_memory_reserve_bytes
        while not self._monitor_stop.wait(_POLL_INTERVAL_SECONDS):
            try:
                available = self._memory_probe()
            except (OSError, ValueError, subprocess.SubprocessError):
                self.stop()
                return
            if type(available) is not int or available < 0 or reserve is None:
                self.stop()
                return
            if available < reserve:
                self._yielded = True
                self.stop()
                return

    def _read_response(
        self,
        process: Any,
        deadline: float,
        cancel_event: threading.Event | None,
    ) -> str:
        result: queue.Queue[str | BaseException] = queue.Queue(maxsize=1)

        def read_line() -> None:
            try:
                result.put(process.stdout.readline())
            except BaseException as exc:
                result.put(exc)

        threading.Thread(target=read_line, daemon=True).start()
        while True:
            if cancel_event is not None and cancel_event.is_set():
                self.stop()
                raise VibeVoiceError("request cancelled")
            if time.monotonic() >= deadline:
                self.stop()
                raise VibeVoiceError("worker timed out")
            try:
                available = self._memory_probe()
            except (OSError, ValueError, subprocess.SubprocessError):
                self.stop()
                raise VibeVoiceError("memory probe unavailable") from None
            reserve = self.settings.higher_priority_memory_reserve_bytes
            if type(available) is not int or available < 0 or reserve is None:
                self.stop()
                raise VibeVoiceError("memory probe unavailable")
            if available < reserve:
                self._yielded = True
                self.stop()
                raise VibeVoiceError("memory reserve reached")
            try:
                line = result.get(timeout=min(_POLL_INTERVAL_SECONDS, max(deadline - time.monotonic(), 0)))
            except queue.Empty:
                continue
            if isinstance(line, BaseException):
                raise VibeVoiceError("worker protocol failed") from None
            if not isinstance(line, str) or not line.endswith("\n"):
                raise VibeVoiceError("invalid worker response")
            if len(line.encode("utf-8")) > _MAX_RESPONSE_LINE_BYTES:
                raise VibeVoiceError("worker response exceeds protocol limit")
            return line

    def _read_wav(self, output_path: Path) -> bytes:
        details = output_path.lstat()
        if not output_path.is_file() or output_path.is_symlink():
            raise VibeVoiceError("worker artifact is invalid")
        artifact_limit = min(
            self.settings.max_output_bytes, self.settings.max_temp_bytes
        )
        if details.st_size <= 0 or details.st_size > artifact_limit:
            raise VibeVoiceError("worker artifact exceeds output limit")
        audio = output_path.read_bytes()
        if len(audio) != details.st_size:
            raise VibeVoiceError("worker artifact changed while reading")
        with wave.open(str(output_path), "rb") as wav_file:
            if wav_file.getnchannels() < 1 or wav_file.getframerate() < 1:
                raise VibeVoiceError("worker artifact is not valid WAV audio")
            wav_file.readframes(wav_file.getnframes())
        return audio

    @staticmethod
    def _terminate(process: Any) -> None:
        try:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass
        except OSError:
            pass
        finally:
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(process, name, None)
                close = getattr(stream, "close", None)
                if close is None:
                    continue
                try:
                    close()
                except OSError:
                    pass


def available_memory_bytes() -> int:
    if platform.system() == "Darwin":
        return _darwin_available_memory()
    try:
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError) as exc:
        raise OSError("available memory is unavailable") from exc
    if available_pages < 0 or page_size <= 0:
        raise OSError("available memory is unavailable")
    return available_pages * page_size


def _darwin_available_memory() -> int:
    try:
        output = subprocess.run(
            ["/usr/bin/vm_stat"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "LC_ALL": "C"},
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise OSError("available memory is unavailable") from exc
    page_size_match = re.search(r"page size of ([\d,]+) bytes", output)
    if page_size_match is None:
        raise ValueError("available memory is unavailable")
    page_size = int(page_size_match.group(1).replace(",", ""))
    if page_size <= 0:
        raise ValueError("available memory is unavailable")
    pages = 0
    for label in ("free", "inactive", "speculative"):
        match = re.search(rf"^Pages {label}:\s*([\d,]+)\.?\s*$", output, re.MULTILINE)
        if match is None:
            raise ValueError("available memory is unavailable")
        pages += int(match.group(1).replace(",", ""))
    return pages * page_size