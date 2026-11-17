# Inspector Feedback — Iteration 3

## Verdict: FAIL

## Acceptance Criteria Check

- [ ] Criterion 1 — BLOCKED: there is no changed access evidence for the
  designated target, so the previously denied SSH attempt was not repeated.
  Target discovery and topology validation remain unavailable; the authorized
  native host was not silently substituted.
- [ ] Criterion 2 — BLOCKED: exact pinned runtime, checkpoint and codec
  revisions, applicable terms, and a suitable smaller candidate remain open in
  T004. No unreviewed download or installation was performed.
- [ ] Criterion 3 — BLOCKED: T005/T006 remain open and there is no approved
  bilingual reference set or live Fish service. The four language/gender
  combinations, playable outputs, engine metadata, measurements and listening
  acceptance therefore remain unverified.
- [ ] Criterion 4 — INCOMPLETE: local container/browser evidence confirms that
  opaque production and prototype choices route through the same server-side
  synthetic credential on distinct mock origins, without rendering a token or
  origin in client assets. A live authenticated Fish prototype on a distinct
  port is still absent.
- [ ] Criterion 5 — FAILED: the credential-free selector routes both exact
  operator-approved targets, rejects an unknown target, and leaves privileged
  configuration authorization in place. However, the latest routing path never
  reads the persisted privileged configuration. An authenticated configuration
  mutation returns 200 and saves the value, but a subsequent unselected health
  request still routes to the original production target. The protected
  mutation is therefore operationally ineffective, regressing the existing
  configured-upstream fallback contract.
- [ ] Criterion 6 — BLOCKED: 311 supported WSL/Python 3.12 tests pass and the
  latest commit does not change backend fallback or lifecycle code. Required
  native admission, unloading, cooldown, pressure/probe and resource checks
  remain unavailable.
- [ ] Criterion 7 — FAILED: the local container test proves selector sessions,
  volume storage and recreation behavior, but it does not prove that the stored
  privileged endpoint controls routing. Direct verification shows that it does
  not. No approved live deployment, rollback, or production before/after check
  occurred.
- [ ] Criterion 8 — FAILED: backend, frontend, build, E2E and serial container
  gates pass, and the Companion record honestly remains `implementing` at T004
  with T004/T005/T006/T010 open. Its extension history proves the earlier
  workflow execution but contains no new iteration-3 hook event. The local
  configured-upstream routing regression and missing native deployment evidence
  prevent acceptance.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from `backend/`
- Result: PASS
- Details: 311 tests passed in 15.02 seconds in WSL after a locked sync into a
  unique temporary `UV_PROJECT_ENVIRONMENT`; the exact temporary directory was
  removed afterward.
- Command: `npm run test:unit`
- Result: PASS
- Details: 8 tests passed.
- Command: `npm run test:e2e`
- Result: PASS
- Details: the build passed; 62 browser tests passed and 2 fidelity tests were
  skipped.
- Command: `npm run test:production`
- Result: PASS
- Details: the self-contained local browser/container helper exercised both
  approved targets, late-request isolation and recreation, then stopped and
  cleaned up its owned resources.
- Command: `npm run test:docker`
- Result: PASS
- Details: all 6 Docker checks passed when run serially.
- Command: direct configured-fallback behavior probe
- Result: FAIL
- Details: authenticated mutation returned 200, but the following request with
  no selector still reached the original production mock rather than the saved
  approved mock.
- Command: `git diff --check HEAD~1..HEAD`
- Result: PASS

## Issues Found

1. `createApiHandler()` now routes speech APIs exclusively through
   `loadApprovedTargets()` and session selection. It no longer uses
   `loadConfiguredUpstream()` for the no-selection fallback, while
   `/api/configuration` still reports successful persistence. This makes the
   privileged configuration endpoint a misleading no-op for actual traffic.
2. Live completion remains blocked by unchanged target access and unresolved
   exact Fish artifact/reference approvals. No live Fish or deployment claims
   were accepted.
3. Companion state is partial and honest, but no iteration-3 hook execution is
   recorded; the workflow remains correctly open at T004.

## What Must Be Fixed

1. Restore the approved persisted configured upstream as the routing fallback
   without exposing origins or credentials, weakening exact target allowlisting,
   or making the opaque selector privileged.
2. Add a regression test proving an authenticated approved configuration
   mutation changes subsequent fallback traffic, including after recreation,
   while unauthorized and arbitrary mutations remain rejected.
3. Run the applicable Companion hook and preserve the honest partial state.
4. After local defects are resolved, retain a BLOCKED outcome until the user
   provides authorized target access and approves exact Fish
   runtime/model/codec artifacts and bilingual reference provenance.
