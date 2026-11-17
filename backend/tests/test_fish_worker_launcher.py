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
    (checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").write_bytes(b"artifact")
    monkeypatch.setenv("FISH_SOURCE_ROOT", str(source))
    monkeypatch.setenv("FISH_CHECKPOINT_ROOT", str(checkpoint))
    monkeypatch.setenv("FISH_WORKER_HOST", "127.0.0.1")
    monkeypatch.setenv("FISH_WORKER_PORT", "8123")
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
