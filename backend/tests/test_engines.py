import pytest

from app.engines import EngineDescriptor, EngineRegistration, EngineRegistry
from app.services import SpeechService, SynthesisUnavailable


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