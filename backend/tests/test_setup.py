import json
import subprocess
from pathlib import Path

import pytest

import setup


def _ready_report():
    return {"ready": True, "complete": True, "diagnostics": []}


def _install_plan(monkeypatch, destination):
    monkeypatch.setattr(setup, "inspect_prerequisites", lambda **_kwargs: _ready_report())
    return setup.build_plan(destination)


def _successful_command(args, **kwargs):
    if len(args) > 1 and args[1] == "sync":
        environment = kwargs["env"]
        interpreter = Path(environment["UV_PROJECT_ENVIRONMENT"]) / "bin" / "python"
        interpreter.parent.mkdir(parents=True, exist_ok=True)
        interpreter.write_text("test interpreter", encoding="utf-8")
    return subprocess.CompletedProcess(args, 0, "verified", "")


def test_plan_requires_explicit_acceptance_and_exact_plan_id(monkeypatch, tmp_path):
    destination = tmp_path / "environment"
    plan = _install_plan(monkeypatch, destination)
    calls = []

    outcome = setup.apply_plan(plan, runner=lambda *args, **kwargs: calls.append(args))
    assert outcome["status"] == "approval-required"
    assert calls == []
    assert not destination.exists()

    outcome = setup.apply_plan(plan, accepted_plan="wrong-plan", runner=_successful_command)
    assert outcome["status"] == "approval-required"
    assert not destination.exists()


def test_plan_only_cli_reports_changes_without_mutation(monkeypatch, tmp_path, capsys):
    destination = tmp_path / "environment"
    monkeypatch.setattr(setup, "inspect_prerequisites", lambda **_kwargs: _ready_report())

    assert setup.main(["--destination", str(destination), "--json"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["plan"]["changes"]
    assert output["plan"]["id"]
    assert not destination.exists()


def test_unsupported_host_refuses_installation(monkeypatch, tmp_path):
    report = {
        "ready": False,
        "complete": True,
        "diagnostics": [{"id": "os", "status": "fail", "reason": "Unsupported host"}],
    }
    monkeypatch.setattr(setup, "inspect_prerequisites", lambda **_kwargs: report)
    plan = setup.build_plan(tmp_path / "environment")
    calls = []

    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=lambda *args, **kwargs: calls.append(args))

    assert outcome["status"] == "blocked"
    assert calls == []


def test_existing_unmanaged_destination_is_not_modified(monkeypatch, tmp_path):
    destination = tmp_path / "environment"
    destination.mkdir()
    existing = destination / "keep.txt"
    existing.write_text("existing installation", encoding="utf-8")
    plan = _install_plan(monkeypatch, destination)
    calls = []

    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=lambda *args, **kwargs: calls.append(args))

    assert outcome["status"] == "blocked"
    assert calls == []
    assert existing.read_text(encoding="utf-8") == "existing installation"


def test_lock_contention_prevents_changes(monkeypatch, tmp_path):
    destination = tmp_path / "environment"
    plan = _install_plan(monkeypatch, destination)
    calls = []

    def lock_contended(*_args):
        raise BlockingIOError

    monkeypatch.setattr(setup.fcntl, "flock", lock_contended)
    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=lambda *args, **kwargs: calls.append(args))

    assert outcome["status"] == "locked"
    assert calls == []
    assert not destination.exists()


def test_failed_install_removes_only_new_environment_and_preserves_credential(monkeypatch, tmp_path):
    destination = tmp_path / "environment"
    credential = tmp_path / "credential"
    credential.write_text("synthetic-secret-marker", encoding="utf-8")
    plan = _install_plan(monkeypatch, destination)

    def failed_command(args, **_kwargs):
        destination.joinpath("partial").write_text("partial", encoding="utf-8")
        return subprocess.CompletedProcess(args, 1, "", "synthetic-secret-marker")

    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=failed_command)

    assert outcome["status"] == "failed"
    assert not destination.exists()
    assert credential.read_text(encoding="utf-8") == "synthetic-secret-marker"
    assert "synthetic-secret-marker" not in json.dumps(outcome)


def test_success_is_verified_and_repeat_run_is_a_noop(monkeypatch, tmp_path):
    destination = tmp_path / "environment"
    plan = _install_plan(monkeypatch, destination)
    calls = []

    def runner(args, **kwargs):
        calls.append(args)
        assert "TTS_API_KEY" not in kwargs["env"]
        assert "GITHUB_TOKEN" not in kwargs["env"]
        return _successful_command(args, **kwargs)

    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=runner)

    assert outcome["status"] == "complete"
    assert outcome["verified"] is True
    assert len(calls) >= 2
    assert all("sudo" not in arg for command in calls for arg in command)

    repeat_plan = setup.build_plan(destination)
    repeat_calls = []
    repeat = setup.apply_plan(
        repeat_plan,
        accepted_plan=repeat_plan["id"],
        runner=lambda *args, **kwargs: repeat_calls.append(args),
    )
    assert repeat["status"] == "no-op"
    assert repeat_calls == []


def test_failed_verification_preserves_existing_credentials(monkeypatch, tmp_path):
    destination = tmp_path / "environment"
    credential = tmp_path / "credential"
    credential.write_text("existing-key", encoding="utf-8")
    plan = _install_plan(monkeypatch, destination)
    calls = 0

    def runner(args, **kwargs):
        nonlocal calls
        calls += 1
        return (
            _successful_command(args, **kwargs)
            if calls == 1
            else subprocess.CompletedProcess(args, 1, "", "")
        )

    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=runner)

    assert outcome["status"] == "failed"
    assert not destination.exists()
    assert credential.read_text(encoding="utf-8") == "existing-key"


def test_missing_uv_is_actionable_without_bootstrap(monkeypatch, tmp_path):
    report = {
        "ready": False,
        "complete": True,
        "diagnostics": [{"id": "uv", "status": "fail", "reason": "uv missing"}],
    }
    monkeypatch.setattr(setup, "inspect_prerequisites", lambda **_kwargs: report)
    plan = setup.build_plan(tmp_path / "environment")
    outcome = setup.apply_plan(plan, accepted_plan=plan["id"], runner=_successful_command)

    assert outcome["status"] == "blocked"
    assert "uv" in json.dumps(outcome).lower()
