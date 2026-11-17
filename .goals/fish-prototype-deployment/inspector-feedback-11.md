# Inspector Feedback — Iteration 11

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: strict non-interactive, public-key-only SSH with
  strict host checking, host-key updates disabled, and forwarding disabled
  reached the designated Apple Silicon macOS target. Read-only discovery found
  distinct production, prototype, Fish-loopback, and UI listeners on the
  expected ports without exposing target identity or credential material.
- [ ] Criterion 2 — FAILED: tagged Fish 1.5 source, inference documentation,
  and the Apache-2.0 source license remain readable, while both authoritative
  model entry points return 403. The live pinned source has two dirty entries
  and 61 ignored entries. The managed configuration has no approval manifest,
  keeps artifact approval false, and has no worker command. Exact accepted
  model/decoder terms and a measured smaller candidate therefore remain absent.
- [ ] Criterion 3 — FAILED: the live source has two WAV files, zero `.lab`
  files, and zero complete pairs. The current catalog reports Fish unavailable
  with zero voices. There are no current qualified German/English male/female
  Fish outputs, managed neural measurements, or subjective listening result.
- [x] Criterion 4 — verified: production and prototype use distinct ports.
  Production, prototype, and UI credential files have identical content and
  owner-only mode 0600. That credential authenticated production and prototype
  speech, while an unauthenticated prototype request returned 401. Two current
  service logs and four deployed browser assets contained neither the
  credential nor sampled speech text; browser assets contained no upstream
  origin.
- [ ] Criterion 5 — FAILED: deployed browser verification selected only opaque
  Production/Prototype targets, generated a playable 2.70-second German WAV
  through the prototype, rejected unauthorized configuration with 401 and an
  unknown target with 403, loaded resources only from the UI origin, and
  exposed no credential input or upstream address. The prototype UI offered
  only `macos-say`; no qualified Fish voice or Fish audio was available.
- [ ] Criterion 6 — FAILED: all local lifecycle, admission, fallback,
  cancellation, deadline, cooldown, and cleanup tests pass. Live Fish-selected
  German and English requests truthfully returned playable native fallback.
  The managed neural worker remains disabled, however, while the separate
  Fish-loopback listener is not owned by the managed prototype. Neural success,
  single-neural admission, idle unload, pressure/probe failure, cooldown,
  cancellation, deadline, and owned cleanup remain unverified live. The
  sampled RSS of the separate listener is not unified/Metal memory isolation.
- [ ] Criterion 7 — FAILED: the portable `exit_code` trap and executable native
  fake-launchctl success/failure tests pass, but the real failure path is not
  repeatable. The managed plist files were mode 0400 after the prior rollback.
  A legitimate verifier failure reached rollback, where `cp -p` could not
  overwrite the read-only destination and returned permission denied. The
  protected restore and deterministic cleanup contract therefore failed.
  The inspector reloaded only the two unchanged managed definitions and
  confirmed final production/prototype/UI health plus authenticated production
  and prototype WAV speech. Production's process age still predated this
  inspection by more than 13 hours.
- [ ] Criterion 8 — FAILED: backend, frontend, browser, runtime, policy,
  production/container, whitespace, privacy, and native zsh test gates pass.
  The checked-in Companion hook fails in the available supported Windows
  invocation because its new test asks Windows `os.stat` for a POSIX executable
  bit. More importantly, live rollback fails, the deployment record incorrectly
  claims it passed, and tasks T004, T005, T006, and T010 remain open.

## Quality Gate

- Command: focused Fish launcher/deployment tests under WSL
- Result: PASS
- Details: 11 tests passed.
- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: all 329 tests passed.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`,
  `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: 9 unit tests passed; builds passed; 62 browser tests passed with 2
  optional fidelity tests skipped; the production scenario and all 6 Docker
  checks passed.
- Command: `python -m pytest -ra frontend/runtime/test_server.py` and
  `python -m pytest -ra checks/tests`
- Result: PASS
- Details: 3 runtime tests and 13 policy/licensing/Spec Kit tests passed.
- Command: isolated `checks/run_companion_validation.sh`
- Result: FAIL
- Details: the backend portion reached
  `test_prototype_recreation_helper_has_portable_exit_trap_and_tests`, where
  Windows `os.stat` did not report `stat.S_IXUSR`. The file is mode 100755 in
  git and native macOS zsh execution passed, so the hook/test is not portable
  across the project's supported invocation environments.
