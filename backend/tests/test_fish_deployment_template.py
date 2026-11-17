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


def test_prototype_operations_quarantines_stale_startup_and_waits_boundedly():
    runbook = (
        Path(__file__).parents[1] / "deployment" / "prototype-operations.md"
    ).read_text(encoding="utf-8")

    assert "launchctl disable" in runbook
    assert 'grep -F "=> disabled"' in runbook
    assert 'mv "<LEGACY_PLIST>" "<LEGACY_PLIST>.quarantined"' in runbook
    assert "sleep 0.25" in runbook
    assert '"$attempt" -lt 40' in runbook
    assert "Do not continue after a wait timeout" in runbook
