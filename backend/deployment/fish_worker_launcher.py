"""Start the reviewed Fish Speech API from locally provisioned artifacts.

The serving backend owns this process through ``FishProcess``. This launcher
does not download checkpoints, accept a public bind address, or read the
backend bearer credential. It also refuses to exec without a local,
hash-checked approval manifest for the exact artifacts and terms. The outer
backend remains the authenticated boundary; the Fish API is loopback-only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")


def _required_directory(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is unavailable")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"{name} is unavailable")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _model_tree_digest(checkpoint: Path, files: list[dict[str, Any]]) -> str:
    if not files or any(
        not isinstance(entry, dict)
        or not isinstance(entry.get("path"), str)
        or not isinstance(entry.get("sha256"), str)
        for entry in files
    ):
        raise SystemExit("Fish model manifest is invalid")
    digest = hashlib.sha256()
    seen: set[str] = set()
    for entry in sorted(files, key=lambda item: str(item["path"])):
        relative = Path(str(entry["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit("Fish model manifest contains an unsafe path")
        normalized = str(relative).replace("\\", "/")
        if normalized in seen:
            raise SystemExit("Fish model manifest contains duplicate paths")
        seen.add(normalized)
        artifact = (checkpoint / relative).resolve()
        if checkpoint not in artifact.parents or not artifact.is_file():
            raise SystemExit("Fish model artifact is unavailable")
        expected = str(entry["sha256"])
        if not _SHA256.fullmatch(expected) or _sha256(artifact) != expected:
            raise SystemExit("Fish model artifact does not match its approval manifest")
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
        digest.update(expected.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _approved_artifacts(checkpoint: Path, decoder: Path) -> None:
    if os.environ.get("FISH_ARTIFACTS_APPROVED", "").lower() not in {"1", "true", "yes"}:
        raise SystemExit("Fish neural deployment is disabled pending artifact approval")
    manifest_name = os.environ.get("FISH_ARTIFACT_MANIFEST")
    if not manifest_name:
        raise SystemExit("Fish neural deployment is disabled pending artifact approval")
    try:
        manifest_path = Path(manifest_name).expanduser().resolve()
        if not manifest_path.is_file():
            raise ValueError
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise SystemExit("Fish artifact approval manifest is unavailable") from None
    if not isinstance(document, dict):
        raise SystemExit("Fish artifact approval manifest is invalid")
    if document.get("status") != "approved":
        raise SystemExit("Fish artifact approval manifest is not approved")
    if not _REVISION.fullmatch(str(document.get("source_revision", ""))):
        raise SystemExit("Fish source revision is not pinned")
    if not _REVISION.fullmatch(str(document.get("model_revision", ""))):
        raise SystemExit("Fish model revision is not pinned")
    for term_key in ("source_terms", "model_terms", "codec_terms"):
        terms = document.get(term_key)
        if (
            not isinstance(terms, dict)
            or not str(terms.get("url", "")).startswith("https://")
            or not str(terms.get("revision", "")).strip()
        ):
            raise SystemExit("Fish artifact terms are not recorded exactly")
    for license_key in ("source_license", "model_license", "codec_license"):
        if not str(document.get(license_key, "")).strip():
            raise SystemExit("Fish artifact terms are not recorded exactly")
    if document.get("intended_use") != "private-noncommercial":
        raise SystemExit("Fish artifact intended use is not approved")
    model_files = document.get("model_files")
    model_sha256 = str(document.get("model_sha256", ""))
    if (
        not isinstance(model_files, list)
        or not model_files
        or not _SHA256.fullmatch(model_sha256)
        or _model_tree_digest(checkpoint, model_files) != model_sha256
    ):
        raise SystemExit("Fish model artifact does not match its approval manifest")
    codec_sha256 = str(document.get("codec_sha256", ""))
    if not _SHA256.fullmatch(codec_sha256) or _sha256(decoder) != codec_sha256:
        raise SystemExit("Fish codec artifact does not match its approval manifest")


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
    _approved_artifacts(checkpoint, decoder)

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
