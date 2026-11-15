from datetime import datetime, timezone


def _manifest():
    authorizations = [
        {
            "authorization_id": "sample-terms",
            "material_type": "sample_text",
            "material_identity": "test samples",
            "terms_reference": "reviewed sample terms",
            "intended_use": "private evaluation",
            "status": "permitted",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "authorization_id": "voice-terms",
            "material_type": "voice",
            "material_identity": "test voice",
            "terms_reference": "reviewed voice terms",
            "intended_use": "private evaluation",
            "status": "permitted",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "authorization_id": "model-terms",
            "material_type": "model",
            "material_identity": "VibeVoice-TTS-1.5B",
            "terms_reference": "terms need review",
            "intended_use": "private evaluation",
            "status": "unresolved",
        },
    ]
    samples = [
        {
            "sample_id": f"en-{index}",
            "language": "en-US",
            "text": f"Sample {index}.",
            "attribution": "test source",
            "terms_authorization_id": "sample-terms",
            "permitted": True,
        }
        for index in range(1, 6)
    ]
    configurations = [
        {
            "configuration_id": "baseline-en",
            "method": "existing_macos",
            "voice": "test voice",
            "language": "en-US",
            "machine_id": "test-machine",
            "terms_authorization_ids": ["voice-terms"],
            "availability": "available",
        },
        {
            "configuration_id": "tts-en",
            "method": "vibevoice",
            "model_variant": "VibeVoice-TTS-1.5B",
            "voice": "test voice",
            "language": "en-US",
            "machine_id": "test-machine",
            "terms_authorization_ids": ["voice-terms", "model-terms"],
            "availability": "unavailable",
            "limitation_reason": "Model terms are unresolved.",
        },
    ]
    return {
        "samples": samples,
        "configurations": configurations,
        "authorizations": authorizations,
    }


def test_inspection_is_read_only_for_selected_machine_and_volume(tmp_path):
    from evaluation.vibevoice.inspection import inspect_manifest

    calls = []
    volume = tmp_path / "chosen-volume"
    result = inspect_manifest(
        _manifest(),
        machine_id="test-machine",
        intended_storage_volume=volume,
        approved_adapters={},
        machine_probe=lambda: calls.append("machine") or {
            "platform": "test-os",
            "architecture": "test-arch",
        },
        storage_probe=lambda path: calls.append(path) or 123456,
        memory_probe=lambda: calls.append("memory") or 654321,
        peak_memory_probe=lambda _configuration: None,
        footprint_probe=lambda _configuration: None,
        adapter_probe=lambda *_args: False,
    )

    assert calls == ["machine", volume, "memory"]
    inspection = result["inspections"][0]
    assert inspection["machine_id"] == "test-machine"
    assert inspection["platform"] == "test-os"
    assert inspection["available_storage_bytes"] == 123456
    assert inspection["available_memory_bytes"] == 654321
    assert inspection["intended_storage_volume"] == str(volume)


def test_inspection_reports_terms_approval_and_missing_measurement_reasons(tmp_path):
    from evaluation.vibevoice.inspection import inspect_manifest

    result = inspect_manifest(
        _manifest(),
        machine_id="test-machine",
        intended_storage_volume=tmp_path,
        approved_adapters={},
        machine_probe=lambda: {"platform": "test-os", "architecture": "test-arch"},
        storage_probe=lambda _path: 123,
        memory_probe=lambda: None,
        peak_memory_probe=lambda _configuration: None,
        footprint_probe=lambda _configuration: None,
        adapter_probe=lambda *_args: False,
        inspected_at="2025-01-01T00:00:00+00:00",
    )

    blockers = result["blockers"]
    assert any("unresolved" in blocker["reason"].lower() for blocker in blockers)
    assert any("explicit" in blocker["reason"].lower() for blocker in blockers)
    measurement = next(
        item for item in result["measurements"] if item["configuration_id"] == "tts-en"
    )
    assert measurement["missing_measurement_reasons"] == {
        "installed_footprint_bytes": "No trusted installed-footprint measurement was provided.",
        "peak_memory_bytes": "Peak memory is not measured during read-only preflight.",
    }
    inspection = result["inspections"][0]
    assert inspection["inspected_at"] == "2025-01-01T00:00:00+00:00"
    assert inspection["available_memory_bytes"] is None
    assert inspection["limitations"]["available_memory_bytes"]
