# Inspector Feedback — Iteration 5

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: token-triggered configuration loading no longer
  overwrites a later edit, successful saves leave Save disabled when clean, and
  the endpoint-switching and stale-discovery browser coverage passes.
- [x] Criterion 2 — verified: supported and legacy behavior passes, and the
  browser suite now separately covers authorization, connectivity, malformed,
  empty, and explicitly unsupported discovery outcomes.
- [x] Criterion 3 — verified: the production test passed three serial runs,
  recreates the container with the same volume, launches a fresh browser, and
  confirms the retained endpoint and routing. File mode and documentation
  evidence remain intact.
- [x] Criterion 4 — verified: overlapping old/new speech coverage proves an old
  finalizer cannot unlock the current request or publish stale output.
  Credential, destination, privacy, limit, language, playback, and download
  checks pass.
- [x] Criterion 5 — verified: the mandatory hook, Docker suite, and three serial
  production-container runs pass. I also opened the built container against
  two synthetic services at desktop and 390×844 mobile sizes, changed and
  saved the endpoint entirely by keyboard, observed unsaved/clean states, and
  generated downloadable audio.
- [ ] Criterion 6 — FAILED: current task/lifecycle claims are not faithful to
  the committed evidence. T009 says the production test performs a keyboard
  endpoint change, but both endpoint changes use Playwright `fill()`; only the
  save uses an actual keyboard Enter. The lifecycle record also claims 64
  passing browser tests, while the mandatory hook reproducibly reports 66
  passing and 2 skipped.
- [ ] Criterion 7 — INCOMPLETE: Builder commit `7759ffb` is role-marked and has
  both required trailers, and `origin/main` is an ancestor. Integration and
  publication remain correctly deferred after this FAIL.

## Quality Gate

- Command: `C:\Program Files\Git\bin\bash.exe checks/run_companion_validation.sh`
- Result: **PASS**
- Details: 155 backend tests, 7 frontend unit tests, 66 browser tests, and 13
  integrity tests passed; 2 optional fidelity tests were skipped.
- Command: `npm --prefix frontend run test:production` (three serial runs)
- Result: **PASS**
- Details: all three runs exercised the built production container, controlled
  services, stale work, speech routing, and same-volume recreation.
- Command: `npm --prefix frontend run test:docker`
- Result: **PASS**
- Details: 6 tests passed.
- Command: `git diff --check`
- Result: **PASS**

## Issues Found

1. T009 and `.spec-context.json` claim a keyboard endpoint change in
   `production.test.js`, but lines 107 and 116 use `fill()`. The test does
   assert unsaved/clean states and uses keyboard Enter for Save, but it does not
   perform the endpoint edit by keyboard as claimed.
2. The iteration-5 lifecycle verification records 64 passing browser tests.
   The checked-in mandatory hook reports 66 passing tests plus 2 skipped.

## What Must Be Fixed

1. Make the committed production test perform the endpoint edit with actual
   keyboard input, or narrow T009 and lifecycle wording so it does not claim
   evidence that the test does not contain.
2. Correct the lifecycle browser-test count to the reproducible hook result.
