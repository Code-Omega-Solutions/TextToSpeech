# Feature Specification: Selectable Speech Engines Prototype

**Source**: .specify/assessments/fish-speech/
**Created**: 2026-11-16
**Status**: Draft
**Input**: Private home automation and Open WebUI need an English/German speech prototype that can select and evaluate TTS engines without breaking existing clients. VibeVoice cannot remain the deployed engine. Fish Speech is a candidate, not an approved model or license.

## Clarifications

### Session 2026-11-16

- Q: After removing the VibeVoice runtime, what should a legacy request with `model=vibevoice` do? → A: Return the existing safe unavailable response; do not treat it as an alias for the configured default.
- Q: Should this prototype add a read-only API response listing configured/available engines and their supported languages and voices? → A: Yes; expose discovery as an additive API capability.
- Q: Which Vue frontend should the engine/voice discovery UI target? → A: Target this repository's frontend; it currently uses vanilla JavaScript, not Vue.
- Q: How should the prototype coexist with the healthy service already running on the target? → A: Deploy in parallel on a separately approved port; leave the existing service untouched.
- Q: Which Fish Speech candidate should the prototype prepare to evaluate first on the target? → A: Compare Fish Speech variants only for size-to-quality ratio; defer candidate selection and installation until the comparison and rights review are complete.

## User Scenarios & Testing

### User Story 1 - Keep existing speech clients working (Priority: P1)

As a home-automation or Open WebUI user, I want my existing speech requests to
continue working while the service gains engine choices, so I do not have to
rewrite working clients just to evaluate a different synthesizer.

**Why this priority**: Engine evaluation is useful only if it preserves existing
client behavior.

**Independent Test**: Exercise the existing authenticated speech request against
the prototype and compare its accepted request shape, status behavior, audio
formats, response headers, limits, and error redaction with the current API.

**Acceptance Scenarios**:

1. **Given** a valid existing request that omits `model`, **When** it is sent to
   the prototype, **Then** the configured default engine returns the same
   MP3/WAV response contract, request ID, and backend/fallback headers.
2. **Given** an existing request that explicitly selects `macos-say`,
   **When** it is sent, **Then** the request and response contract remains
   unchanged.
3. **Given** an invalid, unauthenticated, oversized, or timed-out request,
   **When** it is sent, **Then** existing safe errors and privacy boundaries
   remain in effect.

### User Story 2 - Select an engine for English or German (Priority: P1)

As the operator, I want to select an available speech engine per request or set
one configured default, so I can compare the current engine with an approved
Fish Speech candidate without changing the client integration.

**Why this priority**: The candidate must be comparable before anyone can decide
whether to keep it.

**Independent Test**: With fake engines registered for English and German,
select each through the existing speech interface and verify the chosen engine,
locale, requested audio format, and actual-engine response metadata.

**Acceptance Scenarios**:

1. **Given** two enabled engines and a valid English or German request,
   **When** the caller selects either engine or omits selection, **Then** the
   selected or configured-default engine handles the request.
2. **Given** an engine is unconfigured or unavailable, **When** a request selects
   it, **Then** the API returns a safe unavailable response and does not silently
   substitute another engine.
3. **Given** the engine falls back under an explicitly configured fallback
   policy, **When** it returns audio, **Then** existing headers identify the
   engine that actually generated the audio and whether fallback occurred.
4. **Given** an authenticated client requests discovery, **When** the response is
  returned, **Then** it lists configured engine identifiers, their availability,
  supported English/German languages, and public voice identifiers without
  exposing filesystem paths, credentials, or private host details.

### User Story 3 - Compare Fish variants before enabling one (Priority: P1)

As the operator, I want to compare candidate Fish Speech variants by model
size, language evidence, speech quality, and resource demands before choosing one,
so the prototype does not commit to a model that is too large or unsuitable.

**Why this priority**: The candidate has not been selected, and model size alone
does not establish useful English/German quality or host feasibility.

**Independent Test**: Review the comparison record and verify that each Fish
variant has its source revision, published size/resource claims, English/German
evidence, term status, and a clear separation between vendor claims and local
measurements.

**Acceptance Scenarios**:

1. **Given** published evidence for multiple Fish variants, **When** the
  comparison is prepared, **Then** it records size, platform/resource
  requirements, and language evidence without presenting vendor measurements
  as local results.
2. **Given** model terms, voice provenance, or local runtime authorization is
  unresolved, **When** the comparison is read, **Then** local speech quality and
  performance remain unmeasured and no variant is enabled or downloaded.

### User Story 4 - Retire VibeVoice without breaking the wire contract (Priority: P1)

As an operator replacing the R&D-only VibeVoice deployment, I want requests and
responses to remain contract-compatible while VibeVoice is no longer loaded on
the target, so existing Open WebUI settings can migrate deliberately.

