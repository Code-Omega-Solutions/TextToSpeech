# Backend synthesis - Requirement-to-test map

These references identify existing tests. The backend suite mocks system
executables; it does not qualify synthesis on a native macOS host.
Project-wide license and release-policy evidence is mapped separately in the
[project licensing coverage map](../project-licensing/project-licensing.coverage.md).

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Speech generation is authenticated by default | [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_config.py](../../backend/tests/test_config.py) | Default/disabled auth, protected credential files, conflicting sources, challenge and rejection before synthesis |
| Speech requests are validated against the supported contract | [backend/tests/test_models.py](../../backend/tests/test_models.py), [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_speech_contract.py](../../backend/tests/test_speech_contract.py) | UTF-16 input bounds, streamed 32 KiB body limits, optional backend values, VibeVoice preset compatibility, format, speed, and safe HTTP responses |
| Language is explicit or detected from German and English text | [backend/tests/test_language.py](../../backend/tests/test_language.py), [backend/tests/test_models.py](../../backend/tests/test_models.py), [backend/tests/test_api.py](../../backend/tests/test_api.py) | Locale aliases, configured short-input default, unsupported detection fallback, explicit language validation, and mocked synthesis response |
| Synthesis uses configured system voices and bounded subprocesses | [backend/tests/test_services.py](../../backend/tests/test_services.py), [backend/tests/test_voices.py](../../backend/tests/test_voices.py) | Mocked command arguments, pacing, format, shared deadline, output and temporary-disk limits, permits, cancellation, child termination and cleanup |
| Optional VibeVoice worker is isolated and bounded | [backend/tests/test_vibevoice.py](../../backend/tests/test_vibevoice.py), [backend/tests/test_vibevoice_memory.py](../../backend/tests/test_vibevoice_memory.py) | Fake-process protocol, decoder-only constructor, one-process reuse, line bounds, timeout/cleanup, reserve admission and eviction; no weights or native memory behavior exercised |
| Cross-backend response contract is preserved | [backend/tests/test_services.py](../../backend/tests/test_services.py), [backend/tests/test_speech_contract.py](../../backend/tests/test_speech_contract.py) | Mocked WAV/MP3 media types, actual-backend and fallback metadata, one clean fallback, auth-before-admission and safe errors |
| Health and readiness report distinct service states | [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_voices.py](../../backend/tests/test_voices.py) | Liveness, required executable/codec/voice checks and optional UK voice |
| Optional worker lifecycle does not block macOS readiness | [backend/tests/test_vibevoice_startup.py](../../backend/tests/test_vibevoice_startup.py) | Mocked absent optional assets, status header, readiness and application shutdown cleanup; native startup and resident-model shutdown remain unqualified |
| Errors and logs avoid speech text and credentials | [backend/tests/test_api.py](../../backend/tests/test_api.py) | Safe validation/runtime responses, request/token redaction and safe request logging |
