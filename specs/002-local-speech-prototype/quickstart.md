# Validation Guide: Local Speech Prototype

This is a future validation guide, not an instruction to install, download,
run models, deploy or publish during planning. Commands involving the private
implementation do not exist yet; their concrete invocations must be added to
the private workspace during implementation, not to this publishable guide.

## Prerequisites and authorization

- Verify the [isolation and release boundary](contracts/isolation-and-release.md)
  before creating private prototype code. Document and approve the private
  paths, containment, retention, canary checks and cleanup results privately.
- Obtain separate explicit local-evaluation approval, a consenting reference,
  a target Apple Silicon Mac with 32 GiB unified memory, native `say`, ffmpeg,
  required voices and isolated candidate dependencies. Do not change the
  existing service or its ports; use a separate loopback-only process.
- Pre-register the [evaluation protocol](data-model.md#evaluation-protocol-and-record)
  and resource policy. Approve inputs, voice conditions, repetitions, subjective
  rating, comparison thresholds and safety stop rules before collecting data.
  Candidate package/weight provenance, model rights and runtime compatibility
  must be reviewed first. Qwen3-TTS requires separate approval.

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

Run the private test runner once implemented, without network access, with
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

Evaluate VoxCPM2 first and native baseline using the frozen matrix: German and
English; cloned and non-cloned where supported; short and near-limit text;
MP3/WAV, cancellation, dependency failures, pressure and recovery. Confirm
candidate and baseline audio is playable and complete, with at least one
authorized cloned sample in each language. Record per-cell latency, peak memory
method, disk, quality, similarity, pronunciation, actual engine, failures and
fallback reason. Record blocked and unsupported cells honestly. Perform a
Qwen3-TTS comparison only if separately approved and feasible. Keep all inputs,
samples and detailed measurements private.

Afterward delete transient files and any explicitly selected persisted data;
verify no worker remains and document cleanup failures. Review the decision
record for missing evidence and unresolved rights before any separate release
or publication decision.
