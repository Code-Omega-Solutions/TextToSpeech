# Research: Voice Cloning Interface

All decisions below are proposed for implementation, not evidence that the
optional service exists or that another team has accepted its contract.

## Existing request must remain untouched

**Decision**: Keep ordinary `POST /api/v1/audio/speech` JSON and the existing
health check independent of optional discovery; use a separate clone route.

**Rationale**: `frontend/app.js` sends `input`, `response_format`, `speed`,
and `language` only when explicitly selected. `backend/app/models.py`
forbids extra fields. Existing tests assert the exact JSON request. Failed
discovery must never affect normal submission.

**Alternatives considered**: Add clone fields to the existing request
(breaks strict older services); infer capability from health (health is not a
feature declaration); require the prototype (violates independent release).

## Discovery and explicit opt-in

**Decision**: Propose versioned same-origin capability discovery and a separate
multipart clone request, with the feature disabled by default. Enable clone
only after an explicit service support response, valid constraints and user
choice.

**Rationale**: Existing backend has no capability route; Vite and Nginx
allowlist only health, readiness and speech. The proposed routes are a
cross-project assumption requiring explicit agreement, not a discovered API.

**Alternatives considered**: Feature detection by attempting uploads (leaks
reference data); hard-coded supported formats (may diverge from service);
configuration alone (does not establish service support).

## Upload limits and privacy

**Decision**: Propose a hard 2 MiB maximum file and 3 MiB encoded multipart
request cap, with a service-advertised file limit no higher than the UI cap.
Use a distinct gated route with route-specific limits and streamed byte
enforcement; preserve 32 KiB legacy limits. Verify equivalent Nginx and Vite
boundaries, without browser persistence or access/body logging.

**Rationale**: Both current proxies constrain speech requests to 32 KiB and
the Vite proxy buffers the whole legacy body. Audio needs a distinct bounded
path. These numbers are conservative planning assumptions, not measured
service requirements; an operator and contract owner must agree them. Buffer
or temporary-file behavior and cleanup on abort require explicit review.

**Alternatives considered**: Increase the global limit (weakens legacy
protection); base64 in legacy JSON (larger bodies and incompatible schema);
unbounded multipart (resource and privacy risk); direct browser-to-service
uploads (exposes origin/authentication and changes the CSP boundary).

## Result and error semantics

**Decision**: Carry audio in the response body and actual-engine/fallback
metadata in versioned response headers. Treat missing, malformed, contradictory
or unrecognized metadata as unknown; identify fallback only when explicitly
reported. Map new-route error codes to safe local text.

**Rationale**: Existing audio responses are raw bytes, not a JSON envelope;
the browser must not equate HTTP success with successful cloning or expose
arbitrary server details that might contain private content.

**Alternatives considered**: Infer engine from requested mode or capability
(false claims); always label native (false fallback); trust free-form error
details (potential data disclosure).

## Test and release boundary

**Decision**: Extend existing Node and Playwright tests with mock capability,
multipart and result responses and synthetic bytes. Verify exact legacy
requests, both proxy paths, accessibility and persistence; update living
specs only when behavior is implemented.

**Rationale**: `frontend/tests/e2e/speech.spec.js` already stubs health and
audio and tests request shape, object URL lifecycle and errors; proxy tests
cover independent serving paths. Mocks show UI behavior only.

**Alternatives considered**: Depend on the private prototype or live
recordings (blocks independent publishing and risks disclosure); treat
mocked UI tests as model or native qualification (unsupported).
