from __future__ import annotations

import os
import platform
import re
import subprocess
from typing import Protocol


class ProcessWithPid(Protocol):
    pid: int


def process_resident_memory_bytes(process: ProcessWithPid) -> int:
    process_id = getattr(process, "pid", None)
    if type(process_id) is not int or process_id <= 0:
        return 0
    try:
        output = subprocess.run(
            ["/bin/ps", "-o", "rss=", "-p", str(process_id)],
            check=True, capture_output=True, text=True, timeout=2,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise OSError("worker memory is unavailable") from exc
    try:
        resident_kilobytes = int(output)
    except ValueError as exc:
        raise ValueError("worker memory is unavailable") from exc
    if resident_kilobytes < 0:
        raise ValueError("worker memory is unavailable")
    return resident_kilobytes * 1024


def process_group_resident_memory_bytes(process: ProcessWithPid) -> int:
    output = subprocess.run(
        ["/bin/ps", "-axo", "pgid=,rss="],
        check=True, capture_output=True, text=True, timeout=2,
        env={**os.environ, "LC_ALL": "C"},
    ).stdout
    residents = []
    for line in output.splitlines():
        group, resident = map(int, line.split())
        if group == process.pid:
            if resident < 0:
                raise ValueError("worker memory is unavailable")
            residents.append(resident)
    if not residents:
        raise ValueError("worker memory is unavailable")
    return sum(residents) * 1024


def available_memory_bytes() -> int:
    if platform.system() == "Darwin":
        return _darwin_available_memory()
    try:
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError) as exc:
        raise OSError("available memory is unavailable") from exc
    if available_pages < 0 or page_size <= 0:
        raise OSError("available memory is unavailable")
    return available_pages * page_size


def _darwin_available_memory() -> int:
    try:
        output = subprocess.run(
            ["/usr/bin/vm_stat"], check=True, capture_output=True,
            text=True, timeout=5, env={**os.environ, "LC_ALL": "C"},
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise OSError("available memory is unavailable") from exc
    match = re.search(r"page size of ([\d,]+) bytes", output)
    if match is None:
        raise ValueError("available memory is unavailable")
    page_size = int(match.group(1).replace(",", ""))
    if page_size <= 0:
        raise ValueError("available memory is unavailable")
    pages = 0
    for label in ("free", "inactive", "speculative"):
        match = re.search(rf"^Pages {label}:\s*([\d,]+)\.?\s*$", output, re.MULTILINE)
        if match is None:
            raise ValueError("available memory is unavailable")
        pages += int(match.group(1).replace(",", ""))
    return pages * page_size
