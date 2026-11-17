# Goal: Deploy a Working Fish Speech Prototype

## User Request

Create a working prototype with Fish voices enabled and deployed on the newly
designated host. Remove the need for an additional authentication key and reuse
the production authentication-token mechanism and same token. Run production
and prototype on different ports. Update this project's UI accordingly.

Private host identities and configuration remain outside tracked artifacts.
The orchestrator supplies the designated target privately to the Builder.

## Refined Goal

Deliver and independently verify a usable deployed Fish speech prototype and
updated speech UI, preserving the existing production service. Inspect the
designated host before choosing topology: native inference and resource fallback
require macOS; a non-macOS host may serve the UI/proxy while the existing
authorized Mac retains inference. Reuse the production backend bearer token
server-side with no additional prototype/Fish/operator-token setup for the
user; do not make privileged UI configuration public or expose tokens to browser
assets. Preserve the previously requested headroom-first behavior: start with
a 12 GiB reserve and 16 GiB monitored worker budget, try smaller Fish variants
first, and use native `say` in the resolved requested language when optional
resources are unavailable, regardless of engine/voice preference.

The user invoked this goal explicitly to implement and deploy. The interview
returned that the user is unavailable; pragmatic defaults are isolated prototype
installation and UI deployment after exact artifact/reference review, no
production restart or replacement, and no purchases or external inference.

## Acceptance Criteria

- [ ] Criterion 1: Read-only discovery establishes the target OS, roles, existing
  service identities and free ports without exposing secrets or disrupting
  production. The chosen topology supports native fallback; any incompatible
  target or inaccessible host is reported honestly, not silently substituted.
- [ ] Criterion 2: Exact pinned Fish runtime, model and codec revisions and
  applicable terms are reviewed before download/installation. A smaller
  German/English Fish candidate is evaluated first. No hosted inference or
  unreviewed weight/reference downloads are used.
- [ ] Criterion 3: Live authenticated prototype requests produce valid playable
  Fish speech for German and English, with male and female choices in each.
  References have documented public provenance and appropriate intended-use
  permissions; prefer explicit TTS contributions such as original Thorsten
  WAV/transcript assets. Do not promise bilingual identity without evidence.
  Four combinations are verified with synthetic phrases, reported actual engine
  metadata and measured bounded resource/timing outcomes. Subjective listening
  acceptance, if unavailable, is identified as pending rather than invented.
- [ ] Criterion 4: The deployed production and prototype use distinct ports and
  the same existing production bearer-token mechanism/token. The prototype
  requires no additional user-managed authentication secret. Authentication
  remains enforced; backend/upstream credentials stay server-side and out of
  logs, git, screenshots, tool output and client assets.
- [ ] Criterion 5: The updated UI can select production versus prototype and
  discover/select the qualified Fish voices with language-correct requests,
  returning playable audio. Endpoint allowlisting and privileged configuration
  authorization remain effective; no arbitrary upstream proxy is introduced.
  Verify the deployed UI in a browser, including an unauthorized attempt.
- [ ] Criterion 6: Neural lifecycle and language-only native fallback preserve
  the existing contract, cancellation, output limits and overall deadline.
  Verify single-neural admission, idle unloading, cooldown and pressure/probe
  failure handling without generating artificial memory pressure on shared
  services. Record that sampled RSS is not hard unified/GPU-memory isolation.
  Only owned prototype processes may be terminated. Conditional 8 GiB reserve
  is permitted only with evidence no suitable smaller Fish candidate can fit;
  document any such decision and do not lower limits merely to bypass admission.
- [ ] Criterion 7: Prototype/UI startup configuration persists across an
  approved prototype-only restart/recreation, with documented rollback.
  Production health and authenticated speech work before and after deployment;
  production process/configuration/token are not replaced or restarted.
- [ ] Criterion 8: Relevant backend and frontend tests/build pass. Spec Kit
  feature artifacts, required Companion hooks, living specs and coverage maps
  reflect actual delivered behavior versus open gates. Native deployment claims
  have real evidence, not just mocks. Inspector independently verifies code,
  live services and UI. If a necessary access/rights/platform gate cannot be
  resolved safely, return BLOCKED with precise remaining work rather than PASS.

## Scope Boundaries

