import pytest
from pydantic import ValidationError

from app.models import SpeechRequest


def test_input_is_trimmed_and_required():
    assert SpeechRequest(input="  hello  ").input == "hello"
    with pytest.raises(ValidationError):
        SpeechRequest()
    with pytest.raises(ValidationError):
        SpeechRequest(input=" \t ")
    with pytest.raises(ValidationError):
        SpeechRequest(input="x" * 5001)


@pytest.mark.parametrize("text", ["x" * 5000, "\U0001f600" * 2500, "x" * 4998 + "\U0001f600"])
def test_input_accepts_up_to_5000_utf16_units(text):
    assert SpeechRequest(input=text).input == text


@pytest.mark.parametrize("text", ["x" * 4999 + "\U0001f600", "\U0001f600" * 2501])
def test_input_rejects_more_than_5000_utf16_units(text):
    with pytest.raises(ValidationError):
        SpeechRequest(input=text)


@pytest.mark.parametrize("text", ["\ud800", "\udfff", "text\ud800text"])
def test_input_rejects_unpaired_surrogates(text):
    with pytest.raises(ValidationError):
        SpeechRequest(input=text)


def test_unknown_fields_are_rejected():
    with pytest.raises(ValidationError):
        SpeechRequest(input="hello", unexpected="value")


@pytest.mark.parametrize(
    ("provided", "expected"),
    [("de", "de-DE"), ("de-DE", "de-DE"), ("en", "en-US"), ("en-US", "en-US"), ("en-GB", "en-GB")],
)
def test_language_aliases(provided, expected):
    assert SpeechRequest(input="hello", language=provided).language == expected


def test_invalid_language_is_rejected():
    with pytest.raises(ValidationError):
        SpeechRequest(input="hello", language="fr-FR")


def test_model_and_format_values_are_restricted():
    assert SpeechRequest(input="hello").model == "macos-say"
    assert SpeechRequest(input="hello").response_format == "mp3"
    assert SpeechRequest(input="hello", response_format="wav").response_format == "wav"
    with pytest.raises(ValidationError):
        SpeechRequest(input="hello", model="other")
    with pytest.raises(ValidationError):
        SpeechRequest(input="hello", response_format="ogg")


def test_voice_hint_is_accepted_but_bounded():
    assert SpeechRequest(input="hello", voice="alloy").voice == "alloy"
    assert SpeechRequest(input="hello", voice="v" * 128).voice == "v" * 128
    with pytest.raises(ValidationError):
        SpeechRequest(input="hello", voice="v" * 129)


@pytest.mark.parametrize("speed", [0.5, 1, 2])
def test_speed_boundaries(speed):
    assert SpeechRequest(input="hello", speed=speed).speed == speed


@pytest.mark.parametrize("speed", [0.49, 2.01, float("inf"), float("nan")])
def test_invalid_speed_is_rejected(speed):
    with pytest.raises(ValidationError):
        SpeechRequest(input="hello", speed=speed)
