# Fish Speech Capacity Screening

**Screened**: 2026-11-16
**Host qualification**: blocked
**Candidate selection**: none
**Host inspection**: not authorized; not performed

## Upstream Guidance

| Candidate | Published guidance from the existing research | Qualification limit |
| --- | --- | --- |
| Drama 3 | At least 48 GB GPU memory with FP8; NVIDIA-only; Linux/WSL guidance | This does not establish any available host's capacity. Active parameter count is not the memory requirement. |
| S2-Pro | Requirements table lists at least 24 GB GPU memory; Docker section calls 24 GB recommended; NVIDIA/CPU paths and separate Intel/ROCm notes | The differing wording is preserved, not converted to a measured local minimum. CPU RAM, latency, and storage remain unknown. |

The existing research uses source revision
`0f8a12e8a651062fdee9c33a894bdccd3a8513f1`. It also records that Drama 3
excludes CPU, Apple MPS, and AMD ROCm and that compilation is unsupported on
Windows/macOS in the reviewed guide. None of this qualifies a native macOS
deployment or a laptop. No alternate runtime or platform port was investigated.

## Local Measurements

| Measurement | Status | Missing prerequisite |
| --- | --- | --- |
| Available storage | not measured | An authorized host and inspection scope |
| Available RAM | not measured | An authorized host and inspection scope |
| Available VRAM | not measured | An authorized host and inspection scope |
| Peak runtime memory | not measured | A permitted candidate and separately approved test |
| Higher-priority reserve | not measured | Operator-provided workload and reserve budget |
| Time to first audio | not measured | A permitted candidate, approved test, and timing target |
| Total synthesis time | not measured | A permitted candidate, approved test, and timing target |

Upstream streaming results on an H200 are not local measurements. No host
identity, private capacity snapshot, production configuration, or workload log
is included here.

## Required Inputs

- Q2: An accountable operator and explicit inspection/testing authority.
- Q3: The exact candidate and runtime artifacts, after applicable rights review.
- Q6: Authorized machines, inspection scope, capacity/reserve budgets, and timing
  limits under representative workload conditions.
- Q7: Permitted English/German comparison material and agreed acceptance criteria.

Questions refer to the [assessment](../../.specify/assessments/fish-speech/problem.md#open-questions).

## Stop Boundary

Host qualification remains blocked. Do not inspect a target host, download a
model, install a package, or run synthesis from this report. If documentary
guidance or later authorized evidence rules out the candidate, record the
blocker rather than buying hardware, porting a runtime, or expanding scope.

## Evidence

- [Existing platform and capacity research](../../.specify/assessments/fish-speech/research.md#languages-platforms-and-capacity)
  distinguishes vendor guidance from missing target-machine evidence.
- [Reviewed installation guide](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/install.md)
  identifies the source revision; this screening did not fetch it again.
- [Evaluation concept](../../.specify/assessments/fish-speech/concept.md#option-b---bounded-local-feasibility-evaluation)
  and [constitution](../../.specify/memory/constitution.md) require separate
  approval and preserve higher-priority workload and operational boundaries.
