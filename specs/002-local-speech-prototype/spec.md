# Feature Specification: Local High-Quality Speech Prototype

**Feature Branch**: Not assigned

**Created**: 2026-11-08

**Status**: Draft

**Input**: Evaluate a local high-quality speech alternative, including voice
cloning and memory-pressure fallback, without publishing prototype backend code.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate local speech and cloning (Priority: P1)

An evaluator generates German and English speech locally, including speech in
the voice of a consenting reference speaker, and compares the results with the
existing native speech engine.

**Why this priority**: The prototype must establish whether a candidate offers
enough value to justify further work.

**Independent Test**: With an authorized local test environment and reference
recording, generate and listen to both languages using the candidate and the
native baseline, and record the results without publishing private samples.

**Acceptance Scenarios**:

1. **Given** a usable candidate and sufficient resources, **When** an evaluator
   requests German or English speech, **Then** the prototype returns playable
   speech and identifies the engine that produced it.
2. **Given** a valid, authorized reference recording, **When** the evaluator
   requests a cloned voice, **Then** the candidate generates speech conditioned
   on that reference in each supported language.
3. **Given** an explicit supported language or automatic language selection,
   **When** text is submitted, **Then** existing language-selection behavior is
   preserved and the selected language is used.

### User Story 2 - Protect the machine under pressure (Priority: P1)

An evaluator can continue to obtain speech from the native engine when system
memory pressure or insufficient safe headroom prevents model synthesis.

**Why this priority**: Protecting the shared machine takes precedence over
using the higher-quality candidate.

**Independent Test**: Exercise controlled resource states and verify engine
selection, fallback reporting, and resource release without disrupting unrelated
workloads.

**Acceptance Scenarios**:

1. **Given** high memory pressure or insufficient safe headroom before
   generation, **When** speech is requested, **Then** the native engine is
   selected and the evaluator is told that the cloned voice is not preserved.
2. **Given** pressure rises during candidate generation, **When** continuing
   would exceed the prototype's safety policy, **Then** generation is stopped
   safely, resources are released, and the request either completes using the
   native engine or returns an explicit failure without partial audio.
3. **Given** resources have recovered, **When** the recovery conditions are
   satisfied and another request arrives, **Then** candidate use may resume.

### User Story 3 - Make an evidence-based decision (Priority: P2)

An evaluator records comparable quality, performance, resource and licensing
evidence before deciding whether any model should be integrated or released.

**Why this priority**: A working demo alone does not establish suitability.

**Independent Test**: Run the agreed evaluation set, inspect the resulting
private report, and verify that it distinguishes measured results, open
questions and release decisions.

**Acceptance Scenarios**:

1. **Given** a defined evaluation set and decision criteria, **When** a
   candidate and native baseline are evaluated, **Then** the report records
   per-language results, voice similarity, pronunciation, completeness,
   latency, memory, disk use, failures and pressure behavior.
2. **Given** licensing or ownership questions remain unresolved, **When** the
   evaluation is reviewed, **Then** it identifies those questions as release
   blockers rather than claiming legal approval.

### Edge Cases

- Short, ambiguous, mixed-language or unsupported text follows the existing
  language rules or produces an explicit error; it is not silently relabeled.
- Missing, corrupt, silent, oversized or unauthorized reference audio is
  rejected without retaining partial sensitive data.
- Missing model files, a failed load, cancellation, timeout, a full disk or an
  unavailable native engine produces a bounded, visible outcome.
- Long text near the existing input limit must not silently lose content;
  unsupported cases fail explicitly and are recorded for evaluation.
- A request for a cloned voice cannot imply that native fallback sounds like
  that voice.
- A model failure is distinguishable from an intentional memory-pressure
  fallback; neither may conceal a failed or incomplete result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The prototype MUST run only in an explicitly authorized local
  evaluation environment; it MUST NOT change or deploy an existing service
  without separate operator approval.
- **FR-002**: The prototype MUST evaluate VoxCPM2 first and support a
  documented, separately approved comparison with Qwen3-TTS when feasible;
  comparison availability MUST NOT be represented as a result.
