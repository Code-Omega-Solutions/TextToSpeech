# Feature Specification: VibeVoice Backend Integration

**Status**: Draft
**Created**: 2026-11-15
**Source**: Product decision following [the private VibeVoice evaluation](../001-vibevoice-evaluation/vibevoice-evaluation.spec.md)

## User Scenarios & Testing

### User Story 1 - Choose a speech backend and voice (Priority: P1)

As a caller in the private research deployment, I want to select VibeVoice for
English or German so the operator can measure resource use and fallback while
keeping routine speech on the existing macOS voice.

**Why this priority**: VibeVoice received higher review ratings, while keeping
macOS speech selectable preserves control and a reliable alternative.

**Independent Test**: In explicit research-only mode, select VibeVoice for
English and German. Confirm the reviewed language-compatible preset is used
when admitted, fallback reports macOS speech accurately, and requests outside
research mode cannot start the worker.

**Acceptance Scenarios**:

1. **Given** a qualified private research host with VibeVoice enabled,
   **When** a caller explicitly selects VibeVoice for English or German,
   **Then** the service uses the corresponding reviewed preset unless a
   higher-priority resource need requires macOS speech.
2. **Given** a caller explicitly selects macOS speech, **When** a valid request
   is submitted, **Then** the service uses macOS speech without loading
   VibeVoice.
3. **Given** a VibeVoice request with no explicit voice, **When** the language
   is English or German, **Then** the service uses the reviewed default Carter
   or Spk1 preset respectively.
4. **Given** a research request explicitly selects the German male Spk0 preset,
   **When** the request is admitted, **Then** the worker uses that preset and
   does not substitute another voice.
5. **Given** an unsupported voice or a voice that does not match the selected
   language, **When** a request is validated, **Then** the service rejects it
   before synthesis and returns no audio.
6. **Given** VibeVoice is selected in research-only mode on a qualified host,
   **When** synthesis begins, **Then** the service uses the reviewed Realtime
   0.5B model and records no production-use claim.
7. **Given** VibeVoice is selected and the voice is omitted or blank,
   **When** the language is detected from sufficiently long text, **Then** the
   service selects the default preset for the resolved language.
8. **Given** an operator binds the research service to all interfaces for a
  trusted Open WebUI client, **When** a valid authenticated speech request
  arrives, **Then** it receives the normal response and unauthenticated
  requests remain rejected.

### User Story 2 - Protect higher-priority inference workloads (Priority: P1)

As an operator running image generation or Ollama on the same machine, I want
speech synthesis to give up memory when those workloads need it, so speech does
not prevent higher-priority inference from running.

**Why this priority**: The reviewed warm VibeVoice process used substantial
memory, and speech is explicitly lower priority than other inference on the
machine.

**Independent Test**: Hold VibeVoice in memory, simulate a higher-priority
memory request, and verify that VibeVoice releases its allocations and speech
continues through macOS speech without restarting the service.

**Acceptance Scenarios**:

1. **Given** insufficient memory or an active higher-priority memory claim,
   **When** a VibeVoice request arrives, **Then** the service does not load or
   retain VibeVoice for that request and uses macOS speech if it is available.
2. **Given** a higher-priority workload requests memory during VibeVoice
   generation, **When** the speech operation cannot safely finish, **Then** the
   service discards partial VibeVoice audio, releases its model resources, and
   retries the request through macOS speech.
3. **Given** memory pressure remains after VibeVoice yields, **When** further
   speech requests arrive, **Then** they use macOS speech and do not reload
   VibeVoice.
4. **Given** the higher-priority memory need has ended and sufficient capacity
   is available, **When** a later request selects VibeVoice, **Then** the
   service may load the shared model again and generate speech normally.
5. **Given** multiple requests arrive while VibeVoice is resident, **When** the
   service admits them, **Then** they share the model and remain within the
   configured synthesis bound without creating duplicate model copies or an
   unbounded queue.
6. **Given** VibeVoice yields memory, **When** its allocations are released,
   **Then** no speech-generation model components or voice-prompt caches remain
   resident.

### User Story 3 - Preserve the existing speech service contract (Priority: P1)

As an existing client, I want either backend to return the same supported audio
formats and retain the current request protections, so adding VibeVoice does
not break speech generation or expose private text.

**Why this priority**: Backend selection is useful only if existing clients
continue to receive valid, bounded, authenticated responses.

**Independent Test**: Exercise both backends with valid and invalid requests,
including MP3 and WAV responses, cancellation, timeout, and a backend failure.

**Acceptance Scenarios**:

1. **Given** a valid request for either backend, **When** MP3 or WAV is
   requested, **Then** the response contains playable audio in that format with
   the corresponding media type.
