from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


_LANGUAGE_ALIASES = {"de": "de-DE", "en": "en-US"}
_LANGUAGES = {"de-DE", "en-US", "en-GB"}
_VIBEVOICE_VOICES = {
    "en-Carter_man": "en",
    "de-Spk1_woman": "de",
    "de-Spk0_man": "de",
}


class SpeechRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input: Annotated[str, StringConstraints(strip_whitespace=False, min_length=1)]
    model: Literal["macos-say", "phonon", "fish-speech", "vibevoice"] | None = None
    language: str | None = None
    voice: str | None = Field(default=None, max_length=128)
    response_format: Literal["mp3", "wav"] = "mp3"
    speed: float = Field(default=1.0, ge=0.5, le=2.0, allow_inf_nan=False)

    @field_validator("voice", mode="before")
    @classmethod
    def blank_voice_is_unspecified(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("input")
    @classmethod
    def reject_unpaired_surrogates(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("input must not be blank")
        try:
            value.encode("utf-16-le")
        except UnicodeEncodeError:
            raise ValueError("input must not contain unpaired surrogates") from None
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
