# Private Speech Studio frontend

Recovered frontend for the local `bilingual-speech-web` application. This is a
standalone vanilla HTML/CSS/JavaScript project. Vite supplies development and
production builds; Nginx serves the production output and proxies the existing
speech service. There is no backend implementation in this directory.

## Requirements

- Node.js 24.14.0 or a newer Node 24 release, with npm.
- An authorized HTTP(S) speech-service origin for interactive use.
- Docker with Linux containers and Docker Compose for container deployment/tests.

The supported Node range is enforced by npm. `.node-version` records the recovery
toolchain version; no global version-manager configuration is required.

## Local development

Run these commands from this directory:

```powershell
npm ci
Copy-Item .env.example .env
```

Edit `.env` and set `TTS_UPSTREAM_URL` to the existing speech service's origin,
for example `http://localhost:8000` if it is reachable there **from the host**.
Do not include credentials, a path, query, fragment, or trailing slash.

```powershell
npm run dev
```

Open <http://127.0.0.1:5173>. The server fails if that port is occupied. Vite
proxies only the three documented API endpoints; the browser never receives the
configured upstream origin. Missing/invalid upstream configuration fails startup.
The value may also be supplied as a process environment variable.

```powershell
npm run build
npm run preview
```

The build creates `dist` and does not require a running backend or environment
configuration. Preview serves the build on port 5173, requires the same upstream
configuration as development, and applies the production security headers.
Vite development/preview are local tools, not production servers.

## Docker deployment

With `.env` configured:

```powershell
docker compose up --build -d
docker compose logs frontend
```

Open <http://127.0.0.1:8081>. This Compose project uses its own service identity,
image, and loopback port; it does not replace the original container on port 8080
or start a backend.

The origin must be reachable **from inside the container**. For a service on
the Docker Desktop host, use `http://host.docker.internal:8000`, not `localhost`.
Use the authorized machine's reachable origin if the backend runs elsewhere.
No credentials or machine-specific private addresses are included in the source.

```powershell
docker compose down
```

The multi-stage Dockerfile uses version-pinned Node and Nginx images. Its runtime
contains only the built static assets and recovered deployment configuration,
not npm or source tooling. The Nginx template is rendered at startup; only
`TTS_UPSTREAM_URL` is substituted. Startup validates the origin using the recovered
entrypoint. Shell files are normalized to LF via `.gitattributes`, and the
Dockerfile sets executable permissions.

## GitHub image publishing

The [publishing workflow](../.github/workflows/publish-frontend.yml) builds and
publishes this frontend on every push to `main`. It can also be run manually
from the Actions tab, but only for `main`.

The image name is `ghcr.io/<owner>/<repository>-frontend`, with owner/repository
names converted to lowercase. Each successful build publishes two tags pointing
to the same image version:

- `latest`: the newest published build.
- `build-<workflow-run-id>-<attempt>`: a unique tag for that build, including reruns.

After publishing succeeds, the workflow keeps the **five newest image versions**
and deletes older versions of this frontend package, including their build tags.
The two tags do not count as separate images. A unique OCI version label ensures
even repeated builds of the same commit get distinct image versions. Publishing
and cleanup are serialized to avoid races.

Images target Linux AMD64, matching the recovered deployment. Provenance/SBOM
attestations are disabled so separate registry manifests do not consume image
retention slots. Build caching uses GitHub Actions' cache rather than a separate
registry image.

The workflow uses `GITHUB_TOKEN` with `contents: read` and `packages: write`; no
Docker Hub credentials or personal access token are required. The OCI source
label associates the package with this repository. For an existing package,
ensure this repository has **Admin** access under the package's Actions access
settings so its workflow token can delete old versions. Organization policies
must also permit Actions to publish packages. Cleanup failures fail the workflow
rather than silently skipping retention.

No GitHub remote was configured when this workflow was added. It will run after
the repository is pushed to GitHub and Actions is enabled. Image visibility
follows the GHCR package settings; private images require authentication to pull.
Published images still require `TTS_UPSTREAM_URL` at container startup.

## Tests

```powershell
npx playwright install chromium
npm test
```

On Linux CI hosts, browser system libraries may also be needed:
`npx playwright install --with-deps chromium`.

If a managed Windows network requires the system certificate store for the
browser download, use `$env:NODE_USE_SYSTEM_CA='1'` before the install command.
Do not disable TLS verification.

- `npm run test:unit`: origin validation, exact development-proxy mappings,
  and an actual Vite development-server integration test.
- `npm run test:e2e`: production build followed by desktop/mobile Chromium tests.
- `npm run test:e2e:ui`: the same browser tests in Playwright's interactive runner.
- `npm run test:docker`: builds the image and verifies Nginx, static resources,
  security headers, API forwarding, method/body restrictions, and startup errors.
  Requires a free port 8081 and Docker host connectivity to a temporary local
  fixture server. The fixture briefly listens on an ephemeral host port. Only
  the test's temporary container is removed afterward.

