from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from ipaddress import ip_address
from pathlib import PurePosixPath
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
    default_backend: Literal["macos-say", "fish-speech"] = "macos-say"
    fish_enabled: bool = False
    fish_server_url: str | None = None
    fish_api_key: str | None = Field(default=None, repr=False)
    fish_request_timeout_seconds: int = Field(default=30, ge=1, le=180)
    fish_artifact_manifest: str | None = None
    fish_reference_manifest: str | None = None
    fish_artifacts_approved: bool = False
    fish_references_approved: bool = False
    fish_opportunistic: bool = False
    fish_worker_command: tuple[str, ...] | None = Field(default=None, repr=False)
    fish_worker_peak_memory_bytes: int = Field(default=16 * 1024**3, ge=1)
    fish_memory_reserve_bytes: int = Field(default=12 * 1024**3, ge=1)
    fish_idle_timeout_seconds: int = Field(default=30, ge=1, le=600)
    fish_cooldown_seconds: int = Field(default=30, ge=1, le=600)
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
    def fish_requires_loopback_service_and_credential(self) -> _SettingsValues:
        if self.default_backend == "fish-speech" and not self.fish_enabled and not self.fish_opportunistic:
            raise ValueError("TTS_DEFAULT_BACKEND=fish-speech requires TTS_FISH_ENABLED=true")
        if self.fish_enabled and (
            self.fish_server_url is None
            or self.fish_api_key is None and self.api_key is None
        ):
            raise ValueError(
                "Fish Speech requires a loopback service URL and the shared API key"
            )
        if self.fish_enabled and not self.fish_artifacts_approved:
            raise ValueError(
                "Fish Speech requires exact artifact metadata and terms approval"
            )
        if self.fish_enabled and not self.fish_artifact_manifest:
            raise ValueError("Fish Speech requires an exact artifact approval manifest")
        if self.fish_enabled and not self.fish_references_approved:
            raise ValueError(
                "Fish Speech requires approved German/English reference voices"
            )
        if self.fish_enabled and not self.fish_reference_manifest:
            raise ValueError("Fish Speech requires a qualified reference manifest")
        if self.fish_opportunistic:
            if self.fish_enabled and self.fish_worker_command is None:
                raise ValueError("Opportunistic Fish requires a managed worker command")
            if self.max_concurrent_synthesis < 2:
                raise ValueError("Opportunistic Fish requires reserved native capacity")
        return self

    @field_validator("fish_worker_command", mode="before")
    @classmethod
    def fish_command_is_local_argv(cls, value: object) -> tuple[str, ...] | None:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                raise ValueError("Fish worker command must be a JSON argv list") from None
        if (
            not isinstance(value, (list, tuple))
            or not value
            or any(not isinstance(part, str) or not part.strip() or "\0" in part for part in value)
        ):
            raise ValueError("Fish worker command must be a nonempty string argv list")
        if not PurePosixPath(value[0]).is_absolute():
            raise ValueError("Fish worker executable must be an absolute POSIX path")
        return tuple(value)

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("TTS_API_KEY must not be blank")
        return value

    @field_validator("fish_api_key")
    @classmethod
    def fish_api_key_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and (not value.strip() or "\n" in value or "\r" in value):
            raise ValueError("TTS_FISH_API_KEY must be a nonempty single-line credential")
        return value

    @field_validator("fish_server_url")
    @classmethod
    def fish_server_must_be_loopback_origin(cls, value: str | None) -> str | None:
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
            raise ValueError("TTS_FISH_SERVER_URL must be an HTTP(S) loopback origin")
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

    @field_validator(
        "fish_artifact_manifest",
        "fish_reference_manifest",
        "vibevoice_worker_python",
        "vibevoice_source_path",
        "vibevoice_model_path",
    )
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
    default_backend: Literal["macos-say", "fish-speech"]
    fish_enabled: bool
    fish_server_url: str | None
    fish_api_key: str | None = field(repr=False)
    fish_request_timeout_seconds: int
    fish_artifact_manifest: str | None
    fish_reference_manifest: str | None
    fish_artifacts_approved: bool
    fish_references_approved: bool
    vibevoice_enabled: bool
    vibevoice_research_only: bool
    vibevoice_qualified: bool
    vibevoice_worker_timeout_seconds: int
    vibevoice_worker_python: str | None
    vibevoice_source_path: str | None
    vibevoice_model_path: str | None
    vibevoice_worker_peak_memory_bytes: int | None
    higher_priority_memory_reserve_bytes: int | None
    fish_opportunistic: bool = False
    fish_worker_command: tuple[str, ...] | None = field(default=None, repr=False)
    fish_worker_peak_memory_bytes: int = 16 * 1024**3
    fish_memory_reserve_bytes: int = 12 * 1024**3
    fish_idle_timeout_seconds: int = 30
    fish_cooldown_seconds: int = 30

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
            "TTS_FISH_ENABLED": "fish_enabled",
            "TTS_FISH_SERVER_URL": "fish_server_url",
            "TTS_FISH_API_KEY": "fish_api_key",
            "TTS_FISH_REQUEST_TIMEOUT_SECONDS": "fish_request_timeout_seconds",
            "FISH_ARTIFACT_MANIFEST": "fish_artifact_manifest",
            "FISH_REFERENCE_MANIFEST": "fish_reference_manifest",
            "TTS_FISH_ARTIFACTS_APPROVED": "fish_artifacts_approved",
            "TTS_FISH_REFERENCES_APPROVED": "fish_references_approved",
            "TTS_FISH_OPPORTUNISTIC": "fish_opportunistic",
            "TTS_FISH_WORKER_COMMAND": "fish_worker_command",
            "TTS_FISH_WORKER_PEAK_MEMORY_BYTES": "fish_worker_peak_memory_bytes",
            "TTS_FISH_MEMORY_RESERVE_BYTES": "fish_memory_reserve_bytes",
            "TTS_FISH_IDLE_TIMEOUT_SECONDS": "fish_idle_timeout_seconds",
            "TTS_FISH_COOLDOWN_SECONDS": "fish_cooldown_seconds",
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
        if "TTS_FISH_API_KEY_FILE" in os.environ:
            if "TTS_FISH_API_KEY" in os.environ:
                raise ValueError("TTS_FISH_API_KEY and TTS_FISH_API_KEY_FILE cannot both be set")
            values["fish_api_key"] = _read_credential_file(os.environ["TTS_FISH_API_KEY_FILE"])
        if (
            str(values.get("fish_enabled", "")).lower() in {"true", "1", "yes", "on"}
            and "fish_api_key" not in values
            and "api_key" in values
        ):
            # Fish is an internal prototype transport. Reuse the authenticated
            # backend bearer credential rather than provisioning a second secret.
            values["fish_api_key"] = values["api_key"]
        parsed = _SettingsValues.model_validate(values)
        return cls(**parsed.model_dump())


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