**In scope:**
- Existing uncommitted Fish resource-policy work and feature 007: integrate,
  correct and commit relevant changes as part of this goal.
- Backend managed Fish runtime integration, server-side shared authentication,
  UI configuration/discovery/playback and isolated live prototype deployment.
- Read-only inspection of designated deployment systems and existing authorized
  Mac, using existing SSH trust/credentials; do not modify known_hosts.
- Reviewed runtime/reference downloads, isolated dependency installation and
  prototype/UI service registration or restart necessary for this goal.
- Synthetic short audio checks and private operational evidence outside git;
  sanitized repeatable runbooks in project documentation.

**Out of scope:**
- Production restart, replacement, token rotation, port changes or migration.
- New hardware, purchases, hosted/cloud inference, cloned celebrity voices,
  license/access-control bypasses and private operational data in commits.
- Weakening authentication or exposing configuration publicly to remove a key.
- Unrelated untracked `.github/copilot-memories.jsonl`: preserve untouched and
  never stage it. Preserve all unrelated changes.
- Pushing, merging or rewriting existing history without separate authorization.

## Applicable Project Conventions

**Quality gate commands:**
- Backend (supported Python, Linux/WSL where POSIX checks require it):
  `uv run --python 3.12 --locked --no-sync pytest -ra` from `backend/`, with
  focused selectors first. Restore locked dependencies only after missing-tool
  failure or manifest changes. Existing local environment was restored.
- Frontend: `npm run test:unit`, `npm run build`, relevant
  `npm run test:e2e`; production/container checks where deployment paths change.
- `git diff --check`; inspect new artifacts for secrets/private operational data.
- Native qualification and deployed UI browser checks are additional to mocks.

**Commit convention:**
- Builder: `type(scope): [B] description`, conventional imperative title <=72
  characters; exactly one implementation commit per iteration.
- Inspector: `chore(scope): [I] description`, <=72 characters; exactly one
  feedback/status commit per iteration.
- Required trailers:
  Builder `Assisted-by: OpenAI:GPT-5.6 Luna`;
  Inspector `Assisted-by: OpenAI:GPT-5.6 Sol`.
- Both include `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.

**Guidelines:**
- `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md`.
- `.specify/memory/constitution.md`,
  `.github/instructions/speckit.instructions.md`, applicable nested instructions.
- Existing feature `specs/007-fish-backend-enablement/` and active feature pointer.
- Related feature 005/006, `living-specs.yml` and affected capability maps.

**Rules:**
- Consult memory first where available. Prior attempts found memory-store absent
  and legacy memory files unavailable; do not invent successful memory access.
- Follow required Spec Kit phases/hooks at the earliest outdated artifact, not
  by creating duplicate feature specifications. Keep real deployment permission
  separate from unresolved exact-artifact/reference gates.
- Preserve monorepo boundaries, licensing/NOTICE files, private-data constraints,
  bounded concurrency/deadlines and safe explicit failures.
- Do not commit raw inventories, credentials, private hostnames/addresses, remote
  filesystem paths, recordings or generated audio. Record only sanitized evidence.
- Goal file is immutable. Builder and Inspector communicate only via committed
  work and feedback files; Inspector must assess independently.

## Starting Evidence and Known Gaps

The initial worktree includes opt-in `FishProcess`, shared memory probes,
native fallback and shutdown cleanup, related tests/docs and feature 007.
The previous affected backend check reported 175 passing tests on Linux, not
native Fish qualification. No model was installed and no service was deployed.
Feature 007 currently has 8/12 tasks checked; exact artifact acceptance,
bilingual references, launcher integration and native rollout remain open.

Fish 1.5 tagged documentation provides an MPS path, German/English and reference
cloning claims; generic GPU-memory guidance is not measured total Mac usage.
Tagged source LICENSE is Apache 2.0; separate authoritative checkpoint/codec
metadata fetches previously returned 403. Do not bypass restrictions or equate
source license with weight permission. Drama 3 MLX 3-bit reports ~22.5-24 GB peak,
above the initial worker budget; API compatibility is not established.

Production and prototype previously existed as separate listeners on the Mac.
The existing UI/container has separate operator-token and backend-token concepts;
unifying user setup must retain privilege and upstream security boundaries.
No active goal resumes this work; the prior UI goal is completed.
