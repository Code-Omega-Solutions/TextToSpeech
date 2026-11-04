import pytest
from pydantic import ValidationError

from app.config import Settings


def test_api_key_is_required(monkeypatch):
    monkeypatch.setenv("TTS_AUTH_ENABLED", "true")
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings.from_env()


def test_auth_can_be_disabled_explicitly_without_an_api_key(monkeypatch):
    monkeypatch.setenv("TTS_AUTH_ENABLED", "false")
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    assert Settings.from_env().auth_enabled is False


def test_auth_is_enabled_by_default(settings):
    assert settings.auth_enabled is True


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("TTS_API_KEY", "   "),
        ("TTS_PORT", "0"),
        ("TTS_PORT", "65536"),
        ("TTS_BASE_RATE_WPM", "59"),
        ("TTS_MAX_CONCURRENT_SYNTHESIS", "9"),
        ("TTS_REQUEST_TIMEOUT_SECONDS", "181"),
        ("TTS_MAX_OUTPUT_BYTES", "1024"),
        ("TTS_DEFAULT_LANGUAGE", "fr"),
        ("TTS_MIN_DETECTION_CHARS", "1001"),
    ],
)
def test_invalid_environment_settings_are_rejected(monkeypatch, name, value):
    monkeypatch.setenv("TTS_API_KEY", "unit-test-api-key")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings.from_env()


def test_defaults_and_environment_values(settings):
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.voice_de_de == "Anna (Deutsch (Deutschland))"
    assert settings.voice_en_us == "Samantha"
    assert settings.voice_en_gb == "Daniel"
    assert settings.max_output_bytes == 26_214_400
