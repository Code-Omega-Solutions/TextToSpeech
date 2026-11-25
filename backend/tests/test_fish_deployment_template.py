import os
import plistlib
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_prototype_template_does_not_configure_retired_fish_runtime():
    template = Path(__file__).parents[1] / "deployment" / (
        "com.example.private-speech-studio-backend.plist"
    )
    with template.open("rb") as document:
        plist = plistlib.load(document)

    environment = plist["EnvironmentVariables"]
    assert not any(
        name.startswith("TTS_FISH_")
        or name in {"FISH_SOURCE_ROOT", "FISH_CHECKPOINT_ROOT"}
        for name in environment
    )


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
    assert "prototype-recreation.zsh" in runbook
    assert "VERIFY_SCRIPT" in runbook
    assert "rollback_required=1" in runbook
    assert "exit_code" in runbook
    assert "com.example.private-speech-studio-prototype" in runbook
    assert "com.example.private-speech-studio-ui" in runbook
    assert "atomic" in runbook
    assert "0600" in runbook
    assert "Never continue after a wait timeout" in runbook


def test_prototype_recreation_helper_has_portable_exit_trap_and_tests():
    deployment = Path(__file__).parents[1] / "deployment"
    helper = (deployment / "prototype-recreation.zsh").read_text(encoding="utf-8")
    test = deployment / "test_prototype_recreation.zsh"
    test_text = test.read_text(encoding="utf-8")

    assert "exit_code=$?" in helper
    assert 'exit "$exit_code"' in helper
    assert "status=$?" not in helper
    assert test_text.startswith("#!/bin/zsh")
    assert "run_case success 0" in test_text
    assert "run_case forced-failure 1" in test_text
    tracked_mode = subprocess.run(
        [
            "git",
            "ls-files",
            "--stage",
            "--",
            str(test.relative_to(ROOT)).replace("\\", "/"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split(maxsplit=1)[0]
    assert tracked_mode == "100755"
    if os.name != "nt":
        assert test.stat().st_mode & stat.S_IXUSR
    assert "MANAGED_BACKEND_LABEL" in helper
    assert "MANAGED_UI_LABEL" in helper
    assert "MANAGED_BACKEND_PLIST_NAME" in helper
    assert "MANAGED_UI_PLIST_NAME" in helper
    assert "production labels" not in helper
    assert "restore_plist" in helper
    assert 'mv -f "$temporary" "$destination"' in helper


def test_companion_validation_hook_runs_native_recreation_tests_when_available():
    hook = (
        Path(__file__).parents[2] / "checks" / "run_companion_validation.sh"
    ).read_text(encoding="utf-8")

    assert "command -v zsh" in hook
    assert "zsh backend/deployment/test_prototype_recreation.zsh" in hook
