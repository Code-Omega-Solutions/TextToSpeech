# Tasks: Publishable macOS speech backend

The recovered service is a starting point, not proof of the proposed behavior.
Native qualification and publication require separate authorization and review.
Use the Companion writer to close completed tasks; do not edit checkboxes by hand.

## Phase 1: Setup

No separate scaffolding is needed. The existing Python and frontend projects
provide the dependency manifests and test runners.

## Phase 2: Foundational

Files: `backend/app/config.py`, `backend/app/models.py`,
`backend/tests/test_config.py`, `backend/tests/test_models.py`

**Wave 1: independent tests**

- [x] **T001** [P] Add failing tests for exclusive environment/protected-file credentials, permissions, invalid settings and bounded temporary-disk configuration (FR-015, FR-019, FR-021) · `backend/tests/test_config.py`
- [x] **T002** [P] Add failing request-model tests for exact 5,000 UTF-16 units, supplementary characters, lone surrogates, supported fields, aliases and finite speed (FR-011, FR-012; SC-005) · `backend/tests/test_models.py`

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2: independent implementation**

- [x] **T003** [P] Implement validated settings, exclusive credential sources, protected-file checks and resource limits without exposing secrets (FR-015, FR-019, FR-021) · `backend/app/config.py`
- [x] **T004** [P] Implement speech request validation and UTF-16-unit counting while preserving the existing contract (FR-011, FR-012; SC-005) · `backend/app/models.py`

## Phase 3: User Story 1 - Diagnose without changes (P1)

Files: `backend/prerequisites.py`, `backend/tests/test_prerequisites.py`

**Goal:** Inspect supported platform, dependencies and configuration without
changing the host or importing the service.

**Independent Test:** Run the checker with mocked supported, missing,
incompatible, timeout and unsupported-platform conditions; assert no mutations.

### Tests

**Wave 1:**

- [x] **T005** [US1] Add failing mocked tests for every diagnostic item, read-only behavior, safe output, exit 0/1/2, timeouts and optional UK voice (FR-001-003, FR-007-008; SC-001-002) · `backend/tests/test_prerequisites.py`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation

**Wave 2:**

- [x] **T006** [US1] Implement standalone bounded, noninteractive human/JSON inspection of OS, architecture, say, Python, environment tooling, ffmpeg codecs, voices, configuration, credential access, destination, disk and port without writes or synthesis (FR-001-003, FR-007-008; SC-001-002) · `backend/prerequisites.py`

**Checkpoint:** Check-only reports named blockers and never installs.

## Phase 4: User Story 2 - Install missing prerequisites safely (P1)

Files: `backend/setup.py`, `backend/tests/test_setup.py`

**Goal:** Present and explicitly approve safe, serialized installation changes.

**Independent Test:** Use isolated mocked destinations and injected failures to
verify consent, idempotency, interruption safety and manual voice instructions.

### Tests

**Wave 1:**

- [x] **T007** [US2] Add failing setup tests for explicit acceptance, approval boundaries, lock contention, incompatible environments, failure recovery, verification, no credential overwrite and repeat no-op (FR-004-009; SC-003, SC-007) · `backend/tests/test_setup.py`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation

**Wave 2:**

- [x] **T008** [US2] Implement explicit install planning, destination locking, approved package-manager/locked environment setup, verification and accurate partial/manual results without escalation or modifying existing installations (FR-004-009, FR-019; SC-003, SC-007) · `backend/setup.py`

**Checkpoint:** An approved isolated setup is repeatable and failed work
preserves prior environments, credentials and services.

## Phase 5: User Story 3 - Generate speech through frontend (P1)

Files: `backend/app/main.py`, `backend/app/routers.py`,
`backend/app/services.py`, `backend/app/voices.py`, `backend/app/language.py`,
`backend/tests/test_api.py`, `backend/tests/test_services.py`,
`backend/tests/test_voices.py`, `backend/tests/test_language.py`,
`frontend/config/upstream.js`, `frontend/vite.config.js`,
`frontend/docker/default.conf.template`, `frontend/docker/entrypoint.sh`,
`frontend/Dockerfile`, `frontend/compose.yaml`, `frontend/.env.example`,
`frontend/tests/config.test.js`, `frontend/tests/dev.test.js`,
`frontend/tests/docker.test.js`

**Goal:** Preserve the browser journey and provide authenticated, bounded,
private speech generation through both proxy implementations.

**Independent Test:** Run mocked backend and proxy integrations with fixture
audio and synthetic credentials; do not rely on a production Mac.

### Tests

**Wave 1: independent tests**

- [x] **T009** [P] [US3] Add failing API tests for bearer challenge, fixed routes, streaming 32 KiB boundaries including chunked/false lengths, safe errors and audio response metadata (FR-010-012, FR-015, FR-018; SC-004-006) · `backend/tests/test_api.py`
- [x] **T010** [P] [US3] Add failing synthesis tests for encoding, sentence/paragraph segmentation, 100 segments, capacity, shared deadline, temporary budget, cancellation, owned-child termination and cleanup (FR-014-016; SC-004, SC-007) · `backend/tests/test_services.py`
- [x] **T011** [P] [US3] Extend voice and language tests for required/optional voices, aliases, detection boundaries and unsupported languages (FR-008, FR-013; SC-004) · `backend/tests/test_voices.py`, `backend/tests/test_language.py`
- [x] **T012** [P] [US3] Add Vite proxy tests for server-only secrets, header replacement, allowlisted routes and exact streaming body bounds (FR-012, FR-020; SC-005-006, SC-008) · `frontend/tests/config.test.js`, `frontend/tests/dev.test.js`
- [x] **T013** [P] [US3] Add container proxy tests for read-only secret file, header replacement, routing, request limits and absence of secrets in assets/logs (FR-012, FR-020; SC-005-006, SC-008) · `frontend/tests/docker.test.js`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation

