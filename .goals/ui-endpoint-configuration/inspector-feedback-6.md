# Inspector Feedback — Iteration 6

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: the previously established functional evidence
  remains intact, and the mandatory browser suite again passed endpoint
  validation, save-state, routing, and stale-discovery coverage.
- [x] Criterion 2 — verified: the mandatory suite passed supported and legacy
  speech plus distinct authorization, connectivity, malformed, empty, and
  unsupported discovery outcomes.
- [x] Criterion 3 — verified: prior production persistence and documentation
  evidence remains unchanged; no coupled regression appeared in the mandatory
  suite.
- [x] Criterion 4 — verified: the mandatory suite passed stale speech
  ownership, credential-boundary, privacy, request-limit, language, playback,
  and download coverage.
- [ ] Criterion 5 — FAILED: the corrected production test does use focused
  `Control+A` and keyboard typing, but it failed in the actual production
  container. The first edit produced the endpoint twice, so controlled
  switching and persistence did not execute successfully in this iteration.
- [ ] Criterion 6 — FAILED: the lifecycle record claims the corrected
  production test passes, but the independent production run failed. Its
  browser-count correction is accurate: the mandatory hook reported 66 passed
  and 2 skipped.
- [ ] Criterion 7 — INCOMPLETE: Builder commit `ca5d252` is role-marked, has
  both required trailers, and contains the two claimed evidence corrections;
  `origin/main` is an ancestor. Integration and publication remain pending
  after this FAIL.

## Quality Gate

- Command: `npm --prefix frontend run test:production`
- Result: **FAIL**
- Details: 0 passed, 1 failed. After focused `Control+A` and typing, the first
  endpoint value was duplicated (`aOrigin + aOrigin`) instead of replaced, and
  `toHaveValue(aOrigin)` timed out.
- Command: `C:\Program Files\Git\bin\bash.exe checks/run_companion_validation.sh`
- Result: **PASS**
- Details: 155 backend tests, 7 frontend unit tests, 66 browser tests, and 13
  integrity tests passed; 2 optional fidelity tests were skipped. The
  production command and mandatory hook were run serially.
- Command: `git diff --check`
- Result: **PASS**

## Issues Found

1. The committed keyboard correction is not reliable in the production
   scenario. The operator-token load can populate the endpoint around the
   focus/select/type sequence; this run observed the typed origin appended to
   the populated origin. Consequently the test failed before validating the
   remaining switch, stale-work, speech-routing, and persistence assertions.
2. The iteration-6 lifecycle evidence says
   `npm --prefix frontend run test:production: PASS`, which is contradicted by
   independent execution. The corrected 66-passed/2-skipped browser count is
   reproducible and accurate.

## What Must Be Fixed

1. Make the real focused keyboard endpoint edit deterministic against the
   asynchronous configuration load, while retaining actual keyboard
   `Control+A`/typing evidence, then demonstrate the full production scenario
   passes.
2. Update lifecycle verification so its production result matches reproducible
   evidence.
