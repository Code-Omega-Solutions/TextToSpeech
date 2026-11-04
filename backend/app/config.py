from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _SettingsValues(BaseModel):
    model_config = ConfigDict(frozen=True)

    api_key: str | None = None
    auth_enabled: bool = True
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    voice_de_de: str = "Anna (Deutsch (Deutschland))"
    voice_en_us: str = "Samantha"
    voice_en_gb: str = "Daniel"
    default_language: str = "en-US"
    min_detection_chars: int = Field(default=20, ge=1, le=1000)
    base_rate_wpm: int = Field(default=180, ge=60, le=300)
    max_concurrent_synthesis: int = Field(default=2, ge=1, le=8)
    request_timeout_seconds: int = Field(default=60, ge=1, le=180)
    max_output_bytes: int = Field(default=26_214_400, ge=1_048_576, le=104_857_600)
    say_path: str = "/usr/bin/say"
    ffmpeg_path: str = "ffmpeg"

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("TTS_API_KEY must not be blank")
        return value

    @model_validator(mode="after")
    def enabled_auth_requires_key(self) -> _SettingsValues:
        if self.auth_enabled and self.api_key is None:
            raise ValueError("TTS_API_KEY is required when TTS_AUTH_ENABLED is true")
        return self

    @field_validator("default_language")
    @classmethod
    def default_language_is_supported(cls, value: str) -> str:
        if value not in {"de-DE", "en-US", "en-GB"}:
            raise ValueError("TTS_DEFAULT_LANGUAGE must be de-DE, en-US, or en-GB")
        return value

    @field_validator("voice_de_de", "voice_en_us", "voice_en_gb", "host", "say_path", "ffmpeg_path")
    @classmethod
    def string_setting_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("configured string settings must not be blank")
        return value


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    auth_enabled: bool
    host: str
    port: int
    voice_de_de: str
    voice_en_us: str
    voice_en_gb: str
    default_language: str
    min_detection_chars: int
    base_rate_wpm: int
    max_concurrent_synthesis: int
    request_timeout_seconds: int
    max_output_bytes: int
    say_path: str
    ffmpeg_path: str

    @classmethod
    def from_env(cls) -> Settings:
        env_to_field = {
            "TTS_API_KEY": "api_key",
            "TTS_AUTH_ENABLED": "auth_enabled",
            "TTS_HOST": "host",
            "TTS_PORT": "port",
            "TTS_VOICE_DE_DE": "voice_de_de",
            "TTS_VOICE_EN_US": "voice_en_us",
            "TTS_VOICE_EN_GB": "voice_en_gb",
            "TTS_DEFAULT_LANGUAGE": "default_language",
            "TTS_MIN_DETECTION_CHARS": "min_detection_chars",
            "TTS_BASE_RATE_WPM": "base_rate_wpm",
            "TTS_MAX_CONCURRENT_SYNTHESIS": "max_concurrent_synthesis",
            "TTS_REQUEST_TIMEOUT_SECONDS": "request_timeout_seconds",
            "TTS_MAX_OUTPUT_BYTES": "max_output_bytes",
            "TTS_SAY_PATH": "say_path",
            "TTS_FFMPEG_PATH": "ffmpeg_path",
        }
        values = {
            field: os.environ[env_name]
            for env_name, field in env_to_field.items()
            if env_name in os.environ
        }
        parsed = _SettingsValues.model_validate(values)
        return cls(**parsed.model_dump())