2. **Given** an invalid or unauthenticated request, **When** it reaches the
   speech service, **Then** existing validation and authentication behavior is
   applied before model loading or synthesis.
3. **Given** VibeVoice and macOS speech are both unavailable, **When** speech is
   requested, **Then** the service returns a clear existing-style availability
   error and no partial audio.
4. **Given** VibeVoice was selected but the service fell back to macOS speech,
   **When** the response is returned, **Then** the caller and operator can
   determine which backend actually generated the audio.
5. **Given** a request contains speech text or credentials, **When** an error
   is returned or the request is logged, **Then** neither the response nor the
   logs disclose that private data.
6. **Given** a request uses a supported speed or reaches an existing input or
   output limit, **When** either backend handles it, **Then** the established
   speed behavior and limit response are preserved.

### User Story 4 - Operate VibeVoice without disrupting service startup (Priority: P2)

As an operator, I want VibeVoice to load only when enabled and needed, so
missing model assets or runtime support do not make the existing speech service
unavailable.

**Why this priority**: The model is optional and its runtime has a much larger
footprint than the existing macOS speech path.

**Independent Test**: Start the service with VibeVoice disabled, with its model
assets missing, and with a supported model available. Confirm that macOS speech
remains usable in every case where its own prerequisites are present.

**Acceptance Scenarios**:

1. **Given** VibeVoice is disabled or its assets are unavailable, **When** the
   service starts, **Then** startup completes and macOS speech remains ready.
2. **Given** VibeVoice is enabled, **When** the service starts, **Then** it
   does not download the model or load its weights before a request is admitted.
3. **Given** VibeVoice has yielded its memory, **When** readiness is checked,
   **Then** the service remains ready if macOS speech is available and reports
   VibeVoice as unavailable or yielded.
4. **Given** model terms, artifact provenance, intended use, or host requirements
  are unresolved, **When** a deployment is prepared, **Then** VibeVoice is not
  installed or enabled and macOS speech remains available.
5. **Given** VibeVoice is enabled, **When** a request reaches the service
  without the research-only setting, **Then** configuration fails closed and
  the worker cannot start.

## Edge Cases

- Automatic language detection may choose a language that VibeVoice does not
  support. The service must use macOS speech or return a clear validation error,
  and identify a fallback accurately.
- A request may arrive while VibeVoice is loading, in use, or being evicted.
  Concurrent requests must not create duplicate model copies or wait in an
  unbounded queue.
- A memory-pressure signal may arrive during generation or while voice prompts
  are cached. The service must release both model and prompt-cache allocations.
- Model loading may fail, the installed assets may be incomplete, or a runtime
  may be unsupported. These failures must not disable macOS speech.
- The caller may explicitly choose VibeVoice while resource pressure requires
  fallback. The response must identify the backend actually used.
- If fallback is required but macOS speech or an audio encoder is unavailable,
  the service must return a clear error without partial audio.
- A request may be cancelled or exceed its existing limits while a backend is
  loading or generating. Cancellation must stop work and release its capacity.
- The host may not provide a trustworthy resource-pressure signal. In that
  case, VibeVoice must be treated as unavailable rather than allowed to compete
  blindly with higher-priority workloads.

## Requirements

### Functional Requirements

- **FR-001**: The service MUST allow an operator to select the configured
  default backend from VibeVoice and the existing macOS speech backend.
- **FR-002**: A speech request MUST be able to override the configured default
  backend when that backend is enabled.
- **FR-003**: The service MUST use VibeVoice Realtime 0.5B for the reviewed
  English and German presets only in an explicitly enabled research-only
  deployment.
- **FR-004**: With VibeVoice selected in research-only mode, the default
  English voice MUST be Carter and the default German voice MUST be Spk1.
- **FR-005**: The service MUST allow the reviewed German Spk0 preset for
  research requests and MUST reject unknown or language-incompatible voice
  selections before synthesis.
- **FR-019**: An omitted or blank VibeVoice voice MUST select the default preset
  for the request's resolved language after automatic language detection.
- **FR-020**: The operator MAY bind the research service to all interfaces for
  a trusted private Open WebUI client, but bearer authentication MUST remain
  enabled and unencrypted HTTP MUST NOT be exposed to untrusted networks.
- **FR-006**: Both backends MUST preserve the existing MP3 and WAV response
  formats, media types, speed behavior, and bounded request and output limits.
- **FR-007**: Both backends MUST use the existing authentication and safe error
  behavior; VibeVoice MUST NOT bypass request validation, cancellation, or
  output-size limits.
- **FR-008**: The service MUST load VibeVoice only after a request has been
  admitted and MUST NOT download model assets during service startup or request
  handling.
