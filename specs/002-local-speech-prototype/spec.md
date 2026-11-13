# Feature Specification: Local High-Quality Speech Prototype

**Feature Branch**: Not assigned

**Created**: 2026-11-08

**Updated**: 2026-11-13

**Status**: Draft

**Input**: Exclude VoxCPM2 and Qwen3-TTS as too resource consuming. Request
memory release from local Ollama, then check system memory pressure and available
unified-memory headroom. Use native macOS `say` under pressure; evaluate NeuTTS
Air only when safe resources are available, without publishing prototype code.

**Planning boundary**: This revision supersedes the existing candidate-selection
and admission guidance in the plan, research, data model, quickstart and local
prototype contract. Those artifacts MUST be revised against this specification
before implementation; their previous planned status does not establish readiness.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate local speech and cloning (Priority: P1)

An evaluator assesses NeuTTS Air for German and English speech locally,
including speech in the voice of a consenting reference speaker, and compares
supported results with the existing native speech engine. Missing capabilities
are recorded as suitability blockers, not assumed to work.

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
4. **Given** NeuTTS Air cannot support a required language or cloning case,
   **When** suitability is evaluated, **Then** that gap is recorded explicitly,
   native speech remains available, and full candidate suitability is not claimed.

### User Story 2 - Protect the machine under pressure (Priority: P1)

An evaluator requests cooperative memory release from local Ollama before the
prototype checks system memory pressure and safe unified-memory headroom. The
native macOS `say` command remains available when model synthesis is unsafe.

**Why this priority**: Protecting the shared machine takes precedence over
using the higher-quality candidate.

**Independent Test**: Exercise controlled resource states and verify engine
selection, fallback reporting, and resource release without disrupting unrelated
workloads.

**Acceptance Scenarios**:

1. **Given** local Ollama is reachable with models eligible for release,
  **When** speech is requested, **Then** the prototype requests cooperative
  memory release within a bounded deadline, records the outcome, and obtains
  fresh pressure and headroom measurements after the attempt before selecting
  a speech engine; unrelated active jobs are not interrupted.
2. **Given** high memory pressure, insufficient safe unified-memory headroom or
  an unknown memory state after the release attempt, **When** speech is
  requested, **Then** native macOS `say` is selected without loading NeuTTS Air
  and the evaluator is told that the cloned voice is not preserved.
3. **Given** Ollama is absent, unreachable, refuses release or times out,
  **When** the bounded release attempt ends, **Then** the prototype still
  measures memory and chooses an engine from that evidence; neither release
  failure nor claimed success alone determines candidate admission.
4. **Given** pressure is normal and measured available unified memory meets
  the recorded safety policy, **When** a usable NeuTTS Air candidate is
  requested, **Then** candidate synthesis may proceed and its actual engine
  is reported; total installed memory alone is not sufficient evidence.
5. **Given** pressure rises during candidate generation, **When** continuing
   would exceed the prototype's safety policy, **Then** generation is stopped
   safely, resources are released, and the request either completes using the
   native engine or returns an explicit failure without partial audio.
6. **Given** resources have recovered, **When** the recovery conditions are
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
3. **Given** NeuTTS Air cannot safely run or meet the required capabilities on
  the target machine, **When** the evaluation concludes, **Then** the report
  records a no-go decision and its evidence without substituting an excluded
  model or claiming unmeasured candidate results.

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
- Ollama may have no loaded models, only busy models, or no permitted release
  operation. The prototype must not kill Ollama, stop active jobs, or infer
  reclaimed memory solely from a successful release response.
- Pressure may remain high after Ollama releases memory or rise between the
  post-release measurement and model loading; revalidation must prevent unsafe
  admission. Missing or stale telemetry is not evidence of safe capacity.
- NeuTTS Air or its speech/phonemization dependencies may not support the
  target hardware or required language. Missing support is a recorded blocker,
  not permission to silently change the requested language or claim a clone.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The prototype MUST run only in an explicitly authorized local
  evaluation environment; it MUST NOT change or deploy an existing service
  without separate operator approval.
- **FR-002**: NeuTTS Air MUST be the sole model candidate in this prototype,
  evaluated against native macOS `say` only when safe unified-memory headroom
  is available. VoxCPM2 and Qwen3-TTS MUST NOT be installed, loaded or evaluated
  for this prototype because their resource demands are unacceptable here.
  Candidate availability, compatibility and quality MUST NOT be assumed.
- **FR-003**: The prototype MUST support German and English using the existing
  explicit and automatic language-selection rules, including the short-input
  default and unsupported-language errors.
- **FR-004**: The prototype MUST accept a consenting speaker's reference
  recording for cloning and MUST reject missing or invalid references.
