"""Print a minimal machine-knowledge preview without writing files or running commands."""

from __future__ import annotations

import argparse
import platform
import re
import shutil
from datetime import datetime, timezone
from typing import Sequence


_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)
_COMMAND_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}\Z", re.ASCII)


def _is_identifier(value: str) -> bool:
    return bool(_IDENTIFIER.fullmatch(value))


def _is_command_name(value: str) -> bool:
    return bool(_COMMAND_NAME.fullmatch(value))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print an allowlisted local machine-knowledge preview."
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--shell", required=True)
    parser.add_argument("--boundary", required=True)
    parser.add_argument(
        "--command",
        action="append",
        required=True,
        help="bare executable name to check on PATH; the command is never run",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not all(
        _is_identifier(value)
        for value in (args.project_id, args.host_id, args.shell, args.boundary)
    ):
        parser.error("IDs, shell, and boundary must be simple identifiers")
    if not all(_is_command_name(value) for value in args.command):
        parser.error("commands must be bare executable names, not paths or expressions")

    print("# Machine Knowledge Preview")
    print()
    print(
        "- Observed at (UTC): "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}"
    )
    print(f"- OS: {platform.system()}")
    print(f"- Release: {platform.release()}")
    print(f"- Architecture: {platform.machine()}")
    print(f"- Shell (caller-supplied): {args.shell}")
    print(f"- Execution boundary (caller-supplied): {args.boundary}")
    print("- PATH lookups (not executed):")
    for command in args.command:
        found = shutil.which(command) is not None
        print(f"  - `{command}`: {str(found).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
