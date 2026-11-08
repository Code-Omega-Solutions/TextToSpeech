from __future__ import annotations

import argparse
import ipaddress
import json
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

_TIMEOUT_SECONDS = 5
_MIN_DISK_BYTES = 1
_MAX_CREDENTIAL_BYTES = 4096
_REQUIRED_VOICES = (
    ("voice-de-de", "TTS_VOICE_DE_DE", "Anna (Deutsch (Deutschland))"),
    ("voice-en-us", "TTS_VOICE_EN_US", "Samantha"),
)
_OPTIONAL_VOICE = ("voice-en-gb", "TTS_VOICE_EN_GB", "Daniel")


def _diagnostic(
    item_id: str,
    status: str,
    reason: str,
    remediation: str,
    *,
    version: str | None = None,
    required: bool = True,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "status": status,
        "version": version,
        "reason": reason,
        "remediation": remediation,
        "required": required,
    }


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        stdin=subprocess.DEVNULL,
        shell=False,
    )


def _reported_version(output: str) -> str | None:
    match = re.search(r"\b\d+(?:\.\d+){1,3}(?:[-+._][A-Za-z0-9.-]+)?\b", output)
    return match.group(0) if match else None


def _voice_names(say_path: str) -> set[str]:
    result = _run([say_path, "-v", "?"])
    if result.returncode != 0:
        raise OSError("voice inventory unavailable")
    return {line.split(maxsplit=1)[0] for line in result.stdout.splitlines() if line.split()}


def _voice_present(configured: str, available: set[str]) -> bool:
    return configured.split(maxsplit=1)[0] in available


