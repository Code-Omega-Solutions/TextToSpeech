# Implementation Plan: UI endpoint configuration

## Summary

Add an operator-scoped endpoint configuration API and a browser configuration tab. The backend validates and atomically persists an allowlisted HTTP(S) origin without exposing credentials, while the frontend reloads health, capabilities, and speech routing after a successful save. Capability discovery will model unsupported, failed, and empty results separately, and legacy speech will retain the existing default contract.

## Project Structure

```text
backend/app/config.py
backend/app/main.py
backend/app/routers.py
backend/tests/test_config.py
backend/tests/test_api.py
frontend/index.html
frontend/app.js
frontend/styles.css
frontend/config/upstream.js
frontend/tests/config.test.js
frontend/tests/e2e/engine-discovery.spec.js
frontend/README.md
frontend/compose.yaml
capabilities/frontend-serving/frontend-serving.spec.md
capabilities/speech-generation/speech-generation.spec.md
living-specs.yml
specs/006-ui-endpoint-configuration/
```

Structure Decision: keep shared endpoint state in the serving proxy/backend boundary, use the existing vanilla frontend and FastAPI router patterns, and update only directly affected living specifications and coverage.

## Constitution Check

| Principle | Assessment |
|---|---|
| Evidence-based specifications | PASS. Requirements, tests, and coverage will identify proposed behavior separately from native qualification. |
| Safe, bounded behavior | PASS. Origins, writes, request sizes, timeouts, and atomic replacement remain bounded. |
| Protect users and operational boundaries | PASS. Credentials stay server-side and configuration writes require the existing operator boundary. |
| Verify observable outcomes | PASS. Unit, integration, browser, and persistence evidence will be added without calling mocks native qualification. |
| Precise platform and release claims | PASS. Documentation preserves legal, rights, deployment, and native-support gates. |

## Calls

```calls endpoint-save
+ configuration save @ backend/app/routers.py:1
    validate and authorize @ backend/app/config.py:1
    atomically persist shared settings @ backend/app/config.py:1
    invalidate endpoint-scoped capabilities @ frontend/app.js:1
```

```calls discovery-refresh
~ endpoint switch @ frontend/app.js:1
    health check @ frontend/app.js:1
    capability discovery @ frontend/app.js:1
    speech request @ frontend/app.js:1
```

## States

```states endpoint
configured: A saved endpoint is active and its capabilities are scoped to its generation. (start)
editing: The operator has changed the endpoint field without saving.
saving: The authorized write is being validated and persisted.
ready: The saved endpoint and current capabilities are usable. shows settings
error: The attempted save or discovery failed and the prior saved endpoint remains active. (final)
configured -> editing: edit endpoint
editing -> saving: submit valid-looking endpoint
saving -> ready: persisted and refreshed
saving -> error: rejected or write failed
ready -> editing: edit endpoint
grid:
configured | editing | saving
. | ready | error
```

## Screens

```screen settings Endpoint configuration
title: Configuration
text: Active endpoint: saved origin (changed) (1)
field: Speech-service endpoint (new)
button: Save endpoint (new)
text: Unsaved changes and announced validation status (new)
list: connection status | discovery status | supported options (changed)
```
1: The active endpoint is visibly distinct from pending edits.

```js sketch frontend/app.js
// Increment the endpoint revision before each refresh.
const revision = ++endpointRevision;
if (revision !== endpointRevision) return;
```

## Phase 0 Research

See `research.md` for evidence-backed decisions about persistence, authorization, legacy defaults, and discovery statuses.

## Phase 1 Design

`data-model.md` defines endpoint, capability, and save-result state. `contracts/endpoint-configuration.md` records the browser-facing API and UI identifiers that tests will use.

## Implementation Notes

The implementation must preserve existing audio playback/download, language resolution, request limits, and privacy behavior. No live service or installation is accessed.
