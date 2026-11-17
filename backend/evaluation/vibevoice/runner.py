from __future__ import annotations

import copy
import http.client
import json
import os
import signal
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from evaluation.vibevoice.report import (
    ensure_private_directory,
    new_report,
    save_report,
    validate_report,
)


VIBEVOICE_CANDIDATES = ("VibeVoice-TTS-1.5B", "VibeVoice-Realtime-0.5B")
BASELINE_PATH = "/v1/audio/speech"
DEFAULT_GENERATION_TIMEOUT_SECONDS = 120
MAX_AUDIO_BYTES = 26_214_400

BaselineClient = Callable[[str, str, Mapping[str, Any], int], bytes]
ProcessFactory = Callable[..., Any]


class ManifestError(ValueError):
    pass


class BaselineError(RuntimeError):
    pass


class OutputLimitError(ValueError):
    pass


def validate_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise ManifestError("manifest must be an object")
    result = copy.deepcopy(dict(manifest))
    samples = result.get("samples")
    configurations = result.get("configurations")
    authorizations = result.get("authorizations")
    if not isinstance(samples, list) or not isinstance(configurations, list):
        raise ManifestError("manifest must include samples and configurations lists")
    if not isinstance(authorizations, list):
        raise ManifestError("manifest must include an authorizations list")
    if any(not isinstance(item, Mapping) for item in samples + configurations + authorizations):
        raise ManifestError("manifest records must be objects")

    sample_ids: set[str] = set()
    counts: Counter[str] = Counter()
    languages: set[str] = set()
    auth_by_id: dict[str, Mapping[str, Any]] = {}
    for authorization in authorizations:
        auth_id = _string_field(authorization, "authorization_id")
        if auth_id in auth_by_id:
            raise ManifestError(f"duplicate authorization_id: {auth_id}")
        if authorization.get("status") not in {"permitted", "unresolved", "not_permitted"}:
            raise ManifestError(f"authorization {auth_id} has an invalid status")
        for field in ("material_type", "material_identity", "terms_reference", "intended_use"):
            _string_field(authorization, field)
        auth_by_id[auth_id] = authorization

    for sample in samples:
        sample_id = _string_field(sample, "sample_id")
        if sample_id in sample_ids:
            raise ManifestError(f"duplicate sample_id: {sample_id}")
        sample_ids.add(sample_id)
        language = _string_field(sample, "language")
        language_group = _language_group(language)
        languages.add(language_group)
        counts[language_group] += 1
        text = _string_field(sample, "text")
        try:
            text_units = len(text.encode("utf-16-le")) // 2
        except UnicodeEncodeError as exc:
            raise ManifestError(f"sample {sample_id} contains invalid Unicode text") from exc
        if text_units > 5000:
            raise ManifestError(f"sample {sample_id} exceeds the existing speech API input limit")
        _string_field(sample, "attribution")
        auth_id = _string_field(sample, "terms_authorization_id")
        authorization = auth_by_id.get(auth_id)
        if authorization is None or authorization.get("material_type") != "sample_text":
            raise ManifestError(f"sample {sample_id} must reference a sample-text authorization")
        if type(sample.get("permitted")) is not bool:
            raise ManifestError(f"sample {sample_id} permission must be a boolean")
        if sample["permitted"] != (authorization.get("status") == "permitted"):
            raise ManifestError(f"sample {sample_id} permission does not match its authorization")

    if not languages:
        raise ManifestError("manifest must include at least one language")
    for language in languages:
        if counts[language] != 5:
            raise ManifestError(f"language {language} must have exactly five unique samples")

    configuration_ids: set[str] = set()
    baseline_languages: set[str] = set()
    baseline_machine_languages = {
        (
            _language_group(_string_field(configuration, "language")),
            _string_field(configuration, "machine_id"),
        )
        for configuration in configurations
        if configuration.get("method") == "existing_macos"
    }
    for configuration in configurations:
        configuration_id = _string_field(configuration, "configuration_id")
        if configuration_id in configuration_ids:
            raise ManifestError(f"duplicate configuration_id: {configuration_id}")
        configuration_ids.add(configuration_id)
        language = _language_group(_string_field(configuration, "language"))
        machine_id = _string_field(configuration, "machine_id")
        _string_field(configuration, "voice")
        if language not in languages:
            raise ManifestError(f"configuration {configuration_id} has no matching sample language")
        method = configuration.get("method")
        if method == "existing_macos":
            baseline_languages.add(language)
        elif method == "vibevoice":
            if configuration.get("model_variant") not in VIBEVOICE_CANDIDATES:
                raise ManifestError(f"configuration {configuration_id} has an unknown VibeVoice variant")
        else:
            raise ManifestError(f"configuration {configuration_id} has an unsupported method")
        if configuration.get("availability") not in {
            "available",
            "unavailable",
            "unauthorized",
            "untested",
        }:
            raise ManifestError(f"configuration {configuration_id} has an invalid availability")
        if configuration["availability"] != "available" and not configuration.get(
            "limitation_reason"
        ):
            raise ManifestError(f"configuration {configuration_id} requires a limitation_reason")
        terms_ids = configuration.get("terms_authorization_ids")
        if not isinstance(terms_ids, list) or any(
            not isinstance(auth_id, str) or auth_id not in auth_by_id for auth_id in terms_ids
        ):
            raise ManifestError(f"configuration {configuration_id} has invalid terms authorizations")
        if configuration["availability"] == "available" and (
            not terms_ids
            or any(auth_by_id[auth_id].get("status") != "permitted" for auth_id in terms_ids)
        ):
            raise ManifestError(
                f"available configuration {configuration_id} requires permitted terms"
            )
        if any(
            sample["language"] != configuration["language"]
            for sample in samples
            if _language_group(sample["language"]) == language
        ):
            raise ManifestError(
                f"configuration {configuration_id} language must match its sample language tag"
            )
        if method == "vibevoice" and (language, machine_id) not in baseline_machine_languages:
            raise ManifestError(
                f"configuration {configuration_id} requires a matching baseline on its machine"
            )

    if not languages.issubset(baseline_languages):
        missing = ", ".join(sorted(languages - baseline_languages))
        raise ManifestError(f"the existing speech baseline is missing for: {missing}")
    return result


