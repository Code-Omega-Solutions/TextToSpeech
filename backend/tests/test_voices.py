import subprocess

import pytest

from app.voices import (
    VoiceInventoryError,
    VoiceInventoryTimeout,
    available_voices,
    configured_voices,
    resolve_voice,
    voice_available,
)


def test_configured_voice_mapping_and_resolution(settings_factory):
    settings = settings_factory(
        voice_de_de="Custom German",
        voice_en_us="Custom US",
        voice_en_gb="Custom UK",
    )
    assert configured_voices(settings) == {
        "de-DE": "Custom German",
        "en-US": "Custom US",
        "en-GB": "Custom UK",
    }
    assert resolve_voice("en-GB", settings, {"Custom", "Custom German", "Custom UK"}) == "Custom UK"


def test_localized_german_label_matches_say_voice_identifier(settings):
    assert voice_available(settings.voice_de_de, {"Anna"})
    assert resolve_voice("de-DE", settings, {"Anna"}) == "Anna"


def test_voice_is_unavailable_if_identifier_is_missing(settings):
    with pytest.raises(LookupError):
        resolve_voice("en-GB", settings, {"Anna", "Samantha"})


def test_voice_list_uses_argument_array_and_parses_names(monkeypatch):
    def fake_run(args, **kwargs):
        assert args == ["/usr/bin/say", "-v", "?"]
        assert kwargs["shell"] is False
        return subprocess.CompletedProcess(args, 0, "Anna de_DE\nSamantha en_US\n", "")

    monkeypatch.setattr("app.voices.subprocess.run", fake_run)
    assert available_voices("/usr/bin/say") == {"Anna", "Samantha"}


@pytest.mark.parametrize(
    "exception", [OSError("private path"), subprocess.TimeoutExpired("say", 1)]
)
def test_voice_inventory_failures_are_safe(monkeypatch, exception):
    monkeypatch.setattr("app.voices.subprocess.run", lambda *_args, **_kwargs: (_ for _ in ()).throw(exception))
    expected_error = (
        VoiceInventoryTimeout
        if isinstance(exception, subprocess.TimeoutExpired)
        else VoiceInventoryError
    )
    with pytest.raises(expected_error):
        available_voices("say")
