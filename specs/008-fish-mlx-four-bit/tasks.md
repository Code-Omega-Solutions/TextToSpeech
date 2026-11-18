# Tasks: Fish Speech MLX 4-bit candidate

**Input**: `specs/008-fish-mlx-four-bit/` design documents

## Phase 1: Setup

- [X] T001 Pin optional Apple Silicon MLX dependencies in an isolated candidate manifest under `backend/deployment/`

## Phase 2: Foundational

- [X] T002 Define strict Fish 1.5 configuration and tensor compatibility validation in `backend/deployment/fish_mlx/`
- [X] T003 Define separate candidate provenance and approval binding in `backend/deployment/fish_mlx/APPROVAL.md`

## Phase 3: User Story 1 - Prepare an approved candidate (P1)

**Goal**: Convert the approved semantic checkpoint into real packed 4-bit MLX weights without changing approved trees.

**Independent test**: Convert and strictly reload an approved checkpoint in isolation; reject incompatible, missing or tampered inputs.

- [X] T004 [US1] Add focused conversion, strict load and tampering tests in `backend/tests/test_fish_mlx_conversion.py`
- [X] T005 [US1] Implement offline deterministic conversion and metadata in `backend/deployment/fish_mlx/`
- [X] T006 [US1] Implement exact separate approval validation binding source, checkpoint, codec, references, runtime and derived artifacts in `backend/deployment/fish_mlx/`
- [X] T007 [US1] Implement Fish 1.5 MLX DualAR layers, cache, sampling and strict quantized loading in `backend/deployment/fish_mlx/`
- [X] T008 [US1] Verify native conversion and numerical compatibility on authorized Apple Silicon in `specs/008-fish-mlx-four-bit/quickstart.md`

## Phase 4: User Story 2 - Opt in without disrupting native speech (P1)

**Goal**: Integrate the candidate into the existing managed lifecycle and public speech contract.

**Independent test**: Exercise explicit dispatch, transport, preload and failure with unchanged native fallback.

- [X] T009 [US2] Add candidate dispatch, transport, lifecycle and fallback tests in `backend/tests/test_fish_process.py` and `backend/tests/test_fish_worker_launcher.py` (mocked transport and failure; native WAV remains separately gated)
- [X] T010 [US2] Bridge approved Fish tokenizer, prompt, references and Firefly codec to MLX generation and MessagePack/WAV transport in `backend/deployment/fish_mlx/`
- [X] T011 [US2] Add explicit opt-in managed launch selection and candidate validation in `backend/app/config.py` and `backend/deployment/fish_worker_launcher.py`
- [ ] T012 [US2] Validate approved-reference isolated native synthesis without touching production in `specs/008-fish-mlx-four-bit/quickstart.md`

## Phase 5: User Story 3 - Qualify the candidate (P2)

**Goal**: Separate actual native evidence from unverified performance, quality and rights.

**Independent test**: Review synchronized measurements and explicit qualification gates without implying deployment approval.

- [X] T013 [US3] Document conversion, approvals, activation, isolation and unresolved quality and rights gates in `specs/008-fish-mlx-four-bit/quickstart.md`
- [ ] T014 [US3] Record only authorized synchronized hardware measurements and limitations in `specs/008-fish-mlx-four-bit/quickstart.md`

## Phase 6: Polish & cross-cutting concerns

- [X] T015 Update affected requirements and coverage mappings in `capabilities/backend-synthesis/`
- [X] T016 Run focused regression checks and review the resulting changes in `backend/tests/`

## Dependencies & execution order

T001 precedes native runtime work; T002 and T003 precede US1. US2 depends on US1's runtime and approval; US3 depends on real evidence from US1 and US2. T015 and T016 follow implementation.

## Parallel opportunities

US1 conversion tests and runtime design may proceed independently after foundational contracts. US2 regression tests can be designed independently of the transport bridge. US3 documentation can be drafted independently but evidence must await actual execution.

## Implementation strategy

MVP is US1's genuinely convertible and loadable approved model; proceed to US2 for end-to-end synthesis and US3 for qualification. Do not deploy.
