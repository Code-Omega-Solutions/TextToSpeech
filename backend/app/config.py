from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass, field
from ipaddress import ip_address
from pathlib import Path
from types import MappingProxyType
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _SettingsValues(BaseModel):
    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

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
    max_temp_bytes: int = Field(default=268_435_456, ge=1, le=1_073_741_824)
    say_path: str = "/usr/bin/say"
    ffmpeg_path: str = "ffmpeg"
    default_backend: Literal["macos-say", "phonon"] = "macos-say"
    phonon_enabled: bool = False
    phonon_server_url: str | None = None
    phonon_request_timeout_seconds: int = Field(default=30, ge=1, le=180)
    phonon_approval_file: str | None = None
    vibevoice_enabled: bool = False
    vibevoice_research_only: bool = False
    vibevoice_qualified: bool = False
    vibevoice_worker_timeout_seconds: int = Field(default=60, ge=1, le=180)
    vibevoice_worker_python: str | None = None
    vibevoice_source_path: str | None = None
    vibevoice_model_path: str | None = None
    vibevoice_worker_peak_memory_bytes: int | None = Field(default=None, ge=1)
    higher_priority_memory_reserve_bytes: int | None = Field(default=None, ge=1)
    @model_validator(mode="after")
    def vibevoice_requires_qualification_and_budgets(self) -> _SettingsValues:
        if self.default_backend == "vibevoice" and not self.vibevoice_enabled:
            raise ValueError("TTS_DEFAULT_BACKEND=vibevoice requires TTS_VIBEVOICE_ENABLED=true")
        if self.vibevoice_enabled:
            if not self.vibevoice_research_only:
                raise ValueError("VibeVoice is approved for research-only use")
            if not self.vibevoice_qualified:
                raise ValueError("VibeVoice must be qualified before it can be enabled")
            if (
                self.vibevoice_worker_peak_memory_bytes is None
                or self.higher_priority_memory_reserve_bytes is None
            ):
                raise ValueError("VibeVoice requires measured worker and memory reserve budgets")
        return self

    @model_validator(mode="after")
    def phonon_default_requires_explicit_enable(self) -> _SettingsValues:
        if self.default_backend == "phonon" and not self.phonon_enabled:
            raise ValueError("TTS_DEFAULT_BACKEND=phonon requires TTS_PHONON_ENABLED=true")
        return self

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("TTS_API_KEY must not be blank")
        return value

    @field_validator("phonon_server_url")
    @classmethod
    def phonon_server_must_be_loopback_origin(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname
            port = parsed.port
            loopback = hostname == "localhost"
            if hostname is not None and not loopback:
                loopback = ip_address(hostname).is_loopback
        except ValueError:
            loopback = False
            parsed = None
            port = None
        if (
            parsed is None
            or parsed.scheme not in {"http", "https"}
            or not loopback
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or port is not None and not 1 <= port <= 65535
        ):
            raise ValueError("TTS_PHONON_SERVER_URL must be an HTTP(S) loopback origin")
        return value.rstrip("/")

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

    @field_validator("phonon_approval_file", "vibevoice_worker_python", "vibevoice_source_path", "vibevoice_model_path")
    @classmethod
    def optional_path_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("configured path settings must not be blank")
        return value


@dataclass(frozen=True)
class Settings:
    api_key: str | None = field(repr=False)
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
    max_temp_bytes: int
    say_path: str
    ffmpeg_path: str
    default_backend: Literal["macos-say", "phonon"]
    vibevoice_enabled: bool
    vibevoice_research_only: bool
    vibevoice_qualified: bool
    vibevoice_worker_timeout_seconds: int
    vibevoice_worker_python: str | None
    vibevoice_source_path: str | None
    vibevoice_model_path: str | None
    vibevoice_worker_peak_memory_bytes: int | None
    higher_priority_memory_reserve_bytes: int | None
    phonon_enabled: bool = False
    phonon_server_url: str | None = None
    phonon_request_timeout_seconds: int = 30
    phonon_approval_file: str | None = None
    phonon_approval: PhononApproval | None = None

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
            "TTS_MAX_TEMP_BYTES": "max_temp_bytes",
            "TTS_SAY_PATH": "say_path",
            "TTS_FFMPEG_PATH": "ffmpeg_path",
            "TTS_DEFAULT_BACKEND": "default_backend",
            "TTS_PHONON_ENABLED": "phonon_enabled",
            "TTS_PHONON_SERVER_URL": "phonon_server_url",
            "TTS_PHONON_REQUEST_TIMEOUT_SECONDS": "phonon_request_timeout_seconds",
            "TTS_PHONON_APPROVAL_FILE": "phonon_approval_file",
            "TTS_VIBEVOICE_ENABLED": "vibevoice_enabled",
            "TTS_VIBEVOICE_RESEARCH_ONLY": "vibevoice_research_only",
            "TTS_VIBEVOICE_QUALIFIED": "vibevoice_qualified",
            "TTS_VIBEVOICE_WORKER_TIMEOUT_SECONDS": "vibevoice_worker_timeout_seconds",
            "TTS_VIBEVOICE_WORKER_PYTHON": "vibevoice_worker_python",
            "TTS_VIBEVOICE_SOURCE_PATH": "vibevoice_source_path",
            "TTS_VIBEVOICE_MODEL_PATH": "vibevoice_model_path",
            "TTS_VIBEVOICE_WORKER_PEAK_MEMORY_BYTES": "vibevoice_worker_peak_memory_bytes",
            "TTS_HIGHER_PRIORITY_MEMORY_RESERVE_BYTES": "higher_priority_memory_reserve_bytes",
        }
        values = {
            field: os.environ[env_name]
            for env_name, field in env_to_field.items()
            if env_name in os.environ
        }
        if "TTS_API_KEY_FILE" in os.environ:
            if "TTS_API_KEY" in os.environ:
                raise ValueError("TTS_API_KEY and TTS_API_KEY_FILE cannot both be set")
            values["api_key"] = _read_credential_file(os.environ["TTS_API_KEY_FILE"])
        parsed = _SettingsValues.model_validate(values)
        return cls(
            **parsed.model_dump(),
            phonon_approval=load_phonon_approval(parsed.phonon_approval_file),
        )


