# Tasks: Headroom-First Fish Enablement

**Input**: [plan.md](plan.md), [spec.md](spec.md), research, data model and contracts.
**Tests**: Required by SC-006/007. No native qualification is inferred from mocks.

## Phase 1: Setup

- [x] T001 Record the approved 12 GiB reserve/16 GiB budget and smaller-family evidence, including conflicting tagged license statements, in specs/007-fish-backend-enablement/research.md.

## Phase 2: Foundation

- [x] T002 Add opt-in configuration tests in backend/tests/test_config.py, including invalid argv, missing managed command, and minimum two synthesis permits; implement frozen settings/env mapping in backend/app/config.py.
- [x] T003 Extract shared available/resident-memory probes into backend/app/memory.py without changing historical backend/app/vibevoice.py probe imports or tests.

## Phase 3: US1 - Approve a Feasible Runtime (P1)

**Independent test**: Exact artifacts/terms, authenticated launcher, capacity and
operator approval documented before installation. This gate can remain blocked
without blocking model-independent US3 policy work.

- [ ] T004 [US1] Resolve exact pinned smaller Fish checkpoint/codec/runtime terms and macOS compatibility in specs/007-fish-backend-enablement/research.md; do not download or enable before approval.

## Phase 4: US2 - Bilingual Voices (P1)

**Independent test**: Four approved combinations pass reference and listening
review, independent of lifecycle mocks.

- [ ] T005 [US2] Review local bilingual male/female reference provenance and permissions, including Thorsten's original WAV/transcript candidate, in specs/007-fish-backend-enablement/research.md; keep private recordings/consent outside git.
- [ ] T006 [US2] After T004/T005, integrate the approved launcher and references with backend/app/fish_speech.py, verify the authenticated MessagePack/WAV contract, and expose only qualified voices in backend/app/services.py.

## Phase 5: US3 - Preserve Native Speech and Headroom (P2)

**Independent test**: Resource simulations return language-correct native
fallback, terminate only owned processes and preserve strict default behavior.

- [x] T007 [US3] Write failing lifecycle tests in backend/tests/test_fish_process.py for admission, busy requests, loading/active/idle pressure, probe failure, cancellation, cooldown, idle expiry, verified cleanup and shutdown; implement backend/app/fish_process.py with one neural permit, 0.25-second monitor, low-priority owned process session, 30-second idle/cooldown and offline child environment.
- [x] T008 [US3] Write failing fallback tests in backend/tests/test_engines.py for German/English, disabled/legacy/busy engine, ignored voice, shared deadline, cancellation, size errors and explicit native dispatch; integrate backend/app/services.py, backend/app/routers.py and shutdown cleanup in backend/app/main.py.
- [x] T009 [US3] Add API-level fallback/authentication/invalid-input checks in backend/tests/test_api.py and run focused backend tests.
- [ ] T010 [US3] After T004/T006 and separate rollout approval, follow specs/007-fish-backend-enablement/quickstart.md on the isolated native prototype; measure real memory, deadline and all four voices, verify existing services and rollback without modifying production. Iteration 9 corrected stale startup by exact-label disablement plus non-`.plist` quarantine, added a bounded unload wait, and verified managed recreation/rollback and production preservation. Exact Fish approvals, live neural lifecycle, and four outputs remain open.

## Phase 6: Documentation and Integration

- [x] T011 Update backend/README.md, capabilities/backend-synthesis/backend-synthesis.spec.md, capabilities/backend-synthesis/backend-synthesis.coverage.md, living-specs.yml and specs/README.md for the implemented opt-in policy and explicit deployment gates.
- [x] T012 Run focused and directly affected regression checks from backend/tests/, inspect git diff for private data/unrelated edits, and record actual results in specs/007-fish-backend-enablement/quickstart.md without claiming native qualification.

**Open gates**: T004 has fixed historical private prototype hashes and a
recorded local runtime/codec probe, but the exact approval manifest and
authoritative artifact-term acceptance remain open. The repository launcher
now fails closed without that manifest. T005 has no approved bilingual identity
or cloning consent, so no reference IDs are advertised. T006 has a tested
MessagePack/WAV adapter and lifecycle boundary, but qualified reference
approval and actual Fish output remain open. T010 has historical admission denial and language-preserving native fallback
evidence. Iteration 9 additionally verified exact stale-definition quarantine,
persisted disablement, bounded unload, managed prototype/UI recreation and
rollback evidence, UI isolation/persistence, and production before/after checks.
Neural success, full native lifecycle qualification, and the four consented
voices remain unverified. Keep these four tasks open; the feature is not
complete.

## Dependencies and Execution Order

T001 -> T002/T003 -> T007 -> T008 -> T009 -> T011 -> T012.
T004 depends on T001 and exact external artifact evidence; T005 can be researched
independently. T006 depends on T004/T005. T010 depends on T004/T006 and T012
plus separate deployment approval. Unresolved installation gates must stay open;
do not mark the feature complete.

## Parallel Opportunities

After T001, config tests (T002) and probe extraction (T003) touch separate files.
US1 artifact review and US2 reference review are independent; US3 local policy
does not install either and can proceed while these are blocked.

## Implementation Strategy

Deliver bounded native-fallback policy locally first. Retain the current strict
default and keep Fish disabled on live services. Complete artifact and reference
review before launcher integration, then seek/observe deployment authorization
and native evaluation. This is deliberately not a claim that US1/US2 are done.
