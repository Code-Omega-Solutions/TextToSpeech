# Private VibeVoice evaluation - Requirement-to-test map

These references identify deterministic tests for the isolated evaluator.
Baseline calls, adapter processes, machine details, storage, and measurements
are faked or injected; no candidate model or target machine is exercised.

| Requirement | Test reference | Evidence scope |
| --- | --- | --- |
| The evaluator remains isolated and removable | [backend/tests/test_evaluation.py](../../backend/tests/test_evaluation.py), [backend/tests/test_api.py](../../backend/tests/test_api.py) | Loopback-only evaluator boundary and unchanged production speech API contract; package removal itself is a source-boundary review |
| Terms and sample permission gate each use | [backend/tests/test_evaluation_comparison.py](../../backend/tests/test_evaluation_comparison.py), [backend/tests/test_evaluation_inspection.py](../../backend/tests/test_evaluation_inspection.py) | Exactly five unique samples, unresolved sample-text blocking, terms blockers, and no baseline call for blocked text |
| Comparisons use the existing baseline and approved candidates | [backend/tests/test_evaluation_comparison.py](../../backend/tests/test_evaluation_comparison.py) | Authenticated local baseline contract, shared sample IDs, exact candidate IDs, fake adapter invocation, timeout stop, output limit, and generation timing |
| Feasibility inspection is read-only and records unknowns | [backend/tests/test_evaluation_inspection.py](../../backend/tests/test_evaluation_inspection.py), [backend/tests/test_evaluation_comparison.py](../../backend/tests/test_evaluation_comparison.py) | Injected platform/volume/memory/adapter probes, explicit approval and terms blockers, missing-measurement reasons, and result timing |
| Reports and review remain private to one local run | [backend/tests/test_evaluation.py](../../backend/tests/test_evaluation.py), [backend/tests/test_evaluation_web.py](../../backend/tests/test_evaluation_web.py) | Owner-only atomic persistence, path scrubbing, result-ID audio access, same-origin/session checks, local page headers, and private report display |
| Product-owner decisions are recorded without a score threshold | [backend/tests/test_evaluation.py](../../backend/tests/test_evaluation.py), [backend/tests/test_evaluation_web.py](../../backend/tests/test_evaluation_web.py) | Validated decisions, all four supported outcomes, missing-data display, and no automatic rating threshold |

## What these tests do not establish

The adapter subprocess tests use a deterministic fake process and the baseline
uses an injected fake client. Inspection tests inject every machine and volume
probe. They do not execute a candidate model, access a real target machine,
measure native model footprint or peak memory, verify terms or rights, qualify
macOS performance, publish private data, or validate a deployment. Missing
footprint and peak-memory values remain explicit rather than simulated.
