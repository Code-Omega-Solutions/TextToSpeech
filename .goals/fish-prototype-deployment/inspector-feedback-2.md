# Inspector Feedback — Iteration 2

## Verdict: FAIL

## Acceptance Criteria Check

- [ ] Criterion 1 — BLOCKED: there is no changed access evidence for the
  designated target, so I did not repeat the previously denied SSH attempt.
  Target OS, roles and free ports remain unknown. Earlier read-only evidence for
  the authorized native host is unchanged and does not justify substituting it.
- [ ] Criterion 2 — BLOCKED: exact runtime, checkpoint and codec revisions,
  applicable artifact terms and a smaller qualified candidate remain explicitly
  unresolved. No download or installation was performed.
- [ ] Criterion 3 — BLOCKED: no approved runtime/reference set or live Fish
  deployment exists, so none of the four language/gender combinations, playable
  outputs, engine metadata, bounded measurements or listening results can be
  verified.
- [ ] Criterion 4 — INCOMPLETE: the latest change removes browser credential
  collection. Local production-container verification confirms the same
  server-side backend credential authorizes configuration and proxying, while an
  unauthorized request returns 401. A live Fish prototype using that mechanism
  on a distinct port is still absent.
- [ ] Criterion 5 — FAILED: server-side authorization and the exact origin
  allowlist work (wrong token 401, authorized non-allowlisted origin 403, exact
  allowlisted origin 200), and no token input is rendered. However, the browser
  now has no production/prototype selector or endpoint control at all; its
  Configuration tab is informational only. This silently removes the goal's
  promised UI selection instead of implementing it without exposing credentials.
  No qualified Fish catalog or playable Fish audio is available.
- [ ] Criterion 6 — BLOCKED: 311 backend tests pass on supported WSL/Python 3.12
  and cover mocked lifecycle/resource behavior, but mandatory native admission,
  unload, cooldown, pressure/probe and real resource verification remains open.
- [ ] Criterion 7 — BLOCKED: no approved prototype/UI deployment or recreation
  occurred, so persistence, rollback and production before/after evidence is
  unavailable.
- [ ] Criterion 8 — FAILED: local backend/frontend/build/container gates pass,
  including the corrected Docker argv. Browser verification exposes the missing
  target selector, while native deployment evidence remains blocked. The
  Companion context contains the earlier extension hook history and honestly
  remains `implementing` at the blocked artifact task; it contains no new
  iteration-2 hook event or completed-implementation claim.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from `backend/`
- Result: PASS
- Details: 311 tests passed in 16.29 seconds in WSL after a locked sync into a
  unique temporary `UV_PROJECT_ENVIRONMENT`, which was removed afterward. A
  Windows run was unsuitable for the POSIX-only checks and was not treated as
  the supported gate.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`
- Result: PASS
- Details: 7 unit tests passed; the build passed; 62 E2E tests passed and 2
  fidelity tests were skipped.
- Command: `npm run test:production`
- Result: PASS
- Details: The production-container switching, authorization and persistence
  scenario passed.
- Command: `npm run test:docker`
- Result: PASS
- Details: All 6 Docker contract checks passed. The stray `--env` arguments from
  iteration 1 are corrected.
- Command: Browser UI verification against a local synthetic serving boundary
- Result: FAIL
- Details: The page renders no backend-token input, and authorization plus exact
  allowlisting behave correctly, but there is also no UI control for selecting
  production versus prototype.
- Command: `git diff --check`
- Result: PASS

## Issues Found

1. Removing the browser token field also removed the entire endpoint-selection
   workflow. Updating the feature specification to call the tab informational
   does not satisfy the immutable goal requiring the UI to select production
   versus prototype.
2. The actual Fish outcome remains objectively blocked by unchanged target
   access and unresolved artifact/reference approval. No live deployment claim
   can be accepted.
3. Required Companion state remains open rather than falsely completed, but the
   reported iteration-2 hook/tool failure is not independently evidenced by a
   new hook event or sanitized tracked record.

## What Must Be Fixed

1. Restore a credential-free browser choice between only the operator-approved
   production and prototype targets. Map opaque choices to exact server-side
   destinations; do not return origins or credentials to browser assets, accept
   arbitrary origins, or weaken privileged configuration authorization.
2. Add browser and container coverage proving both choices route correctly,
   unauthorized configuration remains rejected, a non-allowlisted destination
   remains rejected, and no credential reaches client assets.
3. Run the applicable Companion hook after the local correction, or accurately
   record why it cannot run without claiming implementation completion.
4. After all actionable local defects are resolved, retain a BLOCKED verdict
   until authorized target access, exact artifact/reference approval and the
   required live Fish deployment evidence become available.
