import os

from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


SESSION_TOKEN = "test-run-session-token-0123456789abcdef"


@pytest.fixture
def report_data(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir(mode=0o700)
    return {
        "run_id": "run-001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_directory": str(output_dir),
        "state": "reviewing",
        "resource_limits": {},
        "configuration_ids": ["baseline-en"],
        "sample_ids": ["sample-001"],
        "configurations": [
            {
                "configuration_id": "baseline-en",
                "method": "existing_macos",
                "voice": "test voice",
                "language": "en",
                "machine_id": "machine-001",
                "adapter_identity": "/private/model/weights",
                "terms_authorization_ids": ["voice-terms"],
                "availability": "available",
            }
        ],
        "samples": [
            {
                "sample_id": "sample-001",
                "language": "en",
                "text": "Permitted sample text.",
                "attribution": "test source",
                "terms_authorization_id": "sample-terms",
                "permitted": True,
            }
        ],
        "authorizations": [
            {
                "authorization_id": "voice-terms",
                "material_type": "voice",
                "material_identity": "test voice",
                "terms_reference": "reviewed test terms",
                "intended_use": "private evaluation",
                "status": "permitted",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "authorization_id": "sample-terms",
                "material_type": "sample_text",
                "material_identity": "test source",
                "terms_reference": "reviewed test terms",
                "intended_use": "private evaluation",
                "status": "permitted",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            },
        ],
        "results": [
            {
                "sample_result_id": "result-001",
                "run_id": "run-001",
                "configuration_id": "baseline-en",
                "sample_id": "sample-001",
                "status": "completed",
                "audio_path": "audio/sample-001.wav",
                "generation_time_ms": 125,
            }
        ],
        "inspections": [],
        "measurements": [],
        "issues": [],
        "decision": None,
    }


@pytest.fixture
def stored_report(tmp_path, report_data):
    from evaluation.vibevoice.report import save_report

    report_path = save_report(report_data, tmp_path / "review")
    audio_path = Path(report_data["output_directory"]) / "audio" / "sample-001.wav"
    audio_path.parent.mkdir(mode=0o700)
    audio_path.write_bytes(b"RIFF-test-audio")
    audio_path.chmod(0o600)
    return report_path


def _client(report_path):
    from evaluation.vibevoice.server import create_app

    return TestClient(
        create_app(report_path, session_token=SESSION_TOKEN),
        base_url="http://127.0.0.1",
    )


def _headers():
    return {
        "Origin": "http://127.0.0.1",
        "X-Session-Token": SESSION_TOKEN,
    }


def test_report_validation_rejects_bad_rating_and_missing_blocker_reason(report_data):
    from evaluation.vibevoice.report import validate_report

    report_data["results"][0]["rating"] = 11
    with pytest.raises(ValueError, match="rating"):
        validate_report(report_data)

    report_data["results"][0].pop("rating")
    report_data["results"][0]["status"] = "blocked"
    with pytest.raises(ValueError, match="reason"):
        validate_report(report_data)


def test_report_validation_rejects_audio_traversal(report_data):
    from evaluation.vibevoice.report import validate_report

    report_data["results"][0]["audio_path"] = "../../private.wav"
    with pytest.raises(ValueError, match="audio_path"):
        validate_report(report_data)


def test_report_validation_rejects_credentials_and_unsafe_output(report_data, tmp_path):
    from evaluation.vibevoice.report import save_report, validate_report

    report_data["resource_limits"]["api_key"] = "must-not-be-persisted"
    with pytest.raises(ValueError, match="credentials"):
        validate_report(report_data)
    del report_data["resource_limits"]["api_key"]

    report_data["output_directory"] = str(Path(__file__).resolve().parents[2])
    with pytest.raises(PermissionError, match="outside the repository"):
        save_report(report_data, tmp_path / "private-report")


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows does not expose POSIX permission bits",
)
def test_report_persistence_is_atomic_and_owner_only(tmp_path, report_data, monkeypatch):
    import evaluation.vibevoice.report as report_module

    report_path = report_module.save_report(report_data, tmp_path / "private")
    assert report_path.stat().st_mode & 0o077 == 0
    assert report_module.load_report(report_path) == report_data

    original = report_path.read_bytes()

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(report_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failure"):
        report_module.save_report(report_data, tmp_path / "private")
    assert report_path.read_bytes() == original
    assert list(report_path.parent.glob("*.tmp")) == []


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows does not expose POSIX permission bits",
)
def test_existing_unsafe_output_directory_is_rejected(tmp_path, report_data):
    from evaluation.vibevoice.report import save_report

    unsafe_dir = tmp_path / "shared"
    unsafe_dir.mkdir(mode=0o755)
    unsafe_dir.chmod(0o755)
    with pytest.raises(PermissionError, match="owner-only"):
        save_report(report_data, unsafe_dir)
    assert unsafe_dir.stat().st_mode & 0o077 == 0o055


