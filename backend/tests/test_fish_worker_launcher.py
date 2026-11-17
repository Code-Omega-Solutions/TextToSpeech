import json
import os
import subprocess

import pytest

from deployment import fish_worker_launcher


def _git_source(path):
    (path / "tools").mkdir()
    (path / "tools" / "api_server.py").write_text("print('fixture')\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "init"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@example.test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test"],
        check=True,
    )
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", "fixture"],
        check=True,
        capture_output=True,
    )


def _approval_manifest(source, checkpoint, decoder, model_files):
    source_revision, source_tree_sha256 = fish_worker_launcher._source_tree(source)
    model_sha256 = fish_worker_launcher._entry_tree_digest(checkpoint, model_files)
    codec_sha256 = fish_worker_launcher._sha256(decoder)
    return {
        "status": "approved",
        "source_revision": source_revision,
        "source_tree_sha256": source_tree_sha256,
        "model_revision": "b" * 40,
        "source_license": "Apache-2.0",
        "model_license": "CC-BY-NC-SA-4.0",
        "codec_license": "Apache-2.0",
        "intended_use": "private-noncommercial",
        "source_terms": {"url": "https://example.test/source", "revision": source_revision},
        "model_terms": {"url": "https://example.test/model", "revision": "b" * 40},
        "codec_terms": {"url": "https://example.test/codec", "revision": "codec-revision"},
        "model_files": model_files,
        "model_sha256": model_sha256,
        "codec_files": [
            {
                "path": decoder.name,
                "sha256": codec_sha256,
            }
        ],
        "codec_sha256": codec_sha256,
    }


def test_launcher_requires_local_artifacts(monkeypatch, tmp_path):
    monkeypatch.delenv("TTS_FISH_SOURCE_ROOT", raising=False)
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(tmp_path))

    with pytest.raises(SystemExit, match="TTS_FISH_SOURCE_ROOT is unavailable"):
        fish_worker_launcher.main()


def test_launcher_executes_offline_loopback_api(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    decoder.write_bytes(b"artifact")
    model = checkpoint / "model.bin"
    model.write_bytes(b"approved model")
    model_files = [{"path": "model.bin", "sha256": fish_worker_launcher._sha256(model)}]
    manifest = tmp_path / "approval.json"
    manifest.write_text(
        json.dumps(_approval_manifest(source, checkpoint, decoder, model_files)),
        encoding="utf-8",
    )
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_WORKER_HOST", "127.0.0.1")
    monkeypatch.setenv("TTS_FISH_WORKER_PORT", "8123")
    monkeypatch.setenv("TTS_FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(manifest))
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
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.delenv("TTS_FISH_ARTIFACTS_APPROVED", raising=False)
    monkeypatch.delenv("TTS_FISH_ARTIFACT_MANIFEST", raising=False)

    with pytest.raises(SystemExit, match="pending artifact approval"):
        fish_worker_launcher.main()


def test_launcher_rejects_forged_source_revision(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    decoder.write_bytes(b"codec")
    model = checkpoint / "model.bin"
    model.write_bytes(b"model")
    model_files = [{"path": "model.bin", "sha256": fish_worker_launcher._sha256(model)}]
    document = _approval_manifest(source, checkpoint, decoder, model_files)
    document["source_revision"] = "a" * 40
    document["source_terms"]["revision"] = "a" * 40
    manifest = tmp_path / "approval.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(manifest))

    with pytest.raises(SystemExit, match="revision does not match approval"):
        fish_worker_launcher.main()


def test_launcher_rejects_omitted_model_or_codec_files(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    decoder.write_bytes(b"codec")
    model = checkpoint / "model.bin"
    model.write_bytes(b"model")
    tokenizer = checkpoint / "tokenizer.json"
    tokenizer.write_bytes(b"tokenizer")
    model_files = [{"path": "model.bin", "sha256": fish_worker_launcher._sha256(model)}]
    document = _approval_manifest(source, checkpoint, decoder, model_files)
    manifest = tmp_path / "approval.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(manifest))

    with pytest.raises(SystemExit, match="every runtime model file"):
        fish_worker_launcher.main()

    document["model_files"].append(
        {"path": "tokenizer.json", "sha256": fish_worker_launcher._sha256(tokenizer)}
    )
    document["model_sha256"] = fish_worker_launcher._model_tree_digest(
        checkpoint, document["model_files"]
    )
    document["codec_files"] = []
    manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(SystemExit, match="codec artifact"):
        fish_worker_launcher.main()
