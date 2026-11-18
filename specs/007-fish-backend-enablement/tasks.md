# Tasks: Headroom-First Fish Enablement

**Input**: [plan.md](plan.md), [spec.md](spec.md), research, data model and contracts.
**Tests**: Required by SC-006/007. No native qualification is inferred from mocks.

## Phase 1: Setup

- [x] T001 Record the approved 12 GiB reserve/16 GiB budget and exact smaller-family artifact evidence, including the model-weight license and noncommercial gate, in specs/007-fish-backend-enablement/research.md.

## Phase 2: Foundation

- [x] T002 Add opt-in configuration tests in backend/tests/test_config.py, including invalid argv, missing managed command, and minimum two synthesis permits; implement frozen settings/env mapping in backend/app/config.py.
- [x] T003 Extract shared available/resident-memory probes into backend/app/memory.py without changing historical backend/app/vibevoice.py probe imports or tests.

## Phase 3: US1 - Approve a Feasible Runtime (P1)

**Independent test**: Exact artifacts/terms, authenticated launcher, capacity
and operator approval documented before managed inference. This gate can remain
blocked without blocking model-independent US3 policy work.

- [x] T004 [US1] Review the exact Fish source commit and its two local modifications; verify the model/decoder files, runtime entrypoint and terms against the pinned revisions; produce a clean, hash-bound private approval manifest only after targeted tests pass. Record findings in specs/007-fish-backend-enablement/research.md; do not start a managed worker until complete.

## Phase 4: US2 - Language-Specific Voices (P1)

**Independent test**: Four approved combinations pass reference and listening
review, independent of lifecycle mocks.

- [x] T005 [US2] Select one exact German and one exact English Common Voice Spontaneous 5.0 clip for each dataset-declared gender category; review audio quality, transcript, duration and applicable terms; prepare private WAV/`.lab` pairs and hash-bound approvals without retaining contributor IDs in logs or Git.
- [x] T006 [US2] After T004/T005, integrate the approved launcher and four references with backend/app/fish_speech.py, verify the authenticated MessagePack/WAV contract, and expose only qualified voices in backend/app/services.py and the frontend catalog UI. The UI's four friendly voice labels and machine-generated disclosure are implemented, but no unapproved voice is advertised. All four short authenticated selections now return actual managed Fish WAV without fallback under the separately approved startup allowance. Keep generated-output sharing disabled until the MDC personal-data condition is resolved.

## Phase 5: US3 - Preserve Native Speech and Headroom (P2)

**Independent test**: Resource simulations return language-correct native
fallback, terminate only owned processes and preserve strict default behavior.

- [x] T007 [US3] Write failing lifecycle tests in backend/tests/test_fish_process.py for admission, busy requests, loading/active/idle pressure, probe failure, cancellation, cooldown, idle expiry, verified cleanup and shutdown; implement backend/app/fish_process.py with one neural permit, 0.25-second monitor, low-priority owned process session, 30-second idle/cooldown and offline child environment.
- [x] T008 [US3] Write failing fallback tests in backend/tests/test_engines.py for German/English, disabled/legacy/busy engine, ignored voice, shared deadline, cancellation, size errors and explicit native dispatch; integrate backend/app/services.py, backend/app/routers.py and shutdown cleanup in backend/app/main.py.
- [x] T009 [US3] Add API-level fallback/authentication/invalid-input checks in backend/tests/test_api.py and run focused backend tests.
- [ ] T010 [US3] After T004/T006 and separate rollout approval, follow specs/007-fish-backend-enablement/quickstart.md on the isolated native prototype; measure real memory, deadline and all four voices, verify existing services and rollback without modifying production. Keep shared output disabled unless the MDC personal-data condition is resolved. The authorized private cutover, four catalog entries, native fallback and UI/production preservation checks pass. Four actual short Fish outputs, sampled reserve/RSS and idle listener/child-session absence now pass under the approved optimistic startup trial. Broader native pressure/cancellation/restart/quality and exact-current rollback qualification remain open.

## Phase 6: Documentation and Integration

- [x] T011 Update backend/README.md, capabilities/backend-synthesis/backend-synthesis.spec.md, capabilities/backend-synthesis/backend-synthesis.coverage.md, living-specs.yml and specs/README.md for the implemented opt-in policy and explicit deployment gates.
- [x] T012 Run focused and directly affected regression checks from backend/tests/, inspect git diff for private data/unrelated edits, and record actual results in specs/007-fish-backend-enablement/quickstart.md without claiming native qualification.
- [x] T013 Implement the operator-authorized optional startup allowance in backend/app/config.py and backend/app/fish_process.py with focused configuration/boundary tests; retain conservative defaults and unchanged runtime reserve/RSS monitoring, deploy 4 GiB startup allowance privately, and record actual short-request inference observations in quickstart.md.

**Open gates**: T004/T005 are complete for operator-authorized private
evaluation: the exact clean patched source and five checkpoint files pass the
launcher binding, 132 targeted tests now pass natively, and the operator approved
all four converted references after listening and transcript review. The private
prototype/UI now advertise the four approved IDs and use the shared protected
backend credential. T006 now has actual four-way authenticated managed Fish WAV
evidence. T013 changes only startup admission under explicit operator approval:
4 GiB allowance plus 12 GiB reserve, retaining 16 GiB runtime RSS ceiling.
T010 remains open for broader native lifecycle and subjective quality,
long-input peaks and current rollback. Short-request sampling observed at least
13.08 GiB available and peak 3.00 GiB owned-group RSS; it is not hard physical
memory isolation or a measured worst-case peak. Generated-output sharing
remains separately gated on the MDC personal-data restriction. The feature
remains incomplete; no running reserve/RSS ceiling or unrelated workload was changed.

## Dependencies and Execution Order

T001 -> T002/T003 -> T007 -> T008 -> T009 -> T011 -> T012.
T004 depends on T001 and exact external artifact evidence; T005 can proceed
independently using the accepted dataset terms and private archives. T006
depends on T004/T005. T010 depends on T004/T006 and T012 plus separate
deployment approval. Unresolved installation or output-sharing gates must stay
open; do not mark the feature complete.
T013 follows T007/T004/T005 and the explicit operator startup-policy revision.

## Parallel Opportunities

After T001, config tests (T002) and probe extraction (T003) touch separate files.
US1 artifact review and US2 reference review are independent; US3 local policy
does not install either and can proceed while these are blocked.

## Implementation Strategy

Deliver bounded native-fallback policy locally first and retain the strict
default for existing deployments. Artifact/reference review and separate
authorization now permit the isolated private prototype's opt-in configuration,
not changes to production. Complete native evaluation only with admitted
headroom; keep external output sharing gated until its terms are resolved.
Configuration and reference approval do not establish US2 neural-output quality.
