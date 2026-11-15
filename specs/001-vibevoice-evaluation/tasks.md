# Tasks: Private VibeVoice Evaluation

## Phase 1: Setup

**Files:** `backend/evaluation/vibevoice/__init__.py`

**Wave 1: package boundary**
- [x] **T001** Create the isolated evaluator package without importing it from production application code · `backend/evaluation/vibevoice/__init__.py`

## Phase 2: Foundational

**Files:** `backend/evaluation/vibevoice/report.py`, `backend/evaluation/vibevoice/server.py`, `backend/tests/test_evaluation.py`

**Wave 1: test-first**
- [x] **T002** Write failing tests for report validation and atomic persistence, private output handling, loopback-only binding, origin/session checks, run-scoped API access, and safe audio lookup · `backend/tests/test_evaluation.py`

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2: report model**
- [x] **T003** Implement run, configuration, sample, measurement, blocker, rating, and decision records with atomic owner-only JSON persistence · `backend/evaluation/vibevoice/report.py`

**⟶ Wait for Wave 2 to finish, then:**
**Wave 3: local API**
- [x] **T004** Implement the run-scoped review server and validated rating, decision, report, and audio operations; enforce origin/session checks, confine result-ID audio lookup, and bind only to loopback · `backend/evaluation/vibevoice/server.py`

## Phase 3: User Story 1 - Compare speech quality (P1)

Files: `backend/evaluation/vibevoice/runner.py`, `backend/evaluation/vibevoice/listening.html`, `backend/tests/test_evaluation_comparison.py`

### Tests

**Wave 1: test-first**
- [x] **T005** [US1] Write failing tests for identical five-text English/German pairs, the existing authenticated baseline, approved adapters only, exact candidate identity, and incomplete or stopped runs · `backend/tests/test_evaluation_comparison.py`

### Implementation

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2: independent comparison components**
- [x] **T006** [P] [US1] Validate the five-text terms-checked manifest and implement paired baseline and approved-adapter execution with bounded subprocesses, exact configuration metadata, and explicit blockers · `backend/evaluation/vibevoice/runner.py`
- [x] **T007** [P] [US1] Add the private paired-listening page with configuration identity and individual rating and observation controls · `backend/evaluation/vibevoice/listening.html`

**Checkpoint:** The product owner can review paired samples and record per-sample ratings; unavailable comparisons remain explicitly incomplete.

## Phase 4: User Story 2 - Assess real-system feasibility (P1)

Files: `backend/evaluation/vibevoice/inspection.py`, `backend/tests/test_evaluation_inspection.py`

### Tests

**Wave 1: test-first**
- [x] **T008** [US2] Write failing tests for read-only machine and chosen-volume inspection, terms and approval blockers, and explicit missing resource measurements · `backend/tests/test_evaluation_inspection.py`

### Implementation

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2: inspection**
- [x] **T009** [US2] Implement read-only candidate-machine and chosen-volume inspection plus per-result footprint, peak-memory, and generation-time capture; report approval blockers and never download or install · `backend/evaluation/vibevoice/inspection.py`

**Checkpoint:** Each candidate machine can be assessed without modifying it, and every unavailable measurement or prerequisite has a reason.

## Phase 5: User Story 3 - Decide whether to retain the prototype (P2)

Files: `backend/evaluation/vibevoice/cli.py`, `backend/evaluation/vibevoice/summary.html`, `backend/evaluation/vibevoice/README.md`, `backend/tests/test_evaluation_web.py`

### Tests

**Wave 1: test-first**
- [x] **T010** [US3] Write failing tests for CLI inspect/run/serve behavior, the evidence summary, all four owner decisions, missing-data display, and the absence of an automatic rating threshold · `backend/tests/test_evaluation_web.py`

### Implementation

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2: independent review integration**
- [x] **T011** [P] [US3] Implement the operator CLI for inspection, explicitly approved evaluation runs, and loopback review, wiring completed components without authorizing downloads, installs, service changes, or production dependencies · `backend/evaluation/vibevoice/cli.py`
- [x] **T012** [P] [US3] Add the results and decision page with ratings, averages, observations, resource evidence, blockers, and recordable product-owner outcomes · `backend/evaluation/vibevoice/summary.html`

**⟶ Wait for Wave 2 to finish, then:**
**Wave 3: operator boundary**
- [x] **T013** [US3] Document setup, terms and approval gates, private output handling, local review, and how to disable or remove the prototype while preserving the existing speech method · `backend/evaluation/vibevoice/README.md`

**Checkpoint:** The owner can review the evidence, record a decision without a numeric pass threshold, and disable or remove the documented standalone prototype.

## Phase 6: Polish

**Files:** `capabilities/vibevoice-evaluation/vibevoice-evaluation.spec.md`, `capabilities/vibevoice-evaluation/vibevoice-evaluation.coverage.md`, `living-specs.yml`, `specs/README.md`

**Wave 1: implementation documentation**
- [x] **T014** [P] Write the living capability specification for the implemented isolated evaluator and its permission, privacy, and removal boundaries · `capabilities/vibevoice-evaluation/vibevoice-evaluation.spec.md`
- [x] **T015** [P] Map each evaluator requirement to its verifying tests and state which behavior is mocked rather than qualified on target hardware · `capabilities/vibevoice-evaluation/vibevoice-evaluation.coverage.md`

**⟶ Wait for Wave 1 to finish, then:**
**Wave 2: registry**
- [x] **T016** [P] Register the evaluator capability and its owned source and test paths · `living-specs.yml`
- [x] **T017** [P] Add the evaluator capability to the specification index · `specs/README.md`

**⟶ Wait for Wave 2 to finish, then:**
**Wave 3: single-owner validation**
- [x] **T018** Run `uv run pytest` from `backend/`, `python3 -m unittest discover -s checks/tests -v` from the repository root, and `git diff --check`; verify the Success Criteria and existing API contract, without running candidate models or performing target-machine changes · `backend/tests/test_api.py` (existing contract evidence)

## Dependencies & Execution Order

Setup precedes Foundational. Foundational precedes all story work. Story 1 and Story 2 are independently testable after Foundational; they are listed in priority order, but Story 2 has no technical dependency on Story 1. Story 3 follows both because its CLI and evidence view integrate their outputs. Polish follows all stories.

- Setup: Wave 1.
- Foundational: Wave 1 tests → Wave 2 report model → Wave 3 local API.
- Story 1: Wave 1 tests → Wave 2 runner and listening page in parallel.
- Story 2: Wave 1 tests → Wave 2 inspection.
- Story 3: Wave 1 tests → Wave 2 CLI and summary page in parallel → Wave 3 operator documentation.
- Polish: Wave 1 capability specification and coverage map in parallel → Wave 2 registry and index in parallel → Wave 3 validation.

Candidate-machine evaluations, model use, downloads, installations, service changes, and publication remain outside automated validation. Perform them only after the applicable terms are resolved and the operator explicitly approves the target action and destination.
