import pytest
from fastapi import HTTPException

from app.language import resolve_language
from app.models import SpeechRequest


@pytest.mark.parametrize(
    ("text", "expected"),
    [("a" * 19, "en-US"), ("a" * 20, "en-US"), ("ä" * 20, "en-US"), ("1" * 30 + "ä" * 19, "en-US")],
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


@pytest.mark.parametrize(("detected", "expected"), [("de", "de-DE"), ("en", "en-US")])
def test_supported_detected_languages(detected, expected, settings):
    request = SpeechRequest(input="a" * 20)
    assert resolve_language(request, settings, lambda _text: detected) == expected


def test_unsupported_detected_language_returns_actionable_422(settings):
    request = SpeechRequest(input="a" * 20)
    with pytest.raises(HTTPException) as error:
        resolve_language(request, settings, lambda _text: "fr")
    assert error.value.status_code == 422
    assert "German and English" in error.value.detail


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
    monkeypatch.setattr("app.language.langid.classify", lambda _text: ("fr", 0.9))
    with pytest.raises(HTTPException) as error:
        from app.language import detect_language

        detect_language("un texte suffisamment long")
    assert error.value.status_code == 422
