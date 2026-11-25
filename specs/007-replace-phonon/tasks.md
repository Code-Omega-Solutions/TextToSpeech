# Tasks: Replace Fish Speech with Ollama Phonon

## Execution Boundary

Mocked tests may be implemented without model assets or a running Ollama service. Do not download or use a model or voice, inspect a target host, generate speech, or change a service until its exact asset terms and provenance, target compatibility, and trusted endpoint have been reviewed and the required separate approval is given. The implementation must remain disabled by default.

## Phase 1: Setup

### Wave 1 — prerequisite review

- [x] **T001** Review public evidence for exact model and voice candidates, source revisions, applicable terms, intended-use fit, and known target-compatibility constraints; record unresolved items and approval status without downloading assets or probing a host · `specs/007-replace-phonon/research.md`

## Phase 2: Foundational

### Wave 1 — request-boundary regression

- [x] **T002** [P] [US1] Add a request-model regression proving text above 5,000 UTF-16 code units is accepted while invalid Unicode remains rejected · `backend/tests/test_models.py`

**⟶ Wait for Wave 1 to finish, then:**

### Wave 2 — request validation

- [x] **T003** [US1] Remove the fixed 5,000-unit input cap, add the explicit `phonon` request selector, and preserve nonempty input and Unicode validation · `backend/app/models.py`

## Phase 3: User Story 1 — Generate English and German speech with Phonon (P1)

**Goal**: An authenticated client can explicitly select a configured Phonon model and approved voice, receive complete speech in the requested format and speed, and get truthful engine metadata.

**Independent Test**: Exercise `POST /v1/audio/speech` through the public API with a fake Ollama endpoint. Verify English and German selections, a request over the model's 4,096-character limit but within the 32 KiB request bound, exact ordered segment delivery, valid WAV/MP3 responses, and safe failure when Phonon is unavailable.

**Files**: `backend/app/config.py`, `backend/app/phonon.py`, `backend/app/services.py`, `backend/app/routers.py`, `backend/tests/test_config.py`, `backend/tests/test_phonon.py`, `backend/tests/test_phonon_api.py`, `backend/tests/test_phonon_request_contract.py`, `backend/tests/test_phonon_segmentation.py`, `backend/tests/test_phonon_streaming.py`, `backend/tests/test_phonon_response_metadata.py`, `backend/tests/test_phonon_security.py`, `backend/tests/test_phonon_privacy.py`, `backend/tests/test_phonon_approval.py`, `backend/tests/test_phonon_availability.py`, `backend/tests/test_phonon_live.py`, `backend/tests/test_services.py`, `backend/tests/test_engines.py`, `backend/tests/test_api.py`, `backend/tests/test_speech_contract.py`, `backend/tests/test_vibevoice_startup.py`

### Tests

**Wave 1 — independent tests in separate files:**

- [x] **T004** [P] [US1] Add fake-transport tests for proxy bypass, redirect rejection, bounded PCM reads, cancellation, timeout, and malformed responses · `backend/tests/test_phonon.py`, `backend/tests/phonon_test_support.py`
- [x] **T005** [P] [US1] Add public API tests for FR-002: approved English and German model/voice selections return complete speech without selecting an unapproved voice · `backend/tests/test_phonon_api.py`
- [x] **T006** [P] [US1] Add public API tests for FR-004: text over 5,000 units is accepted within the existing encoded-body limit, while authentication, speed, voice, WAV/MP3 format, and response-size safeguards remain effective · `backend/tests/test_phonon_request_contract.py`
- [x] **T007** [P] [US1] Add public API tests for FR-005: text beyond the model's 4,096-character capacity is split, spoken in order, and returned without omission or truncation · `backend/tests/test_phonon_segmentation.py`
- [x] **T008** [P] [US1] Add public API tests for FR-006: the complete-response contract is preserved and the service does not claim client-facing streaming · `backend/tests/test_phonon_streaming.py`
- [x] **T009** [P] [US1] Add public API tests for FR-007: successful metadata names the engine that actually generated the audio · `backend/tests/test_phonon_response_metadata.py`
- [x] **T010** [P] [US1] Add public API tests for FR-008: existing authentication is required and an unauthorized request never reaches the unauthenticated Phonon endpoint · `backend/tests/test_phonon_security.py`
- [x] **T011** [P] [US1] Add public API failure tests for FR-009 proving errors and logs do not reveal speech text, credentials, or endpoint details · `backend/tests/test_phonon_privacy.py`
- [x] **T012** [P] [US1] Add tests for FR-010 proving Phonon remains unavailable and makes no endpoint call without reviewed, approved model and voice provenance; reject unsafe endpoint forms · `backend/tests/test_phonon_approval.py`, `backend/tests/test_config.py`
- [x] **T013** [P] [US1] Add public API tests for FR-011: missing service/model/voice returns a safe unavailable response and never falls back to native speech · `backend/tests/test_phonon_availability.py`
- [x] **T014** [P] [US1] Add opt-in English/German live qualification tests that require explicit approved configuration, skip by default, and never pull assets · `backend/tests/test_phonon_live.py`

