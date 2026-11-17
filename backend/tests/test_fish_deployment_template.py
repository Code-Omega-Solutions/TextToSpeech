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
    assert 'LEGACY_QUARANTINE="${LEGACY_PLIST}.quarantined"' in runbook
    assert 'mv "$LEGACY_PLIST" "$LEGACY_QUARANTINE"' in runbook
    assert 'WAIT_ATTEMPTS=40' in runbook
    assert 'WAIT_SECONDS=0.25' in runbook
    assert "bootout_if_loaded" in runbook
    assert "wait_present" in runbook
    assert 'PROTECTED_DIR="$(mktemp -d' in runbook
    assert 'cp -p "$PROTECTED_DIR/backend.plist" "$BACKEND_PLIST"' in runbook
    assert "rollback_required=1" in runbook
    assert "trap '" in runbook
    assert "Never continue after a wait timeout" in runbook
