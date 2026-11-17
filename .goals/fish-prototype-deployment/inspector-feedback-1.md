# Inspector Feedback — Iteration 1

## Verdict: FAIL

## Acceptance Criteria Check

- [ ] Criterion 1 — FAILED: strict read-only SSH reached the existing authorized
  native host and confirmed its platform plus two healthy, distinct listeners,
  but authentication to the designated target was denied. Its OS, roles and free
  ports therefore remain unknown, exactly as the committed evidence states.
- [ ] Criterion 2 — FAILED: the feature artifacts explicitly leave exact runtime,
  checkpoint and codec revisions and their applicable terms unresolved. No
  candidate has been installed or natively measured.
- [ ] Criterion 3 — FAILED: no Fish runtime or approved bilingual reference set
  exists. No German/English male/female Fish request, playable result, reported
  engine metadata, resource measurement or listening acceptance was verified.
- [ ] Criterion 4 — FAILED: two distinct existing service ports were observed and
  unauthenticated prototype catalog access was rejected, but no deployed Fish
  prototype or authenticated Fish request exists. The UI also asks the browser
  user to enter the production backend token for privileged configuration,
  contrary to the required server-side-only credential handling and no-setup
  behavior.
- [ ] Criterion 5 — FAILED: the deployed UI was browser-tested; health and engine
  discovery worked, and an unauthenticated configuration request returned 401.
  It exposed only the native engine, not qualified Fish voices or playable Fish
  audio. The exact upstream allowlist remains implemented, but the backend token
  is collected in a browser password field.
- [ ] Criterion 6 — FAILED: 311 backend tests verify mocked admission, lifecycle,
  fallback and deadline behavior, and documentation correctly limits RSS claims.
  Mandatory native lifecycle/resource verification was not performed.
- [ ] Criterion 7 — FAILED: no prototype or updated UI deployment/recreation was
  performed in this iteration, so persistence, rollback and production health
  before/after deployment were not established.
- [ ] Criterion 8 — FAILED: backend tests, frontend unit tests, build, E2E and the
  production-container test passed. The container contract gate failed because
  `frontend/tests/docker.test.js` supplies a stray `--env` argument. Feature
  artifacts correctly describe the native work as blocked, but the mandatory
  deployment, Fish speech and UI gates remain open.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from `backend/`
- Result: PASS
- Details: 311 tests passed in WSL after restoring the locked environment.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`
- Result: PASS
- Details: 7 unit tests and 66 E2E tests passed; 2 fidelity tests were skipped.
- Command: `npm run test:production`
- Result: PASS
- Details: The isolated production-container scenario passed.
- Command: `npm run test:docker`
- Result: FAIL
- Details: Serial rerun failed while creating the verification container because
  the test command contains a duplicate bare `--env` argument.
- Command: `git diff --check`
- Result: PASS

## Issues Found

1. The requested outcome is not deployed. The tracked task list deliberately
   leaves artifact approval, reference approval, launcher integration and native
   rollout open; this is policy scaffolding rather than a working Fish prototype.
2. Mandatory live verification cannot proceed safely because access to the
   designated target is denied. The reachable native host still provides no
   evidence of four qualified Fish combinations.
3. Shared-token handling moves the backend bearer token into a browser input for
   configuration authorization. That violates the goal's requirement that the
   credential remain server-side and that no additional user setup be required.
4. The changed container test is broken by an extra `--env` argument, so the
   relevant container quality gate is red.

## What Must Be Fixed

1. Restore authorized read-only/deployment access to the designated target and
   complete topology discovery without changing SSH trust.
2. Resolve and approve exact pinned runtime/model/codec terms and suitable
   reference provenance before any download, then integrate and qualify the
   managed launcher.
3. Deploy the isolated prototype and updated UI, verify all four Fish
   language/gender combinations with bounded measurements, and perform the
   lifecycle, persistence, rollback and production before/after checks.
4. Keep the shared backend credential wholly server-side while retaining
   privileged configuration authorization and the exact upstream allowlist.
5. Remove the malformed container-test argument and rerun every mandatory gate.
