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

### Upstream configuration is explicit, durable and server-side
<!-- touches: frontend/config/**, frontend/vite.config.js, frontend/docker/entrypoint.sh, frontend/.env.example, frontend/tests/config.test.js, frontend/tests/dev.test.js, frontend/tests/docker.test.js, frontend/README.md, frontend/compose.yaml -->

Serving SHALL require `TTS_UPSTREAM_URL` as an HTTP(S) origin without credentials,
path, query, fragment or trailing slash. Development and production serving
SHALL load exactly one backend credential source on the server. Credential files
SHALL be read-only and protected; conflicting sources SHALL prevent startup.
The upstream URL, credential, and generated credential configuration SHALL not
be injected into browser assets. An authorized operator MAY save a replacement
origin through the authenticated server-side configuration API; the browser
configuration tab is informational and never collects credentials. The serving instance SHALL store that
origin at `/var/lib/private-speech-studio/endpoint.json` with restrictive
permissions and atomically replace it. A valid saved origin SHALL take
precedence over startup configuration and survive replacement when the
documented volume is retained.

#### Scenario: proxy credentials are missing or conflicting

- **WHEN** a configured server lacks a required backend credential or has conflicting sources
- **THEN** startup fails with a safe configuration error before accepting proxied requests.

#### Scenario: production serving uses a credential file

- **WHEN** production serving is configured with a protected backend credential file
- **THEN** it reads the credential server-side without modifying the file.

#### Scenario: browser assets are built or served

- **WHEN** the frontend is built or serves browser assets with an upstream URL and credential configured
- **THEN** those assets contain neither the URL nor the credential or generated credential configuration.

#### Scenario: a saved endpoint survives image replacement

- **WHEN** the operator saves a valid origin through the protected server-side
  workflow and recreates the container with
  the documented persistent volume
- **THEN** a fresh browser session uses the saved origin without requiring
  browser-local storage, browser credentials, or an image rebuild.

Configuration reads and writes SHALL require the operator bearer token, and
saved destinations SHALL match the exact `TTS_ALLOWED_UPSTREAMS` origin
allowlist. Failed validation, authorization, policy, or persistence operations
SHALL leave the previously saved origin unchanged.

#### Scenario: an unauthorized or disallowed destination is submitted

- **WHEN** a caller omits the operator token or submits an origin outside the
  configured allowlist
- **THEN** the service rejects the request without changing the persisted
  endpoint or forwarding credentials.

### API forwarding is restricted to the known service routes
<!-- touches: frontend/config/**, frontend/vite.config.js, frontend/docker/default.conf.template, frontend/tests/config.test.js, frontend/tests/dev.test.js, frontend/tests/docker.test.js -->

Serving SHALL forward `/api/healthz`, `/api/readyz`,
`/api/v1/audio/engines` and `/api/v1/audio/speech` to their corresponding
upstream paths without `/api`. Health, discovery, readiness, and speech read
timeouts SHALL remain bounded at 10, 15, 15, and 75 seconds respectively.
Health, readiness, and discovery require GET; speech generation requires POST.
Unknown static/API paths return 404. The proxy replaces any client-provided
upstream Authorization header with its configured credential and enforces a
32 KiB speech-body limit while streaming.

#### Scenario: an unknown route or wrong speech method is received

- **WHEN** a client requests an unknown route or uses GET for speech generation
- **THEN** the proxy returns 404 or 403 without forwarding the request to an arbitrary upstream route.

#### Scenario: engine discovery is proxied with server-side authentication

- **WHEN** a client requests `/api/v1/audio/engines` with GET
- **THEN** the proxy forwards it to `/v1/audio/engines`, replaces any supplied Authorization header, and bounds the read timeout.
- **WHEN** a client uses another method for the discovery route
- **THEN** the proxy denies the request without forwarding it.

#### Scenario: a speech request exceeds the body limit

- **WHEN** a client streams more than 32 KiB to the speech route
- **THEN** the proxy rejects the request without forwarding its body upstream.

#### Scenario: a client supplies an Authorization header

- **WHEN** a proxied request contains a client-provided Authorization header
- **THEN** the upstream receives only the server-configured backend credential.

### Production serving preserves isolation and response safeguards
<!-- touches: frontend/Dockerfile, frontend/Dockerfile.dockerignore, frontend/compose.yaml, frontend/.dockerignore, frontend/.gitattributes, frontend/.gitignore, frontend/docker/**, frontend/vite.config.js, frontend/tests/docker.test.js, LICENSE, NOTICE, SOURCE_OFFER.md, THIRD_PARTY_NOTICES.md -->

The production container SHALL contain built assets, runtime configuration,
project notices, a written corresponding-source offer and a versioned runtime
package inventory, not source tooling or local environment files.
The image SHALL preserve Debian package copyright/license files and expose OCI
labels linking to the source revision and bundled notices. Standalone Compose
binds loopback port 8081. Nginx applies the existing CSP, anti-framing, no-sniff
and referrer safeguards, enforces a 32 KiB request-body limit, and disables speech proxy buffering. Dynamic runtime routing reloads the
retained endpoint file for every request; Nginx remains available for
configuration diagnostics.

#### Scenario: deploying the standalone frontend container

- **WHEN** the standalone Compose frontend starts
- **THEN** it uses its own service identity on loopback port 8081 without replacing the existing port-8080 service.

## Uncovered

- External backend availability, deployment authorization, and any separate
  TLS/access-control boundary remain operator responsibilities.
- The source offer requires the publisher to retain and fulfill corresponding-source requests for at least three years.
