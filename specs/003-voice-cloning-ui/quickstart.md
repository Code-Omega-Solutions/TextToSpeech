# Validation Guide: Voice Cloning Interface

This guide describes validation to perform **after implementation**; it does not
claim that the optional interface, service or tests already exist. Use only a
synthetic audio fixture and mocked service; no model, private prototype,
recording, deployment or publishing is needed. Contract details and state rules
are in [the contract](contracts/capability-and-synthesis.md) and
[data model](data-model.md).

## Prerequisites and setup

- Node 24.14 or newer within Node 24, npm, and installed frontend dependencies;
  Playwright Chromium and its required system libraries for browser checks.
- From `frontend/`, use the existing `npm ci` and
  `npx playwright install chromium` only when dependencies/browser are absent
  and installation is authorized. The tests use intercepted local requests,
  not a live prototype. `frontend/playwright.config.js` starts a loopback
  preview and configures a non-service upstream; avoid an occupied port 5173.
  Supply a synthetic server-side test credential, not an actual credential;
  ensure no `TTS_API_KEY_FILE` or conflicting `.env` credential is configured.
- Docker is needed only for Nginx/container boundary tests; do not publish or
  run against a live service.

## Focused automated checks

Run from `frontend/` after adding the implementation and its tests:

```sh
npm run test:unit
TTS_API_KEY=synthetic-test-only npm run test:e2e
npm run test:docker
npm run build
```

Expected: all selected tests pass, including the existing exact ordinary JSON
shape for auto and all explicit languages, formats, speeds, playback/download,
limits and error paths. Both desktop and mobile projects must run; a mock
backend or a browser-only pass does not prove Nginx upload behavior. Container
tests must use only disposable local resources and synthetic data.
The Docker test builds a local image and starts disposable test containers; it
does not publish an image or deploy a service.

The added tests must explicitly demonstrate:

1. Disabled, absent, malformed, unauthorized, unsupported-version and failed
   discovery never block ordinary speech or send optional fields/reference.
2. Advertised types and exact file and encoded-body thresholds reject zero,
   unsupported, corrupt-when-detectable, over-limit and missing-consent input;
   boundary values, chunked requests, concurrent uploads, cancellation and
   safe errors are covered in both proxy paths. Oversize is rejected, never
   truncated; the legacy 32 KiB path remains enforced.
3. Explicit clone choice, selection, confirmation and multipart request
   succeed with a mock; replacement, removal, clear and disposal reset
   confirmation and release references and previews. Server rejection permits
   retry and normal generation.
4. Candidate, native pressure fallback, missing reason, missing/invalid or
   contradictory metadata, errors, empty audio and changed availability give
   truthful accessible status; late or cancelled requests cannot resurrect
   stale audio or removed reference data.
5. Keyboard workflow, labels, focus, live announcements and narrow viewport
   have no horizontal overflow. Inspect localStorage, sessionStorage,
   IndexedDB and Cache Storage for text, reference and generated audio; verify
   object URLs are revoked and no sensitive values appear in logs or fixtures.
6. Proxy routes are off by default, exact and method-restricted; auth is
   injected server-side, browser auth cannot override it, requests are bounded
   and cleanup/privacy behavior is tested. No private prototype content or
   sensitive audio is included in source, build context or artifacts.

## Review gates

Check `git diff --check`, review the diff and affected living requirements and
coverage mappings. Agree the proposed API and caps with the prototype owner
before real integration. Separately review model rights, licensing, legal and
recovered-source rights, any temporary server-side retention, source-offer
fulfillment and release authorization. No mocked test is native macOS
qualification or evidence of model quality or consent verification.
