# Inspector Feedback — Iteration 2

## Verdict: FAIL

## Acceptance Criteria Check

- [ ] Criterion 1 — FAILED: the development UI shows active and unsaved values,
  rejects a destination outside the allowlist, and switches its API to a second
  controlled service. The shipped image is not a usable application, however:
  its Node static server sends no `Content-Type` for HTML, JavaScript, CSS, or
  SVG while also sending `X-Content-Type-Options: nosniff`. Chromium renders
  the HTML source as plain text, so no tab, validation, save, or speech control
  can run. In the development UI, `.configuration-panel { display: grid }`
  overrides the `hidden` attribute, leaving Configuration and Speech visible
  together regardless of the selected tab. Health and in-flight speech also
  have no endpoint-revision guard, so late old-endpoint responses can still
  overwrite current status/audio.
- [ ] Criterion 2 — FAILED: supported choices and the code path which omits
  model/voice for 404/501 exist, but the shipped UI cannot execute. A
  syntactically valid JSON object with a missing/non-array `engines` field is
  normalized to an empty catalog, so invalid-catalog and empty-catalog failures
  remain indistinguishable. No added assertion exercises legacy generation,
  authentication, malformed/invalid catalogs, network discovery, or late
  discovery.
- [x] Criterion 3 — verified at the API/runtime layer: in the built image I
  saved service B, observed its distinguishable `engine-b` catalog, removed and
  recreated the container with the same named volume, and read service B back.
  The retained file was mode 0600. Failed allowlist saves preserved service B.
  The README identifies the path, precedence, modes, and synthetic volume.
  This does not cure the unusable shipped browser UI.
- [ ] Criterion 4 — FAILED: the exact allowlist and separate operator token
  work when configured, and the backend credential was replaced server-side.
  However `auth()` falls back to `TTS_API_KEY` when `TTS_OPERATOR_TOKEN` is
  absent, conflating the backend credential with the operator boundary instead
  of requiring the documented separate operator credential. The shipped UI
  regression also prevents verification that existing playback/download
  behavior is preserved in the actual image.
- [ ] Criterion 5 — FAILED: I opened the built image in Chromium; it displayed
  raw HTML source because static MIME types are absent. I separately exercised
  the development UI with controlled services A (`engine-a`) and B
  (`engine-b`): an authorized save changed the active endpoint to B and a
  disallowed `:9999` save visibly failed while B stayed active. Unsaved state
  was visible. At 390×844 controls fit horizontally, but both panels remained
  displayed. The unchanged 50 baseline browser tests contain no configuration,
  switching, legacy, stale-response, or persistence assertions. The Docker
  suite checks asset status/body but not MIME or browser execution, so it
  passed despite the shipped-image failure.
- [ ] Criterion 6 — FAILED: living-spec mappings now include the runtime paths,
  but Companion artifacts remain materially inaccurate. `tasks.md` marks
  backend files and tests, new E2E switching/keyboard/late-response tests, and
  replacement/corrupt/unwritable persistence tests complete although those
  files/assertions were not added. `.spec-context.json` still says branch
  `main`, records validation against `e63512c`, retains the obsolete missing-uv
  concern, and says the mandatory hook was deferred/blocked. Existing
  legal/rights/native qualification boundaries remain explicit.
- [ ] Criterion 7 — INCOMPLETE: Builder commit `76d3483` is role marked and
  contains both required trailers; `origin/main` is an ancestor. Merge, push,
  and remote verification are correctly deferred after this FAIL.

## Quality Gate

- Command: `C:\Program Files\Git\bin\bash.exe checks/run_companion_validation.sh`
- Result: **PASS**
- Details: 155 selected backend tests, 6 frontend unit tests, 50 baseline
  browser tests passed (2 fidelity tests skipped), and 13 repository integrity
  tests passed. Inspection of assertions confirms the browser suite has no new
  feature-specific coverage.
- Command: `npm --prefix frontend run test:docker`
- Result: **PASS**
- Details: 6 assertions passed after removing test-fixture/port contention.
  The suite does not assert static MIME types or launch a browser.
- Command: `npm --prefix frontend run build`
- Result: **PASS**
- Command: `python -m unittest discover -s checks/tests -v`
- Result: **PASS** — 13 tests.
- Command: `git diff --check`
- Result: **PASS**

## Issues Found

1. The actual shipped image serves every static file without a MIME type under
   `nosniff`; Chromium renders `index.html` as text and never runs the app.
2. The CSS `display: grid` rule defeats panel `hidden`, so both tabs' panels are
   simultaneously visible in the development UI on desktop and mobile.
3. Late health and speech responses are not revision-isolated; switching can
   still expose stale status/audio from the former service.
4. Invalid JSON catalog shape is reported as an empty catalog.
5. The operator-token fallback reuses the backend proxy credential rather than
   enforcing the documented independent boundary.
6. Added tests cover only configuration API authorization/save/restart. They do
   not cover actual shipped browser execution, controlled switching, legacy
   requests, error taxonomy, stale responses, mobile keyboard behavior, or
   volume-backed container replacement.
7. Companion tasks and lifecycle evidence still claim files, assertions, and
   validation state that do not match the commit or current checks.

## What Must Be Fixed

1. Serve correct static MIME types in the production Node runtime and add a
   browser assertion against the built/running image.
2. Restore real mutually exclusive, keyboard-accessible tab panels, including
   desktop and mobile browser tests.
3. Revision-isolate or cancel health, discovery, and in-flight speech work
   across saves; test deliberately late responses from service A after
   switching to service B.
4. Distinguish invalid catalog shape from a valid empty catalog and add
   assertions for every required discovery outcome and the legacy request
   payload.
5. Require a separate operator credential and keep the backend proxy secret
   unusable as a configuration credential.
6. Add genuine feature-specific shipped-image/container/browser persistence
   and switching assertions rather than relying on unchanged baseline counts.
7. Correct `tasks.md` and `.spec-context.json` so claimed files, tests, branch,
   hook result, commit/tree evidence, and concerns reflect reality.
