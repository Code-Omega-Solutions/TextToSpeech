# Frontend serving - Requirement-to-test map

These are existing test references. Mapping a requirement does not establish
complete assertion coverage or a new passing test run.

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Development and production builds are reproducible | [frontend/tests/dev.test.js](../../frontend/tests/dev.test.js), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js), [frontend/tests/e2e/fidelity.spec.js](../../frontend/tests/e2e/fidelity.spec.js) | Serving/build execution and optional visual fidelity; lockfile installation and port-conflict behavior also need setup validation |
| Upstream configuration is explicit and server-side | [frontend/tests/config.test.js](../../frontend/tests/config.test.js), [frontend/tests/dev.test.js](../../frontend/tests/dev.test.js), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js) | Origin validation, no HTML origin injection and missing/invalid container startup configuration |
| API forwarding is restricted to the known service routes | [frontend/tests/config.test.js](../../frontend/tests/config.test.js), [frontend/tests/dev.test.js](../../frontend/tests/dev.test.js), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js) | Exact mappings, configured timeouts, method restriction, unknown routes and binary forwarding |
| Production serving preserves isolation and response safeguards | [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js) | Isolated container, static assets, headers, method restriction and 16 KiB body limit; image contents and Compose behavior also need deployment review |
