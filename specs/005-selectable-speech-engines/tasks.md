# Tasks: Selectable Speech Engines Prototype

## Scale Note

This feature spans backend engine/configuration code, API contract tests,
frontend discovery controls, model/dependency review, living-spec alignment,
and a parallel remote deployment. Keep the existing service untouched; remote
runtime installation and service activation remain gated on a reviewed plan.

## Phase 1: Setup

### Implementation - Setup

**Wave 1 — sequential dependency review:**

- [x] **T001** [US2] Review the exact MessagePack package terms, add the direct dependency, resolve only lock entries required for a valid backend lock, and update the third-party inventory + `backend/pyproject.toml`, `backend/uv.lock`, `THIRD_PARTY_NOTICES.md`

## Phase 2: Foundational

Files: `backend/app/config.py`, `backend/app/models.py`, `backend/app/engines.py`, `backend/app/fish_speech.py`, `backend/app/services.py`, `backend/app/routers.py`, `backend/app/main.py`

This phase creates the selection contract shared by every story. Story work
does not start until these changes are in place.

### Implementation - Foundational

**Wave 1 — independent configuration and contracts:**

- [x] **T002** [P] [US1] Add validated engine identifiers, default selection, and disabled-by-default Fish endpoint/credential settings + `backend/app/config.py`
- [x] **T003** [P] [US1] Accept the additive `fish-speech` selector while preserving the legacy `vibevoice` request identifier + `backend/app/models.py`
- [x] **T004** [P] [US1] Define the fixed engine interface, descriptors, and registry for macOS and optional Fish engines + `backend/app/engines.py`

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — adapter and service integration:**

- [x] **T005** [US2] Implement bounded MessagePack Fish requests, bearer auth, WAV response validation, cancellation, and timeout without downloading model assets + `backend/app/fish_speech.py`
- [x] **T006** [US1] Route requests through the registry, probe Fish readiness, and preserve actual-engine/fallback metadata and resource limits + `backend/app/services.py`, `backend/app/fish_speech.py`

**⟶ Wait for Wave 2 to finish, then:**

**Wave 3 — API and application lifecycle:**

- [x] **T007** [US1] Add authenticated read-only engine discovery and make legacy VibeVoice selection return the existing safe unavailable response + `backend/app/routers.py`
- [x] **T008** [US4] Stop constructing or loading the VibeVoice worker in the serving application while preserving the health response contract + `backend/app/services.py`, `backend/app/main.py`

## Phase 3: User Story 1 — Keep Existing Speech Clients Working (P1)

Files: `backend/tests/test_models.py`, `backend/tests/test_speech_contract.py`, `backend/tests/test_api.py`, `backend/tests/test_services.py`

**Goal**: Existing clients retain the authenticated speech request/response
contract while engine selection changes internally.

**Independent Test**: Existing tests pass for authentication, validation,
English/German requests, audio formats, headers, errors, and limits.

### Tests - User Story 1

**Wave 1 — independent contract tests (write to fail first):**

- [x] **T009** [P] [US1] Update request-model tests for additive Fish selection, retained legacy identifier, and unchanged validation + `backend/tests/test_models.py`
- [x] **T010** [P] [US1] Assert existing audio formats, headers, safe failures, and engine metadata remain compatible + `backend/tests/test_speech_contract.py`
- [x] **T011** [P] [US1] Assert authenticated legacy and default-selection requests keep the established HTTP contract + `backend/tests/test_api.py`
- [x] **T012** [P] [US1] Update service tests for engine dispatch without changing macOS synthesis behavior + `backend/tests/test_services.py`

**⟶ Wait for Wave 1 to finish, then:**

### Checkpoint - User Story 1

The existing speech clients pass the preserved request/response contract tests.

## Phase 4: User Story 2 — Select English/German Engines and Discover Options (P1)

Files: `backend/tests/test_engines.py`, `backend/tests/test_fish_speech.py`, `backend/tests/test_engine_catalog.py`

**Goal**: The operator can compare independently configured engines through
the same bounded request surface, and authenticated discovery reports only
public engine/language/voice options.

