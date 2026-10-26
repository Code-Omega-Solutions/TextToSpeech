# Frontend serving - Living Spec

> [DRAFT] Adopted from the current development, build and Nginx configuration.
> Current limits are intentional baseline facts, not future backend requirements.

## Purpose

Run the recovered frontend locally or in a separate container while forwarding
only its known speech-service endpoints.

## Requirements

### Development and production builds are reproducible
<!-- touches: frontend/package.json, frontend/package-lock.json, frontend/.npmrc, frontend/.node-version, frontend/vite.config.js, frontend/tests/dev.test.js -->
<!-- adopted: frontend/package.json, frontend/vite.config.js, frontend/tests/dev.test.js -->

The frontend SHALL build with locked dependencies on the supported Node 24
toolchain without requiring a backend connection. Development and preview bind
to loopback port 5173 and fail on a port conflict. Builds preserve original
gradient precision by disabling CSS minification.

#### Scenario: building without an upstream configuration
- **WHEN** a contributor runs the production build with installed locked dependencies
- **THEN** static output is generated without contacting a backend.

### Upstream configuration is explicit and server-side
<!-- touches: frontend/config/**, frontend/vite.config.js, frontend/docker/entrypoint.sh, frontend/.env.example, frontend/tests/config.test.js, frontend/tests/dev.test.js, frontend/tests/docker.test.js -->
<!-- adopted: frontend/config/upstream.js, frontend/docker/entrypoint.sh, frontend/tests/config.test.js -->

Serving SHALL require `TTS_UPSTREAM_URL` as an HTTP(S) origin without credentials,
path, query, fragment or trailing slash. Its configured value is not injected
into browser assets.

#### Scenario: configuration is missing or contains a path
- **WHEN** a configured development, preview or container server starts
- **THEN** startup fails with a clear configuration error instead of selecting a mock or private default.

### API forwarding is restricted to the known service routes
<!-- touches: frontend/config/**, frontend/vite.config.js, frontend/docker/default.conf.template, frontend/tests/config.test.js, frontend/tests/dev.test.js, frontend/tests/docker.test.js -->
<!-- adopted: frontend/docker/default.conf.template, frontend/vite.config.js, frontend/tests/docker.test.js -->

Serving SHALL forward `/api/healthz`, `/api/readyz` and
`/api/v1/audio/speech` to their corresponding upstream paths without `/api`.
Speech generation requires POST. Unknown static/API paths return 404.
Read timeouts are 10, 15 and 75 seconds respectively.

#### Scenario: an unknown route or wrong speech method
- **WHEN** a client requests an unknown route or uses GET for speech generation
- **THEN** it receives 404 or 403 respectively, without forwarding to an arbitrary backend route.

### Production serving preserves isolation and response safeguards
<!-- touches: frontend/Dockerfile, frontend/compose.yaml, frontend/.dockerignore, frontend/.gitattributes, frontend/.gitignore, frontend/docker/**, frontend/vite.config.js, frontend/tests/docker.test.js -->
<!-- adopted: frontend/Dockerfile, frontend/compose.yaml, frontend/docker/default.conf.template, frontend/tests/docker.test.js -->

The production container SHALL contain built assets and runtime configuration,
not source tooling or local environment files. Standalone Compose binds
loopback port 8081. Nginx applies the existing CSP, anti-framing,
no-sniff and referrer safeguards, enforces a 16 KiB request-body limit,
and disables speech proxy buffering.

#### Scenario: deploying alongside the original frontend
- **WHEN** the standalone Compose frontend is started
- **THEN** it uses its own service identity and port without replacing an existing port-8080 service.

## Uncovered

- The current proxy does not inject a backend authentication credential.
- The 16 KiB production limit is not currently enforced by the Vite development
  proxy. The proposed backend requires coordinated 32 KiB limits and server-side
  authentication, not a silent change to this baseline.
- External backend availability and deployment authorization remain operator responsibilities.
