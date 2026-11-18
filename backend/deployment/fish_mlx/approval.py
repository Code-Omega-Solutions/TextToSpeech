"""Separate, exact approval binding for the experimental MLX worker."""

from __future__ import annotations

import json
import hashlib
import os
import platform
import stat
import sys
from pathlib import Path
from typing import Any


def validate_approval(path: Path, binding: dict[str, Any]) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Fish MLX approval is unavailable")
    if os.name == "posix":
        info = path.stat()
        if info.st_uid != os.geteuid() or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ValueError("Fish MLX approval permissions are unsafe")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Fish MLX approval is invalid") from exc
    if not isinstance(document, dict) or document.get("status") != "approved":
        raise ValueError("Fish MLX candidate is not approved")
    if (
        set(document) != {"status", "intended_use", "binding"}
        or document["intended_use"] != "private-noncommercial"
        or document["binding"] != binding
    ):
        raise ValueError("Fish MLX candidate does not match approval")


def _tree_digest(root: Path) -> str:
    from deployment import fish_worker_launcher as launcher

    files = launcher._all_regular_files(root)
    if not files:
        raise ValueError("Fish MLX runtime tree is empty")
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(launcher._sha256(root / name).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _directory(name: str) -> Path:
    raw = os.environ.get(name)
    if not raw:
        raise ValueError(f"{name} is unavailable")
    path = Path(raw).expanduser()
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"{name} is unavailable")
    return path.resolve()


def snapshot() -> dict[str, Any]:
    from deployment import fish_worker_launcher as launcher
    from deployment.fish_mlx.prepare import approved_origin, converter_digest
    from deployment.fish_mlx.validation import validate_config

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("Fish MLX requires Apple Silicon macOS")
    source, checkpoint, references, original = approved_origin()
    candidate = _directory("TTS_FISH_MLX_CANDIDATE_ROOT")
    mlx_site = _directory("TTS_FISH_MLX_SITE_ROOT")
    if os.name == "posix" and (
        candidate.stat().st_uid != os.geteuid() or candidate.stat().st_mode & 0o022
    ):
        raise ValueError("Fish MLX candidate permissions are unsafe")
    backend = Path(__file__).resolve().parents[2]
    repo = backend.parent
    interpreter = Path(sys.executable).absolute()
    fish_site = interpreter.parent.parent / "lib" / "python3.12" / "site-packages"
    stdlib = Path(sys.base_prefix).resolve() / "lib" / "python3.12"
    if sys.version_info[:2] != (3, 12) or not fish_site.is_dir() or not stdlib.is_dir():
        raise ValueError("Fish MLX Python runtime is unsupported")
    fish_site = fish_site.resolve()
    protected = (source, checkpoint, references, repo, fish_site, mlx_site)
    if any(
        candidate == root or candidate in root.parents or root in candidate.parents
        for root in protected
    ):
        raise ValueError("Fish MLX candidate overlaps a protected tree")
    if any(
        mlx_site == root or mlx_site in root.parents or root in mlx_site.parents
        for root in (source, checkpoint, references, repo, fish_site)
    ):
        raise ValueError("Fish MLX runtime overlaps a protected tree")
    if launcher._all_regular_files(candidate) != {"semantic.safetensors", "conversion.json"}:
        raise ValueError("Fish MLX candidate inventory is invalid")
    weights = candidate / "semantic.safetensors"
    conversion = candidate / "conversion.json"
    try:
        metadata = json.loads(conversion.read_text(encoding="utf-8"))
        config = json.loads((checkpoint / "config.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Fish MLX conversion metadata is invalid") from exc
    if not isinstance(metadata, dict) or not isinstance(config, dict):
        raise ValueError("Fish MLX conversion metadata is invalid")
    validate_config(config)
    artifact_manifest = Path(os.environ["TTS_FISH_ARTIFACT_MANIFEST"])
    reference_manifest = Path(os.environ["TTS_FISH_REFERENCE_MANIFEST"])
    if artifact_manifest.is_symlink() or reference_manifest.is_symlink():
        raise ValueError("Fish approval manifest is unsafe")
    reference_hash = launcher._sha256(reference_manifest.resolve())
    semantic_hash = launcher._sha256(weights)
    expected_metadata = {
        "format": "fish-1.5-mlx-affine-v1",
        "bits": 4,
        "group_size": 64,
        "model_sha256": original["model_sha256"],
        "checkpoint_sha256": launcher._sha256(checkpoint / "model.pth"),
        "codec_sha256": original["codec_sha256"],
        "source_revision": original["source_revision"],
        "source_tree_sha256": original["source_tree_sha256"],
        "reference_manifest_sha256": reference_hash,
        "converter_sha256": converter_digest(),
        "requirements_sha256": launcher._sha256(
            backend / "deployment" / "fish_mlx-requirements.txt"
        ),
        "mlx_version": "0.32.4",
        "mlx_metal_version": "0.32.4",
        "semantic_sha256": semantic_hash,
        "config": config,
    }
    if metadata != expected_metadata:
        raise ValueError("Fish MLX conversion provenance does not match approval inputs")
    zip_path = Path(sys.base_prefix).resolve() / "lib" / "python312.zip"
    if zip_path.exists() or zip_path.is_symlink():
        raise ValueError("Fish MLX Python archive is not supported")
    return {
        "source_revision": original["source_revision"],
        "source_tree_sha256": original["source_tree_sha256"],
        "artifact_manifest_sha256": launcher._sha256(artifact_manifest.resolve()),
        "reference_manifest_sha256": reference_hash,
        "semantic_sha256": semantic_hash,
        "conversion_sha256": launcher._sha256(conversion),
        "python_sha256": launcher._sha256(interpreter.resolve()),
        "python_version": platform.python_version(),
        "macos_version": platform.mac_ver()[0],
        "stdlib_tree_sha256": _tree_digest(stdlib),
        "fish_site_tree_sha256": _tree_digest(fish_site),
        "mlx_site_tree_sha256": _tree_digest(mlx_site),
        "app_tree_sha256": _tree_digest(backend / "app"),
        "candidate_code_tree_sha256": _tree_digest(Path(__file__).resolve().parent),
        "deployment_init_sha256": launcher._sha256(backend / "deployment" / "__init__.py"),
        "launcher_sha256": launcher._sha256(backend / "deployment" / "fish_worker_launcher.py"),
        "requirements_sha256": launcher._sha256(backend / "deployment" / "fish_mlx-requirements.txt"),
    }


def write_review(path: Path, binding: dict[str, Any]) -> None:
    document = {
        "status": "review-required",
        "intended_use": "private-noncommercial",
        "binding": binding,
    }
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(document, file, indent=2, sort_keys=True)
        file.write("\n")
