# Inspector Feedback — Iteration 6

## Verdict: FAIL

## Acceptance Criteria Check

- [x] Criterion 1 — verified: strict, non-interactive SSH through the existing
  authorized configuration reached the designated Apple Silicon macOS target.
  Read-only discovery and live checks confirmed distinct production, prototype,
  Fish-loopback, and persistent-UI listeners. Production stayed healthy and
  retained the same listener throughout prototype-only inspection and service
  recreation. No host identity, private path, credential, or raw inventory is
  recorded here.
- [ ] Criterion 2 — FAILED: the loaded managed configuration points to the
  recorded Fish source, model, and Firefly codec artifacts, and independent
  hashing matched all three recorded pins. The tagged source license is
  Apache-2.0 and the tagged README labels model weights CC BY-NC-SA 4.0.
  However, authoritative metadata for the exact model revision still returned
  403, and the applicable terms for the exact Firefly codec artifact remain
  unresolved. Reviewing the local FFmpeg build and FFmpeg legal page does not
  resolve the separately deployed Fish decoder artifact. The installation
  therefore still predates completion of the required exact-artifact/terms
  gate; T004 remains open.
- [ ] Criterion 3 — FAILED: the deployed catalog now truthfully exposes no
  reference IDs, which fixes the prior unqualified SLR83 advertisement.
  Authoritative public evidence supports Thorsten's explicit TTS contribution,
  while SLR83 establishes dataset licensing and volunteer provenance but not
  voice-cloning consent. No exact WAV/transcript pin or approved male/female
  bilingual matrix is present. Both German and English Fish-selected requests
  returned valid native-fallback WAV, not Fish audio. Consequently none of the
  four required Fish/reference combinations can be selected or verified, and
  subjective listening remains correctly pending. T005 and T006 remain open.
- [x] Criterion 4 — verified: production and prototype remain on distinct
  ports, the protected prototype credential authenticated production, and the
  protected UI credential matched it. Both credential files were owner-only.
  Unauthenticated requests returned 401. Fish remained loopback-only, and
  browser targets/assets exposed neither origins nor credentials.
- [ ] Criterion 5 — FAILED: the persistent deployed UI was browser-verified
  before and after recreation. It offered only opaque Production/Prototype
  choices, enforced 401 for unauthorized configuration and 403 for an
  unapproved target, isolated target choice between browser sessions, selected
  Fish with German, and produced playable fallback audio. It exposes no Fish
  voices, however, so the required qualified male/female selections and actual
  Fish playback are absent. The catalog also reports Fish `available` solely
  from lazy launcher configuration even though no managed Fish worker was
  admitted and live Fish-selected requests used `macos-say`; response metadata
  was truthful, but the catalog does not represent a qualified neural service.
- [ ] Criterion 6 — FAILED: the live configuration contains the exact 12 GiB
  reserve, 16 GiB worker budget, one-worker repository launcher, and offline
  artifact roots. Current sampled headroom was below the combined admission
  threshold. German and English Fish-selected requests therefore returned
  playable `macos-say` WAV with fallback `true` within a bounded time, while
  the pre-existing external Fish listener remained unchanged and was not a
  backend descendant. This safely verifies denial and native fallback, not a
  live managed launcher or neural lifecycle. No managed worker was started, so
  live single-neural admission, idle unloading, cooldown, active pressure/probe
  failure, cancellation, neural deadline, owned cleanup, and real worker
  resource behavior remain unqualified. The passing lifecycle tests are mocked
  or disposable-process checks, and the documentation correctly says sampled
  RSS is not hard unified/GPU-memory isolation. T010 remains open.
- [ ] Criterion 7 — FAILED: the persistent UI and currently loaded managed
  prototype agents both survived independent bootout/bootstrap recreation.
  Protected rollback copies exist, rollback is documented, post-recreation UI,
  prototype readiness/fallback speech, and production authenticated speech all
  returned 200, and production's listener was unchanged. However, a second
  unmanaged prototype launch agent remains in the persistent LaunchAgents
  directory with `RunAtLoad` and `KeepAlive`, uses the same prototype port, and
  is neither loaded nor explicitly disabled. A future login/reboot can race the
  managed agent for that port, so deterministic prototype startup and rollback
  are not established.