def run_evaluation(
    manifest: Mapping[str, Any],
    output_directory: str | Path,
    *,
    approve_run: bool,
    baseline_url: str,
    baseline_token: str | None,
    approved_adapters: Mapping[str, Sequence[str]],
    baseline_client: BaselineClient | None = None,
    process_factory: ProcessFactory | None = None,
    timeout_seconds: int = DEFAULT_GENERATION_TIMEOUT_SECONDS,
    preflight: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if approve_run is not True:
        raise PermissionError("the evaluation run requires explicit approval")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
        raise ValueError("timeout_seconds must be between 1 and 3600")
    _validate_baseline_url(baseline_url)

    checked_manifest = validate_manifest(manifest)
    output_root = ensure_private_directory(output_directory)
    run_id = checked_manifest.get("run_id") or f"run-{uuid.uuid4().hex}"
    report = new_report(
        run_id,
        output_root,
        operator=checked_manifest.get("operator"),
        manifest_path=checked_manifest.get("manifest_path"),
    )
    report["resource_limits"] = {"generation_timeout_seconds": timeout_seconds}
    report["configuration_ids"] = [
        configuration["configuration_id"] for configuration in checked_manifest["configurations"]
    ]
    report["sample_ids"] = [sample["sample_id"] for sample in checked_manifest["samples"]]
    report["configurations"] = checked_manifest["configurations"]
    report["samples"] = checked_manifest["samples"]
    report["authorizations"] = checked_manifest["authorizations"]
    if preflight is not None:
        report["inspections"] = list(preflight["inspections"])
        report["measurements"] = list(preflight["measurements"])
        machine_ids = {
            configuration["machine_id"] for configuration in report["configurations"]
        }
        for blocker in preflight["blockers"]:
            if (
                blocker["category"] == "capacity"
                or blocker["scope"] == "run"
                or blocker["scope"] in machine_ids
            ):
                _record_issue(report, blocker["category"], blocker["reason"])
    if not baseline_token:
        for configuration in report["configurations"]:
            if (
                configuration["method"] == "existing_macos"
                and configuration["availability"] == "available"
            ):
                configuration["availability"] = "unavailable"
                configuration["limitation_reason"] = (
                    "The existing authenticated baseline token is unavailable."
                )
    report["state"] = "ready"
    validate_report(report)

    capacity_blockers = [
        blocker
        for blocker in (preflight or {}).get("blockers", [])
        if blocker["category"] == "capacity"
    ]
    if capacity_blockers:
        reason = capacity_blockers[0]["reason"]
        report["state"] = "blocked"
        _block_remaining(report, reason)
        save_report(report, output_root)
        return report

    candidate_variants = {
        configuration["model_variant"]
        for configuration in report["configurations"]
        if configuration["method"] == "vibevoice"
    }
    for variant in VIBEVOICE_CANDIDATES:
        if variant not in candidate_variants:
            _record_issue(
                report,
                "unavailable",
                f"{variant} has no declared configuration and was not evaluated.",
            )

    report["state"] = "generating"
    save_report(report, output_root)
    baseline = baseline_client or _request_baseline
    process_factory = process_factory or subprocess.Popen
    stopped_reason: str | None = None

    try:
        ordered_configurations = sorted(
            report["configurations"],
            key=lambda item: item["method"] != "existing_macos",
        )
        for configuration in ordered_configurations:
            matching_samples = [
                sample
                for sample in report["samples"]
                if _language_group(sample["language"]) == _language_group(configuration["language"])
            ]
            for sample in matching_samples:
                if stopped_reason is not None:
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="blocked",
                        reason=f"Run stopped before this comparison: {stopped_reason}",
                    )
                    continue
                sample_blocker = _sample_blocker(sample, report["authorizations"])
                if sample_blocker is not None:
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="blocked",
                        reason=sample_blocker,
                    )
                    continue
                if configuration["method"] == "vibevoice":
                    baseline_result = next(
                        (
                            result
                            for result in report["results"]
                            if result["sample_id"] == sample["sample_id"]
                            and result["configuration_id"]
                            in {
                                baseline_config["configuration_id"]
                                for baseline_config in report["configurations"]
                                if baseline_config["method"] == "existing_macos"
                                and baseline_config["machine_id"] == configuration["machine_id"]
                                and _language_group(baseline_config["language"])
                                == _language_group(configuration["language"])
                            }
                        ),
                        None,
                    )
                    if baseline_result is None or baseline_result["status"] != "completed":
                        _record_result(
                            report,
                            configuration,
                            sample,
                            status="blocked",
                            reason="The existing speech baseline is not available for this sample.",
                        )
                        continue
                blocked_reason = _configuration_blocker(
                    configuration,
                    report["authorizations"],
                    approved_adapters,
                    baseline_token,
                )
                if blocked_reason is not None:
                    if (
                        configuration["method"] == "vibevoice"
                        and configuration["availability"] == "available"
                    ):
                        configuration["availability"] = "unavailable"
                        configuration["limitation_reason"] = blocked_reason
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="blocked",
                        reason=blocked_reason,
                    )
                    continue
                try:
                    started_at = time.perf_counter()
                    if configuration["method"] == "existing_macos":
                        audio = baseline(
                            baseline_url,
                            baseline_token or "",
                            _baseline_payload(configuration, sample),
                            timeout_seconds,
                        )
                    else:
                        command = approved_adapters[configuration["model_variant"]]
                        audio = _run_adapter(
                            command,
                            configuration,
                            sample,
                            timeout_seconds,
                            process_factory,
                        )
                    generation_time_ms = max(
                        0, round((time.perf_counter() - started_at) * 1000)
                    )
                    if not isinstance(audio, bytes) or not audio:
                        raise ValueError("adapter returned no audio")
                    if len(audio) > MAX_AUDIO_BYTES:
                        raise ValueError("generated audio exceeds the configured size limit")
                    result = _record_result(
                        report,
                        configuration,
                        sample,
                        status="completed",
                        generation_time_ms=generation_time_ms,
                        audio_path=_write_audio(output_root, audio),
                    )
                    save_report(report, output_root)
                except KeyboardInterrupt:
                    stopped_reason = "operator cancelled generation"
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="cancelled",
                        reason=stopped_reason,
                    )
                    report["state"] = "cancelled"
                    _block_remaining(report, stopped_reason)
                    save_report(report, output_root)
                    return report
                except subprocess.TimeoutExpired:
                    stopped_reason = "generation exceeded its time limit"
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="incomplete",
                        reason=stopped_reason,
                    )
                    report["state"] = "failed"
                    _block_remaining(report, stopped_reason)
                    save_report(report, output_root)
                    return report
                except TimeoutError:
                    stopped_reason = "generation exceeded its time limit"
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="incomplete",
                        reason=stopped_reason,
                    )
                    report["state"] = "failed"
                    _block_remaining(report, stopped_reason)
                    save_report(report, output_root)
                    return report
                except (
                    BaselineError,
                    OSError,
                    RuntimeError,
                    ValueError,
                    subprocess.SubprocessError,
                ) as exc:
                    stopped_reason = _safe_failure_reason(exc)
                    _record_result(
                        report,
                        configuration,
                        sample,
                        status="failed",
                        reason=stopped_reason,
                    )
                    report["state"] = "failed"
                    _block_remaining(report, stopped_reason)
                    save_report(report, output_root)
                    return report
    except KeyboardInterrupt:
        report["state"] = "cancelled"
        _block_remaining(report, "operator cancelled generation")
        save_report(report, output_root)
        return report

    completed = any(result["status"] == "completed" for result in report["results"])
    report["state"] = "reviewing" if completed else "blocked"
    save_report(report, output_root)
    return report


