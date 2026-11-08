import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.services import (
    AudioTooLarge,
    SpeechService,
    SpeechSegmentLimitExceeded,
    SynthesisCapacityExceeded,
    SynthesisFailure,
    SynthesisTimeout,
    _speech_segments,
    available_codecs,
)


class CompletedChild:
    def __init__(self, returncode=0):
        self.returncode = returncode

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode


def prepare_service(monkeypatch, settings, output=b"generated audio", expected_voice="Anna"):
    monkeypatch.setattr("app.services.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha", "Daniel"})
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/ffmpeg")

    def fake_popen(arguments, **kwargs):
        assert kwargs["shell"] is False
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["stdout"] == subprocess.DEVNULL
        assert kwargs["stderr"] == subprocess.DEVNULL
        if arguments[0] == settings.say_path:
            assert arguments[arguments.index("-v") + 1] == expected_voice
            assert "secret speech text" not in arguments
            assert Path(arguments[arguments.index("-f") + 1]).read_text(encoding="utf-8") == "secret speech text"
            Path(arguments[arguments.index("-o") + 1]).write_bytes(b"raw audio")
            return CompletedChild()
        assert arguments[arguments.index("-c:a") + 1] == "libmp3lame"
        assert arguments[arguments.index("-b:a") + 1] == "128k"
        assert arguments[arguments.index("-minrate") + 1] == "128k"
        assert arguments[arguments.index("-maxrate") + 1] == "128k"
        Path(arguments[-1]).write_bytes(output)
        return CompletedChild()

    monkeypatch.setattr("app.services.subprocess.Popen", fake_popen)
    return SpeechService(settings)


def test_synthesis_arguments_output_and_temp_cleanup(monkeypatch, tmp_path, settings_factory):
    monkeypatch.setattr("app.services.tempfile.tempdir", str(tmp_path))
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings)
    result = service.synthesize("secret speech text", "de-DE", 1.25, "mp3")
    assert result.audio == b"generated audio"
    assert result.media_type == "audio/mpeg"
    assert result.filename == "speech.mp3"
    assert list(tmp_path.iterdir()) == []


def test_codec_inventory_checks_mp3_and_wav_encoders(monkeypatch):
    output = " A..... libmp3lame MP3 (MPEG audio layer 3)\n A..... pcm_s16le PCM signed 16-bit little-endian\n"

    def fake_run(arguments, **kwargs):
        assert arguments == ["/usr/bin/ffmpeg", "-hide_banner", "-encoders"]
        assert kwargs["timeout"] == 5.0
        assert kwargs["shell"] is False
        return subprocess.CompletedProcess(arguments, 0, output, "")

    monkeypatch.setattr("app.services.subprocess.run", fake_run)
    assert available_codecs("/usr/bin/ffmpeg") == {"libmp3lame", "pcm_s16le"}


