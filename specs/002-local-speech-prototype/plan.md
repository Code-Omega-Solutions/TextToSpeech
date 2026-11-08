# Implementation Plan: Local High-Quality Speech Prototype

**Branch**: `agents/local-speech-prototype-plan` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-local-speech-prototype/spec.md`

## Summary

Design a private, local-only backend evaluation of VoxCPM2 first, optionally
Qwen3-TTS after separate approval, against the existing macOS `say` service.
Keep the running service unchanged. A private supervisor admits, monitors and
terminates isolated candidate workers; safe native fallback is explicit and
never claims to preserve a cloned voice. Publishable documentation is separate
from all implementation, weights, audio, text and evaluation artifacts.
Nothing in this plan authorizes model downloads, implementation, deployment,
redistribution, or publication of prototype code.

## Technical Context

**Language/Version**: Existing backend Python >=3.11; private candidate
runtime version and exact package pins must be resolved per candidate before
an approved experiment, in a separate environment.

**Primary Dependencies**: Existing FastAPI, Pydantic, langid, macOS `say` and
ffmpeg; candidate runtime and model dependencies are unapproved and isolated.

**Storage**: An owner-only private workspace outside all repositories, build
contexts, synced folders and published artifacts; explicit temporary and
persistent subdirectories with quota and deletion policies.

**Testing**: Existing backend pytest suite plus private deterministic policy,
contract, isolation and failure tests; native qualification only on an
authorized Apple Silicon Mac.

**Target Platform**: Evaluation target is macOS on Apple Silicon with 32 GiB
unified memory. Planning was performed on Linux and establishes no native
compatibility.

**Project Type**: Local backend prototype with a private evaluation harness;
no public service or UI change.

**Performance Goals**: Record complete outputs, time to completion, peak
memory and disk use; do not assert unmeasured quality or speed targets.
Pre-register comparison and stopping criteria before measurement.

**Constraints**: Existing 5,000 UTF-16-unit, 32 KiB request, 100-segment,
format, authentication, rate, capacity, timeout and temporary/output limits
remain authoritative. Fail explicitly where equivalence cannot be proved.
Total memory is not bounded by a model cache setting.

**Scale/Scope**: Single authorized evaluator and at most one candidate worker;
no production rollout, public frontend integration or multi-user voice store.

## Constitution Check

| Principle | Pre-research gate | Post-design gate |
|---|---|---|
| Evidence-based specifications | PASS: inspect existing code; distinguish proposed and measured behavior. | PASS: research identifies evidence, unknowns and release gates; no benchmark is claimed. |
| Safe bounded behavior | PASS: isolate and define failure, cleanup and admission policies. | PASS: contracts specify limits, process termination and fail-closed pressure handling. Native policy calibration remains an evaluation prerequisite. |
| User and operational boundaries | PASS: private materials and service remain untouched. | PASS: private storage, consent, no sensitive logs, egress/build/commit gates are designed. Enforcement must be verified before implementation. |
| Observable verification | PASS: require tests and native evaluation, not mocks as proof. | PASS: quickstart specifies evidence and failure cases; actual target execution remains pending approval. |
| Platform and release precision | PASS: Apple Silicon and all third-party rights require qualification. | PASS: unverified compatibility, licensing, redistribution and publication remain blocking gates. |

No constitution exception is requested. These are design checks, not evidence
that a prototype or isolation enforcement already exists.

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
4. With a separate operator approval, pin and inspect VoxCPM2 sources, weights,
   rights and runtime; run only locally in the isolated environment. Verify
   supported controls and fail explicitly where the existing contract cannot
   be honored. Obtain separate approval before Qwen3-TTS comparison.
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
