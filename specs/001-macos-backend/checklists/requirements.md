# Specification Quality Checklist: Open-source macOS speech backend

**Purpose**: Review requirements completeness before technical planning.
**Created**: 2026-10-26
**Feature**: [Backend specification](../spec.md)
**Method**: Stock GitHub Spec Kit specification and requirements-quality review.

Checked items mean the specification was reviewed against that criterion.
They do not mean the backend or installer has been implemented or tested.

## Content quality

- [x] User journeys are prioritized and independently testable.
- [x] Scope excludes deployment, runtime changes, cloud providers, and backend containers.
- [x] Requirements describe observable outcomes rather than prescribing an application architecture.
- [x] Safe defaults and unavailable-user assumptions are explicit.
- [x] Existing frontend integration and intentional behavior changes are documented.

## Requirement completeness

- [x] Prerequisite checks distinguish required tools, codecs, voices, configuration and credentials.
- [x] Check-only and installation operations have separate mutation/consent boundaries.
- [x] Privilege, package-manager bootstrap, voice downloads, offline behavior and failure recovery are covered.
- [x] Repeated and concurrent installation, upgrades and service-registration boundaries are defined.
- [x] All recovered speech routes, fields, language behavior, formats and resource limits are addressed.
- [x] Unicode units, encoded body limits and backend/proxy consistency are explicit.
- [x] Authentication defaults, frontend credential injection and proxy exposure risks are addressed.
- [x] Credential creation, storage, rotation boundaries and failure behavior are specified.
- [x] Diagnostics, health, redaction, temporary storage and child-process cleanup are covered.
- [x] Release files, reachable history, dependency licenses and recovered-source ownership have release gates.
- [x] No real private address, username, home path, token, service file or remote access details appear in the deliverables.
- [x] No unresolved template markers or unbounded claims of platform support remain.

## Measurable acceptance coverage

| Outcome | Requirements | Principal evidence required during implementation |
| --- | --- | --- |
| SC-001 | FR-001, FR-003 | Check-only mutation/network/synthesis instrumentation |
| SC-002 | FR-002, FR-003, FR-007, FR-008, FR-017 | Missing/incompatible prerequisite and readiness fixtures |
| SC-003 | FR-004 through FR-009, FR-023 | Isolated native clean/partial/rerun setup tests |
| SC-004 | FR-010 through FR-018, FR-020 | API, language, audio, authorization and resource-boundary tests |
| SC-005 | FR-011, FR-012 | Unicode and streamed request-size boundary tests at proxy and backend |
| SC-006 | FR-018 through FR-026 | Synthetic-marker redaction, release-file and reachable-history checks |
| SC-007 | FR-009, FR-015, FR-016 | Installer interruption, timeout/cancellation and cleanup tests |
| SC-008 | FR-024, FR-027 | Clean non-macOS mocked CI and fixture proxy integration |
| SC-009 | FR-005 through FR-008, FR-024, FR-026, FR-027 | Clean checkout reproduction, license/notices and qualification records |

## Planning handoff

Requirements-quality review is complete. Technical planning must select and
verify installation/distribution details and qualification targets listed in
the specification's assumptions. License/ownership approval remains a release
gate. Neither a passing checklist nor a future installer grants authorization
to modify the existing Mac or running frontend.
