import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

import prerequisites


def _successful_run(args, **kwargs):
    command = args[0]
    if command == "/usr/bin/say":
        return subprocess.CompletedProcess(args, 0, "Anna\nSamantha\nDaniel\n", "")
    if command == "/usr/local/bin/ffmpeg" and "-version" in args:
        return subprocess.CompletedProcess(args, 0, "ffmpeg version 7.1.1\n", "")
    if command == "/usr/local/bin/ffmpeg":
        return subprocess.CompletedProcess(
            args,
            0,
            " V..... libmp3lame\n A..... pcm_s16le\n",
            "",
        )
    return subprocess.CompletedProcess(args, 0, "1.2.3\n", "")


def _make_supported_host(monkeypatch, tmp_path):
    monkeypatch.setattr(prerequisites.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(prerequisites.platform, "mac_ver", lambda: ("14.0", (), ""))
    monkeypatch.setattr(prerequisites.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(prerequisites.shutil, "which", lambda name: {
        "/usr/bin/say": "/usr/bin/say",
        "uv": "/opt/homebrew/bin/uv",
        "ffmpeg": "/usr/local/bin/ffmpeg",
    }.get(name))
    monkeypatch.setattr(prerequisites.subprocess, "run", _successful_run)
    monkeypatch.setattr(prerequisites.shutil, "disk_usage", lambda _path: SimpleNamespace(free=10**10))
    monkeypatch.setattr(prerequisites.socket, "socket", lambda *args, **kwargs: _AvailablePort())
    monkeypatch.setenv("TTS_API_KEY", "synthetic-secret-marker")
    monkeypatch.delenv("TTS_API_KEY_FILE", raising=False)
    monkeypatch.setenv("TTS_DESTINATION", str(tmp_path))


class _AvailablePort:
    def __init__(self):
        self.bound = False

    def bind(self, address):
        self.bound = True

    def close(self):
        self.bound = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def test_reports_every_prerequisite_with_stable_ids_and_safe_statuses(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)

    report = prerequisites.inspect_prerequisites()
    diagnostics = {item["id"]: item for item in report["diagnostics"]}

    assert set(diagnostics) == {
        "os",
        "architecture",
        "say",
        "python",
        "uv",
        "ffmpeg",
        "voice-de-de",
        "voice-en-us",
        "voice-en-gb",
        "configuration",
        "credential",
        "destination",
        "disk",
        "port",
    }
    assert all(item["status"] in {"pass", "warn", "fail"} for item in diagnostics.values())
    assert diagnostics["os"]["status"] == "pass"
    assert diagnostics["architecture"]["status"] == "pass"
    assert diagnostics["ffmpeg"]["status"] == "pass"
    assert diagnostics["voice-en-gb"]["status"] == "pass"
    assert report["ready"] is True
    assert "synthetic-secret-marker" not in json.dumps(report)


def test_unsupported_platform_is_a_named_blocker(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)
    monkeypatch.setattr(prerequisites.platform, "system", lambda: "Linux")
    monkeypatch.setattr(prerequisites.platform, "mac_ver", lambda: ("", (), ""))

    report = prerequisites.inspect_prerequisites()
    operating_system = next(item for item in report["diagnostics"] if item["id"] == "os")

    assert operating_system["status"] == "fail"
    assert "macOS" in operating_system["reason"]
    assert operating_system["remediation"]
    assert report["ready"] is False


def test_missing_required_items_are_blockers_but_uk_voice_is_optional(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)

    def missing_voice(args, **kwargs):
        if args == ["/usr/bin/say", "-v", "?"]:
            return subprocess.CompletedProcess(args, 0, "Anna\n", "")
        return _successful_run(args, **kwargs)

    monkeypatch.setattr(prerequisites.subprocess, "run", missing_voice)

    report = prerequisites.inspect_prerequisites()
    diagnostics = {item["id"]: item for item in report["diagnostics"]}

    assert diagnostics["voice-de-de"]["status"] == "pass"
    assert diagnostics["voice-en-us"]["status"] == "fail"
    assert diagnostics["voice-en-gb"]["status"] == "warn"
    assert diagnostics["voice-en-gb"]["required"] is False
    assert report["ready"] is False


def test_inspection_is_read_only_and_never_imports_the_application(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)
    mutations = []
    existing_main = sys.modules.get("app.main")
    monkeypatch.setattr(os, "mkdir", lambda *args, **kwargs: mutations.append(("mkdir", args)))
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: mutations.append(("makedirs", args)))
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: mutations.append(("remove", args)))
    monkeypatch.setattr(os, "system", lambda *args, **kwargs: mutations.append(("system", args)))
    monkeypatch.setattr(sys, "modules", {**sys.modules, "app": None})

    prerequisites.inspect_prerequisites()

    assert mutations == []
    assert sys.modules.get("app.main") is existing_main


