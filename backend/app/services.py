from __future__ import annotations

import logging
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path

from app.config import Settings
from app.engines import EngineDescriptor, EngineRegistration, EngineRegistry
from app.fish_process import FishProcess, FishResourceUnavailable
from app.fish_speech import (
    FishSpeechAudioTooLarge,
    FishSpeechEngine,
    FishSpeechError,
    FishSpeechTimeout,
    load_qualified_reference_catalog,
)
from app.voices import (
    VoiceInventoryError,
    VoiceInventoryTimeout,
    available_voices,
    configured_voices,
    required_voices,
    resolve_voice,
    voice_available,
)
_SENTENCE_PAUSE_SECONDS = 0.4
_PARAGRAPH_PAUSE_SECONDS = 1.2
_MAX_SPEECH_SEGMENTS = 100
_PARAGRAPH_BREAK = re.compile(r"(?:\r\n|\r|\n)[ \t]*(?:(?:\r\n|\r|\n)[ \t]*)+")
_SENTENCE_END = re.compile(r"[.!?]+(?:[\"'’”)\]]*)")
_SENTENCE_CLOSERS = "\"'’”)]"
logger = logging.getLogger(__name__)
_ABBREVIATIONS = {
    "d.h",
    "dr",
    "e.g",
    "i.e",
    "mr",
    "mrs",
    "ms",
    "prof",
    "sr",
    "jr",
    "st",
    "u.a",
    "u.s",
    "u.k",
    "z.b",
}


class SynthesisUnavailable(Exception):
    """A required host executable or voice is unavailable."""


class SynthesisCapacityExceeded(Exception):
    """All configured synthesis permits are occupied."""


class SynthesisTimeout(Exception):
    """The complete speech operation exceeded its deadline."""


class AudioTooLarge(Exception):
    """Generated audio exceeds the configured response limit."""


class SynthesisFailure(Exception):
    """A speech or conversion process failed."""


class SpeechSegmentLimitExceeded(Exception):
    """The input contains more speech segments than can be synthesized safely."""


@dataclass(frozen=True)
class SynthesisResult:
    audio: bytes
    media_type: str
    filename: str
    actual_backend: str = "macos-say"
    fallback: bool = False
    failure_reason: str | None = None


def available_codecs(ffmpeg_path: str, timeout: float = 5.0) -> set[str]:
    try:
        result = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SynthesisUnavailable from exc
    if result.returncode != 0:
        raise SynthesisUnavailable
    codecs = set()
    for line in f"{result.stdout}\n{result.stderr}".splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0].startswith("A"):
            codecs.add(fields[1])
    return codecs


def _is_sentence_ending(text: str, match: re.Match[str]) -> bool:
    if match.end() == len(text) or "!" in match.group() or "?" in match.group():
        return True

    punctuation = match.group().rstrip(_SENTENCE_CLOSERS)
    prefix = text[: match.start()] + punctuation
    word = re.search(r"([^\W\d_]+(?:\s*\.\s*[^\W\d_]+)*)\s*\.$", prefix)
    if word is None:
        return True
    abbreviation = re.sub(r"\s+", "", word.group(1)).casefold()
    return abbreviation not in _ABBREVIATIONS


def _split_sentences(paragraph: str) -> list[tuple[str, bool]]:
    sentences: list[tuple[str, bool]] = []
    start = 0
    for match in _SENTENCE_END.finditer(paragraph):
        if match.end() < len(paragraph) and not paragraph[match.end()].isspace():
            continue
        if not _is_sentence_ending(paragraph, match):
            continue

        sentence = paragraph[start : match.end()].strip()
        if sentence:
            sentences.append((sentence, True))
            start = match.end()

    remainder = paragraph[start:].strip()
    if remainder:
        sentences.append((remainder, False))
    return sentences