def _configuration_blocker(
    configuration: Mapping[str, Any],
    authorizations: Sequence[Mapping[str, Any]],
    approved_adapters: Mapping[str, Sequence[str]],
    baseline_token: str | None,
) -> str | None:
    if configuration["availability"] != "available":
        return configuration["limitation_reason"]
    auth_by_id = {item["authorization_id"]: item for item in authorizations}
    for auth_id in configuration["terms_authorization_ids"]:
        authorization = auth_by_id[auth_id]
        if authorization["status"] != "permitted":
            return f"Required {authorization['material_type']} authorization is unresolved or denied."
    if configuration["method"] == "existing_macos":
        if not baseline_token:
            return "The existing authenticated baseline token is unavailable."
        return None
    variant = configuration["model_variant"]
    command = approved_adapters.get(variant)
    if command is None:
        return f"No approved, already-installed adapter is registered for {variant}."
    if not isinstance(command, Sequence) or isinstance(command, str) or not command:
        return f"The approved adapter command for {variant} is invalid."
    if any(not isinstance(argument, str) or not argument for argument in command):
        return f"The approved adapter command for {variant} is invalid."
    executable = shutil.which(command[0]) if not Path(command[0]).is_absolute() else command[0]
    if executable is None or not Path(executable).is_file() or not os.access(executable, os.X_OK):
        return f"The approved adapter executable for {variant} is not installed."
    return None


