# Implementation Tasks: VibeVoice Backend Integration

## Scale note

This plan spans about 24 files across the API, isolated model worker, memory
admission, release records, and target-host qualification. Keep the optional
worker boundary and deferred prototype cleanup visible throughout.

## Phase 1: Setup

**Wave 1 — independent (different files):**

- [x] **T001** [P] [US1] Create a separate optional worker project with pinned-runtime intent and no model download at startup · `backend/vibevoice_worker/pyproject.toml`
- [x] **T002** [P] [US4] Review VibeVoice source, model, voice-preset, and runtime terms and provenance; update the third-party inventory without implying release approval · `THIRD_PARTY_NOTICES.md`

**⟶ Wait for Wave 1 to finish, then:**

- [ ] **T003** [US1] Lock only the approved worker dependencies and verify the lock is reproducible without installing or downloading model assets · `backend/vibevoice_worker/uv.lock`

## Phase 2: Foundational

Files: `backend/app/config.py`, `backend/app/services.py`, `backend/app/vibevoice.py`, `backend/vibevoice_worker/worker.py`, `backend/tests/test_config.py`, `backend/tests/test_vibevoice.py`, `backend/tests/test_services.py`, `backend/tests/test_vibevoice_memory.py`, `backend/tests/test_speech_contract.py`, `backend/tests/test_vibevoice_startup.py`

### Tests

**Wave 1 — independent (different files):**

- [x] **T004** [P] [US4] Add failing tests for default-backend validation, disabled-worker behavior, and required measured worker/reserve budgets · `backend/tests/test_config.py`
- [x] **T005** [P] [US1] Add failing tests for one worker process, bounded JSON-lines messages, decoder-only loading, timeout, and complete process cleanup · `backend/tests/test_vibevoice.py`
- [x] **T006** [P] [US3] Add failing service tests for both backends, WAV/MP3 conversion, actual-backend reporting, and discarding partial output before one fallback · `backend/tests/test_services.py`
- [x] **T007** [P] [US2] Add failing resource tests for admission, reserve crossing, eviction, no reload while pressure remains, and recovery after capacity returns · `backend/tests/test_vibevoice_memory.py`
- [x] **T008** [P] [US3] Add failing cross-backend contract tests for authentication, request/output bounds, media types, cancellation, safe errors, and fallback metadata · `backend/tests/test_speech_contract.py`
- [x] **T009** [P] [US4] Add failing startup/readiness tests for missing VibeVoice assets and worker shutdown without blocking macOS speech · `backend/tests/test_vibevoice_startup.py`

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2 — independent (different files):**

- [x] **T010** [P] [US4] Add validated optional backend, worker, timeout, and explicit memory-budget settings; keep unavailable or unqualified VibeVoice fail-closed · `backend/app/config.py`
- [x] **T011** [P] [US1] Implement the isolated persistent worker protocol, load only the speech decoder and validated local assets, and return bounded WAV artifacts without runtime downloads · `backend/vibevoice_worker/worker.py`

**⟶ Wait for Wave 2 to finish, then:**
**Wave 3 — worker manager:**

- [x] **T012** [US2] Implement the single-worker manager, available-memory admission, bounded serialization, reserve monitoring, eviction by process termination, and safe failure reasons · `backend/app/vibevoice.py`

**⟶ Wait for Wave 3 to finish, then:**
**Wave 4 — service integration:**

- [x] **T013** [US3] Route synthesis through the selected backend, preserve the existing conversion and bounds, and return the actual backend while discarding partial output before at most one fallback · `backend/app/services.py`

**Checkpoint:** The isolated worker and service seam are bounded, testable, lazy, and fail closed when memory, runtime, or assets are unavailable.

## Phase 3: User Story 1 — Choose a speech backend and voice (P1)

Files: `backend/app/models.py`, `backend/app/routers.py`, `backend/tests/test_models.py`, `backend/tests/test_api.py`

**Goal:** A caller can use the configured default or select an enabled backend and a compatible reviewed voice.

