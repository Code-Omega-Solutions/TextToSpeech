import json
import os

import pytest

from deployment import fish_worker_launcher


def test_launcher_requires_local_artifacts(monkeypatch, tmp_path):
    monkeypatch.delenv("FISH_SOURCE_ROOT", raising=False)
    monkeypatch.setenv("FISH_CHECKPOINT_ROOT", str(tmp_path))

    with pytest.raises(SystemExit, match="FISH_SOURCE_ROOT is unavailable"):
        fish_worker_launcher.main()


def test_launcher_executes_offline_loopback_api(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    decoder.write_bytes(b"artifact")
    model = checkpoint / "model.bin"
    model.write_bytes(b"approved model")
    model_files = [{"path": "model.bin", "sha256": fish_worker_launcher._sha256(model)}]
    manifest = tmp_path / "approval.json"
    manifest.write_text(
        json.dumps(
            {
                "status": "approved",
                "source_revision": "a" * 40,
                "model_revision": "b" * 40,
                "source_license": "Apache-2.0",
                "model_license": "CC-BY-NC-SA-4.0",
                "codec_license": "CC-BY-NC-SA-4.0",
                "intended_use": "private-noncommercial",
                "source_terms": {"url": "https://example.test/source", "revision": "apache-2.0"},
                "model_terms": {"url": "https://example.test/model", "revision": "cc-by-nc-sa-4.0"},
                "codec_terms": {"url": "https://example.test/codec", "revision": "cc-by-nc-sa-4.0"},
                "model_files": model_files,
                "model_sha256": fish_worker_launcher._model_tree_digest(checkpoint, model_files),
                "codec_sha256": fish_worker_launcher._sha256(decoder),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("FISH_WORKER_HOST", "127.0.0.1")
    monkeypatch.setenv("FISH_WORKER_PORT", "8123")
    monkeypatch.setenv("FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("FISH_ARTIFACT_MANIFEST", str(manifest))
    monkeypatch.chdir(tmp_path)
    calls = []

    monkeypatch.setattr(
        fish_worker_launcher.os,
        "execv",
        lambda executable, arguments: calls.append((executable, arguments)),
    )
    fish_worker_launcher.main()

    assert len(calls) == 1
    executable, arguments = calls[0]
    assert executable == fish_worker_launcher.sys.executable
    assert arguments[:6] == [
        fish_worker_launcher.sys.executable,
        "-m",
        "tools.api_server",
        "--mode",
        "tts",
        "--listen",
    ]
    assert arguments[6] == "127.0.0.1:8123"
    assert "--workers" in arguments and arguments[arguments.index("--workers") + 1] == "1"
    assert "--device" in arguments and arguments[arguments.index("--device") + 1] == "mps"
    assert "--half" in arguments
    assert "--llama-checkpoint-path" in arguments
    assert arguments[arguments.index("--decoder-checkpoint-path") + 1].endswith(
        "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    )
    assert os.getcwd() == str(source)


def test_launcher_requires_exact_approval_manifest(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    (checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").write_bytes(b"artifact")
    monkeypatch.setenv("FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.delenv("FISH_ARTIFACTS_APPROVED", raising=False)
    monkeypatch.delenv("FISH_ARTIFACT_MANIFEST", raising=False)

    with pytest.raises(SystemExit, match="pending artifact approval"):
        fish_worker_launcher.main()
