# Plan: Publishable macOS speech backend

## Summary

Extend the recovered Python speech backend with safe prerequisite inspection,
explicit user-owned setup, bounded synthesis, and protected credentials. Preserve
the existing speech API while configuring the Vite and Nginx proxies to inject
the backend credential without exposing it to browsers. Validate with mocked
tests on Linux; native operation and publication remain separately gated.

## Project Structure

```text
backend/
  app/                 Existing API, validation, language, synthesis and voices
  tests/               Mocked API, synthesis, configuration and setup tests
  pyproject.toml       Runtime and development dependencies
  uv.lock              Locked Python dependencies
  README.md            Setup, operation and qualification instructions
frontend/
  config/upstream.js   Vite proxy configuration
  vite.config.js       Development and preview server boundary
  docker/              Nginx template and startup configuration
  compose.yaml         Loopback container and secret configuration
  tests/               Proxy, development and container tests
capabilities/          Affected living requirements and coverage maps
specs/001-macos-backend/ Specification, design, tasks and verification
```

**Structure Decision:** Extend the existing projects rather than introducing a
second backend or browser-facing API. Add the setup command under `backend/`
without importing the FastAPI application.

## Calls and state

The browser sends the existing `/api/` requests. Vite or Nginx accepts only
the documented routes, bounds request bytes, removes incoming Authorization,
and sends the configured bearer credential to the fixed upstream. The backend
authenticates, validates, reserves capacity, resolves language and voice,
synthesizes through bounded owned subprocesses, returns audio, and cleans up.

Setup transitions from read-only inspection to a proposed plan, explicit
acceptance, serialized changes, and a fresh readiness report. Incomplete manual
steps or failures remain nonzero results. It must not register, start, or replace
services, overwrite existing environments or credentials, or silently escalate.

## Constitution Check

| Principle | Assessment |
|---|---|
| Evidence-based specifications | PASS: retain draft markers and distinguish recovered behavior from verified changes. |
| Safe, bounded behavior | PASS: inspection is read-only; setup requires consent and resource limits apply. |
| Operational boundaries | PASS: secrets remain server-side, logs are redacted, and deployment is separate. |
| Observable outcomes | PASS: requirements map to tests and native-only checks are identified separately. |
| Platform and release claims | PASS: Intel, Apple Silicon, legal and rights checks remain release gates. |

## Implementation approach

1. Define stable diagnostics and a check-only entry point that does not import
   the application. Add a serialized, opt-in installer with staged changes,
   lockfile-based dependencies, failure reporting and idempotent reruns.
2. Extend configuration to validate exactly one credential source, including
   owner-only protected files. Preserve fail-closed authentication and ensure
   readiness checks credentials, executables, codecs and required voices.
3. Enforce 32 KiB streaming request bounds and 5,000 UTF-16 units, including
   malformed bodies, surrogate rejection, absent or misleading lengths.
   Maintain the language, format, segmentation, capacity and error contracts.
4. Enforce the total deadline, private temporary-disk budget, child termination
   and cleanup across cancellation and all failures. Preserve successful binary
   MP3/WAV responses and exact encoding characteristics.
5. Apply equivalent proxy behavior in Vite development/preview and Nginx,
   including fixed routes, replacement of attacker headers, protected secrets
   and matching 32 KiB bounds. Keep browser code free of backend credentials.
6. Add the portable per-user service example, operating and recovery
   documentation, mocked tests, living-spec changes and release-gate checks.
   Do not register services or run installers during implementation.

## Requirement coverage

| Requirements | Implementation and verification focus |
|---|---|
| FR-001-003 | Read-only bounded inspection, complete prerequisite inventory, stable report identifiers and exit codes. |
| FR-004-006 | Explicit plan acceptance, isolated locked installation, approved distribution and verification, no automatic privileged bootstrap. |
| FR-007-009 | Real ffmpeg codec checks, required and optional voices, manual OS-managed voice steps, serialized and idempotent installation. |
| FR-010-014 | Existing routes, request fields, byte and UTF-16 limits, language detection, pauses, format and segmentation. |
| FR-015-017 | Concurrent capacity, shared deadline, size and temporary-disk budgets, child cleanup and separate liveness/readiness. |
| FR-018-022 | Default bearer authentication, exclusive protected credential sources, server-side proxy authorization, loopback and safe diagnostics. |
| FR-023-027 | Opt-in per-user service example, reproducible documentation, publication and licensing gates, mocked and native qualification. |
| SC-001-003 | Zero-change inspection, actionable readiness blockers, isolated and repeatable authorized setup. |
| SC-004-005 | Locale, encoding, errors, cleanup and exact 5,000-unit/32-KiB boundaries, including chunked and misleading lengths. |
| SC-006-007 | Synthetic secret markers do not escape; interrupted setup and failed synthesis preserve existing state and clean owned resources. |
| SC-008-009 | Portable mocked suites, locked dependencies and separately verified licensing and release evidence. |

## Verification and release gates

Run the backend's locked mocked pytest suite, the frontend unit and browser
scripts where available, and container tests only when Docker is available.
Exercise the exact boundary values and cleanup/error scenarios in the feature
specification. Any unrun checks must be reported rather than inferred.

Native voice inventory, encoding, installation, interruption and rerun checks
require separately authorized machines for each supported architecture. A
release also requires legal approval, rights review, third-party notices and
clean content and reachable-history checks. Neither Linux mocks nor this plan
qualifies a platform or approves publication.
