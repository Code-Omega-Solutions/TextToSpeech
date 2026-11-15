# Implementation Plan: VibeVoice Backend Integration

## Scale note

This change spans about 24 planned files across the speech API, isolated model
worker, host memory admission, deployment documentation, and release cleanup.
Watch the process boundary and memory-yield behavior closely. Do not remove
evaluation references or shared model assets before target-host checks pass.

## Summary

Add VibeVoice Realtime 0.5B as a selectable backend while preserving the
existing macOS speech path and its authenticated MP3/WAV contract. Run the
model in one optional, persistent child process so the backend can keep warm
weights when memory permits and terminate the worker to release model memory
when higher-priority inference needs it. Load only the speech decoder, admit
VibeVoice only when a configured memory reserve can be honored, and fall back
to macOS speech whenever the worker is unavailable or must yield.

## Project Structure

```text
backend/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── routers.py
│   ├── services.py
│   └── vibevoice.py                 # new worker lifecycle and resource gate
├── vibevoice_worker/
│   ├── pyproject.toml               # new optional isolated runtime
│   ├── uv.lock                      # new pinned worker dependencies
│   └── worker.py                    # new persistent decoder-only worker
├── tests/
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_vibevoice.py            # new worker lifecycle tests
│   ├── test_vibevoice_memory.py     # new resource-yield tests
│   ├── test_speech_contract.py      # new cross-backend contract tests
│   └── test_vibevoice_startup.py    # new optional-startup tests
└── README.md
capabilities/
├── backend-synthesis/
│   ├── backend-synthesis.spec.md
│   └── backend-synthesis.coverage.md
└── project-licensing/
    ├── project-licensing.spec.md
    └── project-licensing.coverage.md
living-specs.yml
THIRD_PARTY_NOTICES.md
```

**Structure Decision**: Keep model libraries and weights outside the API
process. The backend owns one worker, serializes VibeVoice requests through it,
and can terminate it to reclaim all model allocations. Keep the evaluator
package as an implementation reference until integration and target-host
verification pass. Register new worker and runtime files with the relevant
living capabilities. Keep licensing records aligned with the optional runtime.

## Constitution Check

| Principle | Result | Rationale |
|---|---|---|
| Keep specifications evidence-based | PASS | Keep proposed behavior distinct from implemented behavior, and update the living requirement and coverage map only with verified implementation evidence. |
| Prefer safe, bounded behavior | PASS | Preserve request bounds, bound worker I/O, require memory admission, and discard partial output before fallback. |
| Protect users and operational boundaries | PASS | Preserve authentication and safe logging. Do not alter higher-priority inference services or remove private references before verification. |
| Verify observable outcomes | PASS | Test selection, admission, eviction, fallback, formats, and cleanup. Qualify native macOS behavior on the target host. |
| Be precise about platform and release claims | PASS | Limit support claims to qualified macOS hosts. Keep model, runtime, provenance, licensing, and redistribution checks as release gates. |

## Calls

```calls select and synthesize
~ create_speech @ backend/app/routers.py:67
~   SpeechService.synthesize_reserved @ backend/app/services.py:181
~     SpeechService._synthesize @ backend/app/services.py:191
+       VibeVoiceWorker.synthesize **new** @ backend/app/vibevoice.py
```

```calls release worker memory
~ create_app @ backend/app/main.py:125
+   application_lifespan @ backend/app/main.py:125
+     SpeechService.close @ backend/app/services.py:181
+       VibeVoiceWorker.stop **new** @ backend/app/vibevoice.py
```

## Worker Lifecycle

```states VibeVoice worker lifecycle
unloaded: No worker or model allocations are resident. (start)
loading: The isolated worker loads only the speech-generation components.
ready: One shared model and the permitted voice prompts are resident.
generating: The worker is generating one bounded request.
yielding: The worker stops or completes current work and exits to release memory.
failed: The worker cannot serve; the request uses the macOS fallback.

unloaded -> loading: request passes memory admission
loading -> ready: worker loads successfully
loading -> failed: worker, model, or capacity is unavailable
ready -> generating: request is admitted
generating -> ready: generation completes
ready -> yielding: memory reserve is reached
generating -> yielding: pressure or cancellation requires eviction
yielding -> unloaded: worker exit releases allocations
failed -> unloaded: failed worker resources are cleaned up
grid:
unloaded | loading | ready
failed | yielding | generating
```

## Phase 0 Research

See [research.md](./research.md) for the runtime, memory-admission,
decoder-only loading, audio-format, and cleanup decisions.

## Phase 1 Design

See [data-model.md](./data-model.md) for backend selection, worker state, and
resource admission. See [contracts/interface.md](./contracts/interface.md) for
the request, response, and private worker protocol.