- **FR-003**: The prototype MUST support German and English using the existing
  explicit and automatic language-selection rules, including the short-input
  default and unsupported-language errors.
- **FR-004**: The prototype MUST accept a consenting speaker's reference
  recording for cloning and MUST reject missing or invalid references.
- **FR-005**: The prototype MUST select the native speech engine when memory
  pressure is high or safe generation headroom is insufficient, and MUST report
  the actual engine and reason for fallback.
- **FR-006**: The prototype MUST define and record a testable admission,
  in-flight pressure, recovery and model-unloading policy before evaluation;
  it MUST NOT treat a cache limit as a bound on total memory.
- **FR-007**: A fallback MUST identify that the native voice is not the
  requested clone. If native synthesis fails, the request MUST fail explicitly.
- **FR-008**: The prototype MUST preserve existing request bounds,
  authentication, language overrides, output formats, cancellation, timeouts,
  and safe logging or document a specific unsupported behavior and fail
  explicitly rather than silently changing the existing contract.
- **FR-009**: Reference recordings, derived voice data, text and generated
  audio MUST be protected from unauthorized access and omitted from logs;
  temporary copies MUST be removed on success, failure and cancellation.
  Any persistence MUST be explicit, private and deletable by the evaluator.
- **FR-010**: Prototype implementation, model weights, reference recordings,
  generated audio, private evaluation results and their copies MUST remain
  outside publishable repository contents and release artifacts until an
  explicit later decision authorizes publication. Publishable specifications
  MUST contain only synthetic examples and no private operational details.
- **FR-011**: Before implementation, the plan MUST define and verify a local
  isolation and release-review boundary that prevents accidental inclusion in
  commits, build contexts, images, uploads and published history.
- **FR-012**: The evaluator MUST define reproducible test inputs and decision
  criteria before measurement, then record candidate and baseline versions,
  language, input length, voice/reference conditions, quality assessments,
  latency, peak memory, disk footprint and fallback outcomes.
- **FR-013**: The evaluation MUST include both languages, cloned and
  non-cloned use, short and long inputs, supported output formats, cancellation,
  constrained resources, unavailable dependencies and recovery.
- **FR-014**: No model selection, production deployment, redistribution or
  release is approved by completion of this prototype; unresolved model,
  dependency, reference-audio, rights and legal reviews remain explicit gates.
- **FR-015**: The prototype MUST offer a capability/status contract for the
  separate interface feature, including actual engine and fallback reason,
  without requiring the public interface to expose prototype-only internals.

### Key Entities

- **Candidate**: A versioned speech model and runtime being evaluated.
- **Reference voice**: Authorized reference audio and any private derived voice
  data used to condition synthesis.
- **Synthesis outcome**: Complete audio or a failure, selected language, actual
  engine and, when applicable, fallback reason.
- **Evaluation record**: Private, reproducible measurements and decision
  findings for a candidate and the native baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The evaluation produces playable candidate and native baseline
  samples in both German and English, including at least one authorized
  cloned-voice sample per language.
- **SC-002**: Every tested high-pressure admission case selects the native
  engine or explicitly fails if it is unavailable; no case is reported as a
  successful clone when the native voice was used.
- **SC-003**: Every tested cancellation, pressure-interruption and failure case
  releases capacity and exposes no partial audio as a successful result.
- **SC-004**: The decision record covers all categories in FR-012 and FR-013,
  identifying unmeasured items and legal uncertainties as open rather than
  passed.
- **SC-005**: A publication-boundary review finds zero prototype code, model
  weights, private recordings, generated audio or private evaluation results in
  the proposed publishable changes and artifacts.

## Assumptions

- The target is an Apple Silicon Mac with 32 GiB unified memory; available
  headroom changes with other workloads.
- The candidate's quality, speed, memory use and license clearance are not yet
  established on the target machine.
- Evaluation inputs and listening criteria will be agreed before benchmarking;
  no unmeasured quality or performance threshold is asserted here.
- The separate UI feature can be published independently and must remain usable
  without the local prototype.