**Wave 2: independent implementation**

- [x] **T014** [P] [US3] Enforce streamed request bounds and safe HTTP logging before routing (FR-012, FR-022) · `backend/app/main.py`
- [x] **T015** [P] [US3] Implement bounded subprocess lifetime, temporary-disk enforcement, cancellation and cleanup while preserving encoding and segmentation (FR-014-016; SC-004, SC-007) · `backend/app/services.py`
- [x] **T016** [P] [US3] Preserve correct voice inventory and explicit/automatic locale behavior including optional UK voice (FR-008, FR-013) · `backend/app/voices.py`, `backend/app/language.py`
- [x] **T017** [P] [US3] Implement development/preview proxy secret sourcing, safe header replacement, fixed route filtering and streamed body enforcement without exposing secrets to the browser (FR-012, FR-020-022) · `frontend/config/upstream.js`, `frontend/vite.config.js`
- [x] **T018** [P] [US3] Implement container secret-file integration, private runtime configuration, header replacement and 32 KiB limits while preserving loopback exposure (FR-012, FR-020-022) · `frontend/docker/default.conf.template`, `frontend/docker/entrypoint.sh`, `frontend/Dockerfile`, `frontend/compose.yaml`, `frontend/.env.example`

**⟶ Wait for Wave 2 to finish, then:**

**Wave 3: integration**

- [x] **T019** [US3] Integrate fail-closed authentication, binary speech responses and distinct liveness/readiness with verified codecs and required voices (FR-010, FR-015, FR-017-018, FR-022) · `backend/app/routers.py`

**Checkpoint:** Mocked browser-to-proxy-to-backend requests preserve the API,
protect credentials and enforce both exact limits.

## Phase 6: User Story 4 - Operate and diagnose (P2)

Files: `backend/service/com.example.texttospeech.plist`,
`backend/tests/test_service_example.py`

**Goal:** Provide an opt-in portable per-user service example with no secret in
arguments or service definition.

**Independent Test:** Check the example and startup instructions in isolation;
do not register or start a service.

### Tests

**Wave 1:**

- [x] **T020** [US4] Add tests for a portable service example, safe credential references and absence of embedded secrets or host-specific paths (FR-023; SC-006) · `backend/tests/test_service_example.py`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation

**Wave 2:**

- [x] **T021** [US4] Provide a per-user service example with operator-selected paths, safe PATH and protected credentials, without automatic registration (FR-023) · `backend/service/com.example.texttospeech.plist`

**Checkpoint:** An operator can review and deliberately configure the example
without changing a live service.

## Phase 7: User Story 5 - Publish and reproduce (P2)

Files: `backend/README.md`, `frontend/README.md`, `THIRD_PARTY_NOTICES.md`,
`specs/README.md`, `checks/tests/test_license_integrity.py`

**Goal:** Document reproduction, operational recovery, explicit removals and
truthful release and qualification gates.

**Independent Test:** Review clean-checkout setup and run existing public
content/license checks without production credentials.

### Tests

**Wave 1:**

- [x] **T022** [US5] Extend publication checks for changed distribution notices and explicit legal/release gate integrity without suppressing findings (FR-024-027; SC-006, SC-009) · `checks/tests/test_license_integrity.py`

**⟶ Wait for Wave 1 to finish, then:**

### Implementation

**Wave 2: independent documentation**

- [x] **T023** [P] [US5] Document fresh/partial setup, check-only, approval, rerun, failure recovery, credentials, voices, service example, removal and native qualification limits (FR-001-009, FR-019, FR-023-024, FR-027) · `backend/README.md`
- [x] **T024** [P] [US5] Document proxy secret-file/environment setup, loopback and separate TLS/access-control boundaries without real credentials (FR-020-022, FR-024) · `frontend/README.md`
- [x] **T025** [P] [US5] Update dependency notices and feature index accurately while retaining legal, source-rights and history-review release gates (FR-025-026; SC-009) · `THIRD_PARTY_NOTICES.md`, `specs/README.md`

**Checkpoint:** A contributor can reproduce the mocked checks and see the
unresolved native, legal and publication gates.

## Phase 8: Polish and validation

Files: `capabilities/backend-synthesis/backend-synthesis.spec.md`,
`capabilities/backend-synthesis/backend-synthesis.coverage.md`,
`capabilities/frontend-serving/frontend-serving.spec.md`,
`capabilities/frontend-serving/frontend-serving.coverage.md`,
`living-specs.yml`, `specs/001-macos-backend/spec.md`

**Wave 1:**

- [x] **T026** Update affected living requirements, coverage and registry through the Companion review/fold process, reflecting actual changes rather than unverified claims · `capabilities/backend-synthesis/backend-synthesis.spec.md`, `capabilities/backend-synthesis/backend-synthesis.coverage.md`, `capabilities/frontend-serving/frontend-serving.spec.md`, `capabilities/frontend-serving/frontend-serving.coverage.md`, `living-specs.yml`, `specs/001-macos-backend/spec.md`

**⟶ Wait for Wave 1 to finish, then:**

**Wave 2:**

- [x] **T027** Run the repository's backend mocked suite, frontend tests/build, applicable release checks and exact SC-001-009 boundary checks; record unavailable Docker/native checks and never claim macOS qualification from Linux · `specs/001-macos-backend/spec.md`

## Dependencies & Execution Order

Setup precedes foundational tests and implementation. Story phases follow the
foundation and are ordered US1, US2, US3, US4 and US5; US2 consumes US1's
checker. Each story's test wave precedes its implementation waves. Polish
follows all stories, and validation follows living-spec reconciliation.
