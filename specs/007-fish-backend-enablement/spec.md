# Feature Specification: Gated Fish Backend Enablement

**Created**: 2026-11-17
**Status**: Draft; local resource/fallback policy implemented, runtime/reference approval and native qualification pending
**Input**: Enable Fish in the isolated speech prototype for noncommercial home
automation and Open WebUI, with one male and one female voice in each of German
and English. Use four language-specific Common Voice reference speakers; keep
model artifacts and source recordings private. The operator also intends to
share generated speech noncommercially, subject to the applicable model,
dataset, and speaker-use terms.

## Clarifications

### Session 2026-11-17

- The operator approved read-only inspection of the existing backend and
  frontend hosts, not package installation or deployment.
- The initial scope preferred two consented bilingual speakers. This preference
  was superseded by the later operator clarification accepting four
  language-specific speakers; no bilingual identity is required.
- Intended use is private, noncommercial home automation and Open WebUI.
  Propose resource limits after inspection; no spending is authorized.
- Preserve the existing production service and the working macOS prototype.
  Earlier documentary approval gates are not waived by this request.
- Subsequent operator clarification fixes the inference target to the existing
  Apple Silicon Mac with 32 GiB unified memory; another machine is not the
  proposed deployment target. Candidate discovery does not itself approve
  downloads or establish voice quality or local usability.
- The operator subsequently authorized proceeding with headroom-first,
  low-priority neural TTS. Use a 12 GiB higher-priority memory reserve and a
  16 GiB neural-worker budget first; screen smaller Fish variants before
  considering an 8 GiB reserve and roughly 24 GB candidate.
- The operator subsequently authorized more aggressive cold-start admission
  relying on continued monitoring and yielding. Use an opt-in 4 GiB startup
  allowance plus the unchanged 12 GiB reserve for private evaluation; retain
  the 16 GiB running-worker ceiling. This is provisional, not a measured peak
  or a guarantee against transient memory pressure.
- The operator accepts four language-specific reference speakers instead of
  requiring two bilingual speakers, and identifies the German and English
  Mozilla Common Voice datasets as the desired source. Male/female selection
  must use the dataset's self-declared metadata, never inference from audio.
- The operator states that permission covers noncommercial sharing of
  generated audio. This operator assurance does not replace the exact
  dataset-specific license, the speaker-use constraints, or the MDC consumer
  terms. The applicable terms must permit the intended use; unresolved
  personal-data or share-alike implications keep shared-output release gated.
- Common Voice data is accessed through MDC. The account holder must accept
  the exact dataset agreement before download. Never identify contributors,
  re-host or re-share the dataset, or put reference assets, transcripts,
  generated audio, account credentials, or consent evidence in git. Any shared
  generated output must be disclosed as machine-generated and must comply with
  the dataset terms.
- Native `say` is the required baseline. Resource denial overrides any valid
  request's engine and voice preference; preserve the resolved requested
  language and the audio response contract. Report the actual engine and
  fallback rather than disguising substitution.
- Thorsten's original neutral recordings with transcripts were an earlier
  German reference candidate. The current request selects Common Voice
  language-specific references; this does not authorize loading Piper/Coqui
  weights into Fish. Exact artifact and dataset review remains required before
  Fish enablement.

## User Scenarios & Testing

### User Story 1 - Approve a feasible Fish runtime (Priority: P1)

As the operator, I want a supported runtime proposal with bounded resource use
and reviewed artifact terms before enabling Fish, so evaluation does not disrupt
existing services or install unapproved material.

**Why this priority**: An enabled setting alone does not provide an inference
service, compatible hardware, or permission to use model and voice assets.

**Independent Test**: Review the candidate artifact set, supported-platform
evidence, capacity proposal, and explicit operator approval. An unresolved
prerequisite must leave Fish disabled without changing working services.

**Acceptance Scenarios**:

1. **Given** inspection-only permission, **When** capacity is assessed,
   **Then** no packages, assets, credentials, or service settings are changed.
2. **Given** unresolved model terms or unsupported runtime evidence,
   **When** enablement is requested, **Then** the missing evidence is reported
   and Fish remains disabled.
3. **Given** reviewed artifacts, a feasible runtime, and approved resource and
   deployment limits, **When** evaluation is authorized separately,
   **Then** only the approved isolated evaluation proceeds.

### User Story 2 - Choose male and female voices by language (Priority: P1)

As a private speech user, I want one male and one female voice in each of
German and English without selecting a different model for each voice.

**Why this priority**: The requested four language/voice combinations depend on
speaker references, not four independent model installations. Four
language-specific speakers are acceptable; cross-language voice identity is
not required.

