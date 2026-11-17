# Inspector Feedback — Iteration 4

## Verdict: FAIL

## Acceptance Criteria Check

- [ ] Criterion 1 — FAILED: the broad routing and stale-discovery behavior
  remains verified, but an actual production-browser operator flow exposed an
  active-versus-unsaved race. Entering the operator token and then editing the
  endpoint can trigger the token's asynchronous `loadConfiguration()` on blur;
  its response replaced the unsaved endpoint with the active endpoint. After a
  successful save, the save button is also re-enabled by `finally` although the
  edit and active endpoint are identical.
- [x] Criterion 2 — verified: the previously verified supported, legacy,
  invalid and empty-catalog behavior is unchanged by this iteration.
- [x] Criterion 3 — verified from the prior independent replacement check,
  file-mode check and documentation review. The new production test contains a
  retained-volume recreation check, although this run failed before reaching
  it and it does not open a fresh post-recreation browser.
- [ ] Criterion 4 — FAILED: credential, authorization, privacy and request
  boundaries remain verified, but removing the revision guard from the speech
  `finally` creates a coupled concurrency regression. After an endpoint switch
  re-enables generation, a new request can start while the old request is still
  pending; the old request's `finally` can then enable and relabel the button
  while the current request is still running, defeating duplicate-submission
  protection.
- [ ] Criterion 5 — FAILED: the mandatory hook and Docker suite pass, and I
  opened the production image at desktop and 390×844 mobile sizes and performed
  a keyboard endpoint save against two controlled services. The mandatory
  serial `test:production` command fails. Its result helper matches static text
  in a hidden result region, so it advances before service B receives speech
  and then fails `b.requests.includes("/v1/audio/speech")`. Its late-health
  assertion also cannot prove stale isolation because both services return the
  same successful observable state.
- [ ] Criterion 6 — FAILED: T009 still claims a keyboard save and
  active-versus-unsaved coverage, but `production.test.js` presses Tab only
  after entering the already-active service A and clicks the service-B save
  button; it asserts neither unsaved state nor the post-save save-button state.
  T013 was changed to remove authentication and network cases rather than
  supplying the cases required by the immutable specification. The lifecycle
  record claims `test:production: PASS`, contrary to this independent serial
  run.
- [ ] Criterion 7 — INCOMPLETE: Builder commit `4b5c940` is role-marked and
  has both required trailers. Merge, push and remote verification remain
  correctly deferred after this FAIL.

## Quality Gate

- Command: `C:\Program Files\Git\bin\bash.exe checks/run_companion_validation.sh`
- Result: **PASS**
- Details: 155 backend tests, 7 frontend unit tests, 58 browser tests and 13
  integrity tests passed; 2 optional fidelity tests were skipped.
- Command: `npm --prefix frontend run test:docker`
- Result: **PASS**
- Details: 6 tests passed, including GET/HEAD/static-method checks.
- Command: `npm --prefix frontend run test:production`
- Result: **FAIL**
- Details: 0 of 1 passed. The assertion that service B received
  `/v1/audio/speech` failed.
- Command: `git diff --check`
- Result: **PASS**

## Issues Found

1. The stale-speech fix restores the previously stuck button, but it no longer
   checks whether a newer speech request owns the loading state. An old request
   can therefore unlock and relabel the button during a current request.
2. The production test is not reliable evidence for new-service speech. It
   polls text that exists even while `#result` is hidden, then immediately
   inspects the service request list. This exact race failed in the required
   serial run.
3. Delayed healthy service A and immediate healthy service B both yield
   `SERVICE CONNECTED`, so the final health text does not establish that the
   late A response was ignored. Old speech publication is likewise not
   asserted before the new generation.
4. The committed production test does not perform a fresh-browser persistence
   check after recreation; its API/file checks were not reached in this run.
5. Token-change configuration loading can overwrite an endpoint edit, and the
   successful-save `finally` re-enables Save despite no unsaved change.
6. T009's mapping still does not match its keyboard/unsaved assertions, T013
   was narrowed below the specification, and the lifecycle PASS claim is not
   reproducible.

## What Must Be Fixed

1. Track speech-request ownership so a stale request restores a stranded
   endpoint-switch state without unlocking or relabeling a newer request. Add
   an overlapping old/new speech regression, not only an old-then-wait flow.
2. Make the production speech assertion wait for a real visible/current result
   or the controlled service request, and explicitly prove old audio/status
   cannot publish.
3. Give delayed health responses distinguishable outcomes and assert that the
   saved endpoint exclusively owns the final state.
4. Complete the recreation check in a fresh browser session and make the
   serial production command deterministic.
5. Prevent token-triggered loads from overwriting later edits and preserve the
   disabled Save state after a successful save.
6. Add the keyboard/unsaved assertions T009 claims, restore authentication and
   connectivity discovery evidence required by the specification, and record
   only quality-gate results that actually pass.
