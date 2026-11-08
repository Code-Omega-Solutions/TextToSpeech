# TextToSpeech Constitution

## Core Principles

### 1. Keep specifications evidence-based
Distinguish implemented behavior from proposed changes. Trace living requirements
to relevant code and tests, and retain draft/adopted markers until the stated
behavior has been reviewed against that evidence. A checklist or coverage map is
not proof that code is implemented or a test has passed.

### 2. Prefer safe, bounded behavior
Define explicit limits, safe defaults, clear failure behavior, and cleanup for
service and installation workflows. Inspection must not mutate the host;
installation and operational changes require explicit consent.

### 3. Protect users and operational boundaries
Keep credentials server-side, avoid logging or publishing speech text and
secrets, and use synthetic examples in public-facing documentation. Repository
changes do not authorize deployment, service changes, or access to a live
installation.

### 4. Verify observable outcomes
Requirements must describe testable outcomes. Update affected specifications
and their coverage maps with behavior changes, then run relevant tests. Mocked
tests establish mocked behavior only; native macOS support requires native
qualification.

### 5. Be precise about platform and release claims
Advertise only verified platform support. Preserve third-party license and
attribution boundaries, and keep unresolved legal, rights, and qualification
reviews explicit as release gates.

## Specification and change constraints

- Keep `living-specs.yml`, capability specs, coverage maps, and `specs/README.md`
  aligned when requirements or owned files change.
- Identify proposed behavior as proposed; do not imply that planning documents,
  licensing language, test coverage, or recovered code constitute approval or
  qualification.
- Keep secrets, private addresses, production configuration, logs, audio, and
  private operational details out of specifications and examples.

## Development workflow

- Feature branches MUST fetch and merge the latest `origin/main` before their
  changes are merged into the main code line. If `origin/main` advances before
  integration, repeat the fetch and merge. A fast-forward satisfies this rule
  when the feature branch has no divergent commits.
- Resolve merge conflicts while preserving intended behavior and existing
  privacy and release boundaries; run checks relevant to the merged changes.
  Syncing a branch does not authorize publishing private work or bypassing
  required approvals. Merging regularly reduces conflict risk but cannot
  guarantee conflict-free integration.

## Governance

This constitution guides new and changed specifications. If an existing
specification or implementation conflicts with it, make the conflict explicit
and resolve it in the affected spec and code rather than silently weakening a
release or safety gate. Amendments must record their rationale and be checked
against the affected capabilities, documentation, and tests.
Review changes for compliance with this constitution before integration.
Amendments require a documented rationale and review; increase the major version
for incompatible principle changes or removals, the minor version for new or
materially expanded guidance, and the patch version for non-semantic
clarifications.

**Version**: 1.1.0 | **Ratified**: 2026-11-07 | **Last Amended**: 2026-11-08
