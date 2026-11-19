from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_LANGUAGE_ALIASES = {"de": "de-DE", "en": "en-US"}
_LANGUAGES = {"de-DE", "en-US", "en-GB"}
_VIBEVOICE_VOICES = {
    "en-Carter_man": "en",
    "de-Spk1_woman": "de",
    "de-Spk0_man": "de",
}


class SpeechRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input: str = Field(min_length=1, max_length=5000)
    model: Literal["macos-say", "fish-speech", "vibevoice"] | None = None
    fish_runtime: Literal["pytorch", "mlx4"] | None = None
    language: str | None = None
    voice: str | None = Field(default=None, max_length=128)
    response_format: Literal["mp3", "wav"] = "mp3"
    speed: float = Field(default=1.0, ge=0.5, le=2.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def fish_runtime_requires_fish_model(self) -> SpeechRequest:
        if self.fish_runtime is not None and self.model != "fish-speech":
            raise ValueError("fish_runtime requires model fish-speech")
        return self

    @field_validator("voice", mode="before")
    @classmethod
    def blank_voice_is_unspecified(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

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

    @model_validator(mode="after")
    def vibevoice_voice_matches_language(self) -> SpeechRequest:
        if self.model != "vibevoice" or self.voice is None:
            return self
        voice_language = _VIBEVOICE_VOICES.get(self.voice)
        if voice_language is None:
            raise ValueError("voice is not a reviewed VibeVoice preset")
        if self.language is not None and not self.language.startswith(voice_language):
            raise ValueError("voice is not compatible with the selected language")
        return self
