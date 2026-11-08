# Implementation Plan: Voice Cloning Interface

**Branch**: `agents/voice-cloning-ui-implementation-plan` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: [Feature specification](spec.md); [related prototype specification](../002-local-speech-prototype/spec.md)

## Summary

Plan an independently publishable, opt-in browser interface for an optional
cloning service. Ordinary synthesis must retain its existing JSON request and
playback/download path even when capability discovery fails. A proposed,
versioned capability and clone contract is documented for simulation and
cross-team agreement, not claimed as an existing or agreed backend API.
Clearly report the service's actual engine, native fallback and unknown
metadata. No private prototype implementation, model, evaluation, deployment
or publication is part of this feature.

## Technical Context

**Language/Version**: Browser JavaScript ES modules, HTML and CSS; Node.js
24.14.0 through Node 24 for build and tests.

**Primary Dependencies**: Existing Vite 8 and Playwright; Nginx production
proxy. No new runtime dependency is planned.

**Storage**: Browser memory only for reference, consent and audio; object URLs
revoked on replacement, clear and disposal. Do not write speech text, reference,
derived data or audio to persistent browser storage. Browser cleanup does not
assert server deletion.

**Testing**: Existing Node test runner and Playwright desktop/mobile projects;
mock service responses and synthetic audio. Existing proxy tests plus targeted
unit, browser and container-boundary tests are planned.

**Target Platform**: Existing desktop and mobile browser configurations;
frontend's current local Vite and Linux AMD64 Nginx serving paths. Native
backend or model operation is not qualified by UI tests.

**Project Type**: Standalone static web frontend and its same-origin proxies.

**Performance Goals**: Do not block ordinary generation on discovery; enforce
the exact size and encoded-body limits in the contract. No unsupported latency,
model quality or capacity target is asserted.

**Constraints**: Preserve 5,000 UTF-16 units, language selection, formats,
speed, 32 KiB legacy request limit, same-origin CSP and server-side upstream
credential. Optional routes remain disabled by default; exact per-route upload
limits and retention controls must be tested in both proxies. Only synthetic
fixtures and safe error messages may enter publishable artifacts.

**Scale/Scope**: One existing speech form; one ephemeral reference and one
generation at a time; no account, microphone recording, stored voice library,
public backend or model lifecycle.

## Constitution Check

*Pre-research: PASS, subject to the external contract and release gates below.*

1. **Evidence**: The existing request, proxy and tests are identified in
   [research.md](research.md). Optional APIs and behavior are proposals, not
   currently implemented facts.
2. **Bounded behavior**: Separate feature-gated upload route, explicit file
   and wire limits, no legacy limit increase, validation, cancellation and
   cleanup are designed in the [contract](contracts/capability-and-synthesis.md).
3. **Privacy and boundaries**: The backend credential remains server-side;
   synthetic fixtures, no body logging or browser persistence, protected upload
   handling and no implied server deletion are required. No operator action is
   authorized by this plan.
4. **Observable verification**: [quickstart.md](quickstart.md) maps focused
   tests to acceptance criteria and requires both proxy paths, accessibility,
   storage and exact legacy wire compatibility. When implemented, update the
   affected living specifications and coverage maps alongside code.
5. **Platform and release**: UI mocks do not qualify macOS or model behavior.
   Model licensing, recovered-source rights, legal review, exact-artifact
   source-offer fulfillment and release authorization remain separate gates.

*Post-design: PASS for planning; integration remains blocked until the
contract owner agrees and validates the provisional contract and limits.
Any required relaxation of upload buffering, request limits, authentication or
data retention must receive a separate security/operational review.*

## Project Structure

### Documentation (this feature)

```text
specs/003-voice-cloning-ui/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/capability-and-synthesis.md
└── quickstart.md
```

### Source Code (repository root)

```text
frontend/
├── index.html, styles.css, app.js     # existing form and behavior
├── config/upstream.js, vite.config.js # dev/preview proxy
├── docker/                            # Nginx template and startup
├── tests/                             # proxy and desktop/mobile browser tests
└── README.md                          # operating and privacy boundaries
capabilities/
├── speech-generation/                 # living requirements and coverage
└── frontend-serving/                  # serving/proxy requirements and coverage
living-specs.yml                       # capability ownership registry
specs/README.md                        # current versus proposed behavior
```

**Structure Decision**: Extend existing frontend and serving boundary rather
than add a second application. The future implementation must assess whether
registry ownership and image-publication coverage also need updating. It must
not add prototype code, change backend synthesis, or create tasks in this
planning phase.

## Implementation Sequence

1. Agree and version the provisional contract with the separately planned
   prototype; until then the frontend can be developed/tested against mocks
   but real integration is blocked. Confirm operator upload cap and privacy
   guarantees before enabling optional proxy routes.
2. Add opt-in exact capability and clone routes to both serving proxies with
   server-held credentials, explicit bounded upload handling and tests; retain
   existing route, 32 KiB limits and default configuration.
3. Implement discovery and explicit clone choice; validate accepted type, size
   and consent; model replacement, removal, reset, navigation and stale-request
   behavior as in [data-model.md](data-model.md).
4. Implement clone submission and truthful outcome/error presentation; preserve
   legacy path byte shape and all existing controls. Use safe service error
   codes rather than rendering arbitrary untrusted error details for new routes.
5. Add focused unit/browser/proxy tests and documentation; update affected
   living requirements, ownership and coverage for actual behavior. Validate
   the release boundary separately; do not infer service or legal readiness.

## Requirement Traceability

| Requirements | Design and verification |
| --- | --- |
| FR-001, FR-008; SC-001 | Legacy contract and exact request regression checks in [quickstart.md](quickstart.md) |
| FR-002, FR-012; SC-002 | Capability and isolated mock integration in [the contract](contracts/capability-and-synthesis.md) |
| FR-003, FR-004, FR-005; SC-004 | Reference and request lifecycle in [data-model.md](data-model.md), input and proxy checks in [quickstart.md](quickstart.md) |
| FR-006, FR-007; SC-003 | Reported engine and fallback rules in [the contract](contracts/capability-and-synthesis.md) |
| FR-009, FR-010; SC-005 | Transient state, accessibility, storage and cleanup checks in [quickstart.md](quickstart.md) |
| FR-011, FR-013; SC-006 | Independent release boundary and review gates in [research.md](research.md) and [quickstart.md](quickstart.md) |

## Complexity Tracking

No constitution violations are proposed. A separate clone route and a
feature-gated per-route body limit are necessary to carry audio without
weakening the existing bounded JSON route.
