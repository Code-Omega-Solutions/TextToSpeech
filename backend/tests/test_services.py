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
)


def prepare_service(monkeypatch, settings, output=b"generated audio", expected_voice="Anna"):
    monkeypatch.setattr("app.services.available_voices", lambda *_args, **_kwargs: {"Anna", "Samantha", "Daniel"})
    monkeypatch.setattr("app.services.shutil.which", lambda _path: "/fake/ffmpeg")

    def fake_run(arguments, **kwargs):
        assert kwargs["shell"] is False
        assert kwargs["capture_output"] is True
        if arguments[0] == settings.say_path:
            assert arguments[arguments.index("-v") + 1] == expected_voice
            assert "secret speech text" not in arguments
            assert Path(arguments[arguments.index("-f") + 1]).read_text(encoding="utf-8") == "secret speech text"
            return subprocess.CompletedProcess(arguments, 0, b"", b"")
        assert arguments[arguments.index("-c:a") + 1] == "libmp3lame"
        assert arguments[arguments.index("-b:a") + 1] == "128k"
        assert arguments[arguments.index("-minrate") + 1] == "128k"
        assert arguments[arguments.index("-maxrate") + 1] == "128k"
        Path(arguments[-1]).write_bytes(output)
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr("app.services.subprocess.run", fake_run)
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


def test_synthesis_uses_requested_wav_encoding(monkeypatch, settings_factory):
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings, b"RIFFwave")

    def fake_run(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            return subprocess.CompletedProcess(arguments, 0, b"", b"")
        assert arguments[arguments.index("-c:a") + 1] == "pcm_s16le"
        assert arguments[arguments.index("-ac") + 1] == "1"
        assert arguments[arguments.index("-ar") + 1] == "44100"
        Path(arguments[-1]).write_bytes(b"RIFFwave")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr("app.services.subprocess.run", fake_run)
    result = service.synthesize("secret speech text", "en-US", 1, "wav")
    assert result.audio == b"RIFFwave"
    assert result.media_type == "audio/wav"
    assert result.filename == "speech.wav"


def test_say_rate_is_scaled_from_speed(monkeypatch, settings_factory):
    settings = settings_factory(base_rate_wpm=180)
    service = prepare_service(monkeypatch, settings)

    def fake_run(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            assert arguments[arguments.index("-r") + 1] == "270"
            return subprocess.CompletedProcess(arguments, 0, b"", b"")
        Path(arguments[-1]).write_bytes(b"ok")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr("app.services.subprocess.run", fake_run)
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

    def fake_run(arguments, **kwargs):
        if arguments[0] == settings.say_path:
            input_path = Path(arguments[arguments.index("-f") + 1])
            spoken_segments.append(input_path.read_text(encoding="utf-8"))
            return subprocess.CompletedProcess(arguments, 0, b"", b"")

        pause_durations = [
            arguments[index + 1]
            for index, argument in enumerate(arguments[:-1])
            if argument == "-t"
        ]
        assert pause_durations == ["0.4", "1.2", "0.4"]
        assert "concat=n=6:v=0:a=1[out]" in arguments[arguments.index("-filter_complex") + 1]
        Path(arguments[-1]).write_bytes(b"paced audio")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr("app.services.subprocess.run", fake_run)
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
    monkeypatch.setattr("app.services.subprocess.run", lambda *args, **kwargs: process_calls.append(args))

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


def test_subprocess_timeout_maps_to_service_timeout(monkeypatch, tmp_path, settings_factory):
    monkeypatch.setattr("app.services.tempfile.tempdir", str(tmp_path))
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings)

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("say", 1)

    monkeypatch.setattr("app.services.subprocess.run", timeout)
    with pytest.raises(SynthesisTimeout):
        service.synthesize("secret speech text", "en-US", 1, "mp3")
    assert list(tmp_path.iterdir()) == []


def test_nonzero_process_exit_is_failure(monkeypatch, settings_factory):
    settings = settings_factory()
    service = prepare_service(monkeypatch, settings)
    monkeypatch.setattr(
        "app.services.subprocess.run",
        lambda arguments, **_kwargs: subprocess.CompletedProcess(arguments, 1, b"", b"private output"),
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

    def blocking_run(arguments, **_kwargs):
        if arguments[0] == settings.say_path:
            entered.set()
            release.wait(timeout=2)
            return subprocess.CompletedProcess(arguments, 0, b"", b"")
        Path(arguments[-1]).write_bytes(b"ok")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr("app.services.subprocess.run", blocking_run)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(service.synthesize, "secret speech text", "en-US", 1, "mp3")
        assert entered.wait(timeout=1)
        with pytest.raises(SynthesisCapacityExceeded):
            service.synthesize("other text", "en-US", 1, "mp3")
        release.set()
        assert future.result(timeout=2).audio == b"ok"