- **FR-005**: After the bounded Ollama release attempt, the prototype MUST
  obtain fresh system memory-pressure and available unified-memory measurements.
  It MUST select native macOS `say` without loading the candidate when pressure
  is high, headroom is insufficient or the memory state cannot be established,
  and MUST report the actual engine and reason for fallback. A normal pressure
  reading alone MUST NOT authorize model loading without sufficient headroom.
- **FR-006**: The prototype MUST define and record a testable admission,
  in-flight pressure, recovery and model-unloading policy before evaluation;
  it MUST include measurement freshness, pressure thresholds, candidate memory
  reservation, reserve for other workloads and native fallback, revalidation
  before loading, recovery hysteresis and cleanup confirmation. It MUST NOT
  treat installed memory or a cache limit as a bound on total memory use.
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
- **FR-016**: Before each synthesis admission decision, the prototype MUST
  ask local Ollama to release eligible idle model memory using only
  operator-authorized cooperative actions. The attempt MUST have a recorded
  finite deadline and distinguish released, nothing eligible, unavailable,
  refused and timed-out outcomes. It MUST NOT interrupt unrelated active jobs,
  terminate Ollama, or wait indefinitely. If Ollama is unavailable, selection
  MUST continue using fresh memory evidence and conservative native fallback.
- **FR-017**: Before a NeuTTS Air generation trial, the evaluator MUST verify
  the exact model and runtime identity, target-machine compatibility, German
  and English capabilities, reference-audio and transcript requirements,
  speech/phonemization dependencies including espeak-ng where required, and
  code, weight and dependency licensing. Capacity qualification MUST measure
  loading and generation peaks and establish a conservative reservation before
  routine candidate admission. Unsupported or unsafe trials MUST be recorded
  as blockers; the prototype MUST remain usable through native speech.

### Key Entities

- **Candidate**: A versioned speech model and runtime being evaluated.
- **Admission record**: Ollama release outcome, fresh pressure and available
  unified-memory evidence, safety-policy decision and selected engine, without
  exposing unrelated workload details or sensitive synthesis inputs.
- **Reference voice**: Authorized reference audio and any private derived voice
  data used to condition synthesis.
- **Synthesis outcome**: Complete audio or a failure, selected language, actual
  engine and, when applicable, fallback reason.
- **Evaluation record**: Private, reproducible measurements and decision
  findings for a candidate and the native baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The evaluation records native baseline samples in both German
  and English and an explicit candidate suitability decision. A positive
  decision requires playable candidate samples in both languages, including at
  least one authorized cloned-voice sample per language; missing or unsafe
  capabilities yield an evidenced no-go decision, not a claimed pass.
- **SC-002**: Every tested high-pressure admission case selects the native
  engine or explicitly fails if it is unavailable; no case is reported as a
  successful clone when the native voice was used. Every tested insufficient
  headroom or unknown-memory case follows the same rule without model loading.
- **SC-003**: Every tested cancellation, pressure-interruption and failure case
  releases capacity and exposes no partial audio as a successful result.
- **SC-004**: The decision record covers all categories in FR-012 and FR-013,
  identifying unmeasured items and legal uncertainties as open rather than
  passed.
- **SC-005**: A publication-boundary review finds zero prototype code, model
  weights, private recordings, generated audio or private evaluation results in
  the proposed publishable changes and artifacts.
- **SC-006**: Every tested admission path records the bounded Ollama release
  attempt before fresh memory assessment, including release success, no idle
  models, busy models, absence, refusal and timeout. No tested path interrupts
  unrelated active work or admits the candidate solely on a release response.
- **SC-007**: Every admitted candidate test has normal pressure and sufficient
  measured unified-memory headroom under the pre-registered safety policy;
  unsafe or stale measurements block candidate loading, and recovery tests
  demonstrate the recorded hysteresis before candidate use resumes.

## Assumptions

- The intended target is the evaluator-described Mac Mini M6 with 32 GB of
  unified memory. Exact hardware, operating system and usable capacity MUST be
  confirmed on the evaluation host; no support or performance is established
  by that description, and available headroom changes with other workloads.
- Local Ollama may hold releasable idle model memory, but its presence,
  cooperation and actual reclaimed capacity are not guaranteed. Authorized
  release mechanisms and the finite deadline will be settled during planning.
- The candidate's quality, speed, memory use and license clearance are not yet
  established on the target machine.
- The supplied comparison motivates evaluating NeuTTS Air; its article URL and
  verifiable citation were not provided. Claims about its model architecture,
  size, few-second cloning and superiority over Piper, VibeVoice or Chatterbox
  remain unverified context, not measured results or reasons to add candidates.
- Evaluation inputs and listening criteria will be agreed before benchmarking;
  no unmeasured quality or performance threshold is asserted here.
- The separate UI feature can be published independently and must remain usable
  without the local prototype.
