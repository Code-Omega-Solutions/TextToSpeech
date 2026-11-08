# Implementation Plan: Local High-Quality Speech Prototype

**Branch**: `agents/local-speech-prototype-plan` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-local-speech-prototype/spec.md`

## Summary

Evaluate Qwen3-TTS privately against the existing macOS `say` service after
the initial VoxCPM2 investigation did not complete its guarded loads. The
operator authorized a reversible interactive test switch that preserves the
original service, plus admission-only pressure checks and per-request worker
exit. The original service is active again at the latest observation. The trial
does not satisfy the proposed in-flight monitoring and measured
reserve contract; this exception is for evaluation, not qualification.
Publishable documentation stays separate from implementation, weights, audio,
text and private results. No publication of prototype code is authorized.

## Current trial status

- Private Qwen English and German inference returned structurally validated
  WAV and MP3 responses; an authenticated live request and an unauthenticated
  rejection were checked. These checks do not establish intelligibility,
  similarity or complete speech.
- The interactive adapter supports German and US English, fixed synthetic
  references, speed 1.0, WAV/MP3 and up to 512 UTF-16 units. Unsupported
  options are rejected. Native fallback on unsafe initial admission reports
  the engine and loss of clone conditioning.
- Initial admission uses a provisional free-page threshold, not a
  measured safe reservation. No pressure sampling occurs during generation;
  peak memory, behavior under concurrent load and in-flight fallback are
  unverified. Worker exit releases process-owned allocations but does not
  guarantee immediate free-page recovery.
- The interactive trial does not yet satisfy the full proposed capability contract,
  complete-speech guarantee, rights review, baseline comparison, resource
  policy or production qualification. Rollback is operator-controlled; the
  original backend and launch configuration are retained. Automatic restoration
  was implemented for activation failures, not proven for every failure mode.

## Technical Context

**Language/Version**: Existing backend Python >=3.11; private candidate
runtime version and exact package pins must be resolved per candidate before
an approved experiment, in a separate environment.

**Primary Dependencies**: Existing FastAPI, Pydantic, langid, macOS `say` and
ffmpeg; the private trial uses `qwen-tts==0.1.1` and pinned model weights.
Dependency and rights review remains a release gate.

**Storage**: An owner-only private workspace outside all repositories, build
contexts, synced folders and published artifacts; explicit temporary and
persistent subdirectories with quota and deletion policies.

**Testing**: Existing backend pytest suite plus private deterministic policy,
contract, isolation and failure tests; native qualification only on an
authorized Apple Silicon Mac.

**Target Platform**: Evaluation target is macOS on Apple Silicon with 32 GiB
unified memory. Native smoke tests succeeded, but platform qualification and
safe operation under varied workloads remain unestablished.

**Project Type**: Private backend prototype and evaluation harness, temporarily
selected on the existing authenticated service endpoint for operator testing.

**Performance Goals**: Record complete outputs, time to completion, peak
memory and disk use; do not assert unmeasured quality or speed targets.
Pre-register comparison and stopping criteria before measurement.

**Constraints**: Existing 5,000 UTF-16-unit, 32 KiB request, 100-segment,
format, authentication, rate, capacity, timeout and temporary/output limits
remain authoritative. Fail explicitly where equivalence cannot be proved.
Total memory is not bounded by a model cache setting.

**Scale/Scope**: Operator-controlled interactive trial and at most one
candidate worker per process; no production rollout or multi-user voice store.
Cross-process coordination remains unverified.

## Constitution Check

| Principle | Pre-research gate | Post-design gate |
|---|---|---|
| Evidence-based specifications | PASS: inspect existing code; distinguish proposed and measured behavior. | PASS: research identifies evidence, unknowns and release gates; no benchmark is claimed. |
| Safe bounded behavior | PASS: isolate and define failure, cleanup and admission policies. | PASS: contracts specify limits, process termination and fail-closed pressure handling. Native policy calibration remains an evaluation prerequisite. |
| User and operational boundaries | PASS: private materials and service remain untouched. | PASS: private storage, consent, no sensitive logs, egress/build/commit gates are designed. Enforcement must be verified before implementation. |
| Observable verification | PASS: require tests and native evaluation, not mocks as proof. | PASS: quickstart specifies evidence and failure cases; actual target execution remains pending approval. |
| Platform and release precision | PASS: Apple Silicon and all third-party rights require qualification. | PASS: unverified compatibility, licensing, redistribution and publication remain blocking gates. |

The table records the original design review, not a current qualification.
The admission-only interactive trial does not satisfy the designed in-flight
pressure, calibrated reserve or inference sandbox gates. It was separately
authorized by the operator and remains an explicit unqualified deviation; no
constitution or production-release exception is implied.

## Project Structure

### Publishable planning documentation

```text
specs/002-local-speech-prototype/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   ├── local-prototype.md
│   └── isolation-and-release.md
└── quickstart.md
```

`tasks.md` belongs to the later tasks workflow and is not generated here.

### Existing source and private prototype

Existing integration reference points are `backend/app/models.py`,
`backend/app/language.py`, `backend/app/routers.py`, `backend/app/services.py`,
`backend/app/main.py`, and `backend/tests/`. They remain unchanged during this
plan. The implementation and tests of the prototype must reside entirely in a
new owner-controlled private workspace outside every Git worktree. A private,
local snapshot of the existing backend may be used for compatibility testing
only; verify its provenance and keep it outside public build contexts. Do not
add prototype code to this repository, even on a nominally private branch.

## Implementation Sequence

The following is the original target sequence, retained as a qualification
backlog rather than a claim that every gate was met in the interactive trial:

1. Establish and test the isolation/release boundary in
   [isolation-and-release.md](contracts/isolation-and-release.md) **before**
   creating prototype files. Identify an owner, an approved local workspace and
   executable controls; if any control cannot be demonstrated, stop.
2. Freeze the existing service contract and establish a private test harness
   that imports or snapshots the existing behavior without changing the live
   service. Lock authentication and network access to the private instance.
3. Implement a private supervisor, native adapter and candidate process adapter
   with one global capacity permit, deadlines, cancellation, private cleanup
   and the pressure state machine in [local-prototype.md](contracts/local-prototype.md).
   Verify with fake telemetry and fake workers before running any model.
4. Record the completed initial VoxCPM2 investigation and approved Qwen trial;
   verify supported controls, provenance and rights, and fail explicitly where
   the existing contract cannot be honored.
5. Before measurement, approve the evaluation set, scoring and decision rules,
   measured memory reserve and a safe native baseline. Perform private native
   runs; record missing cells and failures, not inferred passes.
6. Review publication candidates and every artifact against the boundary;
   retain prototype code privately unless a later explicit publication decision
   and separate rights/security review permit otherwise.

## Complexity Tracking

No constitution violations. Process isolation and separate private storage are
necessary to stop an uncooperative model worker and prevent prototype material
from entering publishable repository history.
