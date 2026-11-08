# Frontend serving - Requirement-to-test map

These are existing test references. Mapping a requirement does not establish
complete assertion coverage or a new passing test run.

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Development and production builds are reproducible | [frontend/tests/dev.test.js](../../frontend/tests/dev.test.js), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js), [frontend/tests/e2e/fidelity.spec.js](../../frontend/tests/e2e/fidelity.spec.js) | Serving/build execution and optional visual fidelity; lockfile installation and port-conflict behavior also need setup validation |
| Upstream configuration is explicit and server-side | [frontend/tests/config.test.js](../../frontend/tests/config.test.js), [frontend/tests/dev.test.js](../../frontend/tests/dev.test.js), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js) | Origin validation, protected credential sources, server-only configuration and missing/invalid startup configuration |
| API forwarding is restricted to the known service routes | [frontend/tests/config.test.js](../../frontend/tests/config.test.js), [frontend/tests/dev.test.js](../../frontend/tests/dev.test.js), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js) | Exact mappings, configured timeouts, method restriction, authorization replacement, streamed 32 KiB limit, unknown routes and binary forwarding |
| Production serving preserves isolation and response safeguards | [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js) | Isolated container, read-only secret file, static assets, headers, method restriction, 32 KiB body limit, bundled legal files, package inventory and OCI labels; Compose behavior still needs deployment review |