@dataclass(frozen=True)
class PhononApproval:
    models_by_language: dict[str, str]
    model_digests_by_language: dict[str, str]
    voices_by_language: dict[str, tuple[str, ...]]
    default_voices_by_language: dict[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "models_by_language", MappingProxyType(dict(self.models_by_language))
        )
        object.__setattr__(
            self, "model_digests_by_language",
            MappingProxyType(dict(self.model_digests_by_language)),
        )
        object.__setattr__(
            self,
            "voices_by_language",
            MappingProxyType(
                {language: tuple(voices) for language, voices in self.voices_by_language.items()}
            ),
        )
        object.__setattr__(
            self,
            "default_voices_by_language",
            MappingProxyType(dict(self.default_voices_by_language)),
        )


_PHONON_LANGUAGES = {"en-US", "de-DE"}
_PHONON_APPROVAL_MAX_BYTES = 64 * 1024


def _approved_provenance(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    return all(
        isinstance(record.get(field), str) and bool(record[field].strip())
        for field in ("source_revision", "terms_revision")
    ) and all(
        isinstance(record.get(field), str) and record[field].startswith("https://")
        for field in ("source_url", "terms_url")
    ) and record.get("terms_status") == "approved"


def load_phonon_approval(path: str | None) -> PhononApproval | None:
    """Load a bounded, explicit provenance record; invalid records fail closed."""
    if not path:
        return None
    try:
        candidate = Path(path).expanduser()
        if candidate.is_symlink() or not candidate.is_file():
            return None
        details = candidate.stat()
        if (
            not stat.S_ISREG(details.st_mode)
            or details.st_size > _PHONON_APPROVAL_MAX_BYTES
            or os.name != "nt"
            and details.st_uid != os.geteuid()
            or os.name != "nt"
            and details.st_mode & 0o022
        ):
            return None
        document = json.loads(candidate.read_text(encoding="utf-8"))
        if (
            not isinstance(document, dict)
            or document.get("status") != "approved"
            or document.get("intended_use") != "private-noncommercial"
            or set(document.get("models", {})) != _PHONON_LANGUAGES
            or set(document.get("voices", {})) != _PHONON_LANGUAGES
        ):
            return None

        models: dict[str, str] = {}
        digests: dict[str, str] = {}
        voices: dict[str, tuple[str, ...]] = {}
        defaults: dict[str, str] = {}
        for language in _PHONON_LANGUAGES:
            model_record = document["models"][language]
            voice_record = document["voices"][language]
            if (
                not isinstance(model_record, dict)
                or not isinstance(model_record.get("tag"), str)
                or not model_record["tag"].strip()
                or len(model_record["tag"]) > 128
                or any(character.isspace() or ord(character) < 32 for character in model_record["tag"])
                or not isinstance(model_record.get("digest"), str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", model_record["digest"]) is None
                or not _approved_provenance(model_record)
                or not isinstance(model_record.get("license"), str)
                or not model_record["license"].strip()
                or not isinstance(voice_record, dict)
                or not _approved_provenance(voice_record)
            ):
                return None
            voice_ids = voice_record.get("ids")
            default_voice = voice_record.get("default")
            if (
                not isinstance(voice_ids, list)
                or not voice_ids
                or any(
                    not isinstance(voice, str)
                    or not voice.strip()
                    or voice != voice.strip()
                    or len(voice) > 128
                    or any(ord(character) < 32 for character in voice)
                    for voice in voice_ids
                )
                or len(set(voice_ids)) != len(voice_ids)
                or default_voice not in voice_ids
            ):
                return None
            models[language] = model_record["tag"]
            digests[language] = model_record["digest"]
            voices[language] = tuple(voice_ids)
            defaults[language] = default_voice
        return PhononApproval(models, digests, voices, defaults)
    except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _read_credential_file(path: str) -> str:
    if not path:
        raise ValueError("Credential file is unavailable or not protected")
    try:
        fd = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        with os.fdopen(fd, "rb") as credential_file:
            info = os.fstat(credential_file.fileno())
            owner_uid = (
                os.geteuid() if hasattr(os, "geteuid") else info.st_uid
            )
            permissions_unverifiable = os.name == "nt"
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != owner_uid
                or (not permissions_unverifiable and info.st_mode & 0o077)
            ):
                raise ValueError("Credential file is unavailable or not protected")
            contents = credential_file.read(4097)
        if len(contents) > 4096:
            raise ValueError("Credential file is invalid")
        credential = contents.decode("utf-8").removesuffix("\r\n").removesuffix("\n")
        if not credential.strip() or "\n" in credential or "\r" in credential:
            raise ValueError("Credential file is invalid")
        return credential
    except (OSError, UnicodeError):
        raise ValueError("Credential file is unavailable or not protected") from None