def _speech_segments(text: str) -> list[tuple[str, float]]:
    paragraphs = [part.strip() for part in _PARAGRAPH_BREAK.split(text) if part.strip()]
    segments: list[tuple[str, float]] = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        sentences = _split_sentences(paragraph)
        for sentence_index, (sentence, ends_sentence) in enumerate(sentences):
            is_last_sentence = sentence_index == len(sentences) - 1
            if not is_last_sentence:
                pause = _SENTENCE_PAUSE_SECONDS
            elif paragraph_index < len(paragraphs) - 1:
                pause = _PARAGRAPH_PAUSE_SECONDS
            elif ends_sentence:
                pause = _SENTENCE_PAUSE_SECONDS
            else:
                pause = 0
            segments.append((sentence, pause))

    if len(segments) > _MAX_SPEECH_SEGMENTS:
        raise SpeechSegmentLimitExceeded
    return segments


class SpeechService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._permits = threading.BoundedSemaphore(settings.max_concurrent_synthesis)
        self.fish_speech = FishSpeechEngine(settings)
        self.fish_process = FishProcess(settings, self.fish_speech)
        self.fish_reference_voices = load_qualified_reference_catalog(
            settings.fish_reference_manifest, settings.fish_reference_root
        )
        self.engine_registry = EngineRegistry(
            (
                EngineRegistration(
                    descriptor=EngineDescriptor(
                        "macos-say",
                        ("de-DE", "en-US", "en-GB"),
                        {
                            "de-DE": (settings.voice_de_de,),
                            "en-US": (settings.voice_en_us,),
                            "en-GB": (settings.voice_en_gb,),
                        },
                    ),
                    enabled=lambda: True,
                    ready=self._macos_engine_ready,
                    synthesize=self._synthesize_macos_engine,
                    voice_catalog=self._macos_voice_catalog,
                ),
                EngineRegistration(
                    descriptor=EngineDescriptor(
                        "fish-speech", ("de-DE", "en-US"), self.fish_reference_voices
                    ),
                    enabled=lambda: settings.fish_enabled,
                    ready=self._fish_engine_ready,
                    synthesize=self._synthesize_fish,
                    voice_catalog=lambda: self.fish_reference_voices,
                ),
            )
        )

    def try_acquire(self) -> bool:
        return self._permits.acquire(blocking=False)

    def release_permit(self) -> None:
        self._permits.release()

    def start(self) -> None:
        if not self.settings.fish_preload:
            return
        if not self.fish_reference_voices:
            logger.warning("fish preload skipped reason=fish_references_unavailable")
            return
        self.fish_process.start_preload()

    def close(self) -> None:
        self.fish_process.close()

    def _fish_engine_ready(self) -> bool:
        # Managed engine discovery checks eligibility, not worker health.
        if not self.fish_reference_voices:
            return False
        if self.settings.fish_worker_command is not None:
            return self.settings.fish_enabled
        return self.fish_speech.is_available()

    def synthesize(
        self,
        text: str,
        language: str,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None = None,
        backend: str | None = None,
        voice: str | None = None,
    ) -> SynthesisResult:
        if not self.try_acquire():
            raise SynthesisCapacityExceeded
        try:
            return self.synthesize_reserved(
                text, language, speed, response_format, cancel_event, backend, voice
            )
        finally:
            self.release_permit()

    def synthesize_reserved(
        self,
        text: str,
        language: str,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None = None,
        backend: str | None = None,
        voice: str | None = None,
        deadline: float | None = None,
    ) -> SynthesisResult:
        selected_backend = backend or self.settings.default_backend
        if (
            voice is None
            and selected_backend == self.settings.default_backend == "fish-speech"
            and self.settings.fish_references_approved
        ):
            voice = {"de-DE": "de-female", "en-US": "en-female"}.get(language)
        if self.settings.fish_opportunistic and selected_backend in {"fish-speech", "vibevoice"}:
            return self._synthesize_opportunistic(
                text,
                language,
                speed,
                response_format,
                cancel_event,
                selected_backend,
                voice,
                deadline=deadline,
            )
        if selected_backend == "vibevoice":
            raise SynthesisUnavailable
        engine = self.engine_registry.resolve(selected_backend)
        if engine is None or not engine.enabled():
            raise SynthesisUnavailable
        if (
            selected_backend == "fish-speech"
            and self.settings.fish_references_approved
            and (
                not self.fish_reference_voices
                or voice not in self.fish_reference_voices.get(language, ())
            )
        ):
            raise SynthesisUnavailable
        return engine.synthesize(
            text, language, speed, response_format, cancel_event, voice
        )

    def _synthesize_opportunistic(
        self,
        text: str,
        language: str,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None,
        selected_backend: str,
        voice: str | None,
        *,
        deadline: float | None = None,
    ) -> SynthesisResult:
        deadline = deadline or time.monotonic() + self.settings.request_timeout_seconds
        if cancel_event is not None and cancel_event.is_set():
            raise SynthesisFailure
        reason = "fish_unavailable"
        if (
            selected_backend == "fish-speech"
            and self.settings.fish_enabled
            and language in {"de-DE", "en-US"}
            and (
                not self.settings.fish_references_approved
                or (
                    self.fish_reference_voices
                    and voice in self.fish_reference_voices.get(language, ())
                )
            )
        ):
            native_reserve = min(10, self.settings.request_timeout_seconds / 2)
            fish_deadline = min(
                deadline - native_reserve,
                time.monotonic() + self.settings.fish_request_timeout_seconds,
            )
            try:
                return self.fish_process.run(
                    lambda: self._synthesize_fish(
                        text, language, speed, response_format, cancel_event, voice,
                        deadline=fish_deadline,
                    ),
                    deadline=fish_deadline,
                    cancel_event=cancel_event,
                )
            except FishResourceUnavailable as exc:
                reason = str(exc)
            except SynthesisUnavailable:
                reason = "fish_unavailable"
            except SynthesisTimeout:
                reason = "fish_timeout"
        if cancel_event is not None and cancel_event.is_set():
            raise SynthesisFailure
        self._remaining(deadline)
        logger.info("speech fallback actual_backend=macos-say locale=%s reason=%s", language, reason)
        result = self._synthesize_macos(
            text, language, speed, response_format, cancel_event, None, deadline=deadline
        )
        return replace(result, fallback=True, failure_reason=reason)

    def _synthesize_macos_engine(
        self,
        text: str,
        language: str,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None,
        voice: str | None,
    ) -> SynthesisResult:
        return self._synthesize_macos(
            text, language, speed, response_format, cancel_event, voice
        )

    def _macos_engine_ready(self) -> bool:
        if shutil.which(self.settings.say_path) is None or shutil.which(self.settings.ffmpeg_path) is None:
            return False
        try:
            if not {"libmp3lame", "pcm_s16le"}.issubset(
                available_codecs(self.settings.ffmpeg_path, timeout=2)
            ):
                return False
            voices = available_voices(self.settings.say_path, timeout=2)
        except (SynthesisUnavailable, VoiceInventoryError, VoiceInventoryTimeout):
            return False
        needed = required_voices(self.settings)
        return all(voice_available(needed[locale], voices) for locale in ("de-DE", "en-US"))

    def _macos_voice_catalog(self) -> dict[str, tuple[str, ...]]:
        try:
            available = available_voices(self.settings.say_path, timeout=2)
        except (VoiceInventoryError, VoiceInventoryTimeout):
            return {}
        return {
            language: (configured.split(maxsplit=1)[0],)
            for language, configured in configured_voices(self.settings).items()
            if voice_available(configured, available)
        }

    def _synthesize_fish(
        self,
        text: str,
        _language: str,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None,
        voice: str | None,
        *,
        deadline: float | None = None,
    ) -> SynthesisResult:
        if deadline is None:
            deadline = time.monotonic() + self.settings.request_timeout_seconds
        try:
            wav_audio = self.fish_speech.synthesize_wav(
                text,
                voice,
                cancel_event,
                timeout_seconds=min(
                    self.settings.fish_request_timeout_seconds,
                    self._remaining(deadline),
                ),
            )
        except FishSpeechAudioTooLarge as exc:
            raise AudioTooLarge from exc
        except FishSpeechTimeout as exc:
            raise SynthesisTimeout from exc
        except FishSpeechError as exc:
            if cancel_event is not None and cancel_event.is_set():
                raise SynthesisFailure from exc
            raise SynthesisUnavailable from None
        return self._transcode_wav(
            wav_audio,
            speed,
            response_format,
            cancel_event,
            actual_backend="fish-speech",
            deadline=deadline,
        )

    def _transcode_wav(
        self,
        wav_audio: bytes,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None,
        *,
        actual_backend: str,
        deadline: float | None = None,
    ) -> SynthesisResult:
        if response_format == "wav" and speed == 1:
            if len(wav_audio) > min(
                self.settings.max_output_bytes, self.settings.max_temp_bytes
            ):
                raise AudioTooLarge
            return SynthesisResult(
                wav_audio, "audio/wav", "speech.wav", actual_backend=actual_backend
            )

        if shutil.which(self.settings.ffmpeg_path) is None:
            raise SynthesisUnavailable
        deadline = deadline or time.monotonic() + self.settings.request_timeout_seconds
        with tempfile.TemporaryDirectory(prefix=f"{actual_backend}-audio-") as temp_dir:
            directory = Path(temp_dir)
            input_path = directory / "input.wav"
            output_path = directory / f"speech.{response_format}"
            if len(wav_audio) > self.settings.max_temp_bytes:
                raise SynthesisFailure
            input_path.write_bytes(wav_audio)
            self._check_temp_budget(directory)
            arguments = [
                self.settings.ffmpeg_path,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(input_path),
            ]
            if speed != 1:
                arguments.extend(["-filter:a", f"atempo={speed:g}"])
            if response_format == "mp3":
                arguments.extend(
                    [
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        "128k",
                        "-minrate",
                        "128k",
                        "-maxrate",
                        "128k",
                        "-bufsize",
                        "256k",
                    ]
                )
            else:
                arguments.extend(["-c:a", "pcm_s16le", "-ac", "1", "-ar", "44100"])
            arguments.extend(
                ["-fs", str(self.settings.max_output_bytes + 1), str(output_path)]
            )
            self._run(arguments, deadline, directory, cancel_event)
            self._check_temp_budget(directory)
            try:
                if output_path.stat().st_size > self.settings.max_output_bytes:
                    raise AudioTooLarge
                audio = output_path.read_bytes()
            except FileNotFoundError as exc:
                raise SynthesisFailure from exc
            if len(audio) > self.settings.max_output_bytes:
                raise AudioTooLarge

        if response_format == "mp3":
            return SynthesisResult(
                audio, "audio/mpeg", "speech.mp3", actual_backend=actual_backend
            )
        return SynthesisResult(
            audio, "audio/wav", "speech.wav", actual_backend=actual_backend
        )

    def _synthesize_macos(
        self,
        text: str,
        language: str,
        speed: float,
        response_format: str,
        cancel_event: threading.Event | None = None,
        requested_voice: str | None = None,
        *,
        deadline: float | None = None,
    ) -> SynthesisResult:
        settings = self.settings
        if deadline is None:
            deadline = time.monotonic() + settings.request_timeout_seconds
        segments = _speech_segments(text)

        try:
            voices = available_voices(settings.say_path, timeout=self._remaining(deadline))
            voice = resolve_voice(language, settings, voices, requested_voice)
        except VoiceInventoryTimeout as exc:
            raise SynthesisTimeout from exc
        except (VoiceInventoryError, LookupError) as exc:
            raise SynthesisUnavailable from exc

        if shutil.which(settings.ffmpeg_path) is None:
            raise SynthesisUnavailable

        rate = round(settings.base_rate_wpm * speed)
        with tempfile.TemporaryDirectory(prefix="macos-speech-") as temp_dir:
            directory = Path(temp_dir)
            raw_paths = []
            pauses = []
            for index, (segment_text, pause) in enumerate(segments):
                input_path = directory / f"input-{index}.txt"
                raw_path = directory / f"speech-{index}.aiff"
                encoded_segment = segment_text.encode("utf-8")
                if self._temporary_size(directory) + len(encoded_segment) > settings.max_temp_bytes:
                    raise SynthesisFailure
                input_path.write_bytes(encoded_segment)
                self._check_temp_budget(directory)
                self._run(
                    [
                        settings.say_path,
                        "-v",
                        voice,
                        "-r",
                        str(rate),
                        "-f",
                        str(input_path),
                        "-o",
                        str(raw_path),
                    ],
                    deadline,
                    directory,
                    cancel_event,
                )
                self._check_temp_budget(directory)
                raw_paths.append(raw_path)
                pauses.append(pause)

            output_path = directory / f"speech.{response_format}"
            ffmpeg_args = [
                settings.ffmpeg_path,
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
            ]
            if len(raw_paths) == 1 and pauses[0] == 0:
                ffmpeg_args.extend(["-i", str(raw_paths[0])])
            else:
                filter_graph = []
                concat_inputs = []
                input_index = 0
                for raw_path, pause in zip(raw_paths, pauses):
                    ffmpeg_args.extend(["-i", str(raw_path)])
                    filter_graph.append(
                        f"[{input_index}:a]aresample=44100,"
                        f"aformat=sample_fmts=s16:channel_layouts=mono,"
                        f"asetpts=PTS-STARTPTS[a{input_index}]"
                    )
                    concat_inputs.append(f"[a{input_index}]")
                    input_index += 1

                    if pause > 0:
                        ffmpeg_args.extend(
                            [
                                "-f",
                                "lavfi",
                                "-t",
                                f"{pause:.1f}",
                                "-i",
                                "anullsrc=r=44100:cl=mono",
                            ]
                        )
                        filter_graph.append(
                            f"[{input_index}:a]aformat=sample_fmts=s16:"
                            f"channel_layouts=mono,asetpts=PTS-STARTPTS[a{input_index}]"
                        )
                        concat_inputs.append(f"[a{input_index}]")
                        input_index += 1

                filter_graph.append(
                    f"{''.join(concat_inputs)}concat=n={len(concat_inputs)}:v=0:a=1[out]"
                )
                ffmpeg_args.extend(
                    ["-filter_complex", ";".join(filter_graph), "-map", "[out]"]
                )

            if response_format == "mp3":
                ffmpeg_args.extend(
                    [
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        "128k",
                        "-minrate",
                        "128k",
                        "-maxrate",
                        "128k",
                        "-bufsize",
                        "256k",
                    ]
                )
            else:
                ffmpeg_args.extend(
                    ["-c:a", "pcm_s16le", "-ac", "1", "-ar", "44100"]
                )
            ffmpeg_args.extend(["-fs", str(settings.max_output_bytes + 1), str(output_path)])
            self._run(ffmpeg_args, deadline, directory, cancel_event)
            self._check_temp_budget(directory)

            try:
                output_size = output_path.stat().st_size
                if output_size > settings.max_output_bytes:
                    raise AudioTooLarge
                with output_path.open("rb") as output:
                    audio = output.read(settings.max_output_bytes + 1)
            except FileNotFoundError as exc:
                raise SynthesisFailure from exc
            if len(audio) > settings.max_output_bytes:
                raise AudioTooLarge

        if response_format == "mp3":
            return SynthesisResult(audio, "audio/mpeg", "speech.mp3")
        return SynthesisResult(audio, "audio/wav", "speech.wav")

    @staticmethod
    def _remaining(deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SynthesisTimeout
        return remaining

    @staticmethod
    def _temporary_size(directory: Path) -> int:
        total_size = 0
        for path in directory.rglob("*"):
            try:
                details = path.lstat()
            except FileNotFoundError:
                continue
            if path.is_file() and not path.is_symlink():
                total_size += details.st_size
        return total_size

    def _check_temp_budget(self, directory: Path) -> None:
        if self._temporary_size(directory) > self.settings.max_temp_bytes:
            raise SynthesisFailure

    @staticmethod
    def _terminate_child(process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
        except OSError:
            return
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                return
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass

    def _run(
        self,
        arguments: list[str],
        deadline: float,
        directory: Path | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        try:
            process = subprocess.Popen(
                arguments,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
        except OSError as exc:
            raise SynthesisUnavailable from exc
        try:
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    raise SynthesisFailure
                try:
                    process.wait(timeout=min(self._remaining(deadline), 0.05))
                    break
                except subprocess.TimeoutExpired:
                    if directory is not None:
                        self._check_temp_budget(directory)
            if directory is not None:
                self._check_temp_budget(directory)
            if process.returncode != 0:
                raise SynthesisFailure
        except SynthesisTimeout:
            self._terminate_child(process)
            raise
        except BaseException:
            self._terminate_child(process)
            raise
