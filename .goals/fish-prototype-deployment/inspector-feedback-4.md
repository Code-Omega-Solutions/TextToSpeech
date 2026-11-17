# Inspector Feedback — Iteration 4

## Verdict: BLOCKED

## Acceptance Criteria Check

- [ ] Criterion 1 — BLOCKED: no changed access evidence exists for the
  designated target, so the previously denied SSH attempt was not repeated.
  Target OS/role/service/port discovery and topology validation remain pending;
  no substitute host or live-system change was used.
- [ ] Criterion 2 — BLOCKED: T004 still honestly records that exact pinned Fish
  runtime, checkpoint and codec revisions, their terms, macOS compatibility and
  a suitable smaller candidate are unresolved. Nothing unreviewed was
  downloaded or installed.
- [ ] Criterion 3 — BLOCKED: T005/T006 remain open, with no approved bilingual
  male/female reference set or live Fish service. Four playable combinations,
  actual engine metadata, bounded measurements and listening acceptance cannot
  yet be verified.
- [ ] Criterion 4 — BLOCKED: local tests verify distinct approved mock targets,
  one server-side credential, overwritten client authorization and no token or
  origin in browser assets. A live prototype on a distinct port using the
  existing production token remains unverified.
- [ ] Criterion 5 — BLOCKED: the prior local regression is fixed.
  `targetFor()` now resolves unselected traffic from the persisted protected
  configuration, requires an exact approved target origin, and preserves opaque
  per-session choices. The focused test verifies immediate and recreated
  fallback routing, rejects wrong authorization and an arbitrary origin, and
  all browser/container gates pass without exposing configuration origins or
  credentials. Deployed Fish discovery/playback and a live unauthorized browser
  attempt remain unavailable.
- [ ] Criterion 6 — BLOCKED: 311 supported WSL/Python 3.12 tests pass, including
  lifecycle/fallback coverage, but native admission, idle unload, cooldown,
  pressure/probe behavior and real resource measurements remain gated on the
  qualified native prototype. No artificial pressure or process termination was
  performed.
- [ ] Criterion 7 — BLOCKED: local persistence is verified immediately and
  after handler/container recreation, and owned helpers cleaned up. Approved
  live deployment/rollback and production health/authenticated speech before
  and after deployment remain unverified.
- [ ] Criterion 8 — BLOCKED: all applicable local backend, frontend, build,
  browser and serial container gates pass. The sanitized Companion writer
  invocation reported `0 new task event(s) (8/12 complete)`, correctly left
  T004/T005/T006/T010 open, and made no semantic context change. Mandatory
  native qualification, live Fish service and deployed UI evidence are absent.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` in WSL
- Result: PASS
- Details: 311 tests passed in 25.61 seconds using supported Python 3.12.
- Command: `npm run test:unit`
- Result: PASS
- Details: 9 tests passed, including the protected persisted-fallback
  regression.
- Command: `npm run test:e2e` (includes `npm run build`)
- Result: PASS
- Details: build passed; 62 browser tests passed and 2 fidelity tests were
  skipped.
- Command: `npm run test:production`
- Result: PASS
- Details: the owned browser/container helper verified opaque target switching,
  late-request isolation, protected persisted configuration and recreation.
- Command: `npm run test:docker`
- Result: PASS
- Details: all 6 Docker checks passed when run serially, including server-side
  credential replacement, static-asset privacy and exact proxy restrictions.
- Command: `python3 .specify/extensions/companion/scripts/write-context.py
  --step implement --status implemented --by extension --tasks-file
  specs/007-fish-backend-enablement/tasks.md`
- Result: PASS
- Details: idempotently synced 0 new events with 8/12 tasks complete; no false
  completion was recorded.
- Command: `git diff --check`
- Result: PASS
- Details: owned test containers and volumes were absent after the gates; the
  unrelated `.github/copilot-memories.jsonl` remained untouched and unstaged.

## Issues Found

No actionable local defect remains in the iteration-4 routing fix. The goal is
still incomplete because its mandatory live and native evidence is blocked by
external access and approval gates.

## Remaining Real-World Requirements

1. Restore authorized access to the designated target, then perform sanitized
   read-only OS/role/service/free-port discovery without changing production.
2. Resolve and approve exact Fish runtime/model/codec artifacts and terms,
   screen the smaller compatible candidate first, and approve bilingual
   male/female reference provenance and permissions.
3. Integrate and deploy only after those gates, on distinct prototype/UI ports
   with the existing server-side production bearer-token mechanism.
4. Verify four live German/English male/female Fish outputs, native lifecycle
   and fallback measurements, production health before/after, rollback, and the
   deployed UI including an unauthorized attempt.
