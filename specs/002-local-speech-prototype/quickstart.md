# Validation Guide: Local Speech Prototype

This guide separates the current private interactive trial from the remaining
qualification work. Concrete private paths, commands, recordings and results
remain in the operator-controlled workspace and must not be copied here.
Nothing in this guide authorizes publication or a production rollout.

## Current trial and rollback

The operator authorized a reversible test switch and admission-only pressure
checks. The private Qwen adapter was activated for interactive evaluation; the
original backend is active again at the latest observation, and both launch
configurations are retained. The private operator
runbook describes restoring the original service; verify its readiness after
restoration. Do not remove the original backend or credentials.

The trial accepts German or US English, WAV or MP3, fixed synthetic reference
voices, speed 1.0, and at most 512 UTF-16 units. Other voice, speed and locale
requests fail explicitly. Native fallback can occur when initial pressure or
headroom is unsuitable and must be identified as non-cloned. The trial checks
no pressure during generation; its free-page threshold is provisional, not
calibrated. Candidate audio is marked as unverified for completeness. Do not
use a structurally valid WAV or MP3 as proof of speech quality or completeness.

## Prerequisites and authorization

- For further qualification, verify the [isolation and release boundary](contracts/isolation-and-release.md)
  and document containment, retention, canary checks and cleanup privately.
  The operator waived network/filesystem isolation for the current trial only.
- Confirm operator authorization, rights to the reference, required native
  tools and candidate dependencies before further runs. A separate loopback
  instance remains the original qualification design; the current live test
  switch is a separately authorized deviation.
- Pre-register the [evaluation protocol](data-model.md#evaluation-protocol-and-record)
  and resource policy. Approve inputs, voice conditions, repetitions, subjective
  rating, comparison thresholds and safety stop rules before collecting data.
  Candidate package/weight provenance, model rights and runtime compatibility
  must be reviewed first. Qwen3-TTS local testing has been approved; release
  and redistribution have not.

## Existing baseline checks

In an already provisioned backend environment, from the repository root:

```sh
cd backend
uv run --offline --no-sync pytest
python3 prerequisites.py --json
```

The tests should pass in a compatible pre-existing environment; missing
dependencies are a blocker, not permission to install them. The prerequisite
checker is read-only and can fail on a non-macOS host. Neither mocked tests nor
the checker demonstrate native synthesis, cloning or model qualification.

## Private implementation verification

Run the private test runner with
fake workers, clocks, memory observations and synthetic inputs. Save the exact
commands, versions and results in the private report. Verify:

1. Explicit `de`, `de-DE`, `en`, `en-US`, `en-GB`, automatic German/English,
   short-input default, unsupported detection and malformed input match the
   existing contract. Check 5,000 UTF-16 units, 32 KiB request body, 100
   segments, speed endpoints, both output formats and the configured limits.
   Unsupported controls must return an explicit error.
2. Authorization, bad or missing references, corrupt/silent/oversized audio,
   revoked consent and invalid header combinations fail safely. No input,
   audio, credentials, voice data or private paths appear in errors or logs.
3. Use deterministic pressure samples to test admission, an in-flight
   interruption, missing and stale telemetry, insufficient headroom, recovery
   hysteresis, candidate process kill/exit confirmation, native failure, and
   candidate errors distinct from fallback. Check actual-engine and clone
   status headers exactly as in the [contract](contracts/local-prototype.md).
4. Test client cancellation, timeout, model-load failure, unavailable native
   engine, full disk, conversion failure, concurrent requests, restart cleanup,
   permit release and no partial successful audio. Verify private persisted
   data is opt-in and reference deletion removes derived copies.
5. Execute the canary, publication inventory and history checks for all
   applicable channels in the [boundary contract](contracts/isolation-and-release.md).
   Zero canaries or private artifacts may be present in proposed commits,
   histories, build contexts, images, uploads or release artifacts.

## Authorized native evaluation

On the separately approved Mac, first verify the native baseline and prove
the pressure telemetry and stop mechanism with controlled synthetic workers.
Establish a safe pre-approved calibration procedure and record measured peak
and native reserve before admitting normal candidate runs. If memory telemetry
or process termination cannot be verified, stop: do not infer safety from a
cache limit.

Record the initial VoxCPM2 investigation and evaluate Qwen and the native
baseline using the frozen matrix: German and
English; cloned and non-cloned where supported; short and near-limit text;
MP3/WAV, cancellation, dependency failures, pressure and recovery. Confirm
candidate and baseline audio is playable and complete, with at least one
authorized cloned sample in each language. Record per-cell latency, peak memory
method, disk, quality, similarity, pronunciation, actual engine, failures and
fallback reason. Record blocked and unsupported cells honestly. Perform an
additional candidate comparison only if separately approved. Keep all inputs,
samples and detailed measurements private.

Afterward delete transient files and any explicitly selected persisted data;
verify no worker remains and document cleanup failures. Review the decision
record for missing evidence and unresolved rights before any separate release
or publication decision.
