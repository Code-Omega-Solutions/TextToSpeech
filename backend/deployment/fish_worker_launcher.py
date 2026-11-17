"""Start the reviewed Fish Speech API from locally provisioned artifacts.

The serving backend owns this process through ``FishProcess``.  This launcher
does not download checkpoints, accept a public bind address, or read the
backend bearer credential.  The outer backend remains the authenticated
boundary; the Fish API is loopback-only.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _required_directory(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is unavailable")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"{name} is unavailable")
    return path


def main() -> None:
    source = _required_directory("FISH_SOURCE_ROOT")
    checkpoint = _required_directory("FISH_CHECKPOINT_ROOT")
    host = os.environ.get("FISH_WORKER_HOST", "127.0.0.1")
    port = os.environ.get("FISH_WORKER_PORT", "8002")
    if host != "127.0.0.1" or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise SystemExit("Fish worker must use a loopback port")

    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    if not decoder.is_file():
        raise SystemExit("Fish decoder artifact is unavailable")

    os.chdir(source)
    sys.path.insert(0, str(source))
    arguments = [
        sys.executable,
        "-m",
        "tools.api_server",
        "--mode",
        "tts",
        "--listen",
        f"{host}:{port}",
        "--workers",
        "1",
        "--device",
        "mps",
        "--half",
        "--max-text-length",
        "5000",
        "--llama-checkpoint-path",
        str(checkpoint),
        "--decoder-checkpoint-path",
        str(decoder),
        "--decoder-config-name",
        "firefly_gan_vq",
    ]
    os.execv(sys.executable, arguments)


if __name__ == "__main__":
    main()
