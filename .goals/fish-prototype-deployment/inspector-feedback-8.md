# Inspector Feedback — Iteration 8

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: the authorized Apple Silicon macOS target was
  reached with the existing pinned key-exchange, strict host-key,
  non-interactive SSH constraints without changing trust. Sanitized discovery
  confirmed distinct production, prototype, UI, and loopback Fish listeners.
  The Fish listener is not owned by the managed prototype.
- [ ] Criterion 2 — FAILED: the launcher now compares the actual clean Git
  source revision/tree and requires complete model-file and codec-file coverage;
  forged-revision and omitted-file adversarial tests pass. However, the live
  configuration contains no source/checkpoint roots or artifact manifest.
  Pinned source and inference documentation remain public, but the exact
  authoritative model endpoints still return 403 and exact codec terms remain
  unavailable. No exact reviewed artifact decision exists.
- [ ] Criterion 3 — FAILED: the live catalog reports Fish unavailable and the
  deployed UI offers only native `macos-say`. There is no reference manifest,
  no exact four-directory WAV/`.lab` matrix, no qualified male/female choices,
  and no current Fish output. None of the four required German/English
  combinations is qualified; subjective listening remains pending.
- [x] Criterion 4 — verified: production and prototype use distinct ports and
  compare equal to the same protected bearer credential without exposing its
  value. Unauthenticated prototype speech returns 401. Two configured service
  logs contain neither the credential nor sampled speech text, and browser
  assets expose no credential or backend origin.
- [ ] Criterion 5 — FAILED: browser verification selected opaque Production and
  Prototype targets, generated playable prototype audio, kept sessions
  isolated, rejected unauthorized configuration with 401, and rejected an
  unapproved target with 403. It cannot discover or select qualified Fish
  voices and cannot return Fish audio because the neural gate remains closed.
- [ ] Criterion 6 — FAILED: authenticated German and English Fish-selected
  requests returned valid WAV through truthful `macos-say` fallback in about
  1.8 s and 1.1 s, respectively. Tests cover one-worker admission, idle unload,
  cooldown, pressure/probe failure, cancellation, deadlines, limits, and owned
  cleanup, and documentation correctly disclaims RSS/Metal isolation. Live
  neural success and those managed lifecycle behaviors remain unverified. The
  healthy loopback Fish process is external and was neither adopted nor
  terminated.
- [ ] Criterion 7 — FAILED: with a bounded post-bootout wait, independent
  managed prototype/UI recreation, protected-copy rollback, endpoint
  persistence, final restoration to Production, and production preservation
  all passed; the production PID/start identity and authenticated speech
  remained unchanged. An immediate recreation following the current runbook
  first failed at bootstrap and required safe recovery. More importantly, a
  second prototype `.plist` with `RunAtLoad` and `KeepAlive` remains in the
  launch-agent directory, is not launchctl-disabled, and is merely unloaded.
  It can conflict again at login, contradicting the recorded disablement claim.
- [ ] Criterion 8 — FAILED: every local backend, frontend, runtime, Docker,
  policy, Companion, and whitespace gate passes. Feature tasks T004, T005,
  T006, and T010 correctly remain open, but the deployment record falsely says
  the stale definition was disabled. Mandatory live Fish/reference and managed
  lifecycle qualification is absent.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: the first attempt found no `pytest` in the disposable environment;
  after the convention-permitted locked restore, all 324 tests passed in
  24.82 seconds.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`,
  `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: 9 unit tests passed; the build passed; 62 browser tests passed with
  2 optional fidelity tests skipped; the production scenario and all 6 Docker
  checks passed.
- Command: `python -m pytest -ra frontend/runtime/test_server.py`
- Result: PASS
- Details: all 3 persistent runtime tests passed.
- Command: `python -m pytest -ra checks/tests`
- Result: PASS
- Details: all 13 policy, licensing, Spec Kit, and Companion-hook tests passed.
- Command: `checks/run_companion_validation.sh`
- Result: PASS
- Details: a clean isolated locked environment completed the backend subset,
  frontend unit/browser suites, and all 13 policy checks.
- Command: live strict-SSH API, recreation/rollback, and browser checks
- Result: FAIL
- Details: auth, privacy, allowlisting, session isolation, native fallback,
  managed recreation/rollback, UI persistence, and production preservation
  passed. Fish/reference/lifecycle qualification is absent, and the stale
  startup definition remains enabled for future login loading.
- Command: authoritative artifact/reference review
- Result: FAIL
- Details: source license and tagged inference requirements are reachable, but
  exact model metadata remains 403, codec acceptance is missing, and no live
  artifact or reference approval manifest exists.
- Command: `git diff ... --check` and changed-artifact privacy scan
- Result: PASS
- Details: no whitespace error or private target identity was found. Pattern
  hits were documentation wording and explicit unit-test placeholders.
  `.github/copilot-memories.jsonl` and `.playwright-mcp/` remain untracked and
  unstaged.

## Issues Found

1. The core requested result is still absent: no approved exact Fish artifacts,
   no four consented references, no four actual Fish outputs, and no live
   managed neural lifecycle evidence.
2. The live startup state contradicts the iteration-8 record. The stale
   prototype launch definition is a loadable `.plist` with automatic restart
   enabled, is not marked disabled by launchctl, and is only currently unloaded.
3. The runbook's immediate bootout/bootstrap sequence failed once. A bounded
   unload wait allowed all later recreation and rollback checks to pass, so the
   documented sequence is not yet deterministic as written.
4. The external healthy Fish listener is outside repository ownership and
   cannot count as managed lifecycle evidence or be terminated by this service.

## What Must Be Fixed

1. Obtain authoritative exact model and codec terms through legitimate access,
   then create an approval manifest bound to the actual clean source checkout
   and every runtime-loaded file.
2. Approve four exact Fish-consumed WAV/`.lab` pairs with verified public
   provenance, cloning consent, terms, and intended use.
3. Disable or safely quarantine the exact stale prototype launch definition and
   verify it remains disabled across startup. Add a bounded unload wait to the
   recreation/rollback procedure and correct the false checked-in claim.
4. Enable only the reviewed managed worker, then verify the four Fish outputs,
   bounded resource/timing results, and all required lifecycle behavior live
   while preserving production and leaving the external process untouched.
