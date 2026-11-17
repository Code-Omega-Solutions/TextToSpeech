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
import subprocess
import sys
from pathlib import Path
from typing import Any


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")


def _required_directory(name: str) -> Path:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is unavailable")
    candidate = Path(value).expanduser()
    if candidate.is_symlink():
        raise SystemExit(f"{name} is unavailable")
    path = candidate.resolve()
    if not path.is_dir():
        raise SystemExit(f"{name} is unavailable")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _entry_tree_digest(root: Path, files: list[dict[str, Any]]) -> str:
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
        candidate = root / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise SystemExit("Fish model artifact is unavailable")
        artifact = candidate.resolve()
        if root not in artifact.parents:
            raise SystemExit("Fish model artifact is unavailable")
        expected = str(entry["sha256"])
        if not _SHA256.fullmatch(expected) or _sha256(artifact) != expected:
            raise SystemExit("Fish model artifact does not match its approval manifest")
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
        digest.update(expected.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _all_regular_files(root: Path) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SystemExit("Fish runtime tree contains an unsafe symlink")
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit("Fish runtime tree contains an unsafe path")
        files.add(str(relative).replace("\\", "/"))
    return files


def _model_tree_digest(checkpoint: Path, files: list[dict[str, Any]]) -> str:
    decoder_name = "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    expected_paths = _all_regular_files(checkpoint) - {decoder_name}
    declared_paths = {
        str(entry.get("path", "")).replace("\\", "/")
        for entry in files
        if isinstance(entry, dict)
    }
    if declared_paths != expected_paths:
        raise SystemExit("Fish model manifest does not cover every runtime model file")
    return _entry_tree_digest(checkpoint, files)


def _source_tree(source: Path) -> tuple[str, str]:
    try:
        revision = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "--verify", "HEAD^{commit}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        tracked = subprocess.run(
            ["git", "-C", str(source), "ls-files", "-z"],
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8")
    except (OSError, UnicodeError, subprocess.CalledProcessError):
        raise SystemExit("Fish source checkout is unavailable") from None
    unexpected_status = [
        line
        for line in status.splitlines()
        if not (line.startswith("?? ") and line[3:].replace("\\", "/").startswith("references/"))
    ]
    if not _REVISION.fullmatch(revision) or unexpected_status:
        raise SystemExit("Fish source checkout is not clean and pinned")
    files: list[dict[str, str]] = []
    for relative_name in tracked.split("\0"):
        if not relative_name:
            continue
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise SystemExit("Fish source checkout contains an unsafe path")
        candidate = source / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise SystemExit("Fish source checkout contains an unsafe file")
        path = candidate.resolve()
        if source not in path.parents:
            raise SystemExit("Fish source checkout contains an unsafe file")
        files.append(
            {
                "path": str(relative).replace("\\", "/"),
                "sha256": _sha256(path),
            }
        )
    return revision, _entry_tree_digest(source, files)


def _approved_artifacts(checkpoint: Path, decoder: Path) -> None:
    if os.environ.get("TTS_FISH_ARTIFACTS_APPROVED", "").lower() not in {
        "1",
        "true",
        "yes",
    }:
        raise SystemExit("Fish neural deployment is disabled pending artifact approval")
    manifest_name = os.environ.get("TTS_FISH_ARTIFACT_MANIFEST")
    if not manifest_name:
        raise SystemExit("Fish neural deployment is disabled pending artifact approval")
    try:
        manifest_candidate = Path(manifest_name).expanduser()
        if manifest_candidate.is_symlink():
            raise ValueError
        manifest_path = manifest_candidate.resolve()
        if not manifest_path.is_file():
            raise ValueError
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise SystemExit("Fish artifact approval manifest is unavailable") from None
    if not isinstance(document, dict):
        raise SystemExit("Fish artifact approval manifest is invalid")
    if document.get("status") != "approved":
        raise SystemExit("Fish artifact approval manifest is not approved")
    source_revision = str(document.get("source_revision", ""))
    if not _REVISION.fullmatch(source_revision):
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
    if (
        document["source_terms"]["revision"] != source_revision
        or document["model_terms"]["revision"] != document["model_revision"]
    ):
        raise SystemExit("Fish artifact terms do not match their pinned revisions")
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
    codec_files = document.get("codec_files")
    codec_sha256 = str(document.get("codec_sha256", ""))
    decoder_relative = str(decoder.relative_to(checkpoint)).replace("\\", "/")
    if (
        not isinstance(codec_files, list)
        or len(codec_files) != 1
        or not isinstance(codec_files[0], dict)
        or codec_files[0].get("path") != decoder_relative
        or not _SHA256.fullmatch(codec_sha256)
        or codec_files[0].get("sha256") != codec_sha256
        or _sha256(decoder) != codec_sha256
    ):
        raise SystemExit("Fish codec artifact does not match its approval manifest")


def main() -> None:
    source = _required_directory("TTS_FISH_SOURCE_ROOT")
    checkpoint = _required_directory("TTS_FISH_CHECKPOINT_ROOT")
    host = os.environ.get("TTS_FISH_WORKER_HOST", "127.0.0.1")
    port = os.environ.get("TTS_FISH_WORKER_PORT", "8002")
    if host != "127.0.0.1" or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise SystemExit("Fish worker must use a loopback port")

    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    if not decoder.is_file():
        raise SystemExit("Fish decoder artifact is unavailable")
    _approved_artifacts(checkpoint, decoder)
    source_revision, source_tree_sha256 = _source_tree(source)
    manifest_path = Path(os.environ["TTS_FISH_ARTIFACT_MANIFEST"]).expanduser().resolve()
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("source_revision") != source_revision:
        raise SystemExit("Fish source checkout revision does not match approval")
    if document.get("source_tree_sha256") != source_tree_sha256:
        raise SystemExit("Fish source checkout does not match approval")

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