def test_synthesis_uses_requested_wav_encoding(monkeypatch, settings_factory):
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings, b"RIFFwave")

    def fake_popen(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            Path(arguments[arguments.index("-o") + 1]).write_bytes(b"raw audio")
            return CompletedChild()
        assert arguments[arguments.index("-c:a") + 1] == "pcm_s16le"
        assert arguments[arguments.index("-ac") + 1] == "1"
        assert arguments[arguments.index("-ar") + 1] == "44100"
        Path(arguments[-1]).write_bytes(b"RIFFwave")
        return CompletedChild()

    monkeypatch.setattr("app.services.subprocess.Popen", fake_popen)
    result = service.synthesize("secret speech text", "en-US", 1, "wav")
    assert result.audio == b"RIFFwave"
    assert result.media_type == "audio/wav"
    assert result.filename == "speech.wav"


def test_say_rate_is_scaled_from_speed(monkeypatch, settings_factory):
    settings = settings_factory(base_rate_wpm=180)
    service = prepare_service(monkeypatch, settings)

    def fake_popen(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            assert arguments[arguments.index("-r") + 1] == "270"
            Path(arguments[arguments.index("-o") + 1]).write_bytes(b"raw audio")
            return CompletedChild()
        Path(arguments[-1]).write_bytes(b"ok")
        return CompletedChild()

    monkeypatch.setattr("app.services.subprocess.Popen", fake_popen)
    service.synthesize("secret speech text", "en-US", 1.5, "mp3")


def test_speech_segments_add_sentence_and_paragraph_pauses():
    assert _speech_segments(
        "First sentence. Second sentence!\n\nThird sentence.\nFourth sentence"
    ) == [
        ("First sentence.", 0.4),
        ("Second sentence!", 1.2),
        ("Third sentence.", 0.4),
        ("Fourth sentence", 0),
    ]


def test_sentence_segmentation_ignores_abbreviations_and_decimals():
    assert _speech_segments("Dr. Smith paid 3.14 dollars. Done.") == [
        ("Dr. Smith paid 3.14 dollars.", 0.4),
        ("Done.", 0.4),
    ]


def test_synthesis_concatenates_speech_and_requested_silence(monkeypatch, settings_factory):
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings)
    spoken_segments = []

    def fake_popen(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            input_path = Path(arguments[arguments.index("-f") + 1])
            spoken_segments.append(input_path.read_text(encoding="utf-8"))
            Path(arguments[arguments.index("-o") + 1]).write_bytes(b"raw audio")
            return CompletedChild()

        pause_durations = [
            arguments[index + 1]
            for index, argument in enumerate(arguments[:-1])
            if argument == "-t"
        ]
        assert pause_durations == ["0.4", "1.2", "0.4"]
        assert "concat=n=6:v=0:a=1[out]" in arguments[arguments.index("-filter_complex") + 1]
        Path(arguments[-1]).write_bytes(b"paced audio")
        return CompletedChild()

    monkeypatch.setattr("app.services.subprocess.Popen", fake_popen)
    result = service.synthesize(
        "First sentence. Second sentence.\n\nThird sentence.", "en-US", 1, "mp3"
    )

    assert spoken_segments == ["First sentence.", "Second sentence.", "Third sentence."]
    assert result.audio == b"paced audio"


def test_too_many_speech_segments_are_rejected_before_external_processes(
    monkeypatch, settings_factory
):
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings)
    process_calls = []
    monkeypatch.setattr("app.services.subprocess.Popen", lambda *args, **kwargs: process_calls.append(args))

    with pytest.raises(SpeechSegmentLimitExceeded):
        service.synthesize("Sentence. " * 101, "en-US", 1, "mp3")

    assert process_calls == []


def test_generated_audio_limit(monkeypatch, tmp_path, settings_factory):
    monkeypatch.setattr("app.services.tempfile.tempdir", str(tmp_path))
    settings = settings_factory()
    service = prepare_service(
        monkeypatch,
        settings,
        b"x" * (settings.max_output_bytes + 1),
        expected_voice="Samantha",
    )
    with pytest.raises(AudioTooLarge):
        service.synthesize("secret speech text", "en-US", 1, "mp3")
    assert list(tmp_path.iterdir()) == []


def test_synthesis_passes_one_deadline_to_every_child(monkeypatch, settings_factory):
    settings = settings_factory(request_timeout_seconds=12)
    service = prepare_service(monkeypatch, settings)
    deadlines = []

    def fake_run(arguments, deadline, _directory=None, _cancel_event=None):
        deadlines.append(deadline)
        if arguments[0] != settings.say_path:
            Path(arguments[-1]).write_bytes(b"ok")
        else:
            Path(arguments[arguments.index("-o") + 1]).write_bytes(b"raw")

    monkeypatch.setattr(service, "_run", fake_run)
    service.synthesize("First. Second.", "en-US", 1, "mp3")
    assert len(deadlines) == 3
    assert len(set(deadlines)) == 1


def test_synthesis_enforces_temporary_disk_budget_and_cleans_up(
    monkeypatch, tmp_path, settings_factory
):
    monkeypatch.setattr("app.services.tempfile.tempdir", str(tmp_path))
    settings = settings_factory(max_temp_bytes=20)
    service = prepare_service(monkeypatch, settings)

    def exceed_budget(arguments, _deadline, _directory=None, _cancel_event=None):
        output_path = Path(arguments[arguments.index("-o") + 1])
        output_path.write_bytes(b"x" * 17)

    monkeypatch.setattr(service, "_run", exceed_budget)
    with pytest.raises(SynthesisFailure):
        service.synthesize("secret speech text", "de-DE", 1, "mp3")
    assert list(tmp_path.iterdir()) == []


def test_cancellation_terminates_owned_child_and_cleans_private_files(
    monkeypatch, tmp_path, settings_factory
):
    monkeypatch.setattr("app.services.tempfile.tempdir", str(tmp_path))
    settings = settings_factory()
    service = SpeechService(settings)
    monkeypatch.setattr("app.services.available_voices", lambda *_args, **_kwargs: {"Anna"})
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/ffmpeg")
    cancel_event = threading.Event()
    started = threading.Event()
    terminated = []

    class BlockingChild:
        returncode = None

        def __init__(self, arguments, **_kwargs):
            self.arguments = arguments
            self.output_path = (
                arguments[arguments.index("-o") + 1]
                if arguments[0] == settings.say_path
                else arguments[-1]
            )
            started.set()

        def wait(self, timeout=None):
            if self.returncode is not None:
                return self.returncode
            if cancel_event.is_set():
                raise subprocess.TimeoutExpired(self.arguments, timeout)
            time.sleep(min(timeout or 0.01, 0.01))
            raise subprocess.TimeoutExpired(self.arguments, timeout)

        def poll(self):
            return self.returncode

        def terminate(self):
            terminated.append(self)
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr("app.services.subprocess.Popen", BlockingChild)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            service.synthesize,
            "secret speech text",
            "de-DE",
            1,
            "mp3",
            cancel_event,
        )
        assert started.wait(timeout=1)
        cancel_event.set()
        with pytest.raises(SynthesisFailure):
            future.result(timeout=2)
    assert terminated
    assert list(tmp_path.iterdir()) == []


