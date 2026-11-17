# Inspector Feedback — Iteration 1

## Verdict: FAIL

## Acceptance Criteria Check

- [ ] Criterion 1 — FAILED: the tab is labeled and keyboard reachable, and invalid
  origin syntax is validated, but unsaved edits have no visible unsaved state.
  More seriously, a browser save from the controlled `:8765` fixture to the
  unused `http://127.0.0.1:9999` was accepted while subsequent health and
  discovery still reported the distinguishable `:8765` fixture as connected
  and ready. `apiProxy()`'s added `router` property therefore did not switch
  Vite routing. The production Nginx runtime contains neither
  `/api/configuration` nor dynamic routing. The 404/501 legacy branch also
  mutates capability state before checking `endpointRevision`, so a late
  unsupported response can restore stale state.
- [ ] Criterion 2 — FAILED: supported choices render, and the browser code can
  omit model/voice on a 404/501 legacy response. However authentication,
  connectivity, and malformed-catalog failures all collapse to the same
  generic message; only unsupported and empty are distinct. No new test covers
  legacy generation, authentication, malformed catalog, late responses, or
  controlled switching. The claimed E2E files were not changed.
- [ ] Criterion 3 — FAILED: the Node helper atomically writes a restrictive JSON
  file and its focused unit test preserves the previous saved value after an
  invalid origin. The shipped image is static Nginx, does not copy or execute
  that helper, has no configuration route, and always proxies the startup
  `TTS_UPSTREAM_URL`. Consequently the Compose volume and documented file
  cannot provide reload/restart/replacement persistence. The Compose recipe
  also does not initialize the documented ownership/modes.
- [ ] Criterion 4 — FAILED: credentials remain absent from browser assets and
  the existing request limits, language, playback, and download suites pass.
  There is nevertheless no operator authentication/authorization on
  `/api/configuration` and no destination allowlist or policy. Any client able
  to reach the server can GET/PUT the shared route, and the browser accepted an
  arbitrary destination. If routing were fixed, the server credential would
  be forwarded to that operator-unauthorized destination.
- [ ] Criterion 5 — FAILED: I opened the actual app with a synthetic local
  service. At desktop 1038×809, supported options rendered; Tab/Enter opened
  Configuration and keyboard focus reached the endpoint field. At mobile
  390×844, the input and save control fit without horizontal overflow and
  keyboard focus again reached the endpoint. This exposed the missing unsaved
  indicator and failed endpoint switch above. The existing 50 passing browser
  tests cover baseline desktop/mobile behavior but not configuration,
  switching, late responses, legacy generation, or persistence. The mandatory
  hook did not pass in the available bash environment.
- [ ] Criterion 6 — FAILED: plan/tasks/implement history exists, but it is not
  consistent with the commit. Tasks claim changes to backend configuration,
  routers and tests, speech-generation living specs, registry, Docker tests,
  and configuration E2E tests; none of those areas changed. `.spec-context.json`
  says `branch = main`, records verification against the initial commit/tree,
  and retains the failed-hook concern while marking all tasks and implementation
  complete. The plan requires an allowlist, authorized backend routes, explicit
  discovery states, and visible unsaved state that were not implemented.
  `capabilities/speech-generation` and `living-specs.yml` were not updated.
  Existing draft/legal/rights/native-qualification wording remains explicit.
- [ ] Criterion 7 — INCOMPLETE: Builder commit `0dc5ed2` has the required `[B]`
  marker and trailers, and local `origin/main` (`e63512c`) is an ancestor.
  Inspector feedback is committed separately. Merge/push/remote verification
  are correctly deferred and must not occur after this FAIL.

## Quality Gate

- Command: `bash checks/run_companion_validation.sh`
- Result: **FAIL**
- Details:
  - First run reproduced Builder's `uv: command not found`.
  - The known Windows executable
    `C:\Users\pgfelle0\.local\bin\uv.exe` was verified as uv 0.12.0. WSL exposes
    it at `/mnt/c/.../uv.exe` but cannot execute the Windows binary
    (`Exec format error`), so the known executable was not ignored.
  - After installing transient Linux uv 0.13.8 and Node 24.14.0, backend tests
    passed, but the hook still exited 1: frontend unit execution under WSL
    failed on protected-file ownership semantics and the Windows-installed
    Rolldown optional native binding on the mounted checkout. This is a genuine
    unresolved mandatory-hook/toolchain blocker, not accepted as PASS.
- Command: Windows hook-equivalent backend selection using the known
  `uv.exe`
- Result: **PASS** — 155 selected backend tests passed after resetting the
  cross-platform ignored `.venv`.
- Command: `TTS_UPSTREAM_URL=http://127.0.0.1:9
  TTS_API_KEY=validation-only-placeholder npm --prefix frontend test`
- Result: **PASS** — 5 unit tests passed; Playwright: 50 passed, 2 optional
  fidelity tests skipped.
- Command: `npm --prefix frontend run build`
- Result: **PASS**
- Command: `python -m unittest discover -s checks/tests -v`
- Result: **PASS** — 13 tests.
- Command: `git diff --check`
- Result: **PASS**

## Browser Evidence and Limitations

The app was served locally with Vite and a synthetic fixture only; no live
installation was accessed. The fixture at `127.0.0.1:8765` returned a unique
`synthetic-engine`. The UI loaded that engine and reported connected. After a
keyboard-only save of `http://127.0.0.1:9999`, the UI reported “Endpoint saved”
and made it active, but after 1.5 seconds still showed the `:8765` engine and
connected state. Before saving, changing the field left status blank and showed
no “unsaved” indication. Production container qualification was not claimed:
source inspection proves the Nginx image has no executable persistence/config
route, and there is no container-replacement acceptance test.

## Issues Found

1. Runtime endpoint switching is nonfunctional in Vite and absent in the
   production image.
2. Configuration writes are unauthenticated and destinations are unrestricted,
   violating the credential and operator boundaries.
3. Documented persistence cannot work in the shipped Nginx container.
4. Discovery errors are not fully distinguished, and late unsupported
   discovery can overwrite newer endpoint state.
5. Active versus unsaved state is not visibly distinguished.
6. Feature-specific switching, error, legacy, race, persistence, container,
   desktop/mobile, and keyboard evidence was marked complete but not added.
7. Companion lifecycle/task/coverage records materially overstate the actual
   changes, and the owning hook remains failed.

## What Must Be Fixed

1. Implement configuration GET/PUT, dynamic routing, atomic persistence, and
   retained-volume startup in the actual production serving runtime, with a
   Compose recipe that initializes usable ownership and permissions.
2. Enforce the real operator access boundary and an operator-approved
   destination policy before saving or forwarding credentials.
3. Prove switching with two distinguishable controlled services and verify
   health, discovery, and speech all move only after a successful save.
4. Add a visible unsaved state, distinct auth/network/malformed/empty/unsupported
   discovery states, and revision checks before every capability mutation.
5. Add feature-specific unit/integration/browser/container tests for failed
   saves, legacy requests, late responses, in-flight speech, reload/restart/
   replacement persistence, and desktop/mobile keyboard behavior.
6. Correct Companion task summaries, lifecycle evidence, capability specs,
   coverage maps, and index/registry links to match actual files and outcomes.
7. Run the checked-in mandatory hook successfully in a supported environment;
   keep mocked browser evidence explicitly separate from container/native
   qualification.