**Why this priority**: The prototype must remove the unsuitable deployed engine
without surprising existing clients or claiming that Fish Speech has passed
evaluation.

**Independent Test**: Run contract tests for every previously accepted request
form and verify the safe unavailable response for a legacy `vibevoice` selection
when the old engine is absent.

**Acceptance Scenarios**:

1. **Given** a client sends a previously accepted request, **When** VibeVoice is
   not installed on the target, **Then** the request is not rejected solely
   because the prototype changed the request schema.
2. **Given** a request uses the legacy `vibevoice` identifier after its runtime
  is removed, **When** it is received, **Then** the service returns the
  existing safe unavailable response and does not route it to another engine.
3. **Given** an operator checks startup and readiness, **When** VibeVoice is not
   installed, **Then** the service does not start its worker or require its
   assets for readiness.

### User Story 5 - Deploy a gated private prototype (Priority: P2)

As the operator, I want the prototype deployed to the authorized private host
with the existing authentication and network boundaries intact, so I can
evaluate English and German speech in the intended environment.

**Why this priority**: Local contract tests are necessary but do not establish
that the target host can run or reach an engine.

**Independent Test**: After target identity, access, runtime, exact model/voice
terms, and deployment settings are approved, verify liveness/readiness and make
authenticated English and German test requests without exposing secrets or
changing unrelated services.

**Acceptance Scenarios**:

1. **Given** target SSH identity is verified and key authentication succeeds,
   **When** the approved prototype is deployed, **Then** only the named service
  is added on a separately approved port and its health/readiness and
  authenticated speech contract are checked while the existing service remains
  unchanged.
2. **Given** target identity or SSH access is unverified, **When** deployment is
   requested, **Then** no key, host-key, service, firewall, or runtime
   configuration is changed.
3. **Given** a candidate's exact terms or voice provenance are unresolved,
   **When** deployment is prepared, **Then** its weights and voices are not
   installed or enabled.

### User Story 6 - Choose an available engine in the speech interface (Priority: P2)

As a home-automation user, I want the existing speech interface to show and let
me choose engines and voices that the service currently advertises, so I can
evaluate available options without entering unsupported identifiers manually.

**Why this priority**: Discovery is useful only when the existing interface can
use it; it remains secondary to preserving the API and safe engine selection.

**Independent Test**: Provide a discovery response with two enabled engines and
supported language/voice combinations, then verify the interface presents only
those choices and sends the selected values in the existing speech request.

**Acceptance Scenarios**:

1. **Given** the discovery response lists available engines and voices,
  **When** the interface loads, **Then** it presents selectable choices
  compatible with the selected language.
2. **Given** discovery fails or no engine is available, **When** the user opens
  the interface, **Then** it displays a safe status and prevents submission of
  an unavailable choice.
3. **Given** the user selects an engine and voice, **When** speech is generated,
  **Then** the interface sends them through the existing `model` and `voice`
  request fields and continues to play/download the returned audio.

## Edge Cases

- The configured default engine is absent, disabled, or not ready at startup.
- A request selects an unknown engine or a voice/locale pair the engine does not
  support.
- One engine is unavailable while another is healthy; fallback must be explicit
  and the actual engine must remain observable.
- VibeVoice is absent while an old Open WebUI client still sends its identifier.
- Fish Speech is installed but its exact checkpoint, codec, or voice terms differ
  from the reviewed artifacts.
- The selected engine cannot emit the requested MP3 or WAV format.
- Host-key verification fails, the target cannot be reached, or SSH key
  authentication cannot be tested without a password prompt.
- A deployment would bind the authenticated HTTP service beyond the approved
  private network boundary.
- Engine startup or synthesis fails after readiness, or returns partial audio.

## Requirements

### Functional Requirements

- **FR-001**: The existing speech route, authentication behavior, request fields,
  response formats, response headers, documented limits, and safe error shape
  MUST remain compatible for existing clients.
- **FR-002**: The operator MUST be able to configure one default engine and the
  caller MUST be able to select an enabled engine using the existing request
  selection mechanism.
- **FR-003**: The backend MUST dispatch engines through a shared contract that
  preserves language, voice, speed, format, cancellation, timeout, and bounded
  error behavior.
- **FR-004**: The prototype MUST support the existing macOS speech engine and a
  Fish Speech variant selected after the required comparison and rights review
  for English and German, without requiring either engine merely to start the
  other.
- **FR-005**: An unknown, disabled, or unavailable selected engine MUST return a
  safe unavailable response; it MUST NOT silently substitute an engine unless
  the operator has explicitly configured that fallback policy.
- **FR-006**: Successful responses MUST continue to identify the actual engine
  and fallback state using the existing response metadata.
