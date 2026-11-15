from __future__ import annotations

import os
import platform
import shutil
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.vibevoice.runner import VIBEVOICE_CANDIDATES, validate_manifest


MachineProbe = Callable[[], Mapping[str, str]]
StorageProbe = Callable[[Path], int]
MemoryProbe = Callable[[], int]
ConfigurationProbe = Callable[[Mapping[str, Any]], int | None]
AdapterProbe = Callable[[str, Sequence[str]], bool]


def inspect_manifest(
    manifest: Mapping[str, Any],
    *,
    machine_id: str,
    intended_storage_volume: str | Path | None,
    approved_adapters: Mapping[str, Sequence[str]],
    machine_probe: MachineProbe | None = None,
    storage_probe: StorageProbe | None = None,
    memory_probe: MemoryProbe | None = None,
    peak_memory_probe: ConfigurationProbe | None = None,
    footprint_probe: ConfigurationProbe | None = None,
    adapter_probe: AdapterProbe | None = None,
    inspected_at: str | None = None,
    execution_approved: bool = False,
) -> dict[str, Any]:
    checked = validate_manifest(manifest)
    if not isinstance(machine_id, str) or not machine_id.strip():
        raise ValueError("machine_id is required")
    configurations = [
        item for item in checked["configurations"] if item["machine_id"] == machine_id
    ]
    if not configurations:
        raise ValueError("machine_id must match a manifest configuration")

    machine_probe = machine_probe or _machine_details
    storage_probe = storage_probe or _available_storage
    memory_probe = memory_probe or _available_memory
    adapter_probe = adapter_probe or _adapter_is_installed
    timestamp = inspected_at or datetime.now().astimezone().isoformat()
    platform_data = dict(machine_probe())
    limitations: dict[str, str] = {}
    storage_bytes: int | None = None
    memory_bytes: int | None = None

    if intended_storage_volume is None:
        limitations["available_storage_bytes"] = "No intended storage volume was selected."
    else:
        try:
            storage_bytes = _measurement_value(storage_probe(Path(intended_storage_volume)))
        except (OSError, ValueError) as exc:
            limitations["available_storage_bytes"] = (
                f"Available storage could not be measured ({type(exc).__name__})."
            )
    try:
        memory_bytes = _measurement_value(memory_probe())
    except (OSError, ValueError) as exc:
        limitations["available_memory_bytes"] = (
            f"Available memory could not be measured ({type(exc).__name__})."
        )

    inspection = {
        "machine_id": machine_id,
        "platform": platform_data.get("platform", "unknown"),
        "architecture": platform_data.get("architecture", "unknown"),
        "inspected_at": timestamp,
        "intended_storage_volume": (
            str(intended_storage_volume) if intended_storage_volume is not None else None
        ),
        "available_storage_bytes": storage_bytes,
        "available_memory_bytes": memory_bytes,
        "requirements": [
            "Candidate runtime compatibility was not executed or inferred during read-only inspection."
        ],
        "permissions_status": "unclear",
        "limitations": limitations,
    }

    blockers: list[dict[str, str]] = []
    if not execution_approved:
        blockers.append(
            {
            "scope": "run",
            "category": "permission",
            "reason": "Evaluation execution requires separate explicit --approve-run approval.",
            }
        )
    blockers.append(
        {
            "scope": machine_id,
            "category": "permission",
            "reason": (
                "No target-machine download, installation, or service-change approval was "
                "provided; those actions remain blocked."
            ),
        }
    )
    for field, measured in (
        ("available_storage_bytes", storage_bytes),
        ("available_memory_bytes", memory_bytes),
    ):
        if measured is None:
            blockers.append(
                {
                    "scope": machine_id,
                    "category": "capacity",
                    "reason": (
                        f"{field} could not be verified; evaluation remains blocked until "
                        "the measurement is available."
                    ),
                }
            )
        elif measured == 0:
            blockers.append(
                {
                    "scope": machine_id,
                    "category": "capacity",
                    "reason": f"{field} is zero; evaluation cannot safely proceed.",
                }
            )
    measurements = []
    authorizations = {
        item["authorization_id"]: item for item in checked["authorizations"]
    }
    for configuration in configurations:
        configuration_id = configuration["configuration_id"]
        for authorization_id in configuration["terms_authorization_ids"]:
            authorization = authorizations[authorization_id]
            if authorization["status"] != "permitted":
                blockers.append(
                    {
                        "scope": configuration_id,
                        "category": "permission",
                        "reason": (
                            f"Required {authorization['material_type']} authorization is "
                            "unresolved or denied."
                        ),
                    }
                )
        if configuration["availability"] != "available":
            blockers.append(
                {
                    "scope": configuration_id,
                    "category": "unavailable",
                    "reason": configuration["limitation_reason"],
                }
            )
        if configuration["method"] == "vibevoice":
            variant = configuration["model_variant"]
            command = approved_adapters.get(variant)
            if command is None or not adapter_probe(variant, command):
                blockers.append(
                    {
                        "scope": configuration_id,
                        "category": "unavailable",
                        "reason": (
                            f"No approved, already-installed adapter is available for {variant}."
                        ),
                    }
                )

        missing: dict[str, str] = {}
        footprint = _optional_measurement(
            footprint_probe, configuration, "installed footprint", missing
        )
        peak_memory = _optional_measurement(
            peak_memory_probe, configuration, "peak memory", missing
        )
        measurements.append(
            {
                "configuration_id": configuration_id,
                "installed_footprint_bytes": footprint,
                "peak_memory_bytes": peak_memory,
                "missing_measurement_reasons": missing,
            }
        )

    present_variants = {
        item["model_variant"]
        for item in configurations
        if item["method"] == "vibevoice"
    }
    for variant in VIBEVOICE_CANDIDATES:
        if variant not in present_variants:
            blockers.append(
                {
                    "scope": machine_id,
                    "category": "unavailable",
                    "reason": f"{variant} has no declared configuration and was not evaluated.",
                }
            )

    for sample in checked["samples"]:
        if sample["terms_authorization_id"] not in authorizations:
            continue
        authorization = authorizations[sample["terms_authorization_id"]]
        if not sample["permitted"] or authorization["status"] != "permitted":
            blockers.append(
                {
                    "scope": sample["sample_id"],
                    "category": "permission",
                    "reason": "Sample-text permission is unresolved or not permitted.",
                }
            )

    return {
        "inspections": [inspection],
        "measurements": measurements,
        "blockers": blockers,
    }


