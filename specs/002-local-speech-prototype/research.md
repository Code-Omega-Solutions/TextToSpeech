# Research: Local Speech Prototype

Research date: 2026-11-08. This is planning evidence only; no model, weights or
prototype was installed or run. Upstream claims are not native qualification or
legal clearance. Revalidate upstream revisions and model cards before any
separately approved acquisition.

## Candidate order and compatibility

**Decision**: Investigate VoxCPM2 first; compare Qwen3-TTS only after separate
approval and a feasibility check. Keep each candidate in its own private
environment and record exact versions and weight checksums.

**Rationale**: The [VoxCPM README at the inspected revision](https://github.com/OpenBMB/VoxCPM/blob/4b8dd4440d33396b3f429201f8af0529b4d2c601/README.md)
describes reference-audio cloning and says its demo can use MPS on Apple
Silicon. The same document lists CUDA in installation requirements, so the
complete Apple Silicon runtime is **not established**. It also documents
reference-only and audio-plus-transcript modes. The
[Qwen3-TTS README at the inspected revision](https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/README.md)
lists German and English and identifies its Base variants for cloning;
its examples use CUDA. No official Apple Silicon qualification was found in
that README. Qwen accepts reference audio and, normally, a transcript; its
speaker-embedding-only mode can omit the transcript with a quality tradeoff.
Accept only local reference files in this prototype, even where an upstream
API permits URLs. Both upstream projects may auto-download weights: private
local paths and blocked inference egress are mandatory.

**Alternatives considered**: Qwen first would ignore FR-002. Selecting an
unofficial Metal port solely on its reported benchmark would replace one
unverified runtime with another; consider it only as a separately reviewed
candidate with its own code, dependency and weight provenance.

## Licenses, model and dependency provenance

**Decision**: Review exact candidate code, weight and transitive dependency
licenses, ownership, attribution, model terms and reference consent before
local acquisition; keep release and redistribution as separate blockers.

**Rationale**: The GitHub repositories identify their code licenses as
Apache-2.0 ([VoxCPM license](https://github.com/OpenBMB/VoxCPM/blob/4b8dd4440d33396b3f429201f8af0529b4d2c601/LICENSE),
[Qwen3-TTS license](https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/LICENSE)).
VoxCPM's README also states Apache-2.0 for its weights. Repository license
metadata alone does not establish the terms of every chosen weight revision,
dependency, training input or recording. Model cards and transitive rights
remain unreviewed and explicitly block release. No rights determination is made.

**Alternatives considered**: Treating upstream marketing or an SPDX label as
blanket clearance would omit weight, dependency, speaker and project rights.

## Runtime and service compatibility

**Decision**: Keep the live service unchanged; use a private separate instance
and process-isolated candidate adapters, retaining the existing backend's
validated request semantics and native engine. Unsupported behavior fails
explicitly. Run each candidate in its own pinned environment.

**Rationale**: `backend/app/models.py`, `language.py`, `routers.py`, `main.py`
and `services.py` establish the current behavior: explicit locales and short
input default; 5,000 UTF-16 units, 32 KiB request body and 100 segments;
authentication, rate, MP3/WAV, deadlines, cancellation, bounded concurrency,
output and temporary storage. The existing model field is fixed to `macos-say`;
private headers rather than silently changing that schema select the prototype
engine. Compatibility of candidate language variants, exact speed and complete
long-input output remains to be demonstrated; reject unsupported cases.
VoxCPM's README specifies Python >=3.10 and <3.13, while the existing backend
requires >=3.11. Independent environments avoid forcing incompatible package
versions into the current service.

**Alternatives considered**: Replacing the running engine risks service and
contract regressions. In-process inference cannot reliably stop an
uncooperative runtime or prove that native fallback has regained resources.

## Memory and failure policy

**Decision**: Admit one candidate worker only with fresh, reliable macOS
pressure/headroom evidence and measured reservations; terminate it on unsafe
conditions and unload after each request. Require hysteresis before recovery.
Specify an explicit safe calibration protocol before normal evaluation.

**Rationale**: The machine uses shared unified memory, and a model cache
ceiling is not a bound on total process, system or accelerator allocation.
The [private contract](contracts/local-prototype.md) defines sample timing,
reservation margin, recovery and failure handling, but does not assert an
unmeasured host-specific capacity. Native pressure-signal reliability, worker
termination latency and actual reserve are pre-evaluation gates.

**Alternatives considered**: Cache-only limits, polling process RSS alone, or
attempting fallback before confirming worker exit could jeopardize other
workloads or produce a misleading success.

## Containment and evaluation

**Decision**: Keep all implementation and sensitive artifacts outside every
repository and publishing/build/upload/sync boundary; verify actual controls
with synthetic canaries before implementation and inspect all proposed history
and release artifacts. Pre-register evaluation inputs and decision thresholds.

**Rationale**: Git ignore rules do not prevent force-add, copies, linked paths,
build context inclusion or published earlier commits. Physical separation plus
channel-specific allowlisting, egress restrictions and independent inventory
are necessary. Private per-cell records and explicit unknowns avoid turning
model availability or mocked test results into claims of quality or readiness.

**Alternatives considered**: A private branch or ignored directory inside a
worktree is not a publication boundary; an unregistered benchmark or isolated
success sample does not support a reliable model choice.
