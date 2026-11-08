from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from prerequisites import inspect_prerequisites

try:
    import fcntl
except ImportError:  # pragma: no cover - unavailable on Windows
    fcntl = None

_BACKEND_DIR = Path(__file__).resolve().parent
_LOCKED_INSTALL_PREREQUISITES = {
    "architecture",
    "configuration",
    "destination",
    "disk",
    "os",
    "python",
    "uv",
}
_SETUP_TIMEOUT_SECONDS = 600
_MARKER_NAME = ".texttospeech-managed.json"


def _lock_hash() -> str:
    return hashlib.sha256((_BACKEND_DIR / "uv.lock").read_bytes()).hexdigest()


def _environment_path(destination: Path) -> Path:
    return destination / "bin" / "python"


def _marker_path(destination: Path) -> Path:
    return destination / _MARKER_NAME


def _managed_environment_is_compatible(destination: Path, lock_hash: str) -> bool:
    try:
        marker = json.loads(_marker_path(destination).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        marker.get("schema") == 1
        and marker.get("lock_hash") == lock_hash
        and marker.get("python") == f"{sys.version_info.major}.{sys.version_info.minor}"
        and _environment_path(destination).is_file()
    )


def _blocking_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report.get("complete", False):
        return [
            {
                "id": "diagnostic-operation",
                "reason": "Prerequisite inspection did not complete.",
            }
        ]
    return [
        item
        for item in report.get("diagnostics", [])
        if item.get("id") in _LOCKED_INSTALL_PREREQUISITES
        and item.get("status") == "fail"
    ]