def test_subprocess_timeout_maps_to_service_timeout(monkeypatch, tmp_path, settings_factory):
    monkeypatch.setattr("app.services.tempfile.tempdir", str(tmp_path))
    settings = settings_factory(request_timeout_seconds=1)
    service = prepare_service(monkeypatch, settings)

    class TimedChild:
        returncode = None

        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired("say", timeout)

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    monkeypatch.setattr("app.services.subprocess.Popen", lambda *_args, **_kwargs: TimedChild())
    ticks = iter([0.0, 2.0])
    monkeypatch.setattr("app.services.time.monotonic", lambda: next(ticks))
    with pytest.raises(SynthesisTimeout):
        service.synthesize("secret speech text", "en-US", 1, "mp3")
    assert list(tmp_path.iterdir()) == []


def test_nonzero_process_exit_is_failure(monkeypatch, settings_factory):
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings)
    monkeypatch.setattr(
        "app.services.subprocess.Popen",
        lambda *_args, **_kwargs: CompletedChild(1),
    )
    with pytest.raises(SynthesisFailure):
        service.synthesize("secret speech text", "en-US", 1, "mp3")


def test_synthesis_permit_is_nonblocking(monkeypatch, settings_factory):
    settings = settings_factory(max_concurrent_synthesis=1)
    service = SpeechService(settings)
    entered = threading.Event()
    release = threading.Event()
    monkeypatch.setattr("app.services.available_voices", lambda *_args, **_kwargs: {"Samantha"})
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/ffmpeg")

    class BlockingChild:
        def __init__(self, arguments, **_kwargs):
            self.arguments = arguments
            self.returncode = None
            if arguments[0] == settings.say_path:
                Path(arguments[arguments.index("-o") + 1]).write_bytes(b"raw")
            else:
                Path(arguments[-1]).write_bytes(b"ok")

        def wait(self, timeout=None):
            if release.is_set():
                self.returncode = 0
                return 0
            if self.arguments[0] == settings.say_path:
                entered.set()
            time.sleep(min(timeout or 0.01, 0.01))
            raise subprocess.TimeoutExpired(self.arguments, timeout)

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    def blocking_popen(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            return BlockingChild(arguments, **kwargs)
        return BlockingChild(arguments, **kwargs)

    monkeypatch.setattr("app.services.subprocess.Popen", blocking_popen)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(service.synthesize, "secret speech text", "en-US", 1, "mp3")
        assert entered.wait(timeout=1)
        with pytest.raises(SynthesisCapacityExceeded):
            service.synthesize("other text", "en-US", 1, "mp3")
        release.set()
        assert future.result(timeout=2).audio == b"ok"
