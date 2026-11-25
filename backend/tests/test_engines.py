import pytest

from app.engines import EngineDescriptor, EngineRegistration, EngineRegistry
from app.services import SpeechService, SynthesisUnavailable
from phonon_test_support import phonon_settings


def registration(identifier, *, enabled=True, ready=True, languages=("en-US",), voices=None):
    descriptor = EngineDescriptor(identifier, tuple(languages), voices or {})
    return EngineRegistration(
        descriptor, lambda: enabled, lambda: ready, lambda *_args: None
    )


def test_registry_resolves_only_registered_engine_identifiers():
    macos = registration("macos-say")
    phonon = registration("phonon", enabled=False, languages=("de-DE", "en-US"))
    registry = EngineRegistry((macos, phonon))

    assert registry.resolve("macos-say") is macos
    assert registry.resolve("phonon") is phonon
    assert registry.resolve("fish-speech") is None
    assert registry.resolve("vibevoice") is None
    assert registry.resolve("unknown") is None


def test_registry_catalog_reports_public_availability_and_voice_options():
    registry = EngineRegistry(
        (
            registration(
                "phonon",
                enabled=True,
                ready=True,
                languages=("de-DE", "en-US"),
                voices={"de-DE": ("fixture-de-voice",), "en-US": ("fixture-en-voice",)},
            ),
            registration("macos-say", enabled=True, ready=False),
        )
    )

    assert registry.catalog() == [
        {
            "id": "macos-say",
            "available": False,
            "languages": ["en-US"],
            "voices": {},
        },
        {
            "id": "phonon",
            "available": True,
            "languages": ["de-DE", "en-US"],
            "voices": {
                "de-DE": ["fixture-de-voice"],
                "en-US": ["fixture-en-voice"],
            },
        },
    ]


def test_registry_rejects_duplicate_identifiers():
    with pytest.raises(ValueError, match="duplicate"):
        EngineRegistry((registration("phonon"), registration("phonon")))


def test_descriptor_rejects_voices_for_unsupported_languages():
    with pytest.raises(ValueError, match="supported language"):
        EngineDescriptor("phonon", ("en-US",), {"de-DE": ("fixture-voice",)})


def test_catalog_uses_dynamic_voice_availability():
    registry = EngineRegistry(
        (
            EngineRegistration(
                EngineDescriptor(
                    "macos-say",
                    ("de-DE", "en-US", "en-GB"),
                    {
                        "de-DE": ("Anna",),
                        "en-US": ("Samantha",),
                        "en-GB": ("Daniel",),
                    },
                ),
                lambda: True,
                lambda: True,
                lambda *_args: None,
                voice_catalog=lambda: {"de-DE": ("Anna",), "en-US": ("Samantha",)},
            ),
        )
    )

    assert registry.catalog()[0]["languages"] == ["de-DE", "en-US"]
    assert registry.catalog()[0]["voices"] == {
        "de-DE": ["Anna"],
        "en-US": ["Samantha"],
    }


def test_phonon_is_disabled_without_explicit_approval(settings_factory):
    service = SpeechService(settings_factory())

    phonon_info = next(
        info for info in service.engine_registry.catalog() if info["id"] == "phonon"
    )
    assert phonon_info == {
        "id": "phonon",
        "available": False,
        "languages": [],
        "voices": {},
    }


def test_phonon_catalog_uses_only_explicitly_approved_fixture_voices(settings_factory):
    service = SpeechService(phonon_settings(settings_factory))

    phonon_info = next(
        info for info in service.engine_registry.catalog() if info["id"] == "phonon"
    )
    assert phonon_info == {
        "id": "phonon",
        "available": True,
        "languages": ["en-US", "de-DE"],
        "voices": {
            "de-DE": ["fixture-de-voice"],
            "en-US": ["fixture-en-voice"],
        },
    }


def test_unknown_and_retired_engine_selection_never_substitute(settings_factory, monkeypatch):
    service = SpeechService(settings_factory())
    monkeypatch.setattr(
        service,
        "_synthesize_macos_engine",
        lambda *_args, **_kwargs: pytest.fail("Unavailable engine fell back to macOS"),
    )

    for engine in ("unknown", "fish-speech", "vibevoice"):
        with pytest.raises(SynthesisUnavailable):
            service.synthesize_reserved("Hello", "en-US", 1, "wav", backend=engine)
