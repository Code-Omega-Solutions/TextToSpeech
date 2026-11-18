"""Start or prepare approval for the isolated Fish 1.5 MLX worker."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    if not sys.flags.isolated or not sys.flags.no_site or not sys.dont_write_bytecode:
        raise SystemExit("Fish MLX requires Python -I -S -B")
    backend = Path(__file__).resolve().parents[2]
    fish_site = Path(sys.executable).absolute().parent.parent / "lib" / "python3.12" / "site-packages"
    if fish_site.is_symlink() or not fish_site.is_dir():
        raise SystemExit("Fish MLX Python environment is unavailable")
    sys.path[:0] = [str(backend), str(fish_site.resolve())]
    from deployment.fish_mlx.approval import snapshot, validate_approval, write_review

    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--review-output", type=Path)
    modes.add_argument("--prepare", type=Path)
    args = parser.parse_args()
    if args.prepare is not None:
        from deployment.fish_mlx.prepare import approved_origin, prepare

        source, checkpoint, references, _approval = approved_origin()
        raw_site = os.environ.get("TTS_FISH_MLX_SITE_ROOT")
        if not raw_site:
            raise SystemExit("Fish MLX runtime is unavailable")
        site = Path(raw_site).expanduser()
        if site.is_symlink() or not site.is_dir():
            raise SystemExit("Fish MLX runtime is unavailable")
        site = site.resolve()
        if any(
            site == root or site in root.parents or root in site.parents
            for root in (source, checkpoint, references, backend.parent, fish_site.resolve())
        ):
            raise SystemExit("Fish MLX runtime overlaps a protected tree")
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        sys.path.insert(0, str(site))
        prepare(args.prepare)
        return
    if args.review_output is None and os.environ.get("TTS_FISH_MLX_APPROVED", "").lower() not in {
        "1", "true", "yes"
    }:
        raise SystemExit("Fish MLX candidate is not approved")
    binding = snapshot()
    if args.review_output is not None:
        destination = args.review_output
        if not destination.is_absolute() or destination.exists() or destination.is_symlink():
            raise SystemExit("Fish MLX review output must be a new absolute file")
        destination = destination.parent.resolve(strict=True) / destination.name
        protected = [
            Path(os.environ[key]).resolve()
            for key in (
                "TTS_FISH_SOURCE_ROOT", "TTS_FISH_CHECKPOINT_ROOT", "TTS_FISH_REFERENCE_ROOT",
                "TTS_FISH_MLX_CANDIDATE_ROOT", "TTS_FISH_MLX_SITE_ROOT",
            )
        ] + [backend.parent, fish_site.resolve()]
        if any(root == destination or root in destination.parents for root in protected):
            raise SystemExit("Fish MLX review output overlaps a protected tree")
        write_review(destination, binding)
        return
    manifest = os.environ.get("TTS_FISH_MLX_APPROVAL_MANIFEST")
    if not manifest:
        raise SystemExit("Fish MLX candidate approval is unavailable")
    validate_approval(Path(manifest).expanduser(), binding)
    host = os.environ.get("TTS_FISH_WORKER_HOST", "127.0.0.1")
    port = os.environ.get("TTS_FISH_WORKER_PORT", "8002")
    if host != "127.0.0.1" or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise SystemExit("Fish worker must use a loopback port")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")
    os.environ.pop("PYTHONPATH", None)
    source = Path(os.environ["TTS_FISH_SOURCE_ROOT"]).resolve()
    mlx_site = Path(os.environ["TTS_FISH_MLX_SITE_ROOT"]).resolve()
    sys.path[:0] = [str(source), str(mlx_site)]
    from deployment.fish_mlx.worker import serve

    serve(host, int(port))


if __name__ == "__main__":
    main()