**Independent Test**: Fake engine and Fish HTTP fixtures verify routing,
MessagePack encoding, unavailable behavior, language support, and catalog
redaction without model downloads.

### Tests - User Story 2

**Wave 1 — isolated registry and transport tests (write to fail first):**

- [x] **T013** [P] [US2] Test registry resolution, configured default, engine availability, and no implicit substitution + `backend/tests/test_engines.py`
- [x] **T014** [P] [US2] Test Fish MessagePack payload, authentication, bounded audio response, timeout, and cancellation against a local fake server + `backend/tests/test_fish_speech.py`
- [x] **T015** [P] [US2] Test authenticated discovery shape, configured availability, public voice identifiers, and private-field exclusion + `backend/tests/test_engine_catalog.py`

**⟶ Wait for Wave 1 to finish, then:**

### Checkpoint - User Story 2

The registry, Fish adapter, and catalog pass their focused tests without
requiring a Fish model service.

## Phase 5: User Story 3 — Compare Fish Variants Before Enabling One (P1)

Files: `specs/005-selectable-speech-engines/fish-variant-comparison.md`

**Goal**: The operator can compare Fish variants by published size/resource
requirements and English/German evidence without confusing upstream claims with
local measurements or treating private use as license clearance.

**Independent Test**: Review the comparison document for pinned sources, both
documented variants, exact term status, and explicit unavailable local results.

### Implementation - User Story 3

**Wave 1 — record source-based comparison:**

- [x] **T016** [US3] Record pinned Fish variant size, platform/resource guidance, language evidence, terms status, and unmeasured local criteria + `specs/005-selectable-speech-engines/fish-variant-comparison.md`

### Checkpoint - User Story 3

No variant is selected, downloaded, installed, or enabled by the comparison.

## Phase 6: User Story 4 — Retire VibeVoice Without Breaking the Wire Contract (P1)

Files: `backend/tests/test_config.py`, `backend/tests/test_vibevoice_retirement.py`, `backend/tests/test_vibevoice_startup.py`, `backend/README.md`, `capabilities/backend-synthesis/backend-synthesis.spec.md`, `capabilities/backend-synthesis/backend-synthesis.coverage.md`, `specs/README.md`

**Goal**: The serving application no longer constructs or starts the VibeVoice
worker. Legacy requests get a safe unavailable response, while historical
evaluation evidence remains distinct from deployed backend support.

**Independent Test**: Verify the app does not load the worker, readiness remains
based on macOS prerequisites plus configured engines, the old identifier is
unavailable, and current documentation no longer presents VibeVoice as a
deployable serving engine.

### Tests - User Story 4

**Wave 1 — retirement and readiness tests (write to fail first):**

- [x] **T017** [P] [US4] Update config expectations for a retired VibeVoice serving default + `backend/tests/test_config.py`
- [x] **T018** [P] [US4] Assert serving startup never constructs or starts the VibeVoice worker + `backend/tests/test_vibevoice_retirement.py`
- [x] **T019** [P] [US4] Replace worker-status readiness assertions with the disabled compatibility header and unaffected macOS readiness + `backend/tests/test_vibevoice_startup.py`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation - User Story 4

- [x] **T020** [US4] Document VibeVoice as retired from the serving prototype while preserving private evaluation scope and legal gates + `backend/README.md`
- [x] **T021** [US4] Update backend synthesis scenarios and touches to describe the engine registry and unavailable legacy VibeVoice identifier + `capabilities/backend-synthesis/backend-synthesis.spec.md`
- [x] **T022** [US4] Align backend requirement-to-test mappings with the new catalog, selection, and retirement tests + `capabilities/backend-synthesis/backend-synthesis.coverage.md`
- [x] **T023** [US4] Index the selectable-engine feature and its gated deployment outcome + `specs/README.md`

**⟶ Wait for Wave 1 and implementation tasks to finish, then:**

### Checkpoint - User Story 4

The app serves macOS and approved optional engines without starting VibeVoice;
existing evaluation records are not presented as runtime qualification.

## Phase 7: User Story 5 — Deploy a Gated Private Prototype (P2)

