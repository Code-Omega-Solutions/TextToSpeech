# Inspector Feedback — Iteration 7

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: the existing authorized SSH path connected with
  the required pinned key-exchange and strict host-key constraints. Read-only
  discovery confirmed the designated Apple Silicon macOS target, distinct
  production/prototype/UI/Fish-loopback roles, and live listeners without
  changing production or exposing private identities, paths, or credentials.
  The Builder's claim that no authorized deployment session was available is
  contradicted by this check.
- [ ] Criterion 2 — FAILED: the tagged Fish 1.5 source, inference documentation,
  and source/model license statements were independently rechecked through
  legitimate public paths. The authoritative model page and exact-revision API
  still return 403, and no exact model/codec approval manifest exists. The new
  launcher is not a sufficient exact-artifact gate: its `source_revision` is a
  syntactic manifest string that is never compared with the source tree, and
  its model manifest may name only an arbitrary subset of checkpoint files.
  The installation therefore still predates exact artifact/terms acceptance.
- [ ] Criterion 3 — FAILED: no qualified four-record reference manifest or
  approved WAV/transcript matrix exists. The deployed catalog has no voices,
  the browser voice selector is disabled, and live German and English
  Fish-selected requests both returned playable `macos-say` fallback rather
  than Fish audio. None of the four required Fish combinations was verified;
  subjective listening remains pending. The local reference gate also does not
  bind its hashed manifest paths to the files Fish 1.5 actually resolves from
  `references/<id>`, so an approved catalog could synthesize from different
  files than those reviewed.
- [x] Criterion 4 — verified: the deployed production and prototype origins are
  distinct and loopback-only, the protected UI/prototype bearer token
  authenticated both services, credential files deny group/other access, and
  unauthenticated speech/configuration requests returned 401. The browser
  exposed neither credentials nor upstream origins, and no second user-managed
  secret was required.
- [ ] Criterion 5 — FAILED: the deployed persistent UI exposes only opaque
  Production/Prototype targets, rejects unauthorized configuration with 401
  and an unapproved target with 403, and returns playable audio. It exposes no
  qualified male/female Fish voices. Worse, the deployed pre-iteration code
  still advertises Fish as available with an empty voice catalog; selecting it
  in the browser produced native fallback, not Fish speech. The local catalog
  fix from this commit is not deployed.
- [ ] Criterion 6 — FAILED: repository tests cover admission, lifecycle,
  cancellation, cleanup, resource sampling, deadlines, and fallback, but the
  authorized target still has the external Fish listener and no qualified
  repository-managed neural run. Live requests only verify language-preserving
  native fallback. Neural success, one-worker admission, idle unload, cooldown,
  pressure/probe failure, cancellation, deadline, and owned cleanup remain
  unverified; sampled RSS remains correctly documented as non-isolation.
- [ ] Criterion 7 — FAILED: the prototype and persistent UI are currently
  healthy, and production health/readiness/authenticated WAV speech succeeded.
  However, the deployed prototype does not match Builder commit `2b7f632`, its
  loaded configuration is not the new fail-closed template, and no
  prototype/UI recreation or rollback was performed this iteration. One
  conflicting legacy prototype launch definition still exists and is not
  disabled, so deterministic startup remains unresolved.
- [ ] Criterion 8 — FAILED: all local backend, frontend, runtime, policy,
  licensing, Spec Kit, Companion, Docker, and whitespace gates pass, and the
  feature artifacts honestly keep T004/T005/T006/T010 open. Mandatory live
  qualification fails: the authorized deployment was not updated, the four
  Fish outputs and managed lifecycle are absent, and deterministic startup is
  still broken.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: 320 tests passed in 23.39 seconds.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`,
  `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: 9 unit tests passed; builds passed; 62 browser tests passed with 2
  optional fidelity tests skipped; the production scenario and all 6 Docker
  checks passed.
- Command: `python -m pytest -ra frontend/runtime/test_server.py`
- Result: PASS
- Details: all 3 persistent UI runtime tests passed.
- Command: `python -m pytest -ra checks/tests`
- Result: PASS
- Details: all 13 policy, licensing, Companion-hook, and Spec Kit checks passed.
- Command: `checks/run_companion_validation.sh`
- Result: PASS
- Details: the first WSL attempt used an obsolete Node binary and the first
  Windows attempt encountered the shared cross-platform environment. A clean
  isolated locked Python 3.12 environment completed the checked-in backend,
  frontend, browser, and policy validation successfully.
- Command: live strict-SSH API checks and deployed browser verification
- Result: FAIL
- Details: access, authentication, production preservation, privacy,
  allowlisting, and native fallback passed. The target still runs older
  prototype code/configuration, exposes no qualified voices or Fish output,
  and retains an enabled conflicting startup definition.
- Command: authoritative artifact/reference review
- Result: FAIL
- Details: legitimate tagged source paths were reachable, while exact
  authoritative model metadata remained 403. Exact codec acceptance and the
  four consented references are absent; the new manifest checks do not bind all
  runtime and reference inputs actually consumed.
- Command: `git diff HEAD^ HEAD --check` and private-data/staging scan
- Result: PASS
- Details: no whitespace errors, private host/address/path evidence, tracked
  authorized-target identity, or staged `.github/copilot-memories.jsonl` was
  found.

## Issues Found

1. The Builder did not use the available authorized deployment path. The live
   target does not contain this iteration's code or fail-closed launch
   configuration.
2. The artifact launcher trusts a declared source revision without verifying
   the source tree and accepts a caller-selected subset of model files. It does
   not establish that every runtime input matches the reviewed revision.
3. The reference manifest hashes arbitrary paths, but Fish 1.5 loads
   `references/<id>` beneath its working directory. Nothing proves that the
   files synthesized for an advertised ID are the files the manifest approved.
4. There are still no consented German/English male/female references or four
   real Fish outputs. The deployed UI offers Fish without voices and returns
   native fallback.
5. The repository-managed worker and its lifecycle remain unqualified, and the
   conflicting legacy prototype startup definition remains enabled.

## What Must Be Fixed

1. Bind artifact approval to the actual source checkout and every runtime-loaded
   checkpoint/codec file; align launcher/config environment names and add
   adversarial tests for forged revisions and omitted files.
2. Bind each qualified reference ID to the exact WAV/transcript files consumed
   by Fish, then obtain and pin four appropriately consented references.
3. Use the available authorized path to deploy the reviewed configuration,
   disable the verified stale prototype definition, and recreate only the
   managed prototype/UI services with rollback evidence.
4. Verify four authenticated German/English male/female requests as actual Fish
   audio with truthful metadata, bounded measurements, and pending/listened
   status recorded honestly.
5. Qualify the managed lifecycle on the native target, then repeat production
   preservation, authentication, privacy, browser, persistence, and startup
   checks.
