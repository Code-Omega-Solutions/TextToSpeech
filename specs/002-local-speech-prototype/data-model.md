# Data Model: Local Speech Prototype

All structures below are proposed private implementation contracts, not
persisted schema or proof of behavior. Fields containing text, recordings,
derived voices, audio, operator paths or private measurements are never logged.

## Candidate

`id` (`voxcpm2` or `qwen3-tts`), immutable source revision, weight identifier
and checksum, runtime/dependency versions, license and provenance review state,
capability matrix and private artifact location. Candidate state is
`unreviewed -> approved-for-local-evaluation -> available -> loaded -> unloaded`;
failure can leave it `unavailable`. Approval for local evaluation is not release
or redistribution approval.

## Reference voice

An opaque random reference ID maps only within the private workspace to
recording, optional derived conditioning data, consent evidence, permitted
languages/use and deletion state. A reference is usable only after verified
authorization and validation of format, duration, size, decodability and
non-silence. Exact limits are fixed in the private experiment protocol before
intake; missing or failed validation is a rejection, with partial copies removed.
Revocation deletes all owned copies and derived data and invalidates the ID.
No reference path or consent identity is exposed in the public contract.

## Synthesis request and outcome

The existing request schema and language resolution remain authoritative.
Private opt-in controls carry an engine preference and optional opaque reference
ID separately, not by weakening the existing `SpeechRequest`. An outcome has
`request_id`, resolved locale, requested engine/voice condition, actual engine,
voice condition, optional fallback reason, state, and either complete bounded
audio plus format or an explicit error. No error or cancellation may contain
partial audio. A native fallback always reports `native`, `not-cloned`, and the
specific fallback reason.

## Resource policy and worker

The policy records a version, pressure signal source, sampling and stale-data
limits, candidate memory reservation, reserve for other workloads, timeout,
recovery hysteresis, and worker stop deadline. States are `NORMAL`, `PRESSURE`,
and `RECOVERING`; see the contract for transitions. One worker belongs to one
admitted request, owns its temporary resources, and holds the permit until
termination and cleanup are confirmed. Uncertain telemetry is not normal.

## Evaluation protocol and record

The protocol is frozen before measurement: candidate/baseline pins, input IDs
and lengths, languages, authorized voice conditions, repetitions/order,
pronunciation/completeness/similarity rating method, acceptable thresholds,
device state, resource policy, and stop conditions. Record each planned cell as
`not-run`, `passed`, `failed`, `blocked`, or `not-applicable` with a reason,
never inferring success from a missing result. Private observations include
latency, sampled peak system/process memory with method, disk footprint,
output completeness and quality, actual engine/fallback, cancellation and
recovery, failures, versions and rights review. A decision record separates
measured facts, unknowns, local-evaluation approval and release blockers.

## Lifecycle and deletion

Private files use an owner-only workspace and per-request subdirectories. On
success, failure, timeout, cancellation, pressure interruption or restart,
remove request temporaries only after workers stop. Persistence of samples or
reports is opt-in, private and independently deletable. Confirm deletion of
reference recordings and derived data on revocation; report cleanup failures
and block further unsafe work rather than reporting success.
