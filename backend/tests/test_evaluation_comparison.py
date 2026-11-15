import io
import json
import subprocess
import sys
from datetime import datetime, timezone

import pytest


BASELINE_URL = "http://127.0.0.1:8000/v1/audio/speech"


def _authorization(auth_id, material_type, identity, status="permitted"):
    record = {
        "authorization_id": auth_id,
        "material_type": material_type,
        "material_identity": identity,
        "terms_reference": "reviewed test terms",
        "intended_use": "private evaluation",
        "status": status,
    }
    if status != "unresolved":
        record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    return record


def _manifest(languages=("en", "de"), *, candidate_available=False):
    authorizations = [
        _authorization("sample-terms", "sample_text", "test sample set"),
        _authorization("voice-terms", "voice", "authorized test voices"),
        _authorization("implementation-terms", "implementation", "test adapter"),
        _authorization("dependency-terms", "dependency", "test runtime"),
        _authorization(
            "tts-model-terms",
            "model",
            "VibeVoice-TTS-1.5B",
            "permitted" if candidate_available else "unresolved",
        ),
        _authorization(
            "realtime-model-terms",
            "model",
            "VibeVoice-Realtime-0.5B",
            "permitted" if candidate_available else "unresolved",
        ),
    ]
    samples = []
    for language in languages:
        for index in range(5):
            samples.append(
                {
                    "sample_id": f"{language}-{index + 1}",
                    "language": "en-US" if language == "en" else "de-DE",
                    "text": f"Permitted {language} sample {index + 1}.",
                    "attribution": "test source",
                    "terms_authorization_id": "sample-terms",
                    "permitted": True,
                }
            )

    configurations = []
    for language in languages:
        config_language = "en-US" if language == "en" else "de-DE"
        configurations.append(
            {
                "configuration_id": f"baseline-{language}",
                "method": "existing_macos",
                "voice": "test baseline voice",
                "language": config_language,
                "machine_id": "test-machine",
                "terms_authorization_ids": ["voice-terms"],
                "availability": "available",
            }
        )
        for variant, model_auth, suffix in (
            ("VibeVoice-TTS-1.5B", "tts-model-terms", "tts"),
            ("VibeVoice-Realtime-0.5B", "realtime-model-terms", "realtime"),
        ):
            config = {
                "configuration_id": f"{suffix}-{language}",
                "method": "vibevoice",
                "model_variant": variant,
                "voice": "test candidate voice",
                "language": config_language,
                "machine_id": "test-machine",
                "terms_authorization_ids": [
                    "voice-terms",
                    "implementation-terms",
                    "dependency-terms",
                    model_auth,
                ],
                "availability": "available" if candidate_available else "unavailable",
            }
            if not candidate_available:
                config["limitation_reason"] = "No authorized adapter is available in this test."
            configurations.append(config)
    return {
        "run_id": "run-us1-test",
        "samples": samples,
        "configurations": configurations,
        "authorizations": authorizations,
    }


def test_manifest_requires_exactly_five_unique_permitted_texts_per_language():
    from evaluation.vibevoice.runner import ManifestError, validate_manifest

    manifest = _manifest()
    checked = validate_manifest(manifest)
    assert len(checked["samples"]) == 10
    assert {
        config.get("model_variant")
        for config in checked["configurations"]
        if config["method"] == "vibevoice"
    } == {"VibeVoice-TTS-1.5B", "VibeVoice-Realtime-0.5B"}

    with pytest.raises(ManifestError, match="exactly five"):
        validate_manifest({**manifest, "samples": manifest["samples"][:-1]})

    duplicate = _manifest()
    duplicate["samples"][1]["sample_id"] = duplicate["samples"][0]["sample_id"]
    with pytest.raises(ManifestError, match="duplicate sample_id"):
        validate_manifest(duplicate)

    mismatched_tag = _manifest(languages=("en",))
    mismatched_tag["configurations"][0]["language"] = "en"
    with pytest.raises(ManifestError, match="sample language tag"):
        validate_manifest(mismatched_tag)

    mismatched_machine = _manifest(languages=("en",))
    mismatched_machine["configurations"][0]["machine_id"] = "other-machine"
    with pytest.raises(ManifestError, match="baseline on its machine"):
        validate_manifest(mismatched_machine)


