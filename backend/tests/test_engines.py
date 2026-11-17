import threading
import time

import pytest

from app.engines import EngineDescriptor, EngineRegistration, EngineRegistry
from app.fish_process import FishResourceUnavailable
from app.services import (
    AudioTooLarge, SpeechService, SynthesisFailure, SynthesisResult,
    SynthesisTimeout, SynthesisUnavailable,
)


def registration(identifier, *, enabled=True, ready=True, languages=("en-US",), voices=None):
    descriptor = EngineDescriptor(
        identifier,
        tuple(languages),
        voices or {},
    )
    return EngineRegistration(descriptor, lambda: enabled, lambda: ready, lambda *_args: None)


def test_registry_resolves_only_registered_engine_identifiers():
    macos = registration("macos-say")
    fish = registration("fish-speech", enabled=False, languages=("de-DE", "en-US"))
    registry = EngineRegistry((macos, fish))

    assert registry.resolve("macos-say") is macos
    assert registry.resolve("fish-speech") is fish
    assert registry.resolve("vibevoice") is None
    assert registry.resolve("unknown") is None


def test_registry_catalog_reports_public_availability_and_voice_options():
    registry = EngineRegistry(
        (
            registration(
                "fish-speech",
                enabled=True,
                ready=True,
                languages=("de-DE", "en-US"),
                voices={"de-DE": ("de-reference",), "en-US": ("en-reference",)},
            ),
            registration("macos-say", enabled=True, ready=False),
        )
    )

    assert registry.catalog() == [
        {
            "id": "fish-speech",
            "available": True,
            "languages": ["de-DE", "en-US"],
            "voices": {"de-DE": ["de-reference"], "en-US": ["en-reference"]},
        },
        {"id": "macos-say", "available": False, "languages": ["en-US"], "voices": {}},
    ]


def test_registry_rejects_duplicate_identifiers():
    with pytest.raises(ValueError, match="duplicate"):
        EngineRegistry((registration("fish-speech"), registration("fish-speech")))


def test_descriptor_rejects_voices_for_unsupported_languages():
    with pytest.raises(ValueError, match="supported language"):
        EngineDescriptor("fish-speech", ("en-US",), {"de-DE": ("speaker",)})


def test_catalog_uses_dynamic_voice_availability():
    registry = EngineRegistry(
        (
            EngineRegistration(
                EngineDescriptor(
                    "macos-say",
                    ("de-DE", "en-US", "en-GB"),
                    {"de-DE": ("Anna",), "en-US": ("Samantha",), "en-GB": ("Daniel",)},
                ),
                lambda: True,
                lambda: True,
                lambda *_args: None,
                voice_catalog=lambda: {"de-DE": ("Anna",), "en-US": ("Samantha",)},
            ),
        )
    )

    assert registry.catalog()[0]["languages"] == ["de-DE", "en-US"]
    assert registry.catalog()[0]["voices"] == {"de-DE": ["Anna"], "en-US": ["Samantha"]}


def test_unknown_and_legacy_vibevoice_selection_never_substitute(settings_factory):
    service = SpeechService(settings_factory())
    for engine in ("unknown", "vibevoice"):
        with pytest.raises(SynthesisUnavailable):
            service.synthesize_reserved("Hello", "en-US", 1, "wav", backend=engine)


@pytest.mark.parametrize("language", ["de-DE", "en-US", "en-GB"])
@pytest.mark.parametrize("engine", ["fish-speech", "vibevoice"])
def test_optional_unavailable_engine_uses_native_locale_not_requested_voice(
    settings_factory, monkeypatch, language, engine
):
    service = SpeechService(settings_factory(fish_opportunistic=True))
    calls = []

    def native(*args, **kwargs):
        calls.append((args, kwargs))
        return SynthesisResult(b"native", "audio/wav", "speech.wav")

    monkeypatch.setattr(service, "_synthesize_macos", native)
    result = service.synthesize_reserved(
        "Hello", language, 1.25, "wav", backend=engine, voice="neural-reference"
    )
    assert calls[0][0][1:4] == (language, 1.25, "wav")
    assert calls[0][0][5] is None
    assert calls[0][1]["deadline"] <= time.monotonic() + 60
    assert result.actual_backend == "macos-say"
    assert result.fallback is True
    assert result.failure_reason