**Independent Test:** Exercise the authenticated route with the configured default, explicit `macos-say`, VibeVoice, each reviewed voice, invalid voices, and language mismatches. Confirm the response reports the backend that actually generated the audio.

### Tests

**Wave 1 — independent (different files):**

- [x] **T014** [P] [US1] Add failing request-model tests for backend values, voice identifiers, language compatibility, and the English/German defaults · `backend/tests/test_models.py`
- [x] **T015** [P] [US1] Add failing route tests for configured defaults, request overrides, authentication before synthesis, and the actual-backend response header · `backend/tests/test_api.py`

### Implementation

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T016** [US1] Extend the request model with the backend selector and validated VibeVoice voice presets while preserving existing fields and limits · `backend/app/models.py`

**⟶ Wait for Wave 2 to finish, then:**
**Wave 3 — route integration:**

- [x] **T017** [US1] Pass the validated backend and voice through the existing authenticated route and expose the service's actual-backend result · `backend/app/routers.py`

**⟶ Wait for Wave 3 to finish, then:**

- [x] **T018** [US1] Run the focused request-model and route tests and confirm invalid requests are rejected before worker admission · `backend/tests/test_models.py`, `backend/tests/test_api.py`

**Checkpoint:** Backend selection and reviewed voice defaults work through the existing authenticated speech endpoint, with invalid voice choices rejected before synthesis.

## Phase 4: User Story 2 — Protect higher-priority inference workloads (P1)

Files: none; resource-policy code and deterministic tests are owned by Foundational.

**Goal:** VibeVoice does not load or remain resident when the configured reserve cannot be honored.

**Independent Test:** Cross the configured reserve during a VibeVoice request. Confirm the worker exits within the qualified bound, partial audio is discarded, the same request falls back to `say`, and subsequent requests do not reload the model while memory remains below the reserve.

### Tests

**Wave 1 — deterministic resource checks:**

- [x] **T019** [US2] Run the Foundational deterministic reserve, eviction, fallback, and recovery tests

### Implementation

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2 — target-host qualification:**

- [ ] **T020** [US2] On an operator-authorized qualified macOS host, use the existing `vm_stat` memory probe to measure the decoder-only worker peak, exercise reserve crossing during generation, and verify memory release, fallback, and no reload under sustained pressure. Keep VibeVoice disabled if the capacity signal or eviction behavior is not trustworthy · `backend/evaluation/vibevoice/inspection.py`

**Checkpoint:** A qualified reserve crossing evicts the worker and preserves higher-priority capacity; otherwise the deployment remains on `say`.

## Phase 5: User Story 3 — Preserve the existing speech service contract (P1)

Files: none; cross-backend contract tests are owned by Foundational.

**Goal:** Existing clients retain authentication, validation, cancellation, bounded requests, and playable MP3/WAV responses.

**Independent Test:** Run the contract suite against both backends and verify media types, size/time bounds, safe errors, actual-backend metadata, and the absence of partial audio after fallback.

### Tests

**Wave 1 — contract test run:**

- [x] **T021** [US3] Run the cross-backend contract tests authored in Foundational, including MP3/WAV responses, authentication, cancellation, limits, and fallback reporting

### Implementation

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2 — consumer contract review:**

- [x] **T022** [US3] Verify the tested public contract preserves existing limits and never exposes text, credentials, subprocess output, or private paths

**Checkpoint:** Both backends satisfy the existing public speech contract, and every response identifies the backend that produced its complete audio.

## Phase 6: User Story 4 — Operate VibeVoice without disrupting service startup (P2)

Files: `backend/app/main.py`

**Goal:** The API starts and remains ready for macOS speech when VibeVoice is disabled, missing, yielded, or unable to load.

**Independent Test:** Start the service with VibeVoice unavailable, synthesize with `say`, check readiness, and shut down with a worker resident. Confirm startup is non-blocking and shutdown releases the worker.

### Tests

**Wave 1 — pre-change startup check:**

