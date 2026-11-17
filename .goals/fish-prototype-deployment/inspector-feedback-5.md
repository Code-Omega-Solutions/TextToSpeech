# Inspector Feedback — Iteration 5

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: strict, non-interactive SSH using the existing
  host key and identity reached the designated target without changing trust.
  Independent read-only checks confirmed Apple Silicon macOS, distinct
  production/prototype listeners, and a loopback-only Fish listener. The
  production process predates this goal and remained healthy during inspection.
- [ ] Criterion 2 — FAILED: the live Fish source revision and both deployed
  model/codec file hashes match the sanitized record. The pinned source license
  is Apache-2.0, upstream labels the model weights CC BY-NC-SA 4.0, and the
  smaller Fish deployment sampled below the 16 GiB worker budget. However,
  authoritative model-revision metadata remained inaccessible and the codec's
  applicable release terms are explicitly unresolved. Installation and
  synthesis therefore occurred before the exact artifact/terms gate required by
  this criterion was complete.
- [ ] Criterion 3 — FAILED: independent authenticated requests produced valid
  playable mono 44.1 kHz WAV for all four German/English and male/female
  combinations, with truthful `fish-speech`/no-fallback headers. Observed
  outcomes were 208,940 bytes/24.91 s, 176,172 bytes/21.50 s,
  163,884 bytes/21.52 s, and 192,556 bytes/23.25 s; sampled Fish listener-tree
  RSS rose from about 3.83 GiB to 4.25 GiB. No subjective listening result was
  invented. Thorsten's public CC0 TTS contribution is strong provenance, but
  the selected SLR83 volunteer recording has only dataset/license provenance,
  not reviewed voice-cloning consent. Exact deployed reference-file pins are
  also absent. The backend nevertheless advertises both references for both
  languages while T005/T006 remain open.
- [x] Criterion 4 — verified: production and prototype use distinct ports; the
  same protected credential authenticated both backends; unauthenticated
  prototype speech returned 401. Fish is loopback-only. Browser assets, target
  discovery, resource URLs, and controls exposed neither backend origins nor a
  credential, and no additional user-managed secret was required.
- [ ] Criterion 5 — FAILED: the current UI code works through a temporary local
  standalone proxy. Browser verification selected Prototype, discovered Fish
  and both references, submitted a German request, and received playable WAV.
  An unauthenticated configuration request returned 401 and an unapproved target
  returned 403. However, this was not a deployed persistent UI service; the
  target has no UI runtime and no other approved UI host/startup registration is
  evidenced. A transient inspector/Builder proxy is not the deployed UI required
  by the criterion.
- [ ] Criterion 6 — FAILED: 311 backend tests cover mocked single admission,
  owned-process cleanup, idle unload, cooldown, pressure/probe failure,
  cancellation, size limits, and remaining-deadline fallback. The live service
  does not use the repository-managed `FishProcess` worker and has opportunistic
  fallback disabled. A valid deployed legacy-neural German request returned 503
  rather than language-correct native speech; the Builder's worker-pause check
  likewise returned 504. Native admission, unload, cooldown, cancellation,
  pressure/probe behavior, and process ownership are therefore unqualified.
  Sampled process-tree RSS is not hard unified/GPU-memory isolation.
- [ ] Criterion 7 — FAILED: production authenticated WAV succeeded immediately
  before and after live Fish checks, its process predates the goal, and the
  Builder records prototype-only launch-agent recreation and rollback. The
  prototype is currently healthy. There is still no persistent UI deployment,
  UI startup configuration, UI recreation check, or UI rollback target, so the
  complete prototype/UI persistence requirement is not met.
- [ ] Criterion 8 — FAILED: backend, frontend, browser, container, policy, and
  isolated Companion-hook gates pass, and feature 007 honestly remains
  `implementing` with 8/12 tasks complete. The live deployment evidence is real,
  not mocked. Nevertheless, the mandatory artifact, reference, managed
  lifecycle/fallback, and deployed-UI gates remain open. Sanitization review
  also found a private target identity still present in the tracked historical
  `specs/005-selectable-speech-engines/.spec-context.json`. It predates this
  goal and was not added by the Builder's diff, but the final repository still
  violates the goal's requirement that private host identities remain outside
  tracked artifacts.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: 311 tests passed in 25.84 seconds.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`
- Result: PASS
- Details: 9 unit tests passed; both builds passed; 62 browser tests passed and
  2 optional visual-fidelity tests were skipped.
- Command: `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: the production recreation scenario passed and all 6 Docker contract
  checks passed; owned test containers and volumes were absent afterward.
- Command: `python -m pytest -ra checks/tests`
- Result: PASS
- Details: all 13 policy, licensing, Companion-hook, and Spec Kit setup tests
  passed.
- Command: Companion context writer and `checks/run_companion_validation.sh`
- Result: PASS
- Details: the writer idempotently synced 0 events and retained the honest
  8/12 `implementing` state. The checked-in hook passed using a unique locked
  Windows environment. A WSL attempt used an incompatible old Node runtime and
  was not accepted as the gate result.
- Command: live strict-SSH service/audio checks and browser verification
- Result: FAIL
- Details: service, four-way Fish audio, shared authentication, production
  preservation, selector, allowlist, unauthorized request, and client privacy
  checks passed. The deployed fallback request returned 503 instead of native
  speech, and the browser UI existed only as a temporary local proxy.
- Command: tracked-artifact sanitization review
- Result: FAIL
- Details: iteration-5 additions contain no private address, but one pre-existing
  tracked Spec Kit context still contains the private target identity.
- Command: `git diff --check`
- Result: PASS

## Issues Found

1. The deployment crossed an unresolved artifact gate. Exact live source/model/
   codec hashes are real, but authoritative model-revision evidence and codec
   terms were not completed before installation.
2. The public references are advertised and deployed before the intended-use
   review is complete. SLR83's CC BY-SA dataset permission and volunteer
   provenance do not by themselves establish consent for voice cloning, and the
   exact deployed reference assets are not immutably identified.
3. The required headroom-first lifecycle is test-only. The deployed external
   worker bypasses managed admission, unloading, cooldown, cancellation and
   pressure behavior, and a live unavailable-neural request does not fall back
   to native speech.
4. UI behavior is functional, secure, and browser-verified, but only through a
   temporary local proxy. No persistent deployed UI/startup/rollback boundary
   exists.
5. A historical tracked Companion context still contains private deployment
   identity data. No new private identifier was added in iteration 5, but the
   repository's final state does not meet the privacy boundary.

## What Must Be Fixed

1. Resolve and record authoritative model/codec/runtime terms and explicit
   artifact acceptance. Disable or remove the private deployment until that
   gate is cleared rather than treating fixed hashes as permission.
2. Pin the exact reference WAV/transcript sources and establish appropriate
   voice-cloning/intended-use consent. Do not advertise a reference-language
   combination until its gate is complete.
3. Deploy a reviewed repository-managed launcher with the 12 GiB reserve,
   16 GiB budget, one-neural admission, and native fallback enabled. Safely
   verify admission, idle unload, cooldown, pressure/probe failure, cancellation,
   overall deadline, and owned-process-only cleanup on the native prototype.
4. Deploy the UI on an approved persistent host/service boundary, then verify
   startup recreation, rollback, selector persistence, unauthorized access, and
   Fish playback there.
5. Sanitize the tracked historical Companion context without committing the
   private values elsewhere, rerun the Companion hook and all quality gates, and
   keep subjective listening explicitly pending until the operator performs it.
