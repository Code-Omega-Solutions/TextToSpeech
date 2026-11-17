# Tasks: UI endpoint configuration

## Phase 1: Setup

**Wave 1 — independent (different files):**
- [x] **T001** [P] [US1] Define endpoint configuration file path, startup precedence, and operator policy · `backend/app/config.py`
- [x] **T002** [P] [US3] Add synthetic persistence and mount instructions · `frontend/README.md`, `frontend/compose.yaml`

## Phase 2: Foundational

**Wave 1 — independent (different files):**
- [x] **T003** [P] [US1] Add validated endpoint and atomic JSON persistence models · `backend/app/config.py`
- [x] **T004** [P] [US2] Add explicit capability outcome model and endpoint revision isolation · `backend/app/routers.py`
- [x] **T005** [P] [US1] Add configuration tab structure and accessible status identifiers · `frontend/index.html`
- [x] **T006** [P] [US1] Add configuration tab layout and responsive styles · `frontend/styles.css`

**⟶ Wait for Wave 1 to finish, then:**
- [x] **T007** [US1] Wire authorized GET/PUT configuration routes into the application boundary · `backend/app/routers.py`, `backend/app/main.py`

## Phase 3: User Story 1 — Choose the intended speech service

Files: `frontend/app.js`, `backend/tests/test_config.py`, `backend/tests/test_api.py`, `frontend/tests/config.test.js`

### Tests

- [x] **T008** [US1] Test valid, invalid, unauthorized, failed, and atomic endpoint saves first · `backend/tests/test_config.py`, `backend/tests/test_api.py`
- [x] **T009** [US1] Test keyboard save, active-versus-unsaved state, and post-save routing first · `frontend/tests/config.test.js`

### Implementation

**Wave 1 — independent (different files):**
- [x] **T010** [P] [US1] Implement endpoint load, edit, save, and announced errors · `frontend/app.js`
- [x] **T011** [P] [US1] Scope health and speech requests to the saved endpoint revision · `frontend/app.js`

**⟶ Wait for Wave 1 to finish, then:**
- [x] **T012** [US1] Integrate save refresh and stale-response cancellation without replaying in-flight speech · `frontend/app.js`

Checkpoint: The operator can save a permitted endpoint and subsequent checks and speech use only that endpoint.

## Phase 4: User Story 2 — Use only supported speech options

Files: `frontend/app.js`, `backend/app/routers.py`, `frontend/tests/e2e/engine-discovery.spec.js`, `backend/tests/test_speech_contract.py`

### Tests

- [x] **T013** [US2] Test supported, unsupported, authentication, network, invalid, and empty discovery outcomes first · `backend/tests/test_api.py`, `frontend/tests/e2e/engine-discovery.spec.js`
- [x] **T014** [US2] Test legacy speech with omitted model/voice and existing default backend contract first · `backend/tests/test_speech_contract.py`

### Implementation

**Wave 1 — independent (different files):**
- [x] **T015** [P] [US2] Return discovery state without leaking credentials or stale catalogs · `backend/app/routers.py`
- [x] **T016** [P] [US2] Render selectors only for supported engine and language voice choices · `frontend/app.js`

**⟶ Wait for Wave 1 to finish, then:**
- [x] **T017** [US2] Preserve legacy speech defaults while rejecting failed discovery as legacy mode · `frontend/app.js`, `backend/app/routers.py`

Checkpoint: Discovery-enabled services show only supported choices and compatible legacy services remain usable.

## Phase 5: User Story 3 — Retain configuration across image replacement

Files: `backend/tests/test_config.py`, `frontend/README.md`, `frontend/compose.yaml`, `capabilities/frontend-serving/frontend-serving.spec.md`, `capabilities/speech-generation/speech-generation.spec.md`, `living-specs.yml`, `specs/README.md`

### Tests

- [x] **T018** [US3] Test reload, restart, replacement storage, corrupt file, and unwritable file behavior first · `backend/tests/test_config.py`

### Implementation

**Wave 1 — independent (different files):**
- [x] **T019** [P] [US3] Document exact path, permissions, initialization, precedence, and synthetic Compose volume · `frontend/README.md`, `frontend/compose.yaml`
- [x] **T020** [P] [US3] Update capability requirements, coverage mappings, living-spec index, and touches markers · `capabilities/frontend-serving/frontend-serving.spec.md`, `capabilities/speech-generation/speech-generation.spec.md`, `living-specs.yml`, `specs/README.md`

**⟶ Wait for Wave 1 to finish, then:**
- [x] **T021** [US3] Verify persisted settings are loaded by a fresh process with retained storage · `backend/app/config.py`, `backend/tests/test_config.py`

Checkpoint: Documented persistent storage retains a nondefault endpoint through reload, restart, and container replacement.

## Phase 6: Polish

**Wave 1 — independent (different files):**
- [x] **T022** [P] [US1] Add desktop and mobile keyboard browser evidence for configuration and playback · `frontend/tests/e2e/speech.spec.js`
- [x] **T023** [P] [US2] Add late-response and controlled-service switching evidence · `frontend/tests/e2e/engine-discovery.spec.js`
- [x] **T024** [P] [US3] Validate against Success Criteria — owned by the project's post-implement validation hook (no separate suite run)

## Dependencies & Execution Order

Setup blocks Foundational. Foundational blocks each user story. User Story 1 and User Story 2 share the routing boundary and run in order; User Story 3 follows persistence integration. Polish runs last. Within each phase, Wave 1 completes before the explicitly joined wave.
