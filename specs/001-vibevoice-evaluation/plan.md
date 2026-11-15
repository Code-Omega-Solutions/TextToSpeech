# Implementation Plan: Private VibeVoice Evaluation

## Summary

Build an isolated evaluation tool under `backend/evaluation/vibevoice/` that compares approved VibeVoice implementations with the existing authenticated macOS speech endpoint. It will require a private, terms-checked run manifest, use only already-installed model adapters, and save audio and results locally for a loopback-only listening and rating page. The production API, configuration, and service remain unchanged.

## Constitution Check

The design follows the constitution's privacy, bounded-operation, evidence, and platform qualification rules.

| Principle | Assessment |
|---|---|
| Keep specifications evidence-based | PASS. Record the observed model, voice, machine, language, and configuration, and distinguish completed, missing, and blocked comparisons. |
| Prefer safe, bounded behavior | PASS. Inspection is read-only, model execution is explicit, and runs stop on failure, cancellation, or agreed limits. |
| Protect users and operational boundaries | PASS. Keep evaluation artifacts local, bind the listener to loopback, and leave the existing service and its contract unchanged. |
| Verify observable outcomes | PASS. Validate comparison counts, ratings, averages, incomplete outcomes, and removal behavior with focused tests. |
| Be precise about platform and release claims | PASS. Treat German support, model availability, platform suitability, and all usage terms as explicit gates. |
| Development workflow | PASS. Integrate from a feature branch synchronized with the latest `origin/main`, and run relevant checks after resolving conflicts. |

## Project Structure

The evaluator stays outside the production application and owns its private runtime, report UI, and tests. Its capability documentation will be registered separately so the prototype does not broaden the existing speech API.

```text
backend/
  evaluation/vibevoice/
    __init__.py
    cli.py
    runner.py
    inspection.py
    server.py
    report.py
    listening.html
    summary.html
    README.md
  tests/
    test_evaluation.py
    test_evaluation_comparison.py
    test_evaluation_inspection.py
    test_evaluation_web.py
capabilities/
  vibevoice-evaluation/
    vibevoice-evaluation.spec.md
    vibevoice-evaluation.coverage.md
living-specs.yml
specs/README.md
```

**Structure Decision:** Keep the prototype as a standalone backend-side tool with story-specific comparison, inspection, and review files. Add no production routes, model dependency changes, checked-in model weights, or service lifecycle changes.

## Calls

```calls Evaluation workflow
+ CLI preflight and execution **new** @ backend/evaluation/vibevoice/cli.py
+   Validate and run approved configurations **new** @ backend/evaluation/vibevoice/runner.py
    POST /v1/audio/speech @ backend/app/routers.py:66
+   Inspect candidate-machine feasibility **new** @ backend/evaluation/vibevoice/inspection.py
+   Validate and aggregate report data **new** @ backend/evaluation/vibevoice/report.py
+   Serve local review UI **new** @ backend/evaluation/vibevoice/server.py
+     Paired listening screen **new** @ backend/evaluation/vibevoice/listening.html
+     Results and decision screen **new** @ backend/evaluation/vibevoice/summary.html
```

The evaluator invokes model adapters as bounded subprocesses without a shell. The baseline uses the existing authenticated `POST /v1/audio/speech` contract; if it is unavailable, the comparison is recorded as blocked rather than substituted.

## States

```states Evaluation lifecycle
preflight: Verify terms, target, capacity, and the sample manifest. (start)
ready: All permissions, prerequisites, and run limits are satisfied.
generating: Run approved comparisons within agreed resource limits.
reviewing: The product owner listens and records sample ratings. shows listening-review
complete: Persist evidence and the product-owner decision. (final) shows results-summary
blocked: Record the unavailable prerequisite or permission. (final) shows results-summary
stopped: Stop failed, cancelled, or over-limit work. (final) shows results-summary
preflight -> ready: all required checks pass
preflight -> blocked: an input, permission, or capacity check fails
ready -> generating: the operator approves the run
generating -> reviewing: generation attempts finish
generating -> stopped: a failure, cancellation, or agreed limit occurs
reviewing -> complete: the report is saved
grid:
| preflight | ready | generating | reviewing |
| blocked | stopped | complete | . |
```

## Screens

```screen listening-review Paired sample review
title: Sample text and language
row:
  list: Baseline audio | Candidate audio
  field: Rating from 1 to 10
  field: Qualitative observation
text: Model, voice, machine, and configuration identity
```

```screen results-summary Evaluation evidence
title: Results by language and configuration
row:
  list: Individual ratings | averages and rating counts
  list: Machine | platform | storage | memory | inspection time
  list: Installed footprint | peak memory | generation time
  text: Missing, failed, blocked, or incomplete result reasons
text: Product-owner decision and rationale
```
