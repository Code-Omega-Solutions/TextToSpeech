# Backend synthesis - Requirement-to-test map

These references identify existing tests. The backend suite mocks system
executables; it does not qualify synthesis on a native macOS host.
Project-wide license and release-policy evidence is mapped separately in the
[project licensing coverage map](../project-licensing/project-licensing.coverage.md).

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Speech generation is authenticated by default | [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_config.py](../../backend/tests/test_config.py) | Default/disabled auth, protected credential files, conflicting sources, challenge and rejection before synthesis |
| Speech requests are validated against the supported contract | [backend/tests/test_models.py](../../backend/tests/test_models.py), [backend/tests/test_api.py](../../backend/tests/test_api.py) | UTF-16 input bounds, streamed 32 KiB body limits, language, model, format, speed, voice hint and safe HTTP responses |
| Language is explicit or detected from German and English text | [backend/tests/test_language.py](../../backend/tests/test_language.py), [backend/tests/test_models.py](../../backend/tests/test_models.py), [backend/tests/test_api.py](../../backend/tests/test_api.py) | Locale aliases, configured short-input default, unsupported detection fallback, explicit language validation, and mocked synthesis response |
| Synthesis uses configured system voices and bounded subprocesses | [backend/tests/test_services.py](../../backend/tests/test_services.py), [backend/tests/test_voices.py](../../backend/tests/test_voices.py) | Mocked command arguments, pacing, format, shared deadline, output and temporary-disk limits, permits, cancellation, child termination and cleanup |
| Health and readiness report distinct service states | [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_voices.py](../../backend/tests/test_voices.py) | Liveness, required executable/codec/voice checks and optional UK voice |
| Errors and logs avoid speech text and credentials | [backend/tests/test_api.py](../../backend/tests/test_api.py) | Safe validation/runtime responses, request/token redaction and safe request logging |
