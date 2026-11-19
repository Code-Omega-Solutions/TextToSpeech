import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from deployment import fish_worker_launcher
from deployment.fish_mlx import approval, prepare
from deployment.fish_mlx.approval import validate_approval
from deployment.fish_mlx.validation import APPROVED_CONFIG


def test_bootstrap_refuses_nonisolated_python():
    bootstrap = Path(__file__).resolve().parents[1] / "deployment" / "fish_mlx" / "bootstrap.py"
    result = subprocess.run(
        [sys.executable, "-B", str(bootstrap)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "requires Python -I -S -B" in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission enforcement")
def test_candidate_rejects_writable_approval(tmp_path):
    manifest = tmp_path / "candidate.json"
    manifest.write_text(
        json.dumps({"status": "approved", "intended_use": "private-noncommercial", "binding": {}}),
        encoding="utf-8",
    )
    manifest.chmod(0o622)
    with pytest.raises(ValueError, match="permissions"):
        validate_approval(manifest, {})


def test_candidate_requires_exact_separate_approval(tmp_path):
    manifest = tmp_path / "candidate.json"
    manifest.write_text(
        json.dumps({"status": "approved", "intended_use": "private-noncommercial",
                    "binding": {"source": "a", "runtime": "b", "weights": "c"}}),
        encoding="utf-8",
    )
    manifest.chmod(0o600)
    validate_approval(manifest, {"source": "a", "runtime": "b", "weights": "c"})
    with pytest.raises(ValueError, match="does not match"):
        validate_approval(manifest, {"source": "a", "runtime": "changed", "weights": "c"})
    with pytest.raises(ValueError, match="does not match"):
        validate_approval(manifest, {"source": "a", "runtime": "b", "weights": "changed"})


@pytest.mark.parametrize("status", ["review-required", "rejected", None])
def test_unapproved_candidate_is_rejected(tmp_path, status):
    manifest = tmp_path / "candidate.json"
    manifest.write_text(
        json.dumps({"status": status, "intended_use": "private-noncommercial", "binding": {}}),
        encoding="utf-8",
    )
    manifest.chmod(0o600)
    with pytest.raises(ValueError, match="not approved"):
        validate_approval(manifest, {})


def test_snapshot_rejects_changed_derived_weights_and_runtime(monkeypatch, tmp_path):
    source, checkpoint, references, candidate, overlay = (
        tmp_path / name for name in ("source", "checkpoint", "references", "candidate", "overlay")
    )
    for path in (source, checkpoint, references, candidate, overlay):
        path.mkdir()
    site = tmp_path / "venv" / "lib" / "python3.12" / "site-packages"
    stdlib = tmp_path / "base" / "lib" / "python3.12"
    binary = tmp_path / "venv" / "bin" / "python"
    site.mkdir(parents=True)
    stdlib.mkdir(parents=True)
    binary.parent.mkdir()
    binary.write_bytes(b"python")
    (site / "dependency.py").write_text("runtime", encoding="utf-8")
    (stdlib / "stdlib.py").write_text("stdlib", encoding="utf-8")
    (overlay / "mlx.py").write_text("mlx", encoding="utf-8")
    (checkpoint / "config.json").write_text(json.dumps(APPROVED_CONFIG), encoding="utf-8")
    (checkpoint / "model.pth").write_bytes(b"approved checkpoint")
    (candidate / "semantic.safetensors").write_bytes(b"derived weights")
    artifact_manifest = tmp_path / "artifact.json"
    reference_manifest = tmp_path / "references.json"
    artifact_manifest.write_text("artifact", encoding="utf-8")
    reference_manifest.write_text("reference", encoding="utf-8")
    original = {
        "model_sha256": "a" * 64, "codec_sha256": "b" * 64,
        "source_revision": "c" * 40, "source_tree_sha256": "d" * 64,
    }
    digest = fish_worker_launcher._sha256
    metadata = {
        "format": "fish-1.5-mlx-affine-v2", "bits": 4, "group_size": 64,
        "fp16_slow_layers": 8,
        "model_sha256": original["model_sha256"],
        "checkpoint_sha256": digest(checkpoint / "model.pth"),
        "codec_sha256": original["codec_sha256"],
        "source_revision": original["source_revision"],
        "source_tree_sha256": original["source_tree_sha256"],
        "reference_manifest_sha256": digest(reference_manifest),
        "converter_sha256": prepare.converter_digest(),
        "requirements_sha256": digest(
            approval.Path(approval.__file__).resolve().parents[2]
            / "deployment" / "fish_mlx-requirements.txt"
        ),
        "mlx_version": "0.32.4",
        "mlx_metal_version": "0.32.4",
        "semantic_sha256": digest(candidate / "semantic.safetensors"),
        "config": APPROVED_CONFIG,
    }
    (candidate / "conversion.json").write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(prepare, "approved_origin", lambda: (source, checkpoint, references, original))
    monkeypatch.setattr(approval.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(approval.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(approval.sys, "executable", str(binary))
    monkeypatch.setattr(approval.sys, "base_prefix", str(tmp_path / "base"))
    monkeypatch.setattr(approval.sys, "version_info", (3, 12, 15))
    monkeypatch.setattr(approval.os, "geteuid", lambda: candidate.stat().st_uid, raising=False)
    monkeypatch.setenv("TTS_FISH_MLX_CANDIDATE_ROOT", str(candidate))
    monkeypatch.setenv("TTS_FISH_MLX_SITE_ROOT", str(overlay))
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(artifact_manifest))
    monkeypatch.setenv("TTS_FISH_REFERENCE_MANIFEST", str(reference_manifest))
    binding = approval.snapshot()
    manifest = tmp_path / "candidate-approval.json"
    manifest.write_text(json.dumps({
        "status": "approved", "intended_use": "private-noncommercial", "binding": binding
    }), encoding="utf-8")
    manifest.chmod(0o600)
    validate_approval(manifest, binding)
    (overlay / "mlx.py").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="does not match"):
        validate_approval(manifest, approval.snapshot())
    (candidate / "semantic.safetensors").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="provenance"):
        approval.snapshot()