### Implementation

**⟶ Wait for the tests above, then:**

### Wave 2 — configuration

- [x] **T015** [US1] Add fail-closed Phonon settings, approval-record validation, and loopback endpoint validation · `backend/app/config.py`

**⟶ Wait for Wave 2 to finish, then:**

### Wave 3 — adapter

- [x] **T016** [US1] Implement the standard-library Ollama speech adapter with no redirects or ambient proxies, bounded PCM reads, cancellation/deadline handling, and ordered capacity-aware segmentation · `backend/app/phonon.py`

**⟶ Wait for Wave 3 to finish, then:**

### Wave 4 — service integration

- [x] **T017** [US1] Register Phonon, keep native `macos-say` intact, convert bounded PCM through the existing WAV/FFmpeg path, retain complete-response behavior, remove Fish dispatch and fallback branches, and delete obsolete Fish settings · `backend/app/services.py`, `backend/app/config.py`, `backend/app/engines.py`

**⟶ Wait for Wave 4 to finish, then:**

### Wave 5 — public contract

- [x] **T018** [US1] Return a safe unavailable response for retired `fish-speech`, avoid Fish health reporting, preserve Phonon response metadata, and update existing integration assertions · `backend/app/routers.py`, `backend/tests/test_api.py`, `backend/tests/test_services.py`, `backend/tests/test_engines.py`, `backend/tests/test_speech_contract.py`, `backend/tests/test_vibevoice_startup.py`

**Checkpoint**: Fake-endpoint public tests prove Phonon request behavior and bounded response guarantees; no live model or voice has been used.

## Phase 4: User Story 2 — Continue using native macOS speech (P1)

**Goal**: Removing Fish and adding Phonon does not make native `say` depend on Phonon or its endpoint.

**Files**: `backend/tests/test_native_speech_preservation.py`

### Tests

**Wave 1 — public API regression:**

- [x] **T019** [US2] Test through the public API for FR-003 that `macos-say` remains selectable and baseline readiness succeeds when Phonon is disabled or unavailable · `backend/tests/test_native_speech_preservation.py`

### Implementation

No separate production change is planned. The User Story 1 integration must preserve the existing native registration and readiness contract.

**Checkpoint**: Native speech remains independently selectable and its readiness does not depend on Phonon.

## Phase 5: User Story 3 — Retire Fish without surprising existing clients (P1)

**Goal**: Fish is absent from discovery and runtime requirements, while old explicit selections fail safely instead of selecting Phonon or the default engine.

**Files**: `backend/tests/test_fish_retirement.py`, `backend/app/fish_speech.py`, `backend/app/fish_process.py`, `backend/deployment/fish_worker_launcher.py`, `backend/deployment/com.example.private-speech-studio-backend.plist`, `backend/tests/test_fish_speech.py`, `backend/tests/test_fish_process.py`, `backend/tests/test_fish_worker_launcher.py`, `backend/tests/test_fish_deployment_template.py`, `backend/README.md`, `backend/deployment/prototype-operations.md`, `backend/voice-preparation.md`, `living-specs.yml`, `capabilities/backend-synthesis/backend-synthesis.spec.md`, `capabilities/backend-synthesis/backend-synthesis.coverage.md`, `specs/README.md`

