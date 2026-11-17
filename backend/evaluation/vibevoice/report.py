from __future__ import annotations

import json
import os
import stat
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal, NotRequired, TypedDict


RunState = Literal[
    "preflight", "ready", "generating", "reviewing", "complete", "blocked", "failed", "cancelled"
]
ResultStatus = Literal["pending", "completed", "failed", "cancelled", "blocked", "incomplete"]
DecisionOutcome = Literal["retain", "partially_retain", "remove", "seek_alternative"]

_RUN_STATES = {
    "preflight",
    "ready",
    "generating",
    "reviewing",
    "complete",
    "blocked",
    "failed",
    "cancelled",
}
_RESULT_STATUSES = {"pending", "completed", "failed", "cancelled", "blocked", "incomplete"}
_DECISIONS = {"retain", "partially_retain", "remove", "seek_alternative"}
_AVAILABILITY = {"available", "unavailable", "unauthorized", "untested"}
_REQUIRED_RESULT_REASON = {"failed", "cancelled", "blocked", "incomplete"}


class ConfigurationRecord(TypedDict):
    configuration_id: str
    method: Literal["existing_macos", "vibevoice"]
    voice: str
    language: str
    machine_id: str
    terms_authorization_ids: list[str]
    availability: Literal["available", "unavailable", "unauthorized", "untested"]
    model_variant: NotRequired[str]
    adapter_identity: NotRequired[str]
    limitation_reason: NotRequired[str]


class SampleRecord(TypedDict):
    sample_id: str
    language: str
    text: str
    attribution: str
    terms_authorization_id: str
    permitted: bool


class AuthorizationRecord(TypedDict):
    authorization_id: str
    material_type: Literal["model", "implementation", "dependency", "voice", "sample_text"]
    material_identity: str
    terms_reference: str
    intended_use: str
    status: Literal["permitted", "unresolved", "not_permitted"]
    reviewed_at: NotRequired[str]
    approved_action: NotRequired[str]
    approver: NotRequired[str]


class SampleResultRecord(TypedDict):
    sample_result_id: str
    run_id: str
    configuration_id: str
    sample_id: str
    status: ResultStatus
    audio_path: NotRequired[str]
    generation_time_ms: NotRequired[int]
    rating: NotRequired[int]
    observation: NotRequired[str]
    reason: NotRequired[str]


class EvaluationReport(TypedDict):
    run_id: str
    created_at: str
    output_directory: str
    state: RunState
    resource_limits: dict[str, Any]
    configuration_ids: list[str]
    sample_ids: list[str]
    configurations: list[ConfigurationRecord]
    samples: list[SampleRecord]
    authorizations: list[AuthorizationRecord]
    results: list[SampleResultRecord]
    inspections: list[dict[str, Any]]
    measurements: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    decision: NotRequired[dict[str, str] | None]
    operator: NotRequired[str]
    manifest_path: NotRequired[str]


def new_report(
    run_id: str,
    output_directory: str | Path,
    *,
    operator: str | None = None,
    manifest_path: str | None = None,
) -> EvaluationReport:
    report: EvaluationReport = {
        "run_id": run_id,
        "created_at": datetime.now().astimezone().isoformat(),
        "output_directory": str(Path(output_directory).resolve()),
        "state": "preflight",
        "resource_limits": {},
        "configuration_ids": [],
        "sample_ids": [],
        "configurations": [],
        "samples": [],
        "authorizations": [],
        "results": [],
        "inspections": [],
        "measurements": [],
        "issues": [],
        "decision": None,
    }
    if operator is not None:
        report["operator"] = operator
    if manifest_path is not None:
        report["manifest_path"] = manifest_path
    return report


