"""Prepare private Fish 1.5 MLX weights from already approved local artifacts."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path

from app.memory import available_memory_bytes, process_resident_memory_bytes
from deployment import fish_worker_launcher as launcher
from deployment.fish_mlx.conversion import BITS, GROUP_SIZE, convert_tensors, inspect_mlx_tensors
from deployment.fish_mlx.validation import validate_config

_RESERVE = 12 * 1024**3
_CONVERSION_ALLOWANCE = 4 * 1024**3
_PEAK = 16 * 1024**3
_DECODER = "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"


def converter_digest() -> str:
    root = Path(__file__).resolve().parent
    names = ("conversion.py", "prepare.py", "validation.py")
    return launcher._entry_tree_digest(
        root, [{"path": name, "sha256": launcher._sha256(root / name)} for name in names]
    )


def check_resources() -> None:
    if available_memory_bytes() < _RESERVE:
        raise RuntimeError("Fish MLX conversion memory reserve is unavailable")
    if process_resident_memory_bytes(type("Process", (), {"pid": os.getpid()})()) > _PEAK:
        raise RuntimeError("Fish MLX conversion exceeded its memory budget")


def approved_origin() -> tuple[Path, Path, Path, dict]:
    source = launcher._required_directory("TTS_FISH_SOURCE_ROOT")
    checkpoint = launcher._required_directory("TTS_FISH_CHECKPOINT_ROOT")
    references = launcher._required_directory("TTS_FISH_REFERENCE_ROOT")
    if source == references or source in references.parents:
        raise SystemExit("Fish reference root must be separate from the source checkout")
    decoder = checkpoint / _DECODER
    if decoder.is_symlink() or not decoder.is_file():
        raise SystemExit("Fish decoder artifact is unavailable")
    document = launcher._approved_artifacts(checkpoint, decoder)
    revision, tree_hash = launcher._source_tree(source)
    if document.get("source_revision") != revision or document.get("source_tree_sha256") != tree_hash:
        raise SystemExit("Fish source checkout does not match approval")
    launcher._runtime_binding(document, source, decoder)
    launcher._approved_references(references)
    return source, checkpoint, references, document


def isolated_destination(path: Path, protected: tuple[Path, ...]) -> Path:
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise ValueError("Fish MLX destination must be an absolute new directory")
    parent = path.parent.resolve(strict=True)
    destination = parent / path.name
    if destination.exists() or destination.is_symlink():
        raise ValueError("Fish MLX destination already exists")
    if any(
        destination == root or destination in root.parents or root in destination.parents
        for root in protected
    ):
        raise ValueError("Fish MLX destination overlaps a protected tree")
    return destination


def prepare(destination: Path) -> None:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("Fish MLX conversion requires Apple Silicon macOS")
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise RuntimeError("Fish MLX conversion requires Python -I -S -B")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    source, checkpoint, references, approval = approved_origin()
    repository = Path(__file__).resolve().parents[3]
    site = Path(os.environ["TTS_FISH_MLX_SITE_ROOT"]).resolve(strict=True)
    fish_site = (
        Path(sys.executable).absolute().parent.parent / "lib" / "python3.12" / "site-packages"
    ).resolve(strict=True)
    output = isolated_destination(
        destination,
        (source, checkpoint, references, repository, site, fish_site, Path(sys.base_prefix).resolve()),
    )
    if available_memory_bytes() < _RESERVE + _CONVERSION_ALLOWANCE:
        raise RuntimeError("Fish MLX conversion startup memory is unavailable")
    check_resources()

    import mlx.core as mx
    import torch

    if mx.__version__ != "0.32.4" or importlib.metadata.version("mlx-metal") != "0.32.4":
        raise RuntimeError("Fish MLX runtime version is not pinned")
    config = json.loads((checkpoint / "config.json").read_text(encoding="utf-8"))
    validate_config(config)
    weights = torch.load(
        checkpoint / "model.pth", map_location="cpu", mmap=True, weights_only=True
    )
    if not isinstance(weights, dict):
        raise ValueError("Fish checkpoint is not a tensor mapping")
    if "state_dict" in weights:
        weights = weights["state_dict"]
    if not isinstance(weights, dict):
        raise ValueError("Fish checkpoint is not a tensor mapping")
    converted = convert_tensors(weights, mx, torch, check_resources)
    output.mkdir(mode=0o700)
    model_path = output / "semantic.safetensors"
    mx.save_safetensors(str(model_path), converted)
    check_resources()
    reloaded = mx.load(str(model_path))
    inspect_mlx_tensors(reloaded)
    mx.eval(*reloaded.values())
    check_resources()
    manifest_path = os.environ.get("TTS_FISH_REFERENCE_MANIFEST")
    if not manifest_path:
        raise RuntimeError("Fish reference approval manifest is unavailable")
    metadata = {
        "format": "fish-1.5-mlx-affine-v1",
        "bits": BITS,
        "group_size": GROUP_SIZE,
        "model_sha256": approval["model_sha256"],
        "checkpoint_sha256": launcher._sha256(checkpoint / "model.pth"),
        "codec_sha256": approval["codec_sha256"],
        "source_revision": approval["source_revision"],
        "source_tree_sha256": approval["source_tree_sha256"],
        "reference_manifest_sha256": launcher._sha256(Path(manifest_path).resolve()),
        "converter_sha256": converter_digest(),
        "requirements_sha256": launcher._sha256(
            Path(__file__).resolve().parents[1] / "fish_mlx-requirements.txt"
        ),
        "mlx_version": mx.__version__,
        "mlx_metal_version": "0.32.4",
        "semantic_sha256": launcher._sha256(model_path),
        "config": config,
    }
    (output / "conversion.json").write_text(
        json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare(args.output)


if __name__ == "__main__":
    main()