- [ ] Criterion 8 — FAILED: backend, frontend, runtime, browser, production,
  container, policy, licensing, Spec Kit, Companion writer/hook, and whitespace
  gates pass. Feature 007 honestly remains `implementing` with 8/12 tasks
  complete and T004/T005/T006/T010 open. Tracked-artifact and browser checks
  found no remaining known deployment identity or live credential. The real
  persistent UI, authentication, fallback, recreation, and production evidence
  is valid, but mandatory artifact terms, reference voices, neural execution,
  lifecycle qualification, and deterministic startup remain incomplete.

## Quality Gate

- Command: `uv run --python 3.12 --locked --no-sync pytest -ra` from
  `backend/` under WSL
- Result: PASS
- Details: 314 tests passed in 40.59 seconds.
- Command: `npm run test:unit`, `npm run build`, `npm run test:e2e`
- Result: PASS
- Details: 9 unit tests passed, both builds passed, 62 browser tests passed,
  and 2 optional visual-fidelity tests were skipped.
- Command: `npm run test:production`, `npm run test:docker`
- Result: PASS
- Details: the production recreation scenario and all 6 Docker contract checks
  passed; no owned test container remained.
- Command: `python -m pytest -q frontend/runtime/test_server.py`
- Result: PASS
- Details: all 3 persistent Python UI runtime tests passed.
- Command: `python -m pytest -ra checks/tests`
- Result: PASS
- Details: all 13 policy, licensing, Companion-hook, and Spec Kit checks passed.
- Command: Companion context materialization and
  `checks/run_companion_validation.sh`
- Result: PASS
- Details: materialization was idempotent and retained the honest 8/12
  `implementing` state. The checked-in hook passed in a clean isolated locked
  Windows environment. An initial unisolated invocation encountered the shared
  cross-platform virtual environment's access permissions and was not accepted
  as the gate result.
- Command: live strict-SSH service/audio checks and persistent browser UI check
- Result: FAIL
- Details: authentication, production preservation, native fallback,
  persistent UI recreation, session isolation, allowlisting, unauthorized
  access, client privacy, and playable fallback audio passed. No managed neural
  worker ran, no qualified Fish voice exists, and a conflicting persistent
  unmanaged prototype agent remains.
- Command: authoritative artifact/reference review and tracked-artifact
  sanitization scan
- Result: FAIL
- Details: tracked deployment identity sanitization passed, but exact model
  metadata and Firefly codec terms remain unavailable, and no four-way
  consented reference set is pinned.
- Command: `git diff --check`
- Result: PASS

## Issues Found

1. The exact installed artifact hashes are reproducible, but authoritative
   exact-revision model metadata and the Fish decoder's applicable terms were
   not completed before installation. FFmpeg review does not close that gate.
2. Removing the unqualified references makes the catalog safer, but it also
   leaves no male/female German/English Fish voices and no actual Fish result.
   A selectable Fish engine that always falls back is not the requested Fish
   prototype.
3. The repository launcher is configured but was never admitted. The live
   listener is still the separate pre-existing worker and is deliberately not
   adopted. Real lifecycle, cancellation, deadline, cleanup, and resource
   qualification therefore remain unverified.
4. Persistent UI deployment, recreation, rollback copies, security, playback,
   and session isolation now work. Persistent backend startup is still
   nondeterministic because an enabled legacy launch definition competes for
   the same port.

## What Must Be Fixed

1. Obtain and record authoritative terms/metadata for the exact model and
   Firefly codec revision before treating the installed artifacts as accepted;
   otherwise remove or disable the neural deployment.
2. Pin exact WAV/transcript assets with appropriate cloning consent for the
   required male/female German/English choices, advertise only those qualified
   references, and verify all four with actual Fish audio and truthful measured
   outcomes.
3. Qualify the repository-managed worker on the native target without adopting
   the external listener: neural admission/success, single-worker behavior,
   idle unload, cooldown, pressure/probe failure, cancellation, overall
   deadline, owned cleanup, resource sampling, and fallback.
4. Remove or explicitly disable the stale unmanaged startup definition, then
   repeat a full prototype/UI startup recreation and rollback check while
   confirming production remains untouched.
