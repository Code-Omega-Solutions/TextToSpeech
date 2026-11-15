import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


SESSION_TOKEN = "private-review-session-token-012345"


def _report_path(tmp_path):
    from evaluation.vibevoice.report import new_report, save_report

    output = tmp_path / "output"
    output.mkdir(mode=0o700)
    report = new_report("web-run", output)
    report["state"] = "reviewing"
    report["configuration_ids"] = ["baseline-en"]
    report["sample_ids"] = ["sample-en"]
    report["configurations"] = [
        {
            "configuration_id": "baseline-en",
            "method": "existing_macos",
            "voice": "test voice",
            "language": "en-US",
            "machine_id": "test-machine",
            "terms_authorization_ids": ["voice-terms"],
            "availability": "available",
        }
    ]
    report["samples"] = [
        {
            "sample_id": "sample-en",
            "language": "en-US",
            "text": "Private test sample.",
            "attribution": "test source",
            "terms_authorization_id": "sample-terms",
            "permitted": True,
        }
    ]
    report["authorizations"] = [
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
    ]
    return save_report(report, tmp_path / "private-report")


def _headers():
    return {"Origin": "http://127.0.0.1", "X-Session-Token": SESSION_TOKEN}


def test_summary_page_shows_evidence_and_all_owner_decisions(tmp_path):
    from evaluation.vibevoice.server import create_app

    with TestClient(
        create_app(_report_path(tmp_path), session_token=SESSION_TOKEN),
        base_url="http://127.0.0.1",
    ) as client:
        page = client.get("/results-summary")

    assert page.status_code == 200
    assert 'id="results-summary"' in page.text
    assert "Generation time (ms)" in page.text
    assert "result.generation_time_ms" in page.text
    assert "configuration.language" in page.text
    assert 'value="retain"' in page.text
    assert 'value="partially_retain"' in page.text
    assert 'value="remove"' in page.text
    assert 'value="seek_alternative"' in page.text
    assert "missing_measurement_reasons" in page.text
    assert "threshold" not in page.text.lower()
    assert page.headers["cache-control"] == "no-store"


def test_decision_api_accepts_all_four_owner_outcomes(tmp_path):
    from evaluation.vibevoice.server import create_app

    with TestClient(
        create_app(_report_path(tmp_path), session_token=SESSION_TOKEN),
        base_url="http://127.0.0.1",
    ) as client:
        for outcome in ("retain", "partially_retain", "remove", "seek_alternative"):
            response = client.put(
                "/api/decision",
                json={"outcome": outcome, "rationale": f"Review result: {outcome}."},
                headers=_headers(),
            )
            assert response.status_code == 200
            assert response.json()["outcome"] == outcome


def test_inspect_cli_uses_selected_read_only_target(monkeypatch, capsys, tmp_path):
    from evaluation.vibevoice import cli

    manifest = {"configurations": [{"machine_id": "target-1"}]}
    observed = {}
    monkeypatch.setattr(cli, "_load_manifest", lambda _path: manifest)

    def inspect_manifest(*args, **kwargs):
        observed.update(kwargs)
        return {"inspections": [], "measurements": [], "blockers": []}

    monkeypatch.setattr(cli, "inspect_manifest", inspect_manifest)
    assert cli.main(
        [
            "inspect",
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--volume",
            str(tmp_path / "chosen-volume"),
        ]
    ) == 0
    assert observed["machine_id"] == "target-1"
    assert observed["intended_storage_volume"] == tmp_path / "chosen-volume"
    assert json.loads(capsys.readouterr().out)["blockers"] == []


def test_run_cli_requires_explicit_approval(tmp_path):
    from evaluation.vibevoice.cli import main

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "run",
                "--manifest",
                str(tmp_path / "manifest.json"),
                "--output-dir",
                str(tmp_path / "output"),
            ]
        )
    assert exc_info.value.code == 2


def test_run_cli_passes_only_explicit_adapter_and_approval(monkeypatch, capsys, tmp_path):
    from evaluation.vibevoice import cli

    manifest = {"configurations": [{"machine_id": "target-1"}]}
    observed = {}
    monkeypatch.setattr(cli, "_load_manifest", lambda _path: manifest)
    monkeypatch.setattr(cli, "_baseline_token", lambda: "test-baseline-token")
    monkeypatch.setattr(
        cli,
        "inspect_manifest",
        lambda *_args, **_kwargs: {
            "inspections": [],
            "measurements": [],
            "blockers": [],
        },
    )
    def run_evaluation(*args, **kwargs):
        observed.update(kwargs)
        return {
            "run_id": "run-test",
            "state": "blocked",
            "output_directory": str(tmp_path / "private-output"),
            "inspections": [],
            "measurements": [],
            "results": [],
            "issues": [],
        }

    monkeypatch.setattr(cli, "run_evaluation", run_evaluation)
    assert cli.main(
        [
            "run",
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--output-dir",
            str(tmp_path / "private-output"),
            "--approve-run",
            "--adapter",
            "VibeVoice-TTS-1.5B=/opt/approved/adapter",
        ]
    ) == 0
    assert observed["approve_run"] is True
    assert observed["approved_adapters"] == {
        "VibeVoice-TTS-1.5B": ["/opt/approved/adapter"]
    }
    assert observed["baseline_token"] == "test-baseline-token"
    assert json.loads(capsys.readouterr().out)["state"] == "blocked"


def test_serve_cli_starts_only_the_loopback_review_server(monkeypatch, tmp_path):
    from evaluation.vibevoice import cli

    observed = {}
    monkeypatch.setattr(cli, "create_session_token", lambda: SESSION_TOKEN)
    monkeypatch.setattr(
        cli,
        "serve",
        lambda path, **kwargs: observed.update(path=path, **kwargs),
    )
    report = tmp_path / "report.json"
    assert cli.main(["serve", "--report", str(report), "--port", "8123"]) == 0
    assert observed == {
        "path": report,
        "session_token": SESSION_TOKEN,
        "port": 8123,
    }