def _baseline_payload(
    configuration: Mapping[str, Any],
    sample: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "input": sample["text"],
        "model": "macos-say",
        "language": configuration["language"],
        "voice": configuration["voice"],
        "response_format": "wav",
        "speed": 1.0,
    }


def _request_baseline(
    url: str,
    token: str,
    payload: Mapping[str, Any],
    timeout_seconds: int,
) -> bytes:
    parts = urlsplit(url)
    host = parts.hostname or ""
    connection = http.client.HTTPConnection(host, parts.port or 80, timeout=timeout_seconds)
    try:
        connection.request(
            "POST",
            BASELINE_PATH,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "audio/wav",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise BaselineError(f"baseline returned HTTP status {response.status}")
        if not (response.getheader("Content-Type") or "").lower().startswith("audio/"):
            raise BaselineError("baseline returned a non-audio response")
        audio = response.read(MAX_AUDIO_BYTES + 1)
        if len(audio) > MAX_AUDIO_BYTES:
            raise BaselineError("baseline audio exceeds the configured size limit")
        if not audio:
            raise BaselineError("baseline returned no audio")
        return audio
    except TimeoutError:
        raise
    except (OSError, http.client.HTTPException) as exc:
        raise BaselineError(f"baseline request failed ({type(exc).__name__})") from exc
    finally:
        connection.close()


def _run_adapter(
    command: Sequence[str],
    configuration: Mapping[str, Any],
    sample: Mapping[str, Any],
    timeout_seconds: int,
    process_factory: ProcessFactory,
) -> bytes:
    payload = json.dumps(
        {
            "text": sample["text"],
            "language": configuration["language"],
            "voice": configuration["voice"],
            "model_variant": configuration["model_variant"],
            "response_format": "wav",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    environment = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL")
        if key in os.environ
    }
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "NO_PROXY": "*",
        }
    )
    with tempfile.TemporaryFile() as audio_output:
        try:
            process = process_factory(
                list(command),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                shell=False,
                cwd=None,
                env=environment,
                start_new_session=True,
            )
        except OSError as exc:
            raise RuntimeError(f"adapter could not start ({type(exc).__name__})") from exc

        if process.stdin is None or process.stdout is None:
            _terminate_process_tree(process)
            raise RuntimeError("adapter pipes could not be created")

        output_limit_exceeded = threading.Event()
        reader_errors: list[OSError] = []
        writer_errors: list[OSError] = []

        def capture_audio() -> None:
            try:
                total = 0
                while chunk := process.stdout.read(64 * 1024):
                    total += len(chunk)
                    if total > MAX_AUDIO_BYTES:
                        output_limit_exceeded.set()
                        _terminate_process_tree(process)
                        return
                    audio_output.write(chunk)
            except OSError as exc:
                reader_errors.append(exc)

        def send_request() -> None:
            try:
                process.stdin.write(payload)
                process.stdin.flush()
            except OSError as exc:
                writer_errors.append(exc)
            finally:
                try:
                    process.stdin.close()
                except OSError as exc:
                    writer_errors.append(exc)

        reader = threading.Thread(target=capture_audio)
        writer = threading.Thread(target=send_request)
        reader.start()
        writer.start()
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            _terminate_process_tree(process)
            raise
        except BaseException:
            _terminate_process_tree(process)
            raise
        finally:
            writer.join()
            reader.join()
        if output_limit_exceeded.is_set():
            raise OutputLimitError("adapter audio exceeds the configured size limit")
        if reader_errors:
            raise RuntimeError(f"adapter audio could not be read ({type(reader_errors[0]).__name__})")
        if writer_errors and process.returncode == 0:
            raise RuntimeError(f"adapter request could not be sent ({type(writer_errors[0]).__name__})")
        if process.returncode != 0:
            raise RuntimeError(f"adapter exited with status {process.returncode}")
        audio_output.seek(0)
        return audio_output.read()