**Independent Test**: With four approved language-specific recordings, verify
all four language/voice combinations are advertised and produce speech using
the selected speaker and language.

**Acceptance Scenarios**:

1. **Given** approved German and English speaker references, **When** either
   language is selected, **Then** its male and female voices are available.
2. **Given** missing recordings or unresolved speaker consent, **When** voices
   are configured, **Then** the affected combinations are not advertised as
   usable and no substitute speaker is silently selected.
3. **Given** a requested advertised combination, **When** speech is generated,
   **Then** the response identifies Fish as the actual engine.
4. **Given** an applicable dataset term or speaker-use restriction that does
   not permit the selected voice reference or intended sharing, **When** the
   catalog is prepared, **Then** the affected voice or sharing mode remains
   disabled and the restriction is reported.

### User Story 3 - Evaluate without disrupting existing speech (Priority: P2)

As the operator, I want bounded English/German comparisons and a rollback path
while the production service and existing speech clients keep working.

**Why this priority**: Model availability is not evidence of acceptable quality,
latency, or operational safety.

**Independent Test**: After separate approval, run the four synthetic
language/voice combinations within agreed limits, confirm playable speech and
listener acceptance, then verify existing service health and rollback.

**Acceptance Scenarios**:

1. **Given** an approved evaluation budget, **When** it is exceeded,
   **Then** evaluation stops without stopping unrelated services.
2. **Given** Fish cannot run within the resource policy, is busy, or is
   unavailable, **When** a valid caller selects any neural engine or voice,
   **Then** native `say` serves the resolved requested language, ignores the
   incompatible voice preference, and identifies the actual engine and fallback.
3. **Given** evaluation or rollback completes, **When** existing clients are
   checked, **Then** their authentication and speech behavior remain intact.
4. **Given** a neural model is resident, **When** other work needs the reserved
   memory, **Then** only the owned neural process is stopped to release its
   memory, including during idle time, and native speech remains usable.
5. **Given** the low-priority policy is not enabled, **When** an unavailable
   engine is requested, **Then** the existing strict unavailable response remains.

### Edge Cases

- The model runs on a processor but cannot meet the approved speech deadline.
- Shared-host capacity changes after inspection or under concurrent workloads.
- A model supports a language but a reference speaker's pronunciation is poor.
- One speaker supplies consent for only one language or a narrower use.
- Exact model, codec, or runtime revisions differ from the reviewed set.
- The candidate runs only on a different host than the existing adapter permits.
- Discovery succeeds but synthesis fails or exceeds memory/output limits.
- Model or reference terms cannot be retrieved for review.
- Resource monitoring fails, capacity changes during model loading or synthesis,
  or a repeated request would thrash the model between loading and unloading.
- A cancelled request must not start a fallback or leak partial neural audio.

## Requirements

### Functional Requirements

- **FR-001**: Read-only assessment MUST precede runtime selection; it MUST NOT
  install packages, download model or voice assets, or change running services.
- **FR-002**: The runtime proposal MUST identify supported-platform evidence,
  measured capacity versus published guidance, higher-priority workload reserve,
  and proposed memory, storage, concurrency, duration, and cost limits.
- **FR-003**: Installation and enablement MUST require separate approval of the
  exact runtime/model/codec revisions, per-file hashes, applicable terms for
  the stated use, voice provenance, resource budget, and service/network
  changes. An exact approval manifest MUST be available before neural exec.
- **FR-004**: Evaluation MUST expose exactly one male and one female
  language-specific voice in German and in English, only after each exact
  WAV/transcript reference and its intended-use permission have been verified.
  Cross-language speaker identity MUST NOT be inferred or required.
- **FR-005**: The model and speaker references MUST be treated as separate
  assets; neither private use nor model availability establishes voice rights.
- **FR-006**: Fish MUST remain unavailable until its approved inference service,
  exact artifact manifest, and complete four-way qualified reference catalog
  are ready. Missing prerequisites MUST be reported explicitly.
- **FR-007**: Enablement MUST preserve production and the existing prototype's
  authentication, request compatibility, limits, and explicit failure behavior.
- **FR-008**: Evaluation MUST cover all four language/voice combinations with
  synthetic material, playable output, correct engine identity, and operator
  listening review under acceptance thresholds agreed before synthesis.
- **FR-009**: Evaluation MUST stop on approved resource/deadline limits or
  degradation of higher-priority services; rollback MUST restore the previously
  working prototype without modifying production.
- **FR-010**: Credentials, speaker identities, consent records, recordings,
  generated audio, raw host inventory, and private configuration MUST remain
  outside tracked specifications and public artifacts.
