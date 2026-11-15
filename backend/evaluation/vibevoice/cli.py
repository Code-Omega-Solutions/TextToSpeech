from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from evaluation.vibevoice.inspection import inspect_manifest
from evaluation.vibevoice.runner import (
    DEFAULT_GENERATION_TIMEOUT_SECONDS,
    VIBEVOICE_CANDIDATES,
    run_evaluation,
)
from evaluation.vibevoice.server import create_session_token, serve


DEFAULT_BASELINE_URL = "http://127.0.0.1:8000/v1/audio/speech"


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "inspect":
            return _inspect(arguments)
        if arguments.command == "run":
            return _run(arguments)
        if arguments.command == "serve":
            serve(
                arguments.report,
                session_token=create_session_token(),
                port=arguments.port,
            )
            return 0
    except (OSError, ValueError) as exc:
        print(f"vibevoice evaluation: {exc}", file=sys.stderr)
        return 2
    parser.error("a command is required")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m evaluation.vibevoice.cli",
        description="Private, local VibeVoice feasibility and comparison evaluator.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="perform read-only local feasibility checks")
    inspect.add_argument("--manifest", required=True, type=Path)
    inspect.add_argument("--machine-id")
    inspect.add_argument("--volume", type=Path)
    inspect.add_argument("--adapter", action="append", default=[], metavar="VARIANT=EXECUTABLE")

    run = commands.add_parser("run", help="run explicitly approved local comparisons")
    run.add_argument("--manifest", required=True, type=Path)
    run.add_argument("--output-dir", required=True, type=Path)
    run.add_argument("--machine-id")
    run.add_argument("--volume", type=Path)
    run.add_argument("--approve-run", action="store_true", required=True)
    run.add_argument("--baseline-url", default=DEFAULT_BASELINE_URL)
    run.add_argument("--timeout-seconds", type=_timeout_seconds, default=DEFAULT_GENERATION_TIMEOUT_SECONDS)
    run.add_argument("--adapter", action="append", default=[], metavar="VARIANT=EXECUTABLE")

    review = commands.add_parser("serve", help="serve a private local report review")
    review.add_argument("--report", required=True, type=Path)
    review.add_argument("--port", type=int, default=8000)
    return parser


def _inspect(arguments: argparse.Namespace) -> int:
    manifest = _load_manifest(arguments.manifest)
    machine_id = arguments.machine_id or _first_machine_id(manifest)
    volume = arguments.volume or manifest.get("intended_storage_volume")
    result = inspect_manifest(
        manifest,
        machine_id=machine_id,
        intended_storage_volume=volume,
        approved_adapters=_parse_adapters(arguments.adapter),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _run(arguments: argparse.Namespace) -> int:
    manifest = _load_manifest(arguments.manifest)
    adapters = _parse_adapters(arguments.adapter)
    machine_id = arguments.machine_id or _first_machine_id(manifest)
    machine_ids = {
        configuration["machine_id"]
        for configuration in manifest.get("configurations", [])
        if isinstance(configuration, Mapping) and isinstance(configuration.get("machine_id"), str)
    }
    if machine_ids != {machine_id}:
        raise ValueError("each run must target exactly one machine_id")
    preflight = inspect_manifest(
        manifest,
        machine_id=machine_id,
        intended_storage_volume=arguments.volume or manifest.get("intended_storage_volume"),
        approved_adapters=adapters,
        execution_approved=True,
    )
    report = run_evaluation(
        manifest,
        arguments.output_dir,
        approve_run=arguments.approve_run,
        baseline_url=arguments.baseline_url,
        baseline_token=_baseline_token(),
        approved_adapters=adapters,
        timeout_seconds=arguments.timeout_seconds,
        preflight=preflight,
    )
    output_directory = Path(report["output_directory"])
    summary = {
        "run_id": report["run_id"],
        "state": report["state"],
        "report_path": str(output_directory / "report.json"),
        "result_count": len(report["results"]),
        "issue_count": len(report["issues"]),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _load_manifest(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise PermissionError("manifest must not be a symlink")
    resolved = path.resolve(strict=True)
    repository_root = Path(__file__).resolve().parents[3]
    if resolved == repository_root or repository_root in resolved.parents:
        raise PermissionError("manifest must be stored outside the repository")
    information = resolved.stat()
    if not stat.S_ISREG(information.st_mode):
        raise ValueError("manifest must be a regular file")
    if information.st_uid != os.geteuid() or information.st_mode & 0o077:
        raise PermissionError("manifest must be owner-only and owned by the current user")
    try:
        manifest = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("manifest must contain valid UTF-8 JSON") from exc
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be a JSON object")
    checked = dict(manifest)
    checked.setdefault("manifest_path", str(resolved))
    return checked


def _parse_adapters(values: Sequence[str]) -> dict[str, list[str]]:
    adapters: dict[str, list[str]] = {}
    for value in values:
        variant, separator, executable = value.partition("=")
        if (
            not separator
            or variant not in VIBEVOICE_CANDIDATES
            or not executable.strip()
            or variant in adapters
        ):
            raise ValueError("each --adapter must be a unique VARIANT=EXECUTABLE pair")
        adapters[variant] = [executable]
    return adapters


def _first_machine_id(manifest: Mapping[str, Any]) -> str:
    configurations = manifest.get("configurations")
    if not isinstance(configurations, list):
        raise ValueError("manifest must include configurations")
    for configuration in configurations:
        if isinstance(configuration, Mapping) and isinstance(
            configuration.get("machine_id"), str
        ):
            return configuration["machine_id"]
    raise ValueError("manifest must identify a target machine")


def _baseline_token() -> str | None:
    try:
        from app.config import Settings

        return Settings.from_env().api_key
    except ValueError:
        return None


def _timeout_seconds(value: str) -> int:
    try:
        timeout = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be an integer") from exc
    if not 1 <= timeout <= 3600:
        raise argparse.ArgumentTypeError("timeout must be between 1 and 3600 seconds")
    return timeout


if __name__ == "__main__":
    raise SystemExit(main())