def test_unresolved_sample_terms_block_pairs_without_calling_baseline(tmp_path):
    from evaluation.vibevoice.runner import run_evaluation

    manifest = _manifest()
    manifest["authorizations"].append(
        {
            "authorization_id": "unresolved-sample-terms",
            "material_type": "sample_text",
            "material_identity": "sample en-1",
            "terms_reference": "pending review",
            "status": "unresolved",
            "intended_use": "private evaluation",
        }
    )
    manifest["samples"][0]["terms_authorization_id"] = "unresolved-sample-terms"
    manifest["samples"][0]["permitted"] = False
    calls = []

    report = run_evaluation(
        manifest,
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={},
        baseline_client=lambda *args: calls.append(args) or b"RIFF-baseline",
    )

    blocked = [result for result in report["results"] if result["sample_id"] == "en-1"]
    assert len(blocked) == 3
    assert all(result["status"] == "blocked" for result in blocked)
    assert all("permission" in result["reason"].lower() for result in blocked)
    assert all(call[2]["input"] != manifest["samples"][0]["text"] for call in calls)


def test_baseline_uses_authenticated_existing_speech_contract_and_shared_samples(tmp_path):
    from evaluation.vibevoice.runner import run_evaluation

    manifest = _manifest()
    calls = []

    def baseline_client(url, token, payload, timeout):
        calls.append((url, token, payload, timeout))
        return b"RIFF-baseline"

    report = run_evaluation(
        manifest,
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={},
        baseline_client=baseline_client,
        timeout_seconds=30,
    )

    baseline_results = [
        result
        for result in report["results"]
        if result["configuration_id"].startswith("baseline-")
    ]
    blocked_candidates = [
        result for result in report["results"] if result["status"] == "blocked"
    ]
    assert len(calls) == len(baseline_results) == 10
    assert {call[0] for call in calls} == {BASELINE_URL}
    assert {call[1] for call in calls} == {"secret-test-token"}
    assert all(call[2]["model"] == "macos-say" for call in calls)
    assert all(call[2]["response_format"] == "wav" for call in calls)
    assert all(call[3] == 30 for call in calls)
    assert {result["sample_id"] for result in baseline_results} == set(report["sample_ids"])
    assert all(type(result["generation_time_ms"]) is int for result in baseline_results)
    assert len(blocked_candidates) == 20
    assert all(result.get("reason") for result in blocked_candidates)
    assert report["state"] == "reviewing"
    assert "secret-test-token" not in json.dumps(report)


def test_baseline_url_must_be_the_loopback_speech_endpoint(tmp_path):
    from evaluation.vibevoice.runner import run_evaluation

    with pytest.raises(ValueError, match="local authenticated speech endpoint"):
        run_evaluation(
            _manifest(),
            tmp_path / "private-results",
            approve_run=True,
            baseline_url="http://example.test/v1/audio/speech",
            baseline_token="secret-test-token",
            approved_adapters={},
            baseline_client=lambda *_: b"unused",
        )


def test_approved_adapter_runs_without_shell_and_writes_private_audio(tmp_path, monkeypatch):
    from evaluation.vibevoice.runner import run_evaluation

    manifest = _manifest(languages=("en",), candidate_available=True)
    manifest["configurations"] = [
        config
        for config in manifest["configurations"]
        if config["method"] == "existing_macos" or config["model_variant"] == "VibeVoice-TTS-1.5B"
    ]
    command = [sys.executable, "-m", "approved_test_adapter"]
    calls = []
    communication_calls = []
    monkeypatch.setenv("TTS_API_KEY", "must-not-be-passed-to-adapter")

    def process_runner(argv, **kwargs):
        calls.append((argv, kwargs))

        class FakeProcess:
            def __init__(self):
                self.payload = b""
                self.returncode = 0
                self.stdout = io.BytesIO(b"RIFF-candidate")

                class FakeInput:
                    def write(inner_self, data):
                        self.payload += data

                    def flush(inner_self):
                        pass

                    def close(inner_self):
                        pass

                self.stdin = FakeInput()

            def wait(self, timeout):
                communication_calls.append((self.payload, timeout))
                return self.returncode

        return FakeProcess()

    report = run_evaluation(
        manifest,
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={"VibeVoice-TTS-1.5B": command},
        baseline_client=lambda *_: b"RIFF-baseline",
        process_factory=process_runner,
        timeout_seconds=17,
    )

    assert len(calls) == 5
    for (argv, kwargs), (process_input, timeout) in zip(calls, communication_calls):
        assert argv == command
        assert kwargs["shell"] is False
        assert kwargs["start_new_session"] is True
        assert timeout == 17
        assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
        assert "TTS_API_KEY" not in kwargs["env"]
        assert json.loads(process_input)["model_variant"] == "VibeVoice-TTS-1.5B"
    candidate_results = [
        result for result in report["results"] if result["configuration_id"] == "tts-en"
    ]
    assert len(candidate_results) == 5
    assert all(result["status"] == "completed" for result in candidate_results)
    assert all(type(result["generation_time_ms"]) is int for result in candidate_results)
    assert {
        result["sample_id"] for result in candidate_results
    } == {
        result["sample_id"]
        for result in report["results"]
        if result["configuration_id"] == "baseline-en"
    }
    audio = tmp_path / "private-results" / candidate_results[0]["audio_path"]
    assert audio.read_bytes() == b"RIFF-candidate"
    assert audio.stat().st_mode & 0o077 == 0


