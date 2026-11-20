import pytest

import app.language as language
from app.language import detect_language, resolve_language
from app.models import SpeechRequest


@pytest.mark.parametrize(
    ("text", "expected"),
    [("a" * 19, "de-DE"), ("a" * 20, "de-DE"), ("ä" * 20, "de-DE"), ("1" * 30 + "ä" * 19, "de-DE")],
)
def test_short_input_counts_unicode_alphabetic_characters(text, expected, settings):
    called = []

    def classifier(value):
        called.append(value)
        return "de"

    result = resolve_language(SpeechRequest(input=text), settings, classifier)
    if sum(character.isalpha() for character in text) < settings.min_detection_chars:
        assert result == expected
        assert not called
    else:
        assert result == "de-DE"
        assert called == [text]


def test_explicit_language_bypasses_detection(settings):
    request = SpeechRequest(input="bonjour", language="en")
    assert resolve_language(request, settings, lambda _text: pytest.fail("classifier called")) == "en-US"


@pytest.mark.parametrize(
    ("alias", "expected"), [("de", "de-DE"), ("en", "en-US"), ("en-GB", "en-GB")]
)
def test_explicit_locale_aliases_and_uk_locale_bypass_detection(alias, expected, settings):
    request = SpeechRequest(input="bonjour", language=alias)
    assert resolve_language(request, settings, lambda _text: pytest.fail("classifier called")) == expected


@pytest.mark.parametrize(
    ("detected", "expected"),
    [("de", "de-DE"), ("de-DE", "de-DE"), ("en", "en-US"), ("en-US", "en-US")],
)
def test_supported_detected_languages(detected, expected, settings):
    request = SpeechRequest(input="a" * 20)
    assert resolve_language(request, settings, lambda _text: detected) == expected


@pytest.mark.parametrize("detected", ["fr", "it", "", "en-GB"])
def test_unsupported_detected_language_falls_back_to_german(settings_factory, detected):
    request = SpeechRequest(input="a" * 20)
    settings = settings_factory(default_language="en-US")
    assert resolve_language(request, settings, lambda _text: detected) == "de-DE"


def test_short_input_retains_configured_default(settings_factory):
    settings = settings_factory(default_language="en-US")
    assert resolve_language(
        SpeechRequest(input="short"), settings, lambda _text: pytest.fail("classifier called")
    ) == "en-US"


def test_detection_boundary_ignores_digits_and_punctuation(settings):
    calls = []

    def classifier(text):
        calls.append(text)
        return "en"

    below = SpeechRequest(input="a" * 19 + "!? 123")
    at_boundary = SpeechRequest(input="a" * 20 + "!? 123")
    assert resolve_language(below, settings, classifier) == settings.default_language
    assert resolve_language(at_boundary, settings, classifier) == "en-US"
    assert calls == [at_boundary.input]


def test_voice_hint_does_not_affect_detection(settings):
    request = SpeechRequest(input="a" * 20, voice="alloy")
    assert resolve_language(request, settings, lambda _text: "de") == "de-DE"


def test_detector_uses_langid_full_language_classifier(monkeypatch):
    if language.langid is None:
        assert detect_language("un texte suffisamment long") == "de-DE"
        return
    monkeypatch.setattr("app.language.langid.classify", lambda _text: ("fr", 0.9))
    assert detect_language("un texte suffisamment long") == "de-DE"


def test_detector_errors_are_not_silently_converted_to_fallback(monkeypatch, settings):
    if language.langid is None:
        pytest.skip("optional langid classifier is unavailable")

    def fail(_text):
        raise RuntimeError("detector unavailable")

    monkeypatch.setattr("app.language.langid.classify", fail)
    with pytest.raises(RuntimeError, match="detector unavailable"):
        resolve_language(SpeechRequest(input="a" * 20), settings)


def test_missing_classifier_uses_bounded_marker_fallback(monkeypatch, settings):
    monkeypatch.setattr(language, "langid", None)
    assert resolve_language(
        SpeechRequest(input="Das ist ein privater deutscher Satz."), settings
    ) == "de-DE"
    assert resolve_language(
        SpeechRequest(input="This is a private English sentence."), settings
    ) == "en-US"
    assert resolve_language(
        SpeechRequest(input="texte suffisamment long sans marqueurs"), settings
    ) == "de-DE"