- **FR-007**: VibeVoice MUST NOT be loaded, installed, or required for readiness
  in the target prototype. Requests using its existing identifier MUST return
  the existing safe unavailable response and MUST NOT be routed to another
  engine.
- **FR-008**: Fish Speech weights, codecs, runtime packages, and voices MUST NOT
  be installed or enabled until the exact artifacts, provenance, applicable
  terms, and intended private use have been reviewed and accepted.
- **FR-009**: English and German readiness MUST reflect the configured engines
  without making an absent optional engine block unrelated available engines.
- **FR-010**: Deployment MUST preserve bearer authentication, protect
  credentials, retain approved network access boundaries, and leave unrelated
  services unchanged.
- **FR-011**: Deployment MUST stop before host or service changes when the
  target host key is unverified or key authentication is unavailable.
- **FR-012**: The deployment target's operating system, runtime, engine assets,
  service manager, and approved network exposure MUST be checked read-only; the
  prototype MUST remain undeployed when required prerequisites are absent or
  unsupported until the operator explicitly approves a remediation.
- **FR-013**: Logs and errors MUST NOT disclose speech text, credentials, raw
  subprocess output, or private host configuration.
- **FR-014**: The API MUST provide authenticated, read-only discovery of
  configured engine availability, supported English/German languages, and
  public voice identifiers without exposing private paths or host details.
- **FR-015**: The repository's speech interface MUST display and submit only
  engine, language, and voice options advertised by discovery, while preserving
  existing speech controls and audio playback.
- **FR-016**: The prototype MUST be deployed as a separate service on a
  separately approved port and MUST NOT stop, overwrite, or reconfigure the
  existing healthy speech service.
- **FR-017**: The evaluation record MUST compare Fish Speech variants using
  published model size/resource requirements and English/German evidence, label
  vendor claims separately from local results, and leave unapproved local
  quality/performance measurements unavailable.

### Key Entities

- **Speech engine**: A provider that accepts the established speech request
  fields and reports audio, actual engine identity, and failure/fallback status.
- **Engine selection**: The configured default or per-request choice among
  enabled providers.
- **Candidate artifact set**: The exact model, codec, runtime packages, voice
  assets, source revision, and terms reviewed together before enabling a
  candidate.
- **Deployment approval**: The verified target identity, authorized access,
  approved engine artifacts, and network/service boundary needed before remote
  changes.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All existing speech contract tests pass unchanged for route,
  authentication, request validation, MP3/WAV response, headers, errors, and
  limits.
- **SC-002**: At least two engine implementations can be selected independently
  for English and German through the same client contract.
- **SC-003**: Tests prove disabled/failed engines cannot silently replace the
  selected engine and successful responses identify the actual provider.
- **SC-004**: Startup and readiness tests pass with each optional engine absent
  while another configured engine remains usable.
- **SC-005**: A target deployment is considered successful only after verified
  host identity, approved runtime/artifacts, authenticated English and German
  requests, and unchanged existing client contract are confirmed.
- **SC-006**: No model or voice asset with unresolved terms/provenance is
  downloaded, installed, or enabled.
- **SC-007**: No credential, speech text, or private host detail appears in the
  checked-in specification, tests, logs, or deployment artifacts.
- **SC-008**: Discovery reports each configured engine's availability and
  English/German language/voice options while exposing no private runtime paths.
- **SC-009**: The speech interface populates engine and voice choices from
  discovery and generates requests using the selected advertised options.
- **SC-010**: Deployment verification confirms the existing service remains
  healthy and unchanged while the prototype is reachable on its approved port.
- **SC-011**: The Fish comparison covers every considered variant's published
  size/resource and English/German evidence, marks local results as unavailable
  until approved tests run, and does not enable a variant before rights review.

## Assumptions

- The OpenAI-compatible endpoint remains `/v1/audio/speech`; existing clients
  continue to send the same fields and receive MP3/WAV bytes.
- The existing `model` field remains the selection mechanism; adding a new
  candidate identifier is additive.
- Engine/voice discovery is a new authenticated, read-only API capability; its
  route and representation are decided during planning.
- The targeted repository frontend is the current vanilla JavaScript interface;
  no Vue framework is introduced by this prototype.
- macOS speech remains available as a baseline where its host prerequisites
  exist. The target OS and actual engine runtime remain unverified.
- “Private use” does not waive model, voice, package, attribution, or usage
  terms. Only the exact artifact terms and voice provenance can establish
  whether a candidate is acceptable.
- No SSH key or host configuration is changed without the user present and
  explicitly approving the exact change after host identity is trusted.
- The prototype will run beside the existing service on a separately approved
  port; its exact service path and port are deployment-plan decisions.
- Candidate comparison is limited to Fish Speech variants; other engine families
  are out of scope for this comparison.
- Deployment can remain blocked while the API-compatible local prototype and
  its tests are implemented.