def _terminate_process_tree(process: Any) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    else:
        process.terminate()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()


def _record_result(
    report: dict[str, Any],
    configuration: Mapping[str, Any],
    sample: Mapping[str, Any],
    *,
    status: str,
    reason: str | None = None,
    generation_time_ms: int | None = None,
    audio_path: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sample_result_id": f"result-{uuid.uuid4().hex}",
        "run_id": report["run_id"],
        "configuration_id": configuration["configuration_id"],
        "sample_id": sample["sample_id"],
        "status": status,
    }
    if audio_path is not None:
        result["audio_path"] = audio_path
    if generation_time_ms is not None:
        result["generation_time_ms"] = generation_time_ms
    if reason is not None:
        result["reason"] = reason
        _record_issue(report, "unavailable" if status == "blocked" else status, reason, configuration, sample)
    report["results"].append(result)
    return result


def _sample_blocker(
    sample: Mapping[str, Any],
    authorizations: Sequence[Mapping[str, Any]],
) -> str | None:
    if not sample["permitted"]:
        return "Sample-text permission is unresolved or not permitted."
    authorization = next(
        item
        for item in authorizations
        if item["authorization_id"] == sample["terms_authorization_id"]
    )
    if authorization["status"] != "permitted":
        return "Sample-text authorization is unresolved or not permitted."
    return None