- **FR-011**: A proposal requiring a new machine, remote processing, changed
  network boundaries, or spending MUST receive explicit approval before use.
- **FR-012**: An explicitly enabled headroom-first policy MUST reserve 12 GiB
  for higher-priority work, admit at most one neural request, and stop the
  owned neural process if it exceeds the 16 GiB budget or reserve is threatened.
  An unreadable or invalid memory measurement MUST deny neural admission and
  stop any owned neural process, rather than assume sufficient memory.
- **FR-013**: Under that policy, unavailable, busy, or resource-denied neural
  requests MUST use native `say` in the resolved requested language regardless
  of engine/voice preference, including legacy engine selections. Invalid or
  unauthenticated input remains rejected. Explicit native requests MUST NOT
  start the neural model.
- **FR-014**: The neural process MUST be independently owned, low priority,
  lazy-started, monitored during loading, synthesis and idle time, and stopped
  on pressure, idle expiry, cancellation, timeout, or application shutdown.
  Stopping it MUST NOT terminate production or an externally managed process.
- **FR-015**: Fallback MUST preserve authentication, format and size limits,
  use remaining request time rather than reset the deadline, and expose safe
  actual-engine/fallback metadata. Native capacity MUST NOT be exhausted solely
  by waiting neural requests.
- **FR-016**: Resource recovery MUST require sufficient start-up headroom and
  a cooldown before a new neural start. No polling, discovery, or startup may
  download model or voice assets. The stricter existing policy remains default.
- **FR-017**: Before a Common Voice reference is downloaded or used, the
  account holder MUST accept its exact MDC dataset agreement. The system MUST
  not identify contributors or re-host or re-share dataset material. Shared
  model-generated audio MUST be disclosed as machine-generated and MUST remain
  disabled unless its content and use comply with the applicable dataset,
  model, and speaker-use terms, including any personal-data restriction.
- **FR-018**: Fish model artifacts and source references MUST remain private
  and non-redistributed. The exact pinned source, model and decoder artifacts,
  hashes, terms, and noncommercial-use conditions MUST be recorded before the
  managed Fish process can start.

### Key Entities

- **Candidate artifact set**: Exact model, codec, runtime revisions and applicable
  terms reviewed together for the intended use.
- **Language-specific voice profile**: A public voice identifier associated
  with one approved language-specific reference and transcript; contributor
  identities and private permission evidence are not exposed.
- **Evaluation authorization**: Approved runtime, resource limits, synthetic
  material, acceptance thresholds, and rollback boundary.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All required model, codec, runtime, voice, and deployment approvals
  are recorded before the first Fish installation or synthesis operation; any
  dataset agreement is accepted by the account holder before its data is used.
- **SC-002**: Both requested voice choices work in both languages: four of four
  combinations produce playable speech accepted by the operator.
- **SC-003**: Every evaluated combination meets the resource and timing
  thresholds approved before execution; unmeasured outcomes remain unqualified.
- **SC-004**: Existing production and prototype baseline health and authenticated
  speech behavior pass checks before and after evaluation and rollback.
- **SC-005**: No secret, speaker identity, recording, private host configuration,
  or generated audio is added to tracked deliverables.
- **SC-006**: Resource-denied tests cover German and English, explicit neural
  and legacy engine/voice preferences, and return native speech with truthful
  fallback metadata; native requests start zero neural processes.
- **SC-007**: Simulated loading, active and idle memory pressure, memory-probe
  failure, shutdown and cancellation stop only the owned process. Tests also
  establish cooldown, single-neural admission, and remaining-deadline behavior.
- **SC-008**: All shared generated audio is identified downstream as
  machine-generated, and no shared output is released unless the applicable
  dataset/model/speaker terms permit it and the output satisfies their
  restrictions.

## Assumptions

- S2-Pro remains an unapproved candidate. Newly found community MLX Drama 3
  quantization evidence also warrants screening for the confirmed Mac target;
  neither checkpoint/runtime combination is approved or qualified.
- Four language-specific Common Voice speakers are the requested outcome.
  The operator asserts permission for private reference use and noncommercial
  sharing of generated speech. No particular recording has yet been obtained,
  associated with that permission, or reviewed; no contributor identity may be
  sought to establish the association.
- Proposed profile names are `de-male`, `de-female`, `en-male`, and `en-female`;
  these are configuration proposals, not downloadable model identifiers.
- Runtime selection and numeric budgets belong to the technical plan after
  read-only assessment. No new hardware purchase or external processing is
  approved.
- Prior Fish findings remain historical evidence, not silently rewritten
  approval. New evidence must identify which missing gate it resolves.