- [x] **T023** [US4] Run the startup/readiness tests authored in Foundational against the current application lifecycle and retain the failing cases for the lifecycle change

### Implementation

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2 — lifecycle change:**

- [x] **T024** [US4] Add application-lifecycle cleanup for the optional worker and keep readiness dependent on the existing macOS prerequisites, not VibeVoice residency · `backend/app/main.py`

**⟶ Wait for Wave 2 to finish, then:**
**Wave 3 — startup verification:**

- [x] **T025** [US4] Re-run the Foundational startup, readiness, and shutdown tests with absent assets, disabled VibeVoice, and a resident worker

**Checkpoint:** Missing optional model assets or runtime never blocks startup or macOS speech readiness, and application shutdown releases a resident worker.

## Phase 7: Polish

Files: `backend/README.md`, `living-specs.yml`, `capabilities/backend-synthesis/backend-synthesis.spec.md`, `capabilities/backend-synthesis/backend-synthesis.coverage.md`, `capabilities/project-licensing/project-licensing.spec.md`, `capabilities/project-licensing/project-licensing.coverage.md`

**Wave 1 — independent (different files):**

- [x] **T026** [P] [US4] Document optional worker setup, backend selection, required memory budgets, fallback, and qualified-host limits · `backend/README.md`
- [x] **T027** [P] [US4] Register the API, worker, tests, and optional runtime files with the correct living capabilities · `living-specs.yml`
- [x] **T028** [P] [US1] Update backend-synthesis requirements and scenarios to match only implemented and verified behavior · `capabilities/backend-synthesis/backend-synthesis.spec.md`
- [x] **T029** [P] [US1] Map each changed backend-synthesis requirement to its focused test and state the evidence scope · `capabilities/backend-synthesis/backend-synthesis.coverage.md`
- [x] **T030** [P] [US4] Record the optional worker's license, provenance, and release gates without claiming legal approval · `capabilities/project-licensing/project-licensing.spec.md`
- [x] **T031** [P] [US4] Map the runtime inventory and licensing gates to their evidence, keeping unresolved review explicit · `capabilities/project-licensing/project-licensing.coverage.md`

**⟶ Wait for Wave 1 to finish, then:**

- [x] **T032** [US3] Run the complete backend suite, license-integrity test, and whitespace check · `backend/tests/`, `checks/tests/test_license_integrity.py`

**⟶ Wait for Wave 2 to finish, then:**

- [ ] **T033** [US4] Run the final target-host smoke and benchmark for both languages, both output formats, warm and cold latency, memory admission, eviction, fallback, and readiness; retain evidence needed for release review

**⟶ Wait for Wave 3 to finish, then:**

- [ ] **T034** [US4] Only after all tests and target-host checks pass, remove prototype-only deployment copies, the evaluator environment, and generated private review artifacts. Preserve aggregate ratings in `specs/001-vibevoice-evaluation/vibevoice-evaluation.spec.md`, preserve repository evaluator source, and retain model weights/cache if the integrated worker uses them · operator-managed evaluation deployment resources

## Dependencies & Execution Order

Setup blocks Foundational; Foundational blocks each user story. User Story 1
provides API selection before target-host memory qualification. User Story 2
must pass its reserve and eviction gate before VibeVoice is enabled. User Story
3 verifies the cross-backend contract. User Story 4 completes optional startup
and shutdown behavior. Polish documentation follows implementation, and
prototype cleanup is last, gated on the full suite and target-host smoke.

Wave order: Setup Wave 1 → Setup Wave 2; Foundational test Wave 1 → implementation
Wave 2 → worker-manager Wave 3 → service Wave 4; User Story 1 test Wave 1 →
model Wave 2 → route and focused validation Wave 3; User Story 2 deterministic
tests → target-host reserve qualification; User Story 3 contract-suite run →
contract confirmation; User Story 4 startup test → lifecycle implementation →
retest; Polish documentation Wave 1 → full suite Wave 2 → target-host smoke Wave
3 → gated cleanup Wave 4.
