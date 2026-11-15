#!/usr/bin/env python3
"""Emit a privacy-limited host metadata preview without writing it anywhere."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import platform
import re
import shutil


IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
COMMAND_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}\Z")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--shell", required=True)
    parser.add_argument("--boundary", required=True)
    parser.add_argument("--command", action="append", required=True)
    arguments = parser.parse_args()

    for label, value in (
        ("host ID", arguments.host_id),
        ("shell", arguments.shell),
        ("boundary", arguments.boundary),
    ):
        if not IDENTIFIER.fullmatch(value):
            parser.error(f"{label} must be a simple identifier")

    for command in arguments.command:
        if not COMMAND_NAME.fullmatch(command):
            parser.error("command names cannot contain paths or shell syntax")

    print("# Machine metadata preview")
    print(f"- observed_at_utc: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"- os: {platform.system()}")
    print(f"- release: {platform.release()}")
    print(f"- architecture: {platform.machine()}")
    print(f"- host_id: {arguments.host_id}")
    print(f"- shell: {arguments.shell}")
    print(f"- boundary: {arguments.boundary}")
    for command in arguments.command:
        available = shutil.which(command) is not None
        print(f"- PATH lookup {command}: {'available' if available else 'not found'}")


if __name__ == "__main__":
    main()