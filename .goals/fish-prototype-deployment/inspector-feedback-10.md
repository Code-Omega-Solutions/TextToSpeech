# Inspector Feedback — Iteration 10

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: strict non-interactive SSH through the corrected
  existing private alias reached the designated Apple Silicon macOS target with
  public-key-only authentication, strict host checking, no forwarding except
  the temporary UI verification tunnel, and no host-key update. Read-only
  discovery confirmed separate production, managed prototype, external Fish,
  and UI listeners on ports 8000, 8001, 8002, and 5173.
- [ ] Criterion 2 — FAILED: tagged Fish 1.5 source documentation and the
  Apache-2.0 source license remain readable, while both authoritative S2-Pro
  entry points return 403. The live Fish checkout is pinned at the recorded
  revision but is not clean: Git reports both status and ignored-file content.
  The managed service has no artifact approval manifest and remains disabled.
  Exact accepted model/codec terms and a qualified smaller candidate therefore
  remain absent.
- [ ] Criterion 3 — FAILED: the live source has two reference WAV files, zero
  `.lab` files, and zero complete pairs. The deployed catalog exposes only
  `macos-say`. There are no qualified German/English male/female Fish voices,
  no four current Fish outputs, no bounded neural measurements, and no
  subjective listening result.
- [x] Criterion 4 — verified: production and prototype remain on distinct
  ports. The protected backend and UI credential files have equal content and
  owner-only permissions; that same bearer value authenticated both production
  and prototype speech. A valid unauthenticated prototype request returned
  401. Four recent log files and four browser assets contained neither the
  credential nor sampled speech text; browser assets contained no upstream
  origin.
- [ ] Criterion 5 — FAILED: deployed browser verification selected opaque
  Production and Prototype targets, generated a playable 3.26-second German
  WAV through the prototype, rejected unauthorized configuration with 401 and
  an unknown target with 403, exposed two targets without origins, and loaded
  resources only from the UI origin. The prototype offered only `macos-say`
  and no qualified Fish voice or Fish audio.
- [ ] Criterion 6 — FAILED: local admission, fallback, cancellation, deadline,
  cooldown, and cleanup tests pass. Live Fish-selected German and English
  requests truthfully returned playable native fallback. The managed neural
  worker is disabled, however, and the external port-8002 listener is not owned
  by a launch agent. Neural success, single-neural admission, idle unload,
  cooldown, pressure/probe failure, cancellation, deadline, sampled-resource,
  and owned cleanup behavior remain unverified live.
- [ ] Criterion 7 — FAILED: the stale definition remains absent from the
  loadable `.plist` set, present once under a quarantine name, disabled, and
  unloaded. Production stayed healthy and its process age remained measured in
  hours after the prototype/UI recreation attempt. The exact checked-in
  recreation procedure is nevertheless broken on the authorized target's
  default zsh: `status` is a read-only special parameter, so the EXIT trap's
  `status=$?` fails before it can test `rollback_required`, invoke rollback, or
  remove the protected directory. The inspector observed successful recreated
  prototype and production speech followed by a nonzero recreation result and
  independently reproduced `read-only variable: status`. The inspector removed
  the resulting owned temporary directory and confirmed both managed labels,
  all health checks, and quarantine state. In addition, the deployed backend
  checkout remains at `316b369`; the iteration-10 launcher hash is not deployed,
  while deployed frontend runtime and bundle hashes match the current build.
- [ ] Criterion 8 — FAILED: all local backend, frontend, runtime, policy,
  production/container, Companion, and whitespace gates pass, and feature
  tasks T004, T005, T006, and T010 remain honestly open. Mandatory exact
  artifact/reference approval, four Fish outputs, managed lifecycle evidence,
  current backend deployment, and reproducible rollback are still incomplete.

## Quality Gate

- Command: focused Fish launcher/deployment tests under WSL
- Result: PASS
- Details: 9 tests passed.
- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: all 327 tests passed.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`,
  `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: 9 unit tests passed; builds passed; 62 browser tests passed with 2
  optional fidelity tests skipped; the production scenario and all 6 Docker
  checks passed.
- Command: `python -m pytest -ra frontend/runtime/test_server.py`,
  `python -m pytest -ra checks/tests`, and isolated
  `checks/run_companion_validation.sh`
- Result: PASS
- Details: 3 runtime tests and 13 policy/licensing/Spec Kit tests passed; the
  full checked-in Companion hook passed.
- Command: strict live SSH, API, deployed browser, privacy, recreation, and
  rollback verification
- Result: FAIL
- Details: SSH access, authentication, native fallback, browser isolation,
  allowlisting, playable native audio, stale quarantine, cleanup, and
  production preservation passed. The documented zsh EXIT trap fails before
  rollback and cleanup, so forced rollback could not be exercised safely.
- Command: authoritative artifact/reference and deployed-state review
- Result: FAIL
- Details: authoritative model endpoints remain 403, the source is dirty, no
  managed approval manifest exists, there are no WAV/`.lab` pairs, Fish is
  disabled, and the deployed backend predates the latest launcher.
- Command: Builder diff and final worktree `git diff --check`, privacy review
- Result: PASS
- Details: no whitespace error or private target identity was found.
  `.github/copilot-memories.jsonl` and `.playwright-mcp/` remain untracked and
  unstaged.

## Issues Found

1. The new rollback trap is not valid in the actual macOS zsh environment.
   Assigning to reserved parameter `status` aborts the trap before rollback or
   cleanup, making the documented failure path unsafe and non-deterministic.
2. The authorized target still runs backend checkout `316b369`; the hardened
   iteration-10 launcher and binding logic are not deployed.
3. Exact model and codec approval remains unavailable. The live source is dirty
   and ignored-file-bearing, and no approval manifest binds a clean source tree,
   runtime entrypoint, model, codec, and applicable terms.
4. No approved WAV/transcript matrix exists, so Fish voices, four Fish outputs,
   managed neural lifecycle measurements, and listening acceptance remain open.

## What Must Be Fixed

1. Replace the zsh-reserved trap variable with a portable name, add an
   executable zsh test for both success and forced-failure paths, and rerun the
   exact native recreation plus protected-copy rollback until rollback and
   cleanup complete deterministically.
2. Deploy the current prototype-only launcher/configuration and verify exact
   deployed hashes without restarting or replacing production.
3. Obtain authoritative model/codec terms and bind an approval manifest to a
   clean pinned source tree and every runtime-loaded artifact.
4. Approve four exact Fish-consumed WAV/`.lab` pairs with provenance,
   intended-use permission, and cloning consent; then enable only the owned
   worker and verify all four Fish outputs and the complete live lifecycle.
