# Implementation Plan: Selectable Speech Engines Prototype

## Scale Note

This oversized change spans the Python backend, vanilla-JavaScript frontend,
dependency/notices, tests, and an isolated remote deployment path. Keep the
existing service contract and target service untouched until the parallel
prototype passes local checks and a separate host install/deployment plan is
approved.

## Summary

Add a fixed engine registry behind the existing authenticated speech route,
preserving all current request and response behavior. Add a protected engine
catalog and connect the repository speech UI to it. Implement Fish as a disabled
adapter to a separate loopback Fish API server using a reviewed MessagePack
dependency. Compare upstream Fish variants but do not download or enable weights
until exact terms and provenance are reviewed. Deploy only as a parallel service
after target prerequisites and the exact service plan are approved.

## Constitution Check

| Principle | Assessment | Rationale |
| --- | --- | --- |
| Evidence-based specifications | PASS | Separate upstream claims, local measurements, and unverified outcomes. |
| Safe, bounded behavior | PASS | Keep current admission/time/output limits, disable unconfigured engines, and block deployment on unmet prerequisites. |
| Protect users and operational boundaries | PASS | Reuse bearer auth, avoid private data in catalog/errors, keep Fish upstream loopback-only, and preserve the existing service. |
| Verify observable outcomes | PASS | Test public API, readiness, discovery, UI choices, and actual-engine headers; do not treat mocks as native qualification. |
| Precise platform and release claims | PASS | Fish/model/voice rights remain explicit gates; the target's observed prerequisites do not qualify Fish. |

## Project Structure

```text
backend/app/config.py
backend/app/models.py
backend/app/services.py
backend/app/routers.py
backend/app/engines.py                 (new)
backend/app/fish_speech.py              (new)
backend/tests/test_engines.py           (new)
backend/tests/test_fish_speech.py       (new)
backend/tests/test_api.py
backend/tests/test_config.py
backend/tests/test_models.py
backend/tests/test_services.py
backend/tests/test_speech_contract.py
backend/pyproject.toml
backend/uv.lock
backend/README.md
THIRD_PARTY_NOTICES.md
frontend/index.html
frontend/app.js
frontend/vite.config.js
frontend/config/upstream.js
frontend/tests/dev.test.js
frontend/tests/e2e/                       (existing browser tests)
specs/README.md
```

**Structure Decision**: Keep provider implementations in the existing backend
boundary, use an explicit registry for the two in-tree engines, and extend the
existing web proxy/UI rather than introducing a new frontend framework or
runtime plugin system. Keep remote service setup separate from code validation.

## Calls

```calls speech request dispatch
~ create_speech @ backend/app/routers.py:67
~   validate/authenticate request @ backend/app/routers.py:67
~   SpeechService.synthesize_reserved @ backend/app/services.py:191
+     EngineRegistry.resolve @ **new** @ backend/app/engines.py
+       MacOSSayEngine.synthesize @ **new** @ backend/app/engines.py
+       FishSpeechEngine.synthesize @ **new** @ backend/app/fish_speech.py
~   return Response with backend/fallback headers @ backend/app/routers.py:125
```

```calls discovery to speech UI
~ checkService @ frontend/app.js:63
+   fetch engine catalog @ frontend/app.js:63
+     restrictApi @ frontend/vite.config.js:19
+       build_router adds authenticated catalog route @ backend/app/routers.py:63
+         registry discovery @ **new** @ backend/app/engines.py
~   submit form request @ frontend/app.js:75
~     existing POST /api/v1/audio/speech @ frontend/app.js:91
```

## State Lifecycle

```states configured engine availability
unconfigured: The engine is not configured or disabled. (start)
checking: A configured engine's local readiness is being checked.
available: The engine is ready for requests. shows studio
unavailable: The engine is configured but its required service or artifacts are unavailable. shows engines-unavailable
unconfigured -> checking: operator enables a fully configured engine
checking -> available: readiness checks succeed
checking -> unavailable: a required dependency or rights gate is unresolved
available -> unavailable: the engine becomes unreachable or fails validation
unavailable -> checking: configuration is corrected and the service restarts
grid:
unconfigured | checking | available | unavailable
```

## Screens

```screen studio Speech generation
title: Private Speech Studio (changed)
row:
  field: Text
  field: Language
row:
  field: Speech engine (1) (new)
  field: Voice (2) (new)
row:
  field: Audio format
  field: Speaking speed
button: Generate speech
list: Audio playback | Download
text: Engine availability and safe error status (new)
```

1: Populate only from authenticated discovery; keep the configured default available without changing existing client defaults.
2: Filter by the selected or detected language; expose public voice identifiers only.

```screen engines-unavailable Engine unavailable
title: Speech engine unavailable (new)
text: The selected engine is not configured or ready. No other engine was substituted. (new)
button: Retry discovery (new)
```