def _block_remaining(report: dict[str, Any], reason: str) -> None:
    completed_pairs = {
        (result["configuration_id"], result["sample_id"]) for result in report["results"]
    }
    for configuration in report["configurations"]:
        for sample in report["samples"]:
            if (
                _language_group(configuration["language"]) == _language_group(sample["language"])
                and (configuration["configuration_id"], sample["sample_id"]) not in completed_pairs
            ):
                _record_result(
                    report,
                    configuration,
                    sample,
                    status="blocked",
                    reason=f"Run stopped before this comparison: {reason}",
                )


def _record_issue(
    report: dict[str, Any],
    category: str,
    reason: str,
    configuration: Mapping[str, Any] | None = None,
    sample: Mapping[str, Any] | None = None,
) -> None:
    report["issues"].append(
        {
            "issue_id": f"issue-{uuid.uuid4().hex}",
            "configuration_id": configuration["configuration_id"] if configuration else None,
            "sample_id": sample["sample_id"] if sample else None,
            "category": category if category in {
                "unavailable",
                "unauthorized",
                "capacity",
                "permission",
                "unsupported_language",
                "failed",
                "cancelled",
                "resource_limit",
            } else "failed",
            "reason": reason,
            "recorded_at": datetime.now().astimezone().isoformat(),
        }
    )


def _write_audio(output_root: Path, audio: bytes) -> str:
    audio_directory = output_root / "audio"
    if audio_directory.exists():
        if audio_directory.is_symlink() or not audio_directory.is_dir():
            raise PermissionError("audio output directory must be a real directory")
        info = audio_directory.stat()
        owner_uid = os.getuid() if hasattr(os, "getuid") else info.st_uid
        if info.st_uid != owner_uid or (
            os.name != "nt" and info.st_mode & 0o077
        ):
            raise PermissionError("audio output directory must be user-owned and owner-only")
    else:
        audio_directory.mkdir(mode=0o700)
    filename = f"{uuid.uuid4().hex}.wav"
    target = audio_directory / filename
    temporary = audio_directory / f".{filename}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(audio)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return f"audio/{filename}"


def _validate_baseline_url(url: str) -> None:
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        is_loopback = ip_address(host).is_loopback
        port = parts.port
    except ValueError:
        is_loopback = False
        parts = urlsplit("")
        port = None
    if (
        parts.scheme != "http"
        or not is_loopback
        or (port is not None and not 1 <= port <= 65535)
        or parts.path != BASELINE_PATH
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
    ):
        raise ValueError("baseline URL must be the local authenticated speech endpoint")


def _language_group(language: str) -> str:
    if not isinstance(language, str) or not language.strip():
        raise ManifestError("language must be a non-empty BCP 47 tag")
    primary = language.split("-", 1)[0].lower()
    if primary not in {"en", "de"}:
        raise ManifestError(f"unsupported evaluation language: {language}")
    return primary


def _string_field(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} is required")
    return value


def _safe_failure_reason(error: Exception) -> str:
    if isinstance(error, BaselineError):
        return str(error)
    if isinstance(error, OutputLimitError):
        return "adapter audio exceeds the configured size limit"
    if isinstance(error, subprocess.TimeoutExpired):
        return "generation exceeded its time limit"
    return f"generation failed ({type(error).__name__})"