- Command: native `zsh -n` plus executable success/forced-failure test
- Result: PASS
- Details: both scripts parsed and the fake-launchctl success and rollback
  paths passed on the authorized macOS target.
- Command: strict live SSH, API, deployed browser, recreation, and rollback
- Result: FAIL
- Details: authentication, native fallback, browser isolation, playable audio,
  final service recovery, and production preservation passed. A real
  verifier-triggered rollback failed while restoring a read-only managed plist.
- Command: authoritative artifact/reference and managed-neural review
- Result: FAIL
- Details: authoritative model pages remain 403, source state is dirty, no
  approval manifest or complete WAV/`.lab` pair exists, Fish has zero qualified
  voices, and the managed worker is disabled.
- Command: Builder diff and final worktree `git diff --check`, privacy review
- Result: PASS
- Details: no whitespace error, secret, or private target identifier was found.
  `.github/copilot-memories.jsonl` and `.playwright-mcp/` remain untracked and
  unstaged.

## Deployed Hash Verification

- Deployed checkout: `316b369b66ca86d80fe36353cac321bee1ee60a0`.
- Launcher: deployed and HEAD both
  `25df2f4489596853613e12f7518505fc1271f121af5db31b6251f06151f85b3e`.
- Recreation helper: deployed and HEAD both
  `e562aaa397e31bea560bc84f927c63acf9543c6e29ed7500e9731aeef8a9cb42`.
- Recreation test: deployed and HEAD both
  `a3ca799b113d4faeda59d9d4f2bd0f0b34a089af612c9663aa8c59857ad132ce`.
- Native-only template: deployed and HEAD both
  `70981e28e355dc00937579c969f57f59a89594b6529a47b8f37ec3b71c02bb86`.
- Runbook: deployed
  `9d1371c1e05e0ba2c51bf19d43f5a082efb394685b05f68aa30cef00fba7fb1c`,
  but HEAD is
  `282c9a56786586a2b5079ebb8c815a8ee968e802684b43f4df093e72f0fce97b`.
  The iteration-11 quickstart incorrectly labels the deployed runbook hash as
  the checked-in hash.
- Frontend runtime and built tree match the current local build at
  `6a1102290737af97b50fe1ae48f938cea1eff58e4696d8d2d99204d5285d7fd3`
  and
  `8d7c8df498593c856356554793ab6b88d9689fecb831622c32aa9b21ba7dbee3`.

## Issues Found

1. The rollback makes its protected copies read-only and restores their mode
   with `cp -p`. After one rollback, the managed destination is mode 0400. A
   later rollback cannot overwrite it, so the procedure is not idempotent and
   can leave both managed labels unloaded.
2. The executable test covers one failure in a fresh directory but never a
   second rollback against files restored read-only. It therefore misses the
   native failure observed here.
3. The helper does not bind labels to known managed identities. It rejects only
   a label containing the lowercase word `production`; arbitrary distinct
   launch labels still pass despite the runbook claiming only the two managed
   prototype labels are accepted.
4. The sanitized iteration-11 deployment record contains a stale runbook hash
   and claims successful protected-copy rollback even though the independently
   exercised current failure path is broken.
5. Exact model/codec acceptance, a clean source tree, four consented and
   provenance-qualified WAV/transcript pairs, four Fish outputs, listening
   acceptance, and complete live managed-neural lifecycle evidence remain open.
6. The required Companion validation hook is not portable to its Windows
   branch because a Python filesystem mode check is used instead of checking
   the git executable mode or running the native executable test where zsh is
   available.

## What Must Be Fixed

1. Preserve secure but writable owner mode for managed destination plists, or
   restore atomically in a way that can replace a read-only destination. Add an
   executable test that performs at least two consecutive forced rollbacks,
   verifies modes/content, and run it plus the exact live failure path again.
2. Bind the helper to explicit approved managed labels/plists rather than a
   substring heuristic, while keeping production outside every operation.
3. Deploy the actual current runbook/backend state and correct the sanitized
   hash and rollback evidence only after independent live success.
4. Make the Companion hook/test pass in its Windows branch without weakening
   the native executable zsh check.
5. Complete T004, T005, T006, and T010: approve exact runtime/model/codec terms
   and a clean manifest, approve four exact references, enable only the owned
   worker, and verify all four Fish outputs plus the full live lifecycle.
