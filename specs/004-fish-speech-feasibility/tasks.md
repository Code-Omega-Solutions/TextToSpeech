# Tasks: Fish Speech Documentary Feasibility

## Setup

- [x] **T001** Add five reader-facing documentary checks + specs/004-fish-speech-feasibility/verify.py

## User Story 1 - Permission findings

- [x] **T002** Record sourced permission findings and missing approvals + specs/004-fish-speech-feasibility/permission-screening.md
- [x] **T003** Run FR-001 permission-separation check + specs/004-fish-speech-feasibility/verify.py

## User Story 2 - Capacity findings

- [x] **T004** Record upstream guidance separately from unavailable local measurements + specs/004-fish-speech-feasibility/capacity-screening.md
- [x] **T005** Run FR-002 capacity/qualification check + specs/004-fish-speech-feasibility/verify.py

## User Story 3 - Honest outcome

- [x] **T006** Record blocked outcome, both languages, and questions Q1-Q8 + specs/004-fish-speech-feasibility/outcome.md
- [x] **T007** Run FR-003 outcome-completeness check + specs/004-fish-speech-feasibility/verify.py
- [x] **T008** Run FR-004 withheld-operations check + specs/004-fish-speech-feasibility/verify.py
- [x] **T009** Run FR-005 evidence/scope check + specs/004-fish-speech-feasibility/verify.py

## Polish

- [x] **T010** Register the feature and run documentary and repository integrity checks + specs/README.md

Execute in order. Each story's checks depend on its report; the outcome depends
on both screening reports. A passing document check does not qualify a model.