- **FR-009**: English and German VibeVoice requests MUST share one resident set
  of model weights rather than loading separate language copies.
- **FR-010**: The serving model MUST load only components required to generate
  speech and MUST release its voice-prompt caches whenever it yields memory.
- **FR-011**: VibeVoice MUST have lower resource priority than image-generation
  and Ollama workloads. Reserve checks for a resident worker MUST exclude the
  worker's own resident memory and MUST yield when external available capacity
  falls below the configured reserve.
- **FR-012**: When VibeVoice cannot safely start or continue, the service MUST
  release its model and prompt-cache allocations and use macOS speech for the
  request at most once when that backend is available.
- **FR-013**: A fallback MUST discard partial VibeVoice audio and MUST make the
  backend that actually generated the response observable to the caller and
  operator.
- **FR-014**: VibeVoice requests MUST be bounded so concurrent work cannot
  create duplicate model instances or an unbounded waiting queue.
- **FR-015**: Failure, disabling, eviction, or missing assets for VibeVoice MUST
  NOT prevent service startup or macOS speech readiness when the macOS
  prerequisites are available.
- **FR-016**: Operational diagnostics MUST identify backend, locale, response
  format, and safe failure reason without logging speech text, credentials, or
  private model paths.
- **FR-017**: Deployment MUST verify the model, runtime, voice, and dependency
  terms, artifact provenance, and supported host requirements before
  installing or distributing them.
- **FR-018**: VibeVoice MUST require an explicit research-only setting and MUST
  NOT be enabled for routine or production speech service.

## Key Entities

- **Speech backend**: The selected speech method, either VibeVoice or the
  existing macOS speech method.
- **Voice preset**: A language-compatible voice choice with a default and any
  supported optional alternatives.
- **Resource claim**: The current memory capacity or higher-priority workload
  signal used to admit, retain, or evict VibeVoice.
- **Synthesis result**: The generated audio, requested format, and actual
  backend used, including whether fallback occurred.

## Success Criteria

### Measurable Outcomes

- **SC-001**: In backend-selection tests, every valid request uses its selected
  backend unless a documented availability, language, or resource condition
  requires fallback.
- **SC-002**: In research-only mode, English defaults to Carter, German
  defaults to Spk1, and an explicitly selected German Spk0 is preserved.
- **SC-003**: Both backends produce playable MP3 and WAV responses with correct
  media types while preserving existing input and output limits.
- **SC-004**: A model-load trace shows one shared VibeVoice weight set for both
  research languages and no resident component that is not required for speech
  generation.
- **SC-005**: Tests show that the worker's own memory does not trigger a false
  reserve crossing, while external pressure below reserve evicts it, blocks
  reload, and preserves macOS speech without restarting the service.
- **SC-006**: When VibeVoice is denied or evicted, the response identifies
  macOS speech as the actual backend; when both backends fail, no partial audio
  is returned.
- **SC-007**: The service remains ready for macOS speech when VibeVoice is
  disabled, unavailable, or evicted, provided the existing macOS prerequisites
  are available.
- **SC-008**: Tests confirm that speech text, credentials, and private model
  paths do not appear in logs or error responses.
- **SC-009**: A benchmark records cold and warm latency and peak memory before
  and after yielding, with the tested host and model configuration identified.
- **SC-010**: OpenAI-compatible requests with an omitted or blank voice select
  Carter for detected English and Spk1 for detected German.
- **SC-011**: On the private research network, an authenticated Open WebUI
  request succeeds through the all-interface listener and an unauthenticated
  request is rejected.

## Assumptions

- VibeVoice Realtime 0.5B is the only VibeVoice variant in scope. The 1.5B
  variant was not selected.
- VibeVoice is the configured default on a qualified host when enabled.
  Operators can instead configure macOS speech, and callers can select a
  permitted backend per request.
- The active VibeVoice presets are `en-Carter_man`, `de-Spk1_woman`, and
  `de-Spk0_man`. German remains experimental and is enabled only for private
  research, not routine or production service.
- Existing language detection and supported output formats remain in place.
  Other supported languages use macOS speech.
- The operator has authorized private R&D use of the English and German
  presets. This does not constitute Microsoft permission, legal approval, or
  authorization to publish or distribute model artifacts or generated data.
- The service will not modify or stop image-generation or Ollama workloads.
  If it cannot reliably detect memory pressure or coordinate resource claims,
  it must choose macOS speech instead of loading VibeVoice.
- Model and runtime terms, artifact provenance, and target-host qualification
  remain deployment gates. This specification does not authorize downloading,
  installing, or deploying model assets.
- The private evaluation remains separate from the production speech service.