def test_timeout_stops_run_and_preserves_incomplete_reasons(tmp_path, monkeypatch):
    from evaluation.vibevoice.runner import run_evaluation

    manifest = _manifest(languages=("en",), candidate_available=True)
    manifest["configurations"] = [
        config
        for config in manifest["configurations"]
        if config["method"] == "existing_macos" or config["model_variant"] == "VibeVoice-TTS-1.5B"
    ]

    class TimeoutProcess:
        pid = 123456
        returncode = None

        def __init__(self):
            self.calls = 0
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(cmd="approved-adapter", timeout=timeout)
            self.returncode = -15
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    def timeout(*_args, **_kwargs):
        return TimeoutProcess()

    monkeypatch.setattr("evaluation.vibevoice.runner.os.killpg", lambda *_args: None)

    report = run_evaluation(
        manifest,
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={"VibeVoice-TTS-1.5B": [sys.executable]},
        baseline_client=lambda *_: b"RIFF-baseline",
        process_factory=timeout,
        timeout_seconds=1,
    )

    assert report["state"] == "failed"
    timed_out = next(result for result in report["results"] if result["status"] == "incomplete")
    assert "time limit" in timed_out["reason"]
    assert all(
        result.get("reason")
        for result in report["results"]
        if result["status"] in {"failed", "incomplete", "blocked"}
    )


def test_adapter_output_limit_stops_and_records_failure(tmp_path, monkeypatch):
    import evaluation.vibevoice.runner as runner
    from evaluation.vibevoice.runner import run_evaluation

    manifest = _manifest(languages=("en",), candidate_available=True)
    manifest["configurations"] = [
        config
        for config in manifest["configurations"]
        if config["method"] == "existing_macos" or config["model_variant"] == "VibeVoice-TTS-1.5B"
    ]
    monkeypatch.setattr(runner, "MAX_AUDIO_BYTES", 4)

    class OversizedProcess:
        returncode = 0

        def __init__(self):
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO(b"12345")

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    report = run_evaluation(
        manifest,
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={"VibeVoice-TTS-1.5B": [sys.executable]},
        baseline_client=lambda *_: b"ab",
        process_factory=lambda *_args, **_kwargs: OversizedProcess(),
    )

    failed = next(
        result
        for result in report["results"]
        if result["configuration_id"] == "tts-en" and result["status"] == "failed"
    )
    assert "size limit" in failed["reason"]
    assert "audio_path" not in failed


def test_unverified_preflight_capacity_blocks_all_generation(tmp_path):
    from evaluation.vibevoice.runner import run_evaluation

    calls = []
    report = run_evaluation(
        _manifest(languages=("en",)),
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={},
        baseline_client=lambda *_: calls.append("baseline") or b"RIFF-baseline",
        preflight={
            "inspections": [],
            "measurements": [],
            "blockers": [
                {
                    "scope": "test-machine",
                    "category": "capacity",
                    "reason": "Available storage could not be verified.",
                }
            ],
        },
    )

    assert report["state"] == "blocked"
    assert calls == []
    assert report["results"]
    assert all(result["status"] == "blocked" for result in report["results"])


def test_adapter_cancellation_terminates_process_and_records_stopped_run(tmp_path, monkeypatch):
    from evaluation.vibevoice.runner import run_evaluation

    manifest = _manifest(languages=("en",), candidate_available=True)
    manifest["configurations"] = [
        config
        for config in manifest["configurations"]
        if config["method"] == "existing_macos" or config["model_variant"] == "VibeVoice-TTS-1.5B"
    ]

    class InterruptedProcess:
        pid = 123456
        returncode = None

        def __init__(self):
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()
            self.wait_calls = 0

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise KeyboardInterrupt
            self.returncode = -15
            return self.returncode

    processes = []

    def process_factory(*_args, **_kwargs):
        process = InterruptedProcess()
        processes.append(process)
        return process

    monkeypatch.setattr("evaluation.vibevoice.runner.os.killpg", lambda *_args: None)
    report = run_evaluation(
        manifest,
        tmp_path / "private-results",
        approve_run=True,
        baseline_url=BASELINE_URL,
        baseline_token="secret-test-token",
        approved_adapters={"VibeVoice-TTS-1.5B": [sys.executable]},
        baseline_client=lambda *_: b"RIFF-baseline",
        process_factory=process_factory,
    )

    assert report["state"] == "cancelled"
    assert processes[0].returncode == -15
    assert any(result["status"] == "cancelled" for result in report["results"])
