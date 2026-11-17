# Inspector Feedback — Iteration 9

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: strict, non-interactive SSH through the existing
  trusted configuration reached the designated Apple Silicon macOS target.
  Sanitized discovery confirmed separate production, managed prototype,
  managed UI, and loopback Fish listeners without changing host-key trust or
  substituting another host.
- [ ] Criterion 2 — FAILED: the tagged Fish source license is reachable, but
  the authoritative S2-Pro page still returns 403. The native source checkout
  is dirty, no artifact approval manifest exists, and exact codec terms remain
  unaccepted. The deployed worker configuration is disabled, so no reviewed
  exact runtime/model/codec set is qualified.
- [ ] Criterion 3 — FAILED: the target has only two reference WAV files and no
  matching `.lab` files or approval manifest. The deployed catalog reports Fish
  unavailable with zero qualified voices. There are no current managed Fish
  results for the German/English male/female matrix, no bounded neural
  measurements, and no subjective listening result.
- [x] Criterion 4 — verified: production and prototype use distinct ports and
  the production, prototype, and UI protected credential files compare equal
  and remain owner-only. Unauthenticated prototype speech returned 401.
  Remote logs and browser assets contained neither the credential nor sampled
  speech text, and browser resources exposed no upstream origins.
- [ ] Criterion 5 — FAILED: browser verification selected opaque Production
  and Prototype targets, kept a fresh session on Production, rejected
  unauthorized configuration with 401 and an unknown target with 403, and
  generated playable German native audio. The prototype exposes only
  `macos-say`; no qualified Fish voice can be selected and no Fish audio is
  returned.
- [ ] Criterion 6 — FAILED: all lifecycle and fallback tests pass, and live
  German/English Fish-selected requests truthfully returned playable native
  WAV. The managed neural worker remains disabled, however, so neural success,
  single-neural admission, idle unload, cooldown, pressure/probe behavior,
  cancellation, deadline handling, and owned cleanup were not verified live.
  The external Fish listener remained outside repository ownership and was not
  adopted or terminated.
- [ ] Criterion 7 — FAILED: the former stale prototype definition is now
  absent from the loadable `.plist` set, present once under a non-`.plist`
  quarantine name, launchctl-disabled, and unloaded; that state survived the
  inspector's managed-service attempts. Production remained healthy and its
  long-running process was not restarted. But an independent execution of the
  documented bounded bootout/bootstrap sequence failed during the recreation
  stage before post-recreation checks completed, so the rollback stage was not
  reached. Prototype-only recovery restored both managed services. The checked-
  in claim of deterministic recreation and rollback is not reproducible.
- [ ] Criterion 8 — FAILED: local backend, frontend, runtime, policy,
  production/container, Companion, and whitespace/privacy gates pass. Feature
  tasks T004, T005, T006, and T010 correctly remain open. Mandatory real Fish
  artifact/reference approval, four-output qualification, managed lifecycle,
  and reproducible recreation/rollback remain incomplete.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: all 325 tests passed.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`,
  `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: 9 unit tests passed; builds passed; 62 browser tests passed with 2
  optional fidelity tests skipped; the production scenario and all 6 Docker
  checks passed.
- Command: `python -m pytest -ra frontend/runtime/test_server.py` and
  `python -m pytest -ra checks/tests`
- Result: PASS
- Details: all 3 runtime tests and all 13 policy/licensing/Spec Kit tests passed.
- Command: `checks/run_companion_validation.sh`
- Result: PASS
- Details: the checked-in hook passed in an isolated locked environment using
  Windows Git Bash and the supported Node runtime.
- Command: strict live SSH, API, recreation/rollback, and deployed browser checks
- Result: FAIL
- Details: quarantine persistence, authentication, native fallback, privacy,
  browser isolation, allowlisting, playable native audio, and production
  preservation passed. The documented managed recreation sequence failed and
  required safe prototype-only recovery; Fish remains unavailable.
- Command: authoritative artifact/reference review
- Result: FAIL
- Details: the model endpoint remains 403, exact codec acceptance is absent,
  the source checkout is dirty, no approval manifests exist, and the reference
  tree has two WAV files with no matching transcripts.
- Command: Builder diff and final worktree `git diff --check`, privacy scan
- Result: PASS
- Details: no whitespace error or private target identity was found.
  `.github/copilot-memories.jsonl` and browser-tool output remain untracked and
  unstaged.

## Issues Found

1. Exact model and codec approval is still unavailable; a dirty source tree and
   absent manifest cannot establish an approved runtime.
2. No consented four-record WAV/transcript matrix exists, so the deployed
   native-only catalog truthfully has no Fish voices or Fish output.
3. Real managed neural lifecycle behavior remains unqualified while the
   external loopback worker stays outside the ownership boundary.
4. Stale-startup quarantine is fixed, but the bounded managed recreation
   procedure failed independently. Recovery succeeded without touching
   production, yet the documentation overstates recreation/rollback evidence.

## What Must Be Fixed

1. Obtain legitimate authoritative model/codec terms and bind an approval
   manifest to a clean pinned source tree and every runtime-loaded artifact.
2. Approve four exact Fish-consumed WAV/`.lab` pairs with public provenance,
   intended-use permission, and cloning consent.
3. Fix and re-run the exact managed prototype/UI recreation and protected-copy
   rollback procedure until it completes deterministically while preserving
   production and the stale-definition quarantine.
4. Only after the approval gates close, enable the owned worker and verify the
   four Fish outputs plus live admission, lifecycle, resource, timing, fallback,
   and listening outcomes.