Files: `specs/005-selectable-speech-engines/deployment-plan.md`

**Goal**: Prepare a parallel deployment plan that keeps the current service
untouched and records prerequisites without exposing host identifiers or
credentials.

**Independent Test**: Review the plan for an approved separate service boundary,
current runtime blockers, explicit install/remediation approvals, and a stop
before any unapproved host change.

### Implementation - User Story 5

**Wave 1 — prepare a read-only deployment plan:**

- [x] **T024** [US5] Record the parallel service boundary, verified SSH-key status, unmet runtime prerequisites, and approvals needed before installation or service registration + `specs/005-selectable-speech-engines/deployment-plan.md`

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T025** [US5] Apply only an explicitly reviewed target setup plan and deploy the prototype in parallel; stop if runtime, artifact rights, port, or service approval is missing + `specs/005-selectable-speech-engines/deployment-plan.md`

### Checkpoint - User Story 5

The existing service remains healthy and unchanged. If an install or service
approval is not granted, deployment remains explicitly blocked and no host
mutation is performed.

## Phase 8: User Story 6 — Choose an Available Engine in the Speech Interface (P2)

Files: `frontend/tests/dev.test.js`, `frontend/tests/e2e/engine-discovery.spec.js`, `frontend/index.html`, `frontend/app.js`, `frontend/config/upstream.js`, `frontend/vite.config.js`

**Goal**: The repository speech screen discovers advertised engines and
language-compatible voices, then sends selections through existing request
fields without exposing upstream credentials.

**Independent Test**: Mock discovery and speech responses in the browser, verify
available/empty/error states, and assert submitted `model`/`voice` fields and
audio playback/download behavior.

### Tests - User Story 6

**Wave 1 — development and browser tests (write to fail first):**

- [x] **T026** [P] [US6] Test development proxy allows catalog GET, denies unsupported methods/paths, and keeps credentials server-side + `frontend/tests/dev.test.js`
- [x] **T027** [P] [US6] Test selector population, language filtering, discovery failure, selected request values, and preserved playback + `frontend/tests/e2e/engine-discovery.spec.js`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation - User Story 6

- [x] **T028** [US6] Add engine and voice selectors plus an accessible discovery status to the existing speech form + `frontend/index.html`
- [x] **T029** [US6] Fetch the catalog, filter public options, preserve the current default when possible, and submit selected values using existing fields + `frontend/app.js`
- [x] **T030** [US6] Add the authenticated catalog GET route to the Vite API allowlist and proxy timeout configuration + `frontend/config/upstream.js`, `frontend/vite.config.js`

**⟶ Wait for implementation tasks to finish, then:**

### Checkpoint - User Story 6

The existing UI generates the same audio contract and only offers catalogued,
available engine/voice choices.

## Final Phase: Polish

**Files**: `checks/run_companion_validation.sh`, `checks/tests/test_companion_validation_hook.py`

### Implementation - Polish

- [x] **T031** Update the validation runner's Windows-compatible backend selection to include the new engine, Fish, and retirement tests + `checks/run_companion_validation.sh`
- [x] **T032** Assert the validation hook continues to own the full Success Criteria suite + `checks/tests/test_companion_validation_hook.py`
- [x] **T033** Validate against Success Criteria, owned by the project's post-implement validation hook (no separate suite run) + `.specify/companion.yml`

## Dependencies & Execution Order

Setup blocks Foundational because the MessagePack codec must be reviewed and
locked first. Foundational blocks all stories by defining engine configuration,
selection, routing, Fish transport, and readiness. User Story 1 verifies the
wire contract; User Story 2 verifies engine and Fish dispatch; User Story 3
records evidence before candidate selection; User Story 4 verifies VibeVoice
retirement; User Story 5 prepares and, only with approval, performs parallel
deployment; User Story 6 delivers the catalog-backed UI. Polish updates the
validation owner and runs the suites in the post-implement hook exactly once.

Within each phase, tasks in a wave use different files and can be handled in any
order. A later wave waits for the preceding wave's tests or shared contract to
finish. Remote deployment is not a prerequisite for local implementation and
remains blocked until its explicit approval gates pass.