def test_timed_out_diagnostic_is_reported_as_actionable_failure(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)

    def timeout_voice(args, **kwargs):
        if args == ["/usr/bin/say", "-v", "?"]:
            raise subprocess.TimeoutExpired(args, kwargs["timeout"])
        return _successful_run(args, **kwargs)

    monkeypatch.setattr(prerequisites.subprocess, "run", timeout_voice)

    report = prerequisites.inspect_prerequisites()
    voice = next(item for item in report["diagnostics"] if item["id"] == "voice-de-de")

    assert voice["status"] == "fail"
    assert "timed out" in voice["reason"].lower()
    assert voice["remediation"]


def test_json_and_human_output_have_documented_exit_codes(monkeypatch, tmp_path, capsys):
    _make_supported_host(monkeypatch, tmp_path)

    assert prerequisites.main(["--json"]) == 0
    output = capsys.readouterr().out
    assert json.loads(output)["ready"] is True
    assert "synthetic-secret-marker" not in output

    monkeypatch.setattr(prerequisites.platform, "system", lambda: "Linux")
    assert prerequisites.main([]) == 1
    assert "os" in capsys.readouterr().out.lower()

    assert prerequisites.main(["--invalid"]) == 2
    assert capsys.readouterr().err


def test_incomplete_check_operation_exits_two(monkeypatch, tmp_path, capsys):
    _make_supported_host(monkeypatch, tmp_path)
    monkeypatch.setattr(
        prerequisites.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("synthetic-secret-marker")),
    )

    assert prerequisites.main(["--json"]) == 2
    output = capsys.readouterr().out
    assert json.loads(output)["complete"] is False
    assert "synthetic-secret-marker" not in output


def test_invalid_credentials_and_unavailable_destination_are_not_ready(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)
    not_a_directory = tmp_path / "not-a-directory"
    not_a_directory.write_text("file", encoding="utf-8")
    monkeypatch.setenv("TTS_API_KEY_FILE", str(tmp_path / "missing"))
    monkeypatch.setenv("TTS_DESTINATION", str(not_a_directory / "install"))

    report = prerequisites.inspect_prerequisites()
    diagnostics = {item["id"]: item for item in report["diagnostics"]}

    assert diagnostics["configuration"]["status"] == "fail"
    assert diagnostics["credential"]["status"] == "fail"
    assert diagnostics["destination"]["status"] == "fail"
    assert report["ready"] is False


def test_authentication_may_be_explicitly_disabled_without_a_credential(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.delenv("TTS_API_KEY_FILE", raising=False)
    monkeypatch.setenv("TTS_AUTH_ENABLED", "false")

    report = prerequisites.inspect_prerequisites()
    diagnostics = {item["id"]: item for item in report["diagnostics"]}

    assert diagnostics["configuration"]["status"] == "pass"
    assert diagnostics["credential"]["status"] == "pass"


def test_missing_credential_is_a_readiness_blocker_not_invalid_configuration(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)
    monkeypatch.delenv("TTS_API_KEY", raising=False)

    report = prerequisites.inspect_prerequisites()
    diagnostics = {item["id"]: item for item in report["diagnostics"]}

    assert diagnostics["configuration"]["status"] == "pass"
    assert diagnostics["credential"]["status"] == "fail"
    assert report["ready"] is False


def test_port_in_use_is_a_named_blocker(monkeypatch, tmp_path):
    _make_supported_host(monkeypatch, tmp_path)

    class _OccupiedPort(_AvailablePort):
        def bind(self, _address):
            raise OSError("address in use")

    monkeypatch.setattr(prerequisites.socket, "socket", lambda *args, **kwargs: _OccupiedPort())

    report = prerequisites.inspect_prerequisites()
    port = next(item for item in report["diagnostics"] if item["id"] == "port")

    assert port["status"] == "fail"
    assert port["remediation"]
