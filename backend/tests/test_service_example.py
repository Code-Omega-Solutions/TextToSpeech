import plistlib
from pathlib import Path


SERVICE_EXAMPLE = (
    Path(__file__).parents[1] / "service" / "com.example.texttospeech.plist"
)


def _service() -> dict:
    with SERVICE_EXAMPLE.open("rb") as service_file:
        return plistlib.load(service_file)


def test_service_example_uses_operator_selected_paths_and_safe_path():
    service = _service()
    arguments = service["ProgramArguments"]
    environment = service["EnvironmentVariables"]

    assert service["Label"] == "com.example.texttospeech"
    assert service["WorkingDirectory"] == "/PATH/TO/texttospeech/backend"
    assert arguments == [
        "/PATH/TO/texttospeech/backend/.venv/bin/python",
        "-m",
        "app.main",
    ]
    assert environment["PATH"] == "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
    assert "TTS_API_KEY_FILE" in environment
    assert environment["TTS_API_KEY_FILE"] == "<USER_HOME>/.config/texttospeech/api-key"


def test_service_example_is_opt_in_and_contains_no_host_or_secret():
    raw = SERVICE_EXAMPLE.read_text(encoding="utf-8")
    service = _service()

    assert service["RunAtLoad"] is False
    assert service["KeepAlive"] is False
    assert "UserName" not in service
    assert "TTS_API_KEY" not in service["EnvironmentVariables"]
    assert "synthetic-secret-marker" not in raw
    assert "/home/" not in raw
    assert "/Users/" not in raw
