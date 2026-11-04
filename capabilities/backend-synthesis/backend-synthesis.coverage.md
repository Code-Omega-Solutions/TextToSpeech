# Backend synthesis - Requirement-to-test map

These references identify existing tests. The backend suite mocks system
executables; it does not qualify synthesis on a native macOS host.
Project-wide license and release-policy evidence is mapped separately in the
[project licensing coverage map](../project-licensing/project-licensing.coverage.md).

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Speech generation is authenticated by default | [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_config.py](../../backend/tests/test_config.py) | Default/disabled auth, invalid credentials, challenge and rejection before synthesis |
| Speech requests are validated against the supported contract | [backend/tests/test_models.py](../../backend/tests/test_models.py), [backend/tests/test_api.py](../../backend/tests/test_api.py) | Input, language, model, format, speed, voice hint and safe HTTP response behavior |
| Language is explicit or detected from German and English text | [backend/tests/test_language.py](../../backend/tests/test_language.py), [backend/tests/test_models.py](../../backend/tests/test_models.py) | Locale aliases, short-input fallback, detection, unsupported-language response |
| Synthesis uses configured system voices and bounded subprocesses | [backend/tests/test_services.py](../../backend/tests/test_services.py), [backend/tests/test_voices.py](../../backend/tests/test_voices.py) | Mocked command arguments, pacing, format, timeout, output limit, permits and temporary-file cleanup |
| Health and readiness report distinct service states | [backend/tests/test_api.py](../../backend/tests/test_api.py), [backend/tests/test_voices.py](../../backend/tests/test_voices.py) | Liveness, required executables/voices and optional UK voice |
| Errors and logs avoid speech text and credentials | [backend/tests/test_api.py](../../backend/tests/test_api.py) | Safe validation/runtime responses and request/token redaction checks |