### Tests

**Wave 1 — public retirement behavior:**

- [x] **T020** [US3] Test through authenticated discovery and speech routes for FR-001 that Fish is not advertised, a retired `fish-speech` selection returns 503 without fallback, and baseline readiness does not require Fish · `backend/tests/test_fish_retirement.py`

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

### Wave 2 — independent cleanup in separate files

- [x] **T021** [P] [US3] Remove the Fish adapter, managed process, launcher, and Fish-only engine tests · `backend/app/fish_speech.py`, `backend/app/fish_process.py`, `backend/deployment/fish_worker_launcher.py`, `backend/tests/test_fish_speech.py`, `backend/tests/test_fish_process.py`, `backend/tests/test_fish_worker_launcher.py`
- [x] **T022** [P] [US3] Replace active Fish setup instructions with the disabled-by-default Phonon boundary, mark Fish operational notes as historical, remove Fish settings from the retained native-only plist, retain generic deployment safeguards, and align the deployment test plus backend living requirements, coverage map, capability registry, and spec index · `backend/deployment/com.example.private-speech-studio-backend.plist`, `backend/tests/test_fish_deployment_template.py`, `backend/README.md`, `backend/deployment/prototype-operations.md`, `backend/voice-preparation.md`, `living-specs.yml`, `capabilities/backend-synthesis/backend-synthesis.spec.md`, `capabilities/backend-synthesis/backend-synthesis.coverage.md`, `specs/README.md`

**Checkpoint**: Fish code and assets are not required at runtime, discovery omits Fish, and legacy requests fail safely.

## Phase 6: Polish

### Wave 1 — project validation

- [x] **T023** Validate the complete change against the feature Success Criteria, owned by the project's post-implement validation hook; do not add a duplicate suite run · `checks/run_companion_validation.sh`

**⟶ Wait for Wave 1 and the release prerequisites, then:**

### Wave 2 — live qualification

- [x] **T024** [US1] Run the opt-in English and German live qualification only after exact asset approval, target compatibility review, trusted endpoint verification, and separate operational consent; do not download assets · `backend/tests/test_phonon_live.py`

**⟶ Wait for Wave 2, then:**

### Wave 3 — browser alignment

- [x] **T025** [US4] Remove fixed browser truncation and validate the complete encoded request against the existing byte bound without discarding input · `frontend/app.js`, `frontend/index.html`, `frontend/tests/e2e/speech.spec.js`
- [x] **T026** [US4] Verify discovered Phonon language and voice selection, retired-engine exclusion, and actual-engine disclosure through the browser · `frontend/tests/e2e/engine-discovery.spec.js`, `frontend/tests/e2e/speech.spec.js`
- [x] **T027** [US4] Align the speech-generation living specification and coverage map with the verified browser behavior · `capabilities/speech-generation/speech-generation.spec.md`, `capabilities/speech-generation/speech-generation.coverage.md`

## Conditional Post-Use Follow-Up

FR-012 does not add a pre-use quality threshold. If the requester reports after productive use that expectations were not met, create a separate follow-up at that time. No such report has been made in this planning step.

## Dependencies & Execution Order

Setup review precedes foundational request changes; Foundational precedes User Story 1; User Story 1 precedes the native-preservation and Fish-retirement stories; Polish follows all three stories. Within User Story 1, all test files in Wave 1 are independent. Configuration precedes the adapter, the adapter precedes service integration, and service integration precedes the public router contract. User Stories 2 and 3 depend on the completed User Story 1 integration but not on each other. Live qualification remains blocked by reviewed assets, target compatibility, a trusted endpoint, and separate operational consent.

**Wave summary**: T002 → T003; T004–T014 → T015 → T016 → T017 → T018; T019; T020 → T021/T022; T023 → T024 after release prerequisites.
