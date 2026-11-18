import hashlib
import io
import json
import os
import subprocess
import wave

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
    entrypoint = source / "tools" / "api_server.py"
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
        "runtime": {
            "entrypoint_path": "tools/api_server.py",
            "entrypoint_sha256": fish_worker_launcher._sha256(entrypoint),
            "mode": "tts",
            "listen_host": "127.0.0.1",
            "workers": 1,
            "device": "mps",
            "half": True,
            "offline": True,
            "max_text_length": 5000,
            "decoder_config_name": "firefly_gan_vq",
            "decoder_path": decoder.name,
        },
    }


def _reference_assets(tmp_path):
    root = tmp_path / "reference-data"
    records = []
    for language, gender, reference_id in (
        ("de-DE", "male", "de-male"),
        ("de-DE", "female", "de-female"),
        ("en-US", "male", "en-male"),
        ("en-US", "female", "en-female"),
    ):
        dataset_id = (
            "cmu5mc2sn00s5mi07udtq2864"
            if language == "de-DE"
            else "cmu5nqn1h00vwmi07b4dbk085"
        )
        reference_dir = root / "references" / reference_id
        reference_dir.mkdir(parents=True)
        wav = reference_dir / f"{reference_id}.wav"
        output = io.BytesIO()
        with wave.open(output, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(24000)
            writer.writeframes(b"\0\0" * 12)
        wav.write_bytes(output.getvalue())
        lab = reference_dir / f"{reference_id}.lab"
        lab.write_text("Test transcript", encoding="utf-8")
        records.append(
            {
                "id": reference_id,
                "language": language,
                "gender": gender,
                "dataset_id": dataset_id,
                "dataset_release": "sps-corpus-5.0-2026-09-11",
                "audio_path": f"references/{reference_id}/{reference_id}.wav",
                "lab_path": f"references/{reference_id}/{reference_id}.lab",
                "audio_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
                "lab_sha256": hashlib.sha256(lab.read_bytes()).hexdigest(),
                "source_url": f"https://example.test/datasets/{dataset_id}",
                "source_revision": "sps-corpus-5.0-2026-09-11",
                "source_license": "CC0-1.0",
                "terms_url": "https://example.test/terms",
                "terms_revision": "accepted-dataset-agreement",
                "permission_basis": "dataset-terms-accepted",
                "terms_status": "approved",
                "intended_use": "private-noncommercial",
            }
        )
    manifest = tmp_path / "references.json"
    manifest.write_text(
        json.dumps({"status": "approved", "references": records}),
        encoding="utf-8",
    )
    manifest.chmod(0o600)
    return root, manifest


def _set_reference_environment(monkeypatch, tmp_path):
    root, manifest = _reference_assets(tmp_path)
    monkeypatch.setenv("TTS_FISH_REFERENCE_ROOT", str(root))
    monkeypatch.setenv("TTS_FISH_REFERENCE_MANIFEST", str(manifest))
    monkeypatch.setenv("TTS_FISH_REFERENCES_APPROVED", "true")
    return root


def test_launcher_requires_local_artifacts(monkeypatch, tmp_path):
    monkeypatch.delenv("TTS_FISH_SOURCE_ROOT", raising=False)
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(tmp_path))

    with pytest.raises(SystemExit, match="TTS_FISH_SOURCE_ROOT is unavailable"):
        fish_worker_launcher.main()


def test_launcher_requires_references_outside_source_checkout(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    _set_reference_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_REFERENCE_ROOT", str(source))

    with pytest.raises(SystemExit, match="separate from the source checkout"):
        fish_worker_launcher.main()


def test_launcher_requires_reference_approval(monkeypatch, tmp_path):
    reference_root = _set_reference_environment(monkeypatch, tmp_path)
    monkeypatch.delenv("TTS_FISH_REFERENCES_APPROVED")

    with pytest.raises(SystemExit, match="pending reference approval"):
        fish_worker_launcher._approved_references(reference_root)


def test_launcher_executes_offline_loopback_api(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    reference_root = _set_reference_environment(monkeypatch, tmp_path)
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
    manifest.chmod(0o600)
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
    assert os.getcwd() == str(reference_root)
    assert os.environ["PYTHONPATH"].split(os.pathsep)[0] == str(source)
    assert os.environ["PYTHONDONTWRITEBYTECODE"] == "1"


def test_launcher_requires_exact_approval_manifest(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _set_reference_environment(monkeypatch, tmp_path)
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
    _set_reference_environment(monkeypatch, tmp_path)
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
    manifest.chmod(0o600)
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(manifest))

    with pytest.raises(SystemExit, match="revision does not match approval"):
        fish_worker_launcher.main()


def test_launcher_rejects_dirty_source_checkout(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    _set_reference_environment(monkeypatch, tmp_path)
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    decoder.write_bytes(b"codec")
    model = checkpoint / "model.bin"
    model.write_bytes(b"model")
    manifest = tmp_path / "approval.json"
    manifest.write_text(
        json.dumps(
            _approval_manifest(
                source,
                checkpoint,
                decoder,
                [{"path": "model.bin", "sha256": fish_worker_launcher._sha256(model)}],
            )
        ),
        encoding="utf-8",
    )
    manifest.chmod(0o600)
    (source / "references").mkdir()
    (source / "references" / "unapproved.wav").write_bytes(b"not approved")
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(manifest))

    with pytest.raises(SystemExit, match="not clean and pinned"):
        fish_worker_launcher.main()


def test_launcher_rejects_runtime_entrypoint_mismatch(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    _set_reference_environment(monkeypatch, tmp_path)
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    decoder.write_bytes(b"codec")
    model = checkpoint / "model.bin"
    model.write_bytes(b"model")
    document = _approval_manifest(
        source,
        checkpoint,
        decoder,
        [{"path": "model.bin", "sha256": fish_worker_launcher._sha256(model)}],
    )
    document["runtime"]["entrypoint_sha256"] = "a" * 64
    manifest = tmp_path / "approval.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    manifest.chmod(0o600)
    monkeypatch.setenv("TTS_FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("TTS_FISH_ARTIFACTS_APPROVED", "true")
    monkeypatch.setenv("TTS_FISH_ARTIFACT_MANIFEST", str(manifest))

    with pytest.raises(SystemExit, match="runtime entrypoint"):
        fish_worker_launcher.main()


def test_launcher_rejects_omitted_model_or_codec_files(monkeypatch, tmp_path):
    source = tmp_path / "source"
    checkpoint = tmp_path / "checkpoint"
    source.mkdir()
    checkpoint.mkdir()
    _git_source(source)
    _set_reference_environment(monkeypatch, tmp_path)
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
    manifest.chmod(0o600)
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