Browser tests own port 5173 and refuse to reuse another server. API responses are
intercepted only by the test harness; test configuration points any accidentally
unhandled API request to an unused local port, never to the real speech service.
Playback/clipboard behavior is controlled in tests to make permission and error
states deterministic. Docker tests use a temporary fixture upstream, not a real
speech backend. Neither suite sends text for real synthesis.

Optional pixel-for-pixel recovery comparison against the original container:

```powershell
$env:ORIGINAL_FRONTEND_URL='http://127.0.0.1:8080'
npm run test:e2e
Remove-Item Env:ORIGINAL_FRONTEND_URL
```

The comparison captures both pages in the same browser at desktop/mobile sizes,
with health responses intercepted. It is skipped unless explicitly enabled.
Playwright traces and reports are ignored by Git.

## Preserved interface and backend contract

The UI supports a required text field limited to 5,000 JavaScript string code
units, clipboard paste and clear, auto-detection or `de-DE`/`en-US`/`en-GB`,
MP3/WAV, and speed 0.5-2.0 in steps of 0.1 (default 1.0).

| Browser endpoint | Upstream endpoint | Behavior |
| --- | --- | --- |
| `GET /api/healthz` | `/healthz` | HTTP success means connected; checked on page load |
| `GET /api/readyz` | `/readyz` | Preserved readiness proxy; not currently called by the UI |
| `POST /api/v1/audio/speech` | `/v1/audio/speech` | JSON request; binary audio response |

Speech request:

```json
{
  "input": "Text to speak",
  "response_format": "mp3",
  "speed": 1,
  "language": "en-US"
}
```

Auto-detection omits `language` entirely. Successful nonempty audio is made
available through an object URL for playback and download as `speech.mp3` or
`speech.wav`. HTTP errors use a string `detail` from a JSON response when
available, otherwise an HTTP-status message. Network, empty-audio, clipboard,
and blocked-autoplay states have user-visible feedback.

The recovered Nginx configuration retains a 16 KiB request-body limit, speech
POST restriction, 5-second connection timeout, read timeouts of 10/15/75 seconds
for health/readiness/speech, disabled speech proxy buffering, security headers,
and 404 responses for unknown static paths. The 5,000-unit text limit and
16 KiB encoded request limit are distinct existing constraints.

The original app marks the service unavailable after a generation failure and
connected after success; it does not poll health continuously. No frontend text
storage, telemetry, external fonts, or remote assets are introduced. The frontend
does not determine the backend's own storage/logging policy.

Future backend restoration should satisfy this contract and update the
server-side origin configuration. No frontend redesign or backend restoration
is required to run this project against the existing service.

## Recovery provenance

Recovered directly from container `bilingual-speech-web`, image
`bilingual-speech-web:local`, image ID
`sha256:279ec8db54024a2f050d221188ab4389672aee70a2f4f8d12752b93a09a7c23e`.

The running image reported Nginx 1.30.6 and retained readable, unminified source.
The original assets and deployment files were extracted and their SHA-256 hashes
verified against the container:

| Recovered source | Original SHA-256 |
| --- | --- |
| `index.html` | `8748b51440eba9117792b519637fae89bd90f3ff6c24c79327fd07d6a6278903` |
| `app.js` | `ba59f5ccd186bc487c68608bfa7c9ffb9d82abdc889ea4fdbdce8b9733560692` |
| `styles.css` | `a287420c4b9a3bb2b1d52db9553d2e0c10345328e93f35a86aadee219bcff641` |
| `public/icon.svg` | `359a43d251faa19c99c7b793b27751456c1a86cb43cc1fa6ec873b057451a259` |
| `docker/entrypoint.sh` | `076ac76de6d356da94ff914522065c9920556a3ccb353ccc6167cff647d3ae86` |
| `docker/default.conf.template` | `63da4ab8f5139f3e63b31dbf062bf6346ccfda7c9924306e4dd2bf3ba92479e4` |

Paths inside the container were `/usr/share/nginx/html` for web assets,
`/entrypoint.sh`, and `/etc/nginx/templates/default.conf.template`.
The only application-source integration change is making the HTML script a
module so Vite can build it. The icon is placed in Vite's `public` directory.
CSS minification is disabled to preserve the original gradient's exact color
values rather than quantizing its alpha channel during build optimization.
Application JavaScript, CSS, icon content, Nginx template, and entrypoint are
otherwise unchanged.

Package metadata, dependency lockfile, Vite/Playwright configuration, tests,
Dockerfile, Compose definition, and this documentation are reconstructed setup.
The original build configuration and Git history were not present in the
container and are not claimed to have been recovered.