@pytest.mark.parametrize("failure", [FishResourceUnavailable("fish_busy"), SynthesisUnavailable(), SynthesisTimeout()])
def test_optional_neural_denial_uses_remaining_deadline(settings_factory, monkeypatch, failure):
    service = SpeechService(settings_factory(
        fish_enabled=True, fish_opportunistic=True, request_timeout_seconds=20,
    ))
    clock = [100.0]
    monkeypatch.setattr("app.services.time.monotonic", lambda: clock[0])

    def denied(_callback, *, deadline, cancel_event):
        assert deadline == 110.0
        clock[0] = 108.0
        raise failure

    def native(*_args, **kwargs):
        assert kwargs["deadline"] == 120.0
        return SynthesisResult(b"native", "audio/wav", "speech.wav")

    monkeypatch.setattr(service.fish_process, "run", denied)
    monkeypatch.setattr(service, "_synthesize_macos", native)
    assert service.synthesize_reserved("Hello", "en-US", 1, "wav", backend="fish-speech").fallback


@pytest.mark.parametrize("cause", ["cancel", "oversize", "native_failure"])
def test_optional_policy_never_masks_cancellation_size_or_native_failure(settings_factory, monkeypatch, cause):
    service = SpeechService(settings_factory(fish_enabled=True, fish_opportunistic=True))
    cancel = threading.Event()

    def neural(_callback, **_kwargs):
        if cause == "cancel":
            cancel.set()
            raise FishResourceUnavailable("fish_cancelled")
        if cause == "oversize":
            raise AudioTooLarge
        raise FishResourceUnavailable("fish_busy")

    monkeypatch.setattr(service.fish_process, "run", neural)

    def native(*_args, **_kwargs):
        if cause != "native_failure":
            pytest.fail("cancel/oversize triggered fallback")
        raise SynthesisUnavailable

    monkeypatch.setattr(service, "_synthesize_macos", native)
    with pytest.raises({
        "cancel": SynthesisFailure, "oversize": AudioTooLarge,
        "native_failure": SynthesisUnavailable,
    }[cause]):
        service.synthesize_reserved("Hello", "en-US", 1, "wav", cancel, backend="fish-speech")


def test_native_request_does_not_invoke_optional_worker(settings_factory, monkeypatch):
    service = SpeechService(settings_factory(fish_opportunistic=True))
    monkeypatch.setattr(
        service.fish_process, "run",
        lambda *_args, **_kwargs: pytest.fail("native request started neural worker"),
    )
    monkeypatch.setattr(
        service, "_synthesize_macos",
        lambda *_args: SynthesisResult(b"native", "audio/wav", "speech.wav"),
    )
    assert not service.synthesize_reserved(
        "Hello", "en-US", 1, "wav", backend="macos-say"
    ).fallback
    with pytest.raises(SynthesisUnavailable):
        service.synthesize_reserved("Hello", "en-US", 1, "wav", backend="unknown")


def test_neural_success_preserves_selected_reference_and_engine(settings_factory, monkeypatch):
    service = SpeechService(settings_factory(fish_enabled=True, fish_opportunistic=True))
    monkeypatch.setattr(service.fish_process, "run", lambda callback, **_kwargs: callback())

    def fish(*args, **kwargs):
        assert args[5] == "approved-reference"
        assert kwargs["deadline"] < time.monotonic() + 60
        return SynthesisResult(b"fish", "audio/wav", "speech.wav", actual_backend="fish-speech")

    monkeypatch.setattr(service, "_synthesize_fish", fish)
    result = service.synthesize_reserved(
        "Hello", "en-US", 1, "wav", backend="fish-speech", voice="approved-reference"
    )
    assert result.actual_backend == "fish-speech" and not result.fallback


def test_fallback_does_not_restart_expired_overall_deadline(settings_factory, monkeypatch):
    service = SpeechService(settings_factory(fish_enabled=True, fish_opportunistic=True))
    clock = [100.0]
    monkeypatch.setattr("app.services.time.monotonic", lambda: clock[0])

    def timed_out(_callback, **_kwargs):
        clock[0] = 161.0
        raise SynthesisTimeout

    monkeypatch.setattr(service.fish_process, "run", timed_out)
    monkeypatch.setattr(
        service, "_synthesize_macos",
        lambda *_args, **_kwargs: pytest.fail("expired request restarted native synthesis"),
    )
    with pytest.raises(SynthesisTimeout):
        service.synthesize_reserved("Hello", "en-US", 1, "wav", backend="fish-speech")