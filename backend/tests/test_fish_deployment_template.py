import plistlib
from pathlib import Path


def test_prototype_template_is_native_only_until_fish_gates_are_closed():
    template = Path(__file__).parents[1] / "deployment" / (
        "com.example.private-speech-studio-backend.plist"
    )
    with template.open("rb") as document:
        plist = plistlib.load(document)

    environment = plist["EnvironmentVariables"]
    assert environment["TTS_FISH_ENABLED"] == "false"
    assert environment["TTS_FISH_ARTIFACTS_APPROVED"] == "false"
    assert environment["TTS_FISH_REFERENCES_APPROVED"] == "false"
    assert "TTS_FISH_WORKER_COMMAND" not in environment
    assert "FISH_SOURCE_ROOT" not in environment
    assert "FISH_CHECKPOINT_ROOT" not in environment
