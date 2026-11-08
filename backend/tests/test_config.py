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


def test_protected_credential_file_is_used(monkeypatch, tmp_path):
    credential = tmp_path / "credential"
    credential.write_text("test-file-key\n", encoding="utf-8")
    credential.chmod(0o600)
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.setenv("TTS_API_KEY_FILE", str(credential))
    assert Settings.from_env().api_key == "test-file-key"


def test_credential_sources_must_not_conflict(monkeypatch, tmp_path):
    credential = tmp_path / "credential"
    credential.write_text("file-key", encoding="utf-8")
    credential.chmod(0o600)
    monkeypatch.setenv("TTS_API_KEY", "environment-key")
    monkeypatch.setenv("TTS_API_KEY_FILE", str(credential))
    with pytest.raises(ValueError):
        Settings.from_env()


@pytest.mark.parametrize("mode", [0o640, 0o644, 0o666])
def test_credential_file_requires_private_permissions(monkeypatch, tmp_path, mode):
    credential = tmp_path / "credential"
    credential.write_text("file-key", encoding="utf-8")
    credential.chmod(mode)
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.setenv("TTS_API_KEY_FILE", str(credential))
    with pytest.raises(ValueError):
        Settings.from_env()


@pytest.mark.parametrize("contents", ["", "  \n"])
def test_empty_credential_file_is_rejected(monkeypatch, tmp_path, contents):
    credential = tmp_path / "credential"
    credential.write_text(contents, encoding="utf-8")
    credential.chmod(0o600)
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.setenv("TTS_API_KEY_FILE", str(credential))
    with pytest.raises(ValueError):
        Settings.from_env()


def test_missing_credential_file_is_rejected(monkeypatch, tmp_path):
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.setenv("TTS_API_KEY_FILE", str(tmp_path / "missing"))
    with pytest.raises(ValueError):
        Settings.from_env()


def test_credential_symlink_is_rejected(monkeypatch, tmp_path):
    credential = tmp_path / "credential"
    credential.write_text("file-key", encoding="utf-8")
    credential.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(credential)
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.setenv("TTS_API_KEY_FILE", str(link))
    with pytest.raises(ValueError):
        Settings.from_env()


def test_invalid_settings_do_not_include_credential_in_error(monkeypatch):
    monkeypatch.setenv("TTS_API_KEY", "synthetic-secret-marker")
    monkeypatch.setenv("TTS_PORT", "invalid")
    with pytest.raises(ValueError) as exc:
        Settings.from_env()
    assert "synthetic-secret-marker" not in str(exc.value)


@pytest.mark.parametrize("value", ["0", "-1", "invalid"])
def test_temporary_disk_budget_must_be_positive(monkeypatch, value):
    monkeypatch.setenv("TTS_MAX_TEMP_BYTES", value)
    with pytest.raises(ValueError):
        Settings.from_env()


def test_default_temporary_disk_budget(settings):
    assert settings.max_temp_bytes == 256 * 1024 * 1024
