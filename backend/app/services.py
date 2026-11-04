from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.voices import (
    VoiceInventoryError,
    VoiceInventoryTimeout,
    available_voices,
    resolve_voice,
)

_SENTENCE_PAUSE_SECONDS = 0.4
_PARAGRAPH_PAUSE_SECONDS = 1.2
_MAX_SPEECH_SEGMENTS = 100
_PARAGRAPH_BREAK = re.compile(r"(?:\r\n|\r|\n)[ \t]*(?:(?:\r\n|\r|\n)[ \t]*)+")
_SENTENCE_END = re.compile(r"[.!?]+(?:[\"'’”)\]]*)")
_SENTENCE_CLOSERS = "\"'’”)]"
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

    def try_acquire(self) -> bool:
        return self._permits.acquire(blocking=False)

    def release_permit(self) -> None:
        self._permits.release()

    def synthesize(self, text: str, language: str, speed: float, response_format: str) -> SynthesisResult:
        if not self.try_acquire():
            raise SynthesisCapacityExceeded
        try:
            return self.synthesize_reserved(text, language, speed, response_format)
        finally:
            self.release_permit()

    def synthesize_reserved(
        self, text: str, language: str, speed: float, response_format: str
    ) -> SynthesisResult:
        return self._synthesize(text, language, speed, response_format)

    def _synthesize(self, text: str, language: str, speed: float, response_format: str) -> SynthesisResult:
        settings = self.settings
        deadline = time.monotonic() + settings.request_timeout_seconds
        segments = _speech_segments(text)

        try:
            voices = available_voices(settings.say_path, timeout=self._remaining(deadline))
            voice = resolve_voice(language, settings, voices)
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
                input_path.write_text(segment_text, encoding="utf-8")
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
                )
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
            self._run(ffmpeg_args, deadline)

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

    def _run(self, arguments: list[str], deadline: float) -> None:
        try:
            result = subprocess.run(
                arguments,
                check=False,
                capture_output=True,
                timeout=self._remaining(deadline),
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SynthesisTimeout from exc
        except OSError as exc:
            raise SynthesisUnavailable from exc
        if result.returncode != 0:
            raise SynthesisFailure
