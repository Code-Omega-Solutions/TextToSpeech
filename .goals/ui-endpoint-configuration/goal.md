# Goal: Complete and publish UI endpoint configuration

## User Request

"complete implementation of the spec and merge the the feature into main"

"after the merge, push main to origin"

## Refined Goal

Implement all requirements in `specs/006-ui-endpoint-configuration/ui-endpoint-configuration.spec.md`, including the configuration tab, safe runtime endpoint switching, capability-aware speech controls, compatible legacy generation, and durable container-side settings with operator documentation. Complete the required Companion planning, tasks, implementation, and directly related living-spec updates. Obtain independent Inspector verification, including browser verification, before merging the feature into local main and pushing main to origin. Do not change any live installation.

## Acceptance Criteria

- [ ] Criterion 1: FR-001 through FR-005 work: accessible settings tab, visible active versus unsaved endpoint, validation and explicit errors, new routing without image rebuilding, and stale discovery isolation.
- [ ] Criterion 2: FR-006 through FR-008 work: supported engine/voice choices appear, unsupported selectors are absent, legacy speech works using an evidence-backed default contract, and unsupported discovery is distinguished from authentication, network, invalid-catalog and empty-catalog failures.
- [ ] Criterion 3: FR-009 through FR-012 work: failed saves preserve saved configuration; a shared container-side file survives reload, restart and container replacement with retained storage; documentation gives its exact path, permissions, initialization, precedence and a synthetic Compose example.
- [ ] Criterion 4: FR-013 through FR-015 work: credentials stay server-side, settings writes respect the operator boundary, unauthorized destinations cannot receive credentials, and existing speech privacy, bounded requests, language behavior and playback/download behavior are preserved.
- [ ] Criterion 5: Acceptance evidence covers controlled-service switching, late responses, failure cases, supported and legacy speech, desktop/mobile keyboard use, and persistence. The independent Inspector opens the UI in a browser and verifies observable behavior. Relevant existing tests/build and the mandatory validation hook pass; no mocked result is called native or container qualification.
- [ ] Criterion 6: Companion plan/tasks/implementation artifacts and lifecycle state are consistent with completed work; relevant capability scenarios, touches markers, coverage mappings and index links match changed behavior. Existing draft/legal/rights/native-qualification gates remain explicit.
- [ ] Criterion 7: Builder and Inspector produce auditable role-marked commits. Latest origin/main is incorporated into the feature branch before integration, the independently verified feature is merged into main, main is pushed without force, and remote main is verified to match local main.

## Scope Boundaries

**In scope:**
- Feature 006 and directly necessary runtime routing, operator-authorized configuration, UI, tests and documentation.
- Existing uncommitted `specs/README.md` entry and `specs/006-ui-endpoint-configuration/` artifacts, which were created for this user request and must be preserved and incorporated.
- Required Companion phases and hooks, with any review-gate pause reported to the orchestrator rather than silently bypassed.
- Local feature branch, synchronization, merge and explicitly requested push to origin/main after independent PASS.
- Goal process artifacts and independent feedback.

**Out of scope:**
- Live/private deployment access, restarts, migrations, port changes or service installation.
- Model installation, voice cloning, production enablement, relaxing legal/rights/release gates, and unrelated refactors.
- Publishing credentials, private addresses/configuration, speech text, audio or operational logs.
- Force pushing, history rewriting, destructive cleanup, automatic squash, and overwriting unrelated work.

## Applicable Project Conventions

**Quality gate commands:**
- `bash checks/run_companion_validation.sh`: mandatory after-implement-exec node hook, owning validation. It runs platform-selected backend tests, frontend unit/E2E tests, and checks unittest discovery. Inspect and obey the checked-in script; do not substitute a success-shaped fallback.
- `npm --prefix frontend run build`: existing production build.
- `npm --prefix frontend test`: existing frontend unit and browser suite.
- `python3 -m unittest discover -s checks/tests -v`: repository integrity tests.
- `git diff --check`: whitespace integrity.
- Use the smallest relevant test selection during changes; avoid redundant full-suite runs when the mandatory hook already owns them.
- Install/restore dependencies only following a missing-dependency failure or changed dependency manifests. Report genuine unavailable tools and resolve feasible local blockers without touching live services.

**Commit convention:**
- Conventional commits with titles at most 72 characters.
- Builder: `type(scope): [B] description`, one commit per completed iteration.
- Inspector: `chore(scope): [I] description`, one feedback/status commit per iteration.
- Builder trailer: `Assisted-by: OpenAI:GPT-5.6 Luna`.
- Inspector trailer: `Assisted-by: OpenAI:GPT-5.6 Sol`.
- Every created commit must also include `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.

**Guidelines:**
- Root `AGENTS.md`; `frontend/AGENTS.md` and `backend/AGENTS.md` where applicable.
- `.specify/memory/constitution.md` and `.github/instructions/speckit.instructions.md`.
- `.github/skills/speckit-companion-plan/SKILL.md`, then Companion tasks and implement skills.
- `.specify/extensions.yml` and `.specify/companion.yml` lifecycle/node hooks.
- `living-specs.yml`, `specs/README.md`, and directly affected `capabilities/` specifications and coverage.
- No `.agents/guidelines/` or `.github/guidelines/` were found.

**Rules:**
- Worktree started on main at `e63512c4023e0bc93986d7b127f3d1947bc52967`. Create a feature branch before product changes. Preserve any unexpected independent work.
- Constitution requires fetching and merging latest origin/main into a feature branch before integration. Repeat if origin/main advances; rerun relevant checks after consequential merges. Never force-push.
- Consult memory first. Discovery records memory-store unavailable, no fallback plugin found, and reference memory files absent. Attempt an available supported consultation mechanism, otherwise record the limitation honestly and use checked-in policy/spec evidence. Do not invent memory contents or block otherwise safe local work indefinitely.
- Feature 006 is normal-sized, specify-complete, and points through `.specify/feature.json`. Do not regenerate its valid upstream specification.
- Existing Companion recorder/resolver scripts may be absent. Use documented graceful fallback and preserve unknown context fields and append-only history.
- Root guidance requires monorepo boundaries, Pydantic backend conventions and existing frontend conventions. Never modify LICENSE or NOTICE.
- Keep credentials server-side. Endpoint visibility is only for the authorized operator; editable destinations must not turn the proxy into an unrestricted credential-forwarding service.
- Legal/rights/model/native support and deployment authorization are separate gates, not established by passing tests.
- Use synthetic examples only. This goal does not authorize access to the reported deployment.

## Orchestration and Delivery

- Builder implements; Inspector independently verifies with fresh context. The orchestrator coordinates and handles final integration/publication, not product coding or quality judgments.
- Builder must return the actual commands and results, commit SHA, important decisions and any blockers. A plan review gate must be surfaced rather than silently crossed.
- Inspector checks the immutable goal and repository evidence, writes `.goals/ui-endpoint-configuration/inspector-feedback-N.md`, updates status, and ends with PASS or FAIL. A real verification blocker must be explicit, not disguised as PASS.
- Do not merge or push from Builder/Inspector. The orchestrator integrates only independently verified work and confirms remote main after pushing.
- Goal artifacts are intentionally retained in git. Never execute the optional squash command.
