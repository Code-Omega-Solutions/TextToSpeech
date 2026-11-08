from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


_LANGUAGE_ALIASES = {"de": "de-DE", "en": "en-US"}
_LANGUAGES = {"de-DE", "en-US", "en-GB"}


class SpeechRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input: str = Field(min_length=1, max_length=5000)
    model: Literal["macos-say"] = "macos-say"
    language: str | None = None
    voice: str | None = Field(default=None, max_length=128)
    response_format: Literal["mp3", "wav"] = "mp3"
    speed: float = Field(default=1.0, ge=0.5, le=2.0, allow_inf_nan=False)

    @field_validator("input")
    @classmethod
    def limit_utf16_units(cls, value: str) -> str:
        try:
            units = len(value.encode("utf-16-le")) // 2
        except UnicodeEncodeError:
            raise ValueError("input must not contain unpaired surrogates") from None
        if units > 5000:
            raise ValueError("input must not exceed 5000 UTF-16 code units")
        return value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = _LANGUAGE_ALIASES.get(value, value)
        if normalized not in _LANGUAGES:
            raise ValueError("language must be de-DE, en-US, or en-GB")
        return normalized