def validate_report(report: Mapping[str, Any]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("report must be a mapping")
    _reject_credentials(report)

    run_id = _required_string(report, "run_id")
    _validate_timestamp(_required_string(report, "created_at"), "created_at")
    if report.get("state") not in _RUN_STATES:
        raise ValueError("state must be a recognized evaluation run state")
    output_directory = _required_string(report, "output_directory")
    if not Path(output_directory).is_absolute():
        raise ValueError("output_directory must be an absolute path")

    configurations = _required_list(report, "configurations")
    samples = _required_list(report, "samples")
    authorizations = _required_list(report, "authorizations")
    results = _required_list(report, "results")
    configuration_ids = _required_list(report, "configuration_ids")
    sample_ids = _required_list(report, "sample_ids")
    for collection, name in (
        (configurations, "configurations"),
        (samples, "samples"),
        (authorizations, "authorizations"),
        (results, "results"),
    ):
        if any(not isinstance(item, Mapping) for item in collection):
            raise ValueError(f"{name} must contain objects")

    config_ids = [_required_string(item, "configuration_id") for item in configurations]
    sample_record_ids = [_required_string(item, "sample_id") for item in samples]
    authorization_ids = [_required_string(item, "authorization_id") for item in authorizations]
    result_ids = [_required_string(item, "sample_result_id") for item in results]
    _validate_unique(config_ids, "configuration_id")
    _validate_unique(sample_record_ids, "sample_id")
    _validate_unique(authorization_ids, "authorization_id")
    _validate_unique(result_ids, "sample_result_id")

    if configuration_ids != config_ids:
        raise ValueError("configuration_ids must match the configuration records")
    if sample_ids != sample_record_ids:
        raise ValueError("sample_ids must match the sample records")

    for authorization in authorizations:
        if authorization.get("material_type") not in {
            "model",
            "implementation",
            "dependency",
            "voice",
            "sample_text",
        }:
            raise ValueError("authorization material_type must be recognized")
        for field in ("material_identity", "terms_reference", "intended_use"):
            _required_string(authorization, field)
        if authorization.get("status") not in {"permitted", "unresolved", "not_permitted"}:
            raise ValueError("authorization status must be recognized")
        if authorization["status"] in {"permitted", "not_permitted"}:
            _validate_timestamp(_required_string(authorization, "reviewed_at"), "reviewed_at")

    for configuration in configurations:
        method = configuration.get("method")
        if method not in {"existing_macos", "vibevoice"}:
            raise ValueError("method must be existing_macos or vibevoice")
        for field in ("voice", "language", "machine_id"):
            _required_string(configuration, field)
        terms_ids = configuration.get("terms_authorization_ids")
        if not isinstance(terms_ids, list):
            raise ValueError("terms_authorization_ids must be a list")
        _validate_unique(terms_ids, "terms_authorization_ids")
        if not set(terms_ids).issubset(authorization_ids):
            raise ValueError("configuration references an unknown terms authorization")
        availability = configuration.get("availability")
        if availability not in _AVAILABILITY:
            raise ValueError("availability must be recognized")
        if availability != "available" and not configuration.get("limitation_reason"):
            raise ValueError("limitation_reason is required for unavailable configurations")
        if method == "vibevoice" and not configuration.get("model_variant"):
            raise ValueError("model_variant is required for VibeVoice configurations")
        if method == "vibevoice" and configuration["model_variant"] not in {
            "VibeVoice-TTS-1.5B",
            "VibeVoice-Realtime-0.5B",
        }:
            raise ValueError("model_variant must be an identified VibeVoice candidate")
        if availability == "available" and (
            not terms_ids
            or any(
                authorization["status"] != "permitted"
                for authorization in authorizations
                if authorization["authorization_id"] in terms_ids
            )
        ):
            raise ValueError("available configurations require permitted terms records")

    for sample in samples:
        for field in ("language", "text", "attribution", "terms_authorization_id"):
            _required_string(sample, field)
        if type(sample.get("permitted")) is not bool:
            raise ValueError("sample permitted must be a boolean")
        authorization = next(
            (
                item
                for item in authorizations
                if item["authorization_id"] == sample["terms_authorization_id"]
            ),
            None,
        )
        if authorization is None:
            raise ValueError("sample references an unknown terms_authorization_id")
        if sample["permitted"] != (authorization["status"] == "permitted"):
            raise ValueError("sample permission must match its terms authorization")

    for result in results:
        if result.get("run_id") != run_id:
            raise ValueError("result run_id must match the report run_id")
        if result.get("configuration_id") not in config_ids:
            raise ValueError("result references an unknown configuration_id")
        if result.get("sample_id") not in sample_record_ids:
            raise ValueError("result references an unknown sample_id")
        status = result.get("status")
        if status not in _RESULT_STATUSES:
            raise ValueError("result status must be recognized")
        if status in _REQUIRED_RESULT_REASON and not result.get("reason"):
            raise ValueError(f"reason is required for {status} results")
        if status == "completed" and "generation_time_ms" not in result and not result.get("reason"):
            raise ValueError("reason is required when generation_time_ms is unavailable")
        if "generation_time_ms" in result and (
            type(result["generation_time_ms"]) is not int or result["generation_time_ms"] < 0
        ):
            raise ValueError("generation_time_ms must be a non-negative integer")
        if "rating" in result:
            rating = result["rating"]
            if type(rating) is not int or not 1 <= rating <= 10:
                raise ValueError("rating must be an integer from 1 through 10")
            if status != "completed":
                raise ValueError("rating is allowed only for completed results")
        if "audio_path" in result:
            _validate_relative_audio_path(result["audio_path"])
        if status == "completed" and not result.get("audio_path"):
            raise ValueError("completed results require audio_path")
        configuration = next(
            item
            for item in configurations
            if item["configuration_id"] == result["configuration_id"]
        )
        sample = next(item for item in samples if item["sample_id"] == result["sample_id"])
        if configuration["language"] != sample["language"]:
            raise ValueError("result sample language must match its configuration")
        if status == "completed" and not sample["permitted"]:
            raise ValueError("unpermitted samples cannot have completed results")
        if configuration["availability"] != "available" and status == "completed":
            raise ValueError("unavailable configurations cannot have completed results")

    decision = report.get("decision")
    if decision is not None:
        if not isinstance(decision, Mapping) or decision.get("outcome") not in _DECISIONS:
            raise ValueError("decision outcome must be a recognized product-owner decision")
        if not isinstance(decision.get("rationale"), str) or not decision["rationale"].strip():
            raise ValueError("decision rationale is required")
        _required_string(decision, "decided_by")
        _validate_timestamp(_required_string(decision, "decided_at"), "decided_at")


def save_report(report: Mapping[str, Any], directory: str | Path) -> Path:
    validate_report(report)
    report_directory = ensure_private_directory(directory)
    ensure_private_directory(report["output_directory"])
    report_path = report_directory / "report.json"
    atomic_write_json(report_path, report)
    return report_path


def load_report(report_path: str | Path) -> EvaluationReport:
    path = Path(report_path)
    _require_private_directory(path.parent)
    _require_private_file(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read evaluation report: {exc}") from exc
    validate_report(data)
    _require_private_directory(Path(data["output_directory"]))
    return data


def ensure_private_directory(directory: str | Path) -> Path:
    requested = Path(directory)
    if requested.is_symlink():
        raise PermissionError("output directory must not be a symlink")
    resolved = requested.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    if resolved == repository_root or repository_root in resolved.parents:
        raise PermissionError("output directory must be outside the repository")
    if not resolved.exists():
        if not resolved.parent.is_dir():
            raise FileNotFoundError("output directory parent must already exist")
        resolved.mkdir(mode=0o700)
    _require_private_directory(resolved)
    return resolved


def atomic_write_json(path: str | Path, data: Mapping[str, Any]) -> None:
    target = Path(path)
    _require_private_directory(target.parent)
    encoded = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".report-", suffix=".tmp", dir=target.parent)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        else:
            os.chmod(temporary_name, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, target)
        if os.name != "nt":
            directory_descriptor = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def resolve_audio_path(report: Mapping[str, Any], sample_result_id: str) -> Path:
    result = next(
        (
            item
            for item in report["results"]
            if item.get("sample_result_id") == sample_result_id
        ),
        None,
    )
    if result is None or result.get("status") != "completed" or not result.get("audio_path"):
        raise FileNotFoundError("completed audio result was not found")
    relative = _validate_relative_audio_path(result["audio_path"])
    root = Path(report["output_directory"]).resolve(strict=True)
    audio_path = (root / Path(*relative.parts)).resolve(strict=True)
    if root not in audio_path.parents or not audio_path.is_file():
        raise FileNotFoundError("completed audio result was not found")
    _require_private_file(audio_path)
    return audio_path


def update_rating(
    report: dict[str, Any],
    sample_result_id: str,
    rating: int,
    observation: str,
    *,
    listened: bool,
) -> dict[str, Any]:
    result = next(
        (
            item
            for item in report["results"]
            if item.get("sample_result_id") == sample_result_id
        ),
        None,
    )
    if result is None:
        raise KeyError("sample result was not found")
    if result.get("status") != "completed":
        raise ValueError("only completed results may be rated")
    if not listened:
        raise ValueError("audio must be accessed before it can be rated")
    if type(rating) is not int or not 1 <= rating <= 10:
        raise ValueError("rating must be an integer from 1 through 10")
    if not isinstance(observation, str):
        raise ValueError("observation must be text")
    result["rating"] = rating
    if observation:
        result["observation"] = observation
    else:
        result.pop("observation", None)
    validate_report(report)
    return result


def update_decision(report: dict[str, Any], outcome: str, rationale: str) -> dict[str, str]:
    if outcome not in _DECISIONS:
        raise ValueError("decision outcome must be retain, partially_retain, remove, or seek_alternative")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("decision rationale is required")
    decision = {
        "outcome": outcome,
        "rationale": rationale.strip(),
        "decided_at": datetime.now().astimezone().isoformat(),
        "decided_by": report.get("operator", "local operator"),
    }
    report["decision"] = decision
    validate_report(report)
    return decision


def _validate_relative_audio_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("audio_path must be a safe relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("audio_path must be a safe relative path")
    return path


def _reject_credentials(value: Any) -> None:
    if isinstance(value, Mapping):
        forbidden = {"credential", "credentials", "token", "api_key", "password", "secret"}
        for key, child in value.items():
            if isinstance(key, str) and key.casefold() in forbidden:
                raise ValueError("credentials must not be stored in an evaluation report")
            _reject_credentials(child)
    elif isinstance(value, list):
        for item in value:
            _reject_credentials(item)


def _required_string(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value


def _required_list(record: Mapping[str, Any], field: str) -> list[Any]:
    value = record.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _validate_timestamp(value: str, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")


def _validate_unique(values: list[str], field: str) -> None:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{field} values must be non-empty strings")
    if len(set(values)) != len(values):
        raise ValueError(f"{field} values must be unique")


def _require_private_directory(directory: Path) -> None:
    resolved = directory.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    if resolved == repository_root or repository_root in resolved.parents:
        raise PermissionError("output directory must be outside the repository")
    try:
        info = resolved.lstat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"private directory does not exist: {resolved}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise PermissionError("output directory must be a real directory")
    owner_uid = os.getuid() if hasattr(os, "getuid") else info.st_uid
    if info.st_uid != owner_uid or (
        os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077
    ):
        raise PermissionError("output directory must be user-owned and owner-only")


def _require_private_file(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"report or audio file does not exist: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise PermissionError("report and audio files must be regular files")
    owner_uid = os.getuid() if hasattr(os, "getuid") else info.st_uid
    if info.st_uid != owner_uid or (
        os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077
    ):
        raise PermissionError("report and audio files must be user-owned and owner-only")
