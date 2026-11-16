---
description: Follow the repository's Spec Kit workflow when creating, updating, implementing, or reviewing specifications and their associated code.
applyTo: "**"
---

# Spec Kit Workflow

Use this guidance when a task invokes Spec Kit or creates, changes, implements, or reviews a feature specification, plan, task list, living capability spec, or coverage map. For unrelated work, follow the applicable repository and directory instructions without starting a Spec Kit workflow.

## Repository Context

- Read the root `AGENTS.md` and any applicable nested `AGENTS.md` before changing code.
- Treat `.specify/memory/constitution.md` as governing policy. Keep specifications evidence-based: distinguish implemented behavior from proposals, and do not treat checklists, coverage maps, or mocked tests as proof of implementation or platform qualification.
- Use `specs/README.md` and `living-specs.yml` to locate existing feature specifications, registered capabilities, and coverage maps. Preserve the separation between numbered feature specs (planned work) and `capabilities/*/*.spec.md` (living behavior).
- Keep `living-specs.yml`, the affected capability spec and coverage map, and `specs/README.md` aligned when ownership, requirements, or links change. Do not edit unrelated requirements or mappings.
- Keep secrets, private addresses, production configuration, logs, audio, and private operational details out of specifications and examples. Preserve the project's explicit legal, rights, native qualification, privacy, and release gates.

## Feature Workflow

For new feature work, use the repository's available `/speckit-*` commands or the matching skills under `.github/skills/` in this order:

1. `/speckit-specify`: create or update one feature specification from the user's request. Resolve unclear scope before planning; use the repository's spec template and constitution.
2. `/speckit-clarify` when material ambiguities remain, then recheck the specification and its requirements checklist.
3. `/speckit-plan`: make technical decisions consistent with the codebase and constitution; record research and design artifacts where needed.
4. `/speckit-tasks`: derive an ordered, testable task list from the approved specification and plan. Keep tasks in `tasks.md`, not duplicated in the spec or plan.
5. `/speckit-implement`: work from the tasks and existing code, preserve user changes, and run focused tests and other relevant project checks. Report checks that could not be run and what they do not establish.

Start at the earliest missing or outdated artifact; do not regenerate valid upstream artifacts just to begin at the top of the sequence. Do not silently skip required phases when a feature task needs them. For a narrowly scoped bug fix or direct code change that does not need new feature planning, make the code and relevant living-spec updates directly rather than creating unnecessary Spec Kit artifacts.

After the initial implementation, `/speckit-converge` is an optional gap check. Run it only after `/speckit-tasks` has produced the complete task list and `/speckit-implement` has run. It compares current code with the feature artifacts and may append traceable work to `tasks.md`; it must not rewrite the spec, plan, or existing tasks. If it appends tasks, implement and verify those tasks before considering the feature complete.

Follow `.specify/extensions.yml` for lifecycle hooks. In this checkout, enabled Companion hooks are configured as mandatory for the specify, plan, tasks, implement, and converge phases. Execute mandatory hooks as directed by the corresponding skill; do not substitute a status update for running a hook. Respect optional hooks as opt-in.

When implementing behavior owned by a living capability, update that capability's requirement scenarios and `touches` markers with the code change, update its coverage map when test mappings change, and run the relevant behavior tests. Keep draft/adopted markers until requirements have been reviewed against code and test evidence.

## Optional Consistency Checks

These are useful maintenance checks, not automatic gates. Run them when requested, when investigating suspected inconsistencies, or when they materially help verify the current task. Report skipped checks and reasons; a successful process exit alone does not mean the report was clean.

- **Companion doctor:** After a Spec Kit run, optionally inspect its record with `python3 .specify/extensions/companion/scripts/doctor.py`; use `--feature-dir specs/<NNN>-<slug>` for a specific feature or `--all` for a repository sweep. It is read-only and retroactive. Report findings as-is; fixing them is a separate action.
- **Spec analysis:** When useful, run `/speckit-analyze` to check the consistency of the feature's specification, plan, and tasks before implementation. Treat its findings as input for deliberate updates, not as permission to rewrite unrelated artifacts.
- **Living-spec drift:** Optionally run `python3 .specify/extensions/companion/scripts/drift.py` to inspect committed changes, or add `--working` to include uncommitted and untracked changes. This is read-only and opt-in. Check the report's checked and skipped counts: drift can be reported while the command still exits successfully, and uncommitted living-spec baselines may be skipped.
- **Drift consolidation:** To fold working-tree changes into living specs, use the opt-in `speckit.companion.living-sync` skill (or `python3 .specify/extensions/companion/scripts/drift.py --working --json` as its documented sync-plan input). This edits only affected capability specs, leaves changes uncommitted, and reports skipped capabilities. Do not run it as an implicit side effect of a read-only drift check; make the sync an intentional part of the task and keep each edit limited to the reported files and capability.
- **Coverage:** Optionally run `python3 .specify/extensions/companion/scripts/check-coverage.py` to report requirement-to-test mappings. It is read-only and a signal, not proof that tests pass or a gate by itself.

Use `python3` availability as documented by each skill. If it is unavailable, state that the optional check was skipped; do not fail unrelated work. For generated skill behavior and exact command prerequisites, defer to the corresponding `.github/skills/*/SKILL.md` rather than duplicating or weakening its detailed rules here.
