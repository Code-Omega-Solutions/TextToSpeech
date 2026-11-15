# Private VibeVoice evaluation - Living Spec

> [DRAFT] Describes the isolated evaluator and mocked evidence. It does not
> qualify candidate models or target hardware.

## Purpose

Offer an optional, local way to assess the two identified VibeVoice variants
against the existing authenticated speech endpoint without changing production
speech behavior.

## Requirements

### The evaluator remains isolated and removable
<!-- touches: backend/evaluation/vibevoice/**, backend/tests/test_evaluation*.py -->

The evaluator SHALL remain outside the production application and SHALL add no
production speech route, model dependency, automatic fallback, or service
lifecycle behavior. Operators can disable it by not invoking its module and can
remove its package and evaluator-only tests without changing the existing
speech method.

#### Scenario: the prototype is not invoked
- **WHEN** an operator does not invoke the evaluator module
- **THEN** the existing speech application continues to use its existing route and configuration.

#### Scenario: the prototype is removed
- **WHEN** the evaluator package and its evaluator-only tests are removed
- **THEN** the production speech route and service configuration remain unchanged.

### Terms and sample permission gate each use
<!-- touches: backend/evaluation/vibevoice/runner.py, backend/evaluation/vibevoice/inspection.py, backend/tests/test_evaluation_comparison.py, backend/tests/test_evaluation_inspection.py -->

Each manifest SHALL identify exactly five unique sample texts per evaluated
language, their attribution and sample-text authorization, and the applicable
voice, model, implementation, and dependency authorizations. Unresolved or
denied permission blocks the affected use. No model or adapter is substituted
silently.

#### Scenario: a manifest contains an unresolved sample-text permission
- **WHEN** the evaluation encounters the affected sample
- **THEN** it records blocked paired results and does not send the text to the baseline or adapter.

#### Scenario: a language sample count is not exactly five
- **WHEN** a manifest has fewer or more than five unique samples for a language
- **THEN** manifest validation rejects it before generation.

### Comparisons use the existing baseline and approved candidates
<!-- touches: backend/evaluation/vibevoice/runner.py, backend/tests/test_evaluation_comparison.py -->

The baseline SHALL use the existing authenticated local speech endpoint. Candidate
execution SHALL use only explicitly registered, already-installed adapters for
`VibeVoice-TTS-1.5B` or `VibeVoice-Realtime-0.5B`. Adapter processes run without a
shell, within a timeout and audio-output limit, and receive no baseline
credential. A failure, cancellation, unavailable comparison, or limit SHALL be
reported with a reason.

#### Scenario: a baseline comparison completes
- **WHEN** the local authenticated endpoint is available and the sample is permitted
- **THEN** the baseline result uses the same sample ID as each feasible candidate result and records generation time.

#### Scenario: an adapter exceeds its time or output bound
- **WHEN** an approved adapter exceeds the configured timeout or audio-size limit
- **THEN** the run stops and the result is incomplete or failed without publishing partial audio.

### Feasibility inspection is read-only and records unknowns
<!-- touches: backend/evaluation/vibevoice/inspection.py, backend/evaluation/vibevoice/runner.py, backend/tests/test_evaluation_inspection.py, backend/tests/test_evaluation_comparison.py -->

Inspection SHALL record the selected machine, platform, chosen storage volume,
available storage and memory, inspection time, and explicit blockers. It SHALL
not download or install software, change a service, or run a candidate model.
Installed footprint and peak memory remain absent with a reason unless a trusted
measurement is available. Generation time is recorded per completed result.
Target-machine changes and evaluation execution require separate explicit
approval.

#### Scenario: a chosen volume or resource cannot be measured
- **WHEN** a read-only probe cannot obtain a storage or memory value
- **THEN** the report leaves the value absent and records why it is unavailable.

#### Scenario: candidate permission or run approval is unresolved
- **WHEN** inspection identifies an unresolved permission or missing execution approval
- **THEN** it reports the blocker and performs no model execution or target-machine change.

### Reports and review remain private to one local run
<!-- touches: backend/evaluation/vibevoice/report.py, backend/evaluation/vibevoice/server.py, backend/evaluation/vibevoice/listening.html, backend/evaluation/vibevoice/summary.html, backend/tests/test_evaluation.py, backend/tests/test_evaluation_web.py -->

Reports and audio SHALL be stored in owner-only locations. The review server
binds only to loopback, uses same-origin and run-scoped authorization for API
operations, resolves audio by completed result ID, and omits filesystem paths
from API responses. The review pages display paired results, individual
ratings, observations, averages, measurements, and reasons for missing data.

#### Scenario: a report request omits its session token or uses another origin
- **WHEN** a caller attempts a protected report mutation without matching run authorization
- **THEN** the server rejects the request.

#### Scenario: a caller requests audio by an arbitrary path
- **WHEN** an audio request names anything other than a completed result ID
- **THEN** the server returns no audio.

### Product-owner decisions are recorded without a score threshold
<!-- touches: backend/evaluation/vibevoice/report.py, backend/evaluation/vibevoice/server.py, backend/evaluation/vibevoice/summary.html, backend/tests/test_evaluation.py, backend/tests/test_evaluation_web.py -->

The product owner can record `retain`, `partially_retain`, `remove`, or
`seek_alternative` with a rationale. Rating averages are descriptive evidence
and SHALL NOT choose or imply a decision automatically.

#### Scenario: the owner records an outcome
- **WHEN** the owner submits one of the four supported outcomes and a rationale
- **THEN** the report persists that decision without applying a numeric pass threshold.

## Evidence boundary

The evaluator tests use deterministic baseline and process fakes, injected
machine and volume probes, and temporary owner-only directories. They do not
download or run candidate models, inspect or modify target machines, publish
results, or establish native platform feasibility.