def test_api_is_loopback_only_and_does_not_accept_host_override(stored_report):
    from evaluation.vibevoice.server import DEFAULT_HOST, create_app

    assert DEFAULT_HOST == "127.0.0.1"
    with pytest.raises(TypeError):
        create_app(stored_report, session_token=SESSION_TOKEN, host="0.0.0.0")


def test_get_run_and_report_exclude_private_filesystem_paths(stored_report):
    with _client(stored_report) as client:
        run = client.get("/api/run", headers=_headers())
        report = client.get("/api/report", headers=_headers())

    assert run.status_code == 200
    assert run.json()["run_id"] == "run-001"
    assert "output_directory" not in run.json()
    assert "adapter_identity" not in run.json()["configurations"][0]
    assert report.status_code == 200
    assert "output_directory" not in report.json()
    assert "audio_path" not in report.json()["results"][0]


def test_listening_review_page_embeds_session_token_and_keeps_data_local(stored_report):
    with _client(stored_report) as client:
        page = client.get("/listening-review")

    assert page.status_code == 200
    assert 'id="listening-review"' in page.text
    assert f'content="{SESSION_TOKEN}"' in page.text
    assert "https://" not in page.text
    assert "file://" not in page.text


def test_write_endpoints_require_matching_origin_and_run_token(stored_report):
    payload = {"rating": 8, "observation": "Clear pronunciation"}
    with _client(stored_report) as client:
        missing_token = client.put(
            "/api/ratings/result-001",
            json=payload,
            headers={"Origin": "http://127.0.0.1"},
        )
        wrong_origin = client.put(
            "/api/ratings/result-001",
            json=payload,
            headers={**_headers(), "Origin": "http://example.test"},
        )
        valid = client.put(
            "/api/ratings/result-001",
            json=payload,
            headers=_headers(),
        )

    assert missing_token.status_code == 401
    assert wrong_origin.status_code == 403
    assert valid.status_code == 409


def test_audio_is_resolved_by_result_id_and_rating_requires_audio_access(stored_report):
    with _client(stored_report) as client:
        before_listening = client.put(
            "/api/ratings/result-001",
            json={"rating": 8, "observation": "Good"},
            headers=_headers(),
        )
        audio = client.get("/api/audio/result-001", headers=_headers())
        rating = client.put(
            "/api/ratings/result-001",
            json={"rating": 8, "observation": "Good"},
            headers=_headers(),
        )
        unknown = client.get("/api/audio/unknown", headers=_headers())

    assert before_listening.status_code == 409
    assert audio.status_code == 200
    assert audio.content == b"RIFF-test-audio"
    assert rating.status_code == 200
    assert rating.json()["rating"] == 8
    assert unknown.status_code == 404


def test_rating_requires_completed_result_and_integer_rating(stored_report):
    with _client(stored_report) as client:
        bad_rating = client.put(
            "/api/ratings/result-001",
            json={"rating": 8.5, "observation": ""},
            headers=_headers(),
        )
        missing_result = client.put(
            "/api/ratings/unknown",
            json={"rating": 8, "observation": ""},
            headers=_headers(),
        )

    assert bad_rating.status_code == 422
    assert missing_result.status_code == 404


def test_decision_accepts_only_contract_outcomes(stored_report):
    with _client(stored_report) as client:
        invalid = client.put(
            "/api/decision",
            json={"outcome": "accept", "rationale": "Looks good"},
            headers=_headers(),
        )
        valid = client.put(
            "/api/decision",
            json={"outcome": "partially_retain", "rationale": "Keep the review UI."},
            headers=_headers(),
        )

    assert invalid.status_code == 422
    assert valid.status_code == 200
    assert valid.json()["outcome"] == "partially_retain"