def _machine_details() -> Mapping[str, str]:
    return {
        "platform": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
    }


def _available_storage(volume: Path) -> int:
    return shutil.disk_usage(volume).free


def _available_memory() -> int:
    available_pages = os.sysconf("SC_AVPHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    if available_pages < 0 or page_size < 0:
        raise OSError("available memory is unavailable")
    return available_pages * page_size


def _adapter_is_installed(_variant: str, command: Sequence[str]) -> bool:
    if not command:
        return False
    executable = command[0]
    resolved = executable if Path(executable).is_absolute() else shutil.which(executable)
    return bool(resolved and Path(resolved).is_file() and os.access(resolved, os.X_OK))


def _measurement_value(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("measurement must be a non-negative integer")
    return value


def _optional_measurement(
    probe: ConfigurationProbe | None,
    configuration: Mapping[str, Any],
    label: str,
    missing: dict[str, str],
) -> int | None:
    field = "installed_footprint_bytes" if label == "installed footprint" else "peak_memory_bytes"
    if probe is None:
        missing[field] = (
            "No trusted installed-footprint measurement was provided."
            if field == "installed_footprint_bytes"
            else "Peak memory is not measured during read-only preflight."
        )
        return None
    try:
        value = probe(configuration)
        if value is None:
            missing[field] = (
                "No trusted installed-footprint measurement was provided."
                if field == "installed_footprint_bytes"
                else "Peak memory is not measured during read-only preflight."
            )
            return None
        return _measurement_value(value)
    except (OSError, ValueError) as exc:
        missing[field] = f"{label.capitalize()} could not be measured ({type(exc).__name__})."
        return None