def build_plan(destination: str | Path) -> dict[str, Any]:
    target = Path(destination).expanduser()
    if not target.is_absolute():
        raise ValueError("Installation destination must be an absolute path.")
    lock_hash = _lock_hash()
    report = inspect_prerequisites(
        env={**os.environ, "TTS_DESTINATION": str(target)}
    )
    blockers = _blocking_diagnostics(report)
    if not target.parent.is_dir() or not os.access(target.parent, os.W_OK | os.X_OK):
        blockers.append(
            {
                "id": "destination",
                "reason": "The destination parent must already exist and be user-writable.",
            }
        )
    else:
        try:
            effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
            if effective_uid is not None and target.parent.stat().st_uid != effective_uid:
                blockers.append(
                    {
                        "id": "destination",
                        "reason": "The destination parent must be owned by the current user.",
                    }
                )
        except OSError:
            blockers.append(
                {"id": "destination", "reason": "The destination parent could not be inspected."}
            )
    if target.exists():
        if _managed_environment_is_compatible(target, lock_hash):
            action = "no-op"
            changes: list[str] = []
        else:
            action = "blocked"
            changes = []
            blockers.append(
                {
                    "id": "destination",
                    "reason": "Existing destination is not a compatible managed environment.",
                }
            )
    elif blockers:
        action = "blocked"
        changes = []
    else:
        action = "install"
        changes = [
            f"Create a dedicated Python environment at {target}.",
            "Install the locked backend dependencies with uv sync --locked.",
        ]
    plan_content = {
        "action": action,
        "destination": str(target),
        "lock_hash": lock_hash,
        "changes": changes,
        "blockers": blockers,
    }
    plan_id = hashlib.sha256(
        json.dumps(plan_content, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return {
        **plan_content,
        "id": plan_id,
        "ready_after_setup": report.get("ready", False),
        "diagnostics": report.get("diagnostics", []),
    }


def _lock_path(destination: Path) -> Path:
    identity = hashlib.sha256(str(destination).encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / f"texttospeech-setup-{os.getuid()}-{identity}.lock"


def _open_lock(destination: Path) -> int:
    if fcntl is None:
        raise OSError("Advisory file locking is unavailable.")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(_lock_path(destination), flags, 0o600)
    info = os.fstat(fd)
    effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
    if (
        not stat.S_ISREG(info.st_mode)
        or (effective_uid is not None and info.st_uid != effective_uid)
        or info.st_mode & 0o077
    ):
        os.close(fd)
        raise PermissionError("Setup lock is not private.")
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return fd


def _command_environment(destination: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key
        in {
            "PATH",
            "HOME",
            "TMPDIR",
            "TEMP",
            "TMP",
            "LANG",
            "LC_ALL",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
            "SYSTEMROOT",
            "WINDIR",
        }
    }
    environment["UV_PROJECT_ENVIRONMENT"] = str(destination)
    return environment


def _run_installation_command(
    runner: Callable[..., subprocess.CompletedProcess[str]],
    command: list[str],
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=_SETUP_TIMEOUT_SECONDS,
        stdin=subprocess.DEVNULL,
        shell=False,
        env=environment,
    )


def _write_marker(destination: Path, lock_hash: str) -> None:
    marker = {
        "schema": 1,
        "lock_hash": lock_hash,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    }
    fd = os.open(
        _marker_path(destination),
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
    with os.fdopen(fd, "w", encoding="utf-8") as marker_file:
        json.dump(marker, marker_file, sort_keys=True)
        marker_file.write("\n")


def _outcome(status: str, message: str, **details: Any) -> dict[str, Any]:
    return {"status": status, "message": message, **details}


def apply_plan(
    plan: dict[str, Any],
    *,
    accepted_plan: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    if accepted_plan != plan.get("id"):
        return _outcome(
            "approval-required",
            "Execution requires explicit acceptance of this exact plan.",
            plan_id=plan.get("id"),
        )
    if plan.get("action") == "blocked":
        return _outcome("blocked", "Setup is blocked by unresolved prerequisites.", blockers=plan["blockers"])
    if plan.get("action") == "no-op":
        return _outcome("no-op", "The managed environment already matches the lockfile.", verified=True)

    destination = Path(plan["destination"])
    current_plan = build_plan(destination)
    if current_plan.get("id") != plan.get("id") or current_plan.get("action") != "install":
        return _outcome("stale-plan", "Prerequisites or destination changed after planning.")

    try:
        lock_fd = _open_lock(destination)
    except BlockingIOError:
        return _outcome("locked", "Another setup operation is using this destination.")
    except OSError:
        return _outcome("failed", "A private setup lock could not be acquired.")

    created_destination = False
    try:
        if destination.exists():
            return _outcome("blocked", "Destination appeared after planning; it was not modified.")
        uv_path = shutil.which("uv")
        if uv_path is None:
            return _outcome("blocked", "uv is unavailable; install it from an approved channel.")
        destination.mkdir(mode=0o700)
        created_destination = True
        environment = _command_environment(destination)
        install_command = [
            uv_path,
            "sync",
            "--locked",
            "--project",
            str(_BACKEND_DIR),
            "--python",
            sys.executable,
        ]
        installed = _run_installation_command(runner, install_command, environment)
        if installed.returncode != 0:
            raise RuntimeError("locked dependency installation failed")

        interpreter = _environment_path(destination)
        if not interpreter.is_file():
            raise RuntimeError("managed Python environment was not created")
        verification = _run_installation_command(
            runner,
            [
                str(interpreter),
                "-c",
                "import fastapi, langid, pydantic, uvicorn",
            ],
            environment,
        )
        if verification.returncode != 0:
            raise RuntimeError("dependency verification failed")
        _write_marker(destination, plan["lock_hash"])
        final_report = inspect_prerequisites(
            env={**os.environ, "TTS_DESTINATION": str(destination)}
        )
        if not final_report.get("complete", False):
            return _outcome(
                "incomplete",
                "The environment was installed, but prerequisite rechecking did not complete.",
                verified=True,
                diagnostics=final_report.get("diagnostics", []),
            )
        if not final_report.get("ready", False):
            return _outcome(
                "incomplete",
                "The environment was installed; remaining prerequisites require operator action.",
                verified=True,
                diagnostics=final_report.get("diagnostics", []),
            )
        return _outcome("complete", "Locked dependencies are installed and prerequisites are ready.", verified=True)
    except (OSError, subprocess.SubprocessError, RuntimeError):
        if created_destination:
            shutil.rmtree(destination)
        return _outcome(
            "failed",
            "Setup failed; artifacts created by this attempt were removed.",
        )
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def _write_report(report: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(report, sort_keys=True))
        return
    if "plan" in report:
        plan = report["plan"]
        print(f"Setup plan {plan['id']}: {plan['action']}")
        for change in plan["changes"]:
            print(f"- {change}")
        for blocker in plan["blockers"]:
            print(f"BLOCKED {blocker.get('id', 'unknown')}: {blocker.get('reason', 'Unresolved')}")
    else:
        print(f"{report['status']}: {report['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan and explicitly approve backend setup.")
    parser.add_argument(
        "--destination",
        default=str(_BACKEND_DIR / ".venv"),
        help="absolute path for the dedicated environment",
    )
    parser.add_argument("--accept", help="accept the exact plan ID printed by a prior invocation")
    parser.add_argument("--json", action="store_true", help="write machine-readable output")
    try:
        args = parser.parse_args(argv)
        plan = build_plan(args.destination)
    except (SystemExit, ValueError, OSError) as exc:
        if isinstance(exc, SystemExit):
            return int(exc.code)
        error = _outcome("invalid", "Setup plan could not be created.")
        _write_report(error, "--json" in (argv or []))
        return 2
    if args.accept is None:
        _write_report({"plan": plan}, args.json)
        return 1 if plan["action"] == "blocked" else 0
    outcome = apply_plan(plan, accepted_plan=args.accept)
    _write_report(outcome, args.json)
    if outcome["status"] in {"complete", "no-op"}:
        return 0
    if outcome["status"] in {"approval-required", "stale-plan"}:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
