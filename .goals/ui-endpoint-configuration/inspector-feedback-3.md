# Inspector Feedback — Iteration 3

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified except as qualified under Criterion 5: the built
  application exposes the keyboard-accessible Configuration tab, distinguishes
  active and unsaved origins, rejects a disallowed save without changing the
  active origin, and routes health/discovery/speech to the newly saved service.
  A deliberately late service-A catalog did not replace service B.
- [x] Criterion 2 — verified: a real supported service exposed only its
  `engine-B` choice. A real legacy service returned 404 for discovery, hid the
  selectors, produced downloadable audio, and received the exact body
  `{"input":"legacy real","response_format":"mp3","speed":1}`. Source and
  focused browser assertions distinguish unsupported, authorization,
  connectivity, malformed, invalid-shape, and empty-catalog outcomes.
- [x] Criterion 3 — verified: a failed allowlist save retained service A; a
  successful service-B save survived removal and recreation of the production
  container with the same named volume, despite service A being the startup
  value. The retained file was mode 0600. Documentation gives the path,
  precedence, modes, initialization behavior, and synthetic Compose volume.
- [x] Criterion 4 — verified for the operator/credential boundary: the runtime
  requires an independent `TTS_OPERATOR_TOKEN`; the backend credential cannot
  authorize configuration; exact allowlisting prevents forwarding it to an
  arbitrary destination. Existing bounded-body, language, audio, playback and
  download checks pass.
- [ ] Criterion 5 — FAILED: the built application was opened and exercised at
  desktop and 390×844 mobile sizes, including keyboard-only tab switching,
  real two-service routing, saves, legacy speech, persistence and delayed
  responses. A late old-endpoint speech response exposed a functional
  regression: after switching from B to A, the stale response was correctly
  prevented from publishing audio, but the button remained disabled and
  permanently displayed “Generating…”. The `finally` revision guard returns
  before restoring the button. Production Docker tests pass but still contain
  no container-replacement persistence assertion or browser launch. The new
  late-response E2E covers only discovery, not health or speech.
- [ ] Criterion 6 — FAILED: the corrected artifacts still overstate evidence.
  T009 attributes keyboard save/post-save routing to `config.test.js`, which
  has no browser assertion; T013 claims authentication and network discovery
  cases that the E2E file does not assert; T018 attributes replacement
  persistence to `docker.test.js`, which never recreates a container with its
  retained volume. `.spec-context.json` records “6 unit” tests although the
  mandatory hook runs 7, and claims a built-container Chromium smoke pass not
  represented by the committed assertions. Legal/rights/native qualification
  boundaries remain explicit.
- [ ] Criterion 7 — INCOMPLETE: Builder commit `71fac35` is role-marked and has
  both required trailers; `origin/main` is an ancestor. Merge, push and remote
  verification remain correctly deferred after this FAIL.

## Quality Gate

- Command: `C:\Program Files\Git\bin\bash.exe checks/run_companion_validation.sh`
- Result: **PASS**
- Details: 155 backend tests, 7 frontend unit tests, 58 browser tests passed,
  2 optional fidelity tests skipped, and 13 integrity tests passed.
- Command: `npm --prefix frontend run test:docker`
- Result: **PASS**
- Details: 6 tests passed after a clean serial rerun. An initial concurrent run
  collided with the mandatory hook over their shared fixture file and was not
  treated as a product failure.
- Command: `git diff --check`
- Result: **PASS**

## Issues Found

1. Switching endpoints during speech generation leaves the UI permanently
   disabled after the old response settles. `app.js` returns from `finally`
   when the revision changed, so it never restores “Generate speech”.
2. Static serving accepts `POST /` and returns the application HTML with 200.
   Traversal and protected-path probes returned 404, and API method/body limits
   passed, but the replacement global runtime should retain the former static
   method boundary by serving assets only for GET/HEAD.
3. Committed feature evidence still does not test late health or speech
   responses, a browser against the production container, or retained-volume
   container replacement. The delayed discovery test uses intercepted browser
   requests rather than two real services.
4. Tasks and lifecycle evidence claim tests/results that do not match the
   committed assertions or current mandatory-hook counts.

## What Must Be Fixed

1. On stale speech completion, suppress stale status/audio but always restore
   the current UI's generate-button state and label; add a deliberately late
   real or production-runtime speech test that verifies continued usability.
2. Restrict static file serving to GET/HEAD and add regression assertions for
   static methods alongside the existing path and API-limit safeguards.
3. Add production-container/browser evidence for real two-service switching,
   late health/speech responses, and retained-volume container replacement.
4. Correct T009, T013, T018 and `.spec-context.json` so file mappings, counts,
   and claimed browser/container evidence exactly match what was executed.