def _credential_is_accessible(env: dict[str, str]) -> bool:
    environment_key = env.get("TTS_API_KEY")
    file_path = env.get("TTS_API_KEY_FILE")
    auth_disabled = env.get("TTS_AUTH_ENABLED", "true").lower() == "false"
    if environment_key is None and file_path is None:
        return auth_disabled
    if bool(environment_key) == bool(file_path):
        return False
    if environment_key is not None:
        return bool(environment_key.strip())
    try:
        fd = os.open(file_path or "", os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as credential_file:
            info = os.fstat(credential_file.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o077
            ):
                return False
            contents = credential_file.read(_MAX_CREDENTIAL_BYTES + 1)
        if len(contents) > _MAX_CREDENTIAL_BYTES:
            return False
        value = contents.decode("utf-8").removesuffix("\n")
        return bool(value.strip()) and "\n" not in value and "\r" not in value
    except (OSError, UnicodeError):
        return False


def _configuration_valid(env: dict[str, str]) -> bool:
    try:
        port = int(env.get("TTS_PORT", "8000"))
        max_temp_bytes = int(env.get("TTS_MAX_TEMP_BYTES", str(256 * 1024 * 1024)))
        auth_enabled = env.get("TTS_AUTH_ENABLED", "true").lower()
        ipaddress.ip_address(env.get("TTS_HOST", "127.0.0.1"))
        has_environment_key = "TTS_API_KEY" in env
        has_credential_file = "TTS_API_KEY_FILE" in env
        credential_sources_valid = not (has_environment_key and has_credential_file)
        return (
            1 <= port <= 65535
            and _MIN_DISK_BYTES <= max_temp_bytes <= 1024 * 1024 * 1024
            and auth_enabled in {"true", "false"}
            and credential_sources_valid
            and all(
                env.get(name, default).strip()
                for name, default in (
                    ("TTS_SAY_PATH", "/usr/bin/say"),
                    ("TTS_FFMPEG_PATH", "ffmpeg"),
                    ("TTS_VOICE_DE_DE", "Anna (Deutsch (Deutschland))"),
                    ("TTS_VOICE_EN_US", "Samantha"),
                    ("TTS_VOICE_EN_GB", "Daniel"),
                )
            )
        )
    except (ValueError, TypeError):
        return False


def _destination(env: dict[str, str]) -> Path:
    return Path(env.get("TTS_DESTINATION", str(Path(__file__).resolve().parent / ".venv")))


def _destination_accessible(destination: Path) -> bool:
    if not destination.is_absolute():
        return False
    candidate = destination
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    if not candidate.is_dir():
        return False
    if destination.exists() and not destination.is_dir():
        return False
    return os.access(candidate, os.W_OK | os.X_OK)


def _port_available(host: str, port: int) -> bool:
    address = ipaddress.ip_address(host)
    family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as listener:
        listener.bind((host, port))
    return True


def inspect_prerequisites(env: dict[str, str] | None = None) -> dict[str, Any]:
    env = dict(os.environ) if env is None else dict(env)
    diagnostics: list[dict[str, Any]] = []
    try:
        system = platform.system()
        mac_version = platform.mac_ver()[0]
        try:
            mac_major = int(mac_version.split(".", maxsplit=1)[0])
        except ValueError:
            mac_major = 0
        os_supported = system == "Darwin" and mac_major >= 13
        diagnostics.append(
            _diagnostic(
                "os",
                "pass" if os_supported else "fail",
                f"macOS 13 or newer required; detected {system} {mac_version or 'unknown'}.",
                "Run setup on macOS 13 or newer.",
                version=f"{system} {mac_version or 'unknown'}",
            )
        )

        machine = platform.machine().lower()
        architecture_supported = machine in {"arm64", "aarch64", "x86_64", "amd64"}
        diagnostics.append(
            _diagnostic(
                "architecture",
                "pass" if architecture_supported else "fail",
                "Supported architecture detected." if architecture_supported else "Only Apple Silicon and Intel are supported.",
                "Use a qualified Apple Silicon or Intel Mac.",
                version=machine or "unknown",
            )
        )

        say_path = env.get("TTS_SAY_PATH", "/usr/bin/say")
        found_say = shutil.which(say_path)
        diagnostics.append(
            _diagnostic(
                "say",
                "pass" if found_say else "fail",
                "Speech executable is available." if found_say else "The macOS speech executable is unavailable.",
                "Use the macOS-provided say command and configure TTS_SAY_PATH if needed.",
                version=f"macOS {mac_version}" if found_say else None,
            )
        )

        python_supported = sys.version_info >= (3, 11)
        diagnostics.append(
            _diagnostic(
                "python",
                "pass" if python_supported else "fail",
                "Python 3.11 or newer is required.",
                "Install or select Python 3.11 or newer.",
                version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            )
        )

        uv_path = shutil.which("uv")
        uv_version: str | None = None
        uv_reason = "The isolated-environment tool is unavailable."
        uv_status = "fail"
        if uv_path:
            try:
                uv_result = _run([uv_path, "--version"])
            except subprocess.TimeoutExpired:
                uv_reason = "The environment-tool version check timed out."
            else:
                uv_version = _reported_version(uv_result.stdout)
                if uv_result.returncode == 0 and uv_version:
                    uv_status = "pass"
                    uv_reason = "The isolated-environment tool is available."
                else:
                    uv_reason = "The environment-tool version could not be verified."
        diagnostics.append(
            _diagnostic(
                "uv",
                uv_status,
                uv_reason,
                "Install uv using its approved distribution channel.",
                version=uv_version,
            )
        )

        ffmpeg_path = env.get("TTS_FFMPEG_PATH", "ffmpeg")
        found_ffmpeg = shutil.which(ffmpeg_path)
        ffmpeg_ok = False
        ffmpeg_version: str | None = None
        if found_ffmpeg:
            try:
                version_result = _run([found_ffmpeg, "-version"])
                result = _run([found_ffmpeg, "-hide_banner", "-encoders"])
                ffmpeg_ok = (
                    version_result.returncode == 0
                    and bool(_reported_version(version_result.stdout))
                    and result.returncode == 0
                    and ("libmp3lame" in result.stdout or " mp3 " in result.stdout)
                    and "pcm_s16le" in result.stdout
                )
                ffmpeg_version = _reported_version(version_result.stdout)
            except subprocess.TimeoutExpired:
                diagnostics.append(
                    _diagnostic(
                        "ffmpeg",
                        "fail",
                        "The codec inspection timed out.",
                        "Verify the ffmpeg executable and retry the check.",
                    )
                )
            else:
                if not any(item["id"] == "ffmpeg" for item in diagnostics):
                    diagnostics.append(
                        _diagnostic(
                            "ffmpeg",
                            "pass" if ffmpeg_ok else "fail",
                            "MP3 and WAV encoders are available."
                            if ffmpeg_ok
                            else "Required MP3 or WAV encoders are unavailable.",
                            "Install ffmpeg with MP3 and PCM WAV encoder support.",
                            version=ffmpeg_version if ffmpeg_ok else None,
                        )
                    )
        else:
            diagnostics.append(
                _diagnostic(
                    "ffmpeg",
                    "fail",
                    "The ffmpeg executable is unavailable.",
                    "Install ffmpeg with MP3 and PCM WAV encoder support.",
                )
            )

        voices: set[str] = set()
        voice_error: str | None = None
        if found_say:
            try:
                voices = _voice_names(found_say)
            except subprocess.TimeoutExpired:
                voice_error = "Voice inventory check timed out."
            except OSError:
                voice_error = "Voice inventory could not be queried."
        else:
            voice_error = "The macOS speech executable is unavailable."
        for item_id, env_name, default in (*_REQUIRED_VOICES, _OPTIONAL_VOICE):
            required = item_id != "voice-en-gb"
            voice = env.get(env_name, default)
            present = _voice_present(voice, voices) if not voice_error else False
            status = "pass" if present else ("warn" if not required else "fail")
            reason = (
                "Configured voice is available."
                if present
                else voice_error or "Configured voice is unavailable."
            )
            remediation = (
                "No action required."
                if present
                else f"Install or select the configured voice for {env_name}."
            )
            diagnostics.append(
                _diagnostic(
                    item_id,
                    status,
                    reason,
                    remediation,
                    version="available" if present else None,
                    required=required,
                )
            )

        configuration_ok = _configuration_valid(env)
        diagnostics.append(
            _diagnostic(
                "configuration",
                "pass" if configuration_ok else "fail",
                "Configuration values are valid."
                if configuration_ok
                else "One or more configuration values are invalid.",
                "Correct the invalid TTS configuration values.",
                version="valid" if configuration_ok else None,
            )
        )

        credential_ok = _credential_is_accessible(env)
        diagnostics.append(
            _diagnostic(
                "credential",
                "pass" if credential_ok else "fail",
                "Exactly one accessible credential source is configured."
                if credential_ok
                else "A single nonempty credential source is required.",
                "Set TTS_API_KEY or a protected TTS_API_KEY_FILE, but not both.",
                version="available" if credential_ok else None,
            )
        )

        destination = _destination(env)
        destination_ok = _destination_accessible(destination)
        diagnostics.append(
            _diagnostic(
                "destination",
                "pass" if destination_ok else "fail",
                "Installation destination is accessible."
                if destination_ok
                else "Installation destination is unavailable or not writable.",
                "Choose an absolute, user-writable installation destination.",
                version="available" if destination_ok else None,
            )
        )

        disk_path = destination if destination.exists() else destination.parent
        disk_usage = shutil.disk_usage(disk_path)
        try:
            min_disk = int(env.get("TTS_MAX_TEMP_BYTES", str(256 * 1024 * 1024)))
        except ValueError:
            min_disk = 1
        disk_ok = disk_usage.free >= min_disk
        diagnostics.append(
            _diagnostic(
                "disk",
                "pass" if disk_ok else "fail",
                "Available disk space meets the configured temporary-storage budget."
                if disk_ok
                else "Available disk space is below the configured temporary-storage budget.",
                "Free disk space or lower TTS_MAX_TEMP_BYTES within its supported range.",
                version=f"{disk_usage.free} bytes free",
            )
        )

        try:
            port = int(env.get("TTS_PORT", "8000"))
            host = env.get("TTS_HOST", "127.0.0.1")
            port_ok = _port_available(host, port) if 1 <= port <= 65535 else False
        except (OSError, ValueError):
            port_ok = False
            port = 0
        diagnostics.append(
            _diagnostic(
                "port",
                "pass" if port_ok else "fail",
                "Configured service port is available."
                if port_ok
                else "Configured service port is invalid or already in use.",
                "Stop the conflicting process or choose an available TTS_PORT.",
                version=str(port) if port else None,
            )
        )
    except (OSError, subprocess.SubprocessError) as exc:
        diagnostics.append(
            _diagnostic(
                "diagnostic-operation",
                "fail",
                f"Diagnostic operation could not be completed ({type(exc).__name__}).",
                "Check host permissions and retry the prerequisite inspection.",
            )
        )
        return {"ready": False, "complete": False, "diagnostics": diagnostics}

    ready = not any(item["status"] == "fail" and item["required"] for item in diagnostics)
    return {"ready": ready, "complete": True, "diagnostics": diagnostics}


def _human_report(report: dict[str, Any]) -> str:
    lines = [f"Prerequisites: {'ready' if report['ready'] else 'not ready'}"]
    for item in report["diagnostics"]:
        version = f" ({item['version']})" if item["version"] else ""
        lines.append(
            f"{item['status'].upper()} {item['id']}{version}: {item['reason']} "
            f"Remediation: {item['remediation']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect macOS speech prerequisites without changes.")
    parser.add_argument("--json", action="store_true", help="write machine-readable diagnostics")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    report = inspect_prerequisites()
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(_human_report(report))
    if not report["complete"]:
        return 2
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
