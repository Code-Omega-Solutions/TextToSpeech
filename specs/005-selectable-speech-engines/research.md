# Research: Selectable Speech Engines Prototype

## Decision 1: Compare Fish Variants Before Selecting One

**Decision**: Compare only the documented Fish Speech variants, Drama 3 and
S2-Pro, using separate columns for published model size, platform/resource
claims, language evidence, terms, and local measurements. Do not select or
install a variant in this plan.

**Rationale**: The pinned upstream README lists Drama 3 at 35B total/3B active
parameters and S2-Pro at 4B parameters. The installation guide describes Drama
3 as NVIDIA-only with at least 48 GB GPU memory and excludes CPU and Apple MPS.
It lists an S2-Pro CPU path and 24 GB GPU guidance. Neither vendor benchmark nor
parameter count demonstrates English/German quality, latency, or suitable
performance on the target. [R1, R2]

**Alternatives considered**: Select Drama 3 because it is newer; rejected
because its published platform requirements do not match the observed target
class. Select S2-Pro immediately because it is smaller; rejected because
smaller does not establish weight permissions, macOS support, local quality, or
responsiveness. Compare other TTS families; excluded by the user's clarification.

## Decision 2: Keep Engine Selection Static and Explicit

**Decision**: Replace backend identifier branching with a small, statically
registered engine interface used by the existing `SpeechService`. Register
`macos-say` and the optional `fish-speech` adapter. Preserve `vibevoice` as a
legacy request identifier that returns the established safe unavailable
response without constructing or loading its worker.

**Rationale**: The API already selects a backend using the optional `model`
field, and response metadata already reports the actual engine and fallback.
Tests cover the existing audio/auth/error contract. A fixed registry supports
the two real engines without introducing plugin discovery, dynamic imports, or
an independently versioned extension system. [R3, R4]

**Alternatives considered**: Add a general runtime plugin loader; rejected as
unnecessary for two in-tree engines and harder to audit. Alias old VibeVoice
requests to the default; rejected by the user's clarification because it would
hide a client migration and silently change engine selection.

## Decision 3: Run Fish as a Separately Managed Local Inference Service

**Decision**: Implement the backend Fish adapter as a bounded HTTP client for a
separately managed Fish Speech API server on a loopback origin. Use the pinned
upstream `POST /v1/tts` MessagePack protocol and its WAV output, then use the
existing audio conversion path for requested MP3/WAV responses. The adapter is
disabled when its endpoint or credential is not configured. Do not package Fish
model weights or launch its model server from the API process.

**Rationale**: Upstream documents `/v1/tts` as MessagePack and states the loaded
checkpoint determines the model, with no per-request model selector. A separate
service keeps the API process and its startup/readiness independent of a large
model runtime. The user wants engine selection while Fish is still under
evaluation. [R2]

**Alternatives considered**: Import Fish runtime packages into the API process;
rejected because this couples startup and dependency/asset lifecycle to model
weights. Spawn the upstream CLI for every request; rejected because the
documented API server already provides a stable service boundary and avoids
unbounded per-request child processes. Send requests to an arbitrary remote URL;
rejected because credentials and speech text must not be sent to an unreviewed
network destination.

## Decision 4: Add a Protected Engine Catalog and Drive the Existing UI

**Decision**: Add an authenticated, read-only `GET /v1/audio/engines` route that
reports configured engine identifiers, availability, supported languages, and
public voice identifiers only. Extend the existing Vite allowlist/proxy for that
GET route. Add engine and voice selectors to the repository's existing
vanilla-JavaScript speech screen; keep Open WebUI's API contract unchanged.

**Rationale**: The user asked for a discovery response and selected this
repository's frontend, which is not Vue. The current UI has no engine or voice
selection controls. The existing proxy replaces browser authorization with a
protected server-side credential and denies unknown API paths; the discovery
route must preserve both boundaries. [R3, R5]

**Alternatives considered**: Expose model-server reference paths or filesystem
locations; rejected because discovery should expose identifiers, not private
runtime layout. Publish discovery unauthenticated; rejected because the existing
service authenticates speech and a private catalog can reveal enabled runtime
capabilities. Edit Open WebUI's Vue source; rejected because that source is not
in this workspace.

## Decision 5: Keep Remote Deployment Parallel and Approval-Gated

**Decision**: Preserve the existing healthy listener and plan the prototype as
a separate service on a separately approved port. Do not install model weights,
Python runtimes, audio tools, or register/start a service as part of local code
implementation. Before any remote changes, review the exact install plan and
obtain approval for host runtime prerequisites and service paths.

**Rationale**: SSH public-key authentication succeeded after the user accepted
the displayed host-key fingerprint. Read-only inspection found a healthy
service already using the default backend port, while the target lacks the
backend's required Python generation and `ffmpeg`; the installed CLI's
prerequisite guidance describes the backend as macOS and requires Python 3.11+
and `ffmpeg`. These facts are not recorded with host names, addresses, usernames,
credentials, or private paths. [R3, R6]

**Alternatives considered**: Replace the current service in place; rejected
because it risks downtime and contradicts the user's parallel-deployment
choice. Change the existing port or service configuration; rejected because
the existing listener remains untouched. Trust a host key automatically or
disable host-key checking; rejected because the user must verify a new host key.

## Decision 6: Preserve Exact Rights and Evidence Boundaries

**Decision**: Keep Fish disabled until the exact checkpoint, codec, packages,
and any voice references have reviewed terms and provenance for this use. Add
no weights or voice samples to the repository. Treat Fish's API/README claims as
upstream evidence and local quality, latency, memory, or readiness as unknown
until explicitly approved tests run.

**Rationale**: The existing assessment records that the repository's reviewed
Fish Audio Community License does not establish S2-Pro weight rights; its README
states that S2-Pro weights use a separate Research License. Private use does
not remove voice consent, attribution, or model-specific obligations. The
project licensing capability requires exact artifact review before installation
or release. [R2, R7, R8]

**Alternatives considered**: Treat public/community weights as unrestricted;
rejected because the project policy and upstream terms distinguish code, model
weights, codecs, voices, and intended use. Infer German quality from a broad
multilingual claim; rejected because no local comparison is available.

## Decision 7: Use the Documented Fish MessagePack Protocol

**Decision**: The candidate adapter sends Fish requests as MessagePack to the
pinned upstream `POST /v1/tts?format=msgpack` endpoint and consumes its audio
response. Add the MessagePack codec as a direct, version-locked backend
dependency only after reviewing its exact distribution license and updating the
third-party inventory. Send only the text, configured voice reference, and
supported synthesis options needed for the request.

**Rationale**: The pinned upstream API client uses `ormsgpack.packb`, sets
`Content-Type: application/msgpack`, and supports a bearer API key. The server
loads a selected model at startup; its request does not select a different
checkpoint. The backend currently has no MessagePack dependency in its main
runtime group. [R2, R9]

**Alternatives considered**: Treat Fish as an OpenAI-compatible JSON endpoint;
rejected because the pinned server documentation specifies MessagePack. Vendor
Fish's client or runtime into the application; rejected because it adds unrelated
playback/CLI dependencies and model-runtime coupling.

## Sources

- **R1**: [Pinned Fish Speech README](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/README.md).
- **R2**: [Pinned Fish Speech inference guide](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/inference.md) and [installation requirements](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/install.md).
- **R3**: [Backend synthesis living spec](../../capabilities/backend-synthesis/backend-synthesis.spec.md) and [backend deployment prerequisites](../../backend/README.md).
- **R4**: [Backend speech-contract tests](../../backend/tests/test_speech_contract.py).
- **R5**: [Repository speech UI](../../frontend/app.js), [HTML](../../frontend/index.html), and [API proxy boundary](../../frontend/vite.config.js).
- **R6**: User-authorized, read-only host preflight in this session. Private host identifiers, local account names, and service details are intentionally omitted.
- **R7**: [Fish Speech recovered research](../../.specify/assessments/fish-speech/research.md#data--constraints).
- **R8**: [Project licensing living spec](../../capabilities/project-licensing/project-licensing.spec.md) and [third-party notices](../../THIRD_PARTY_NOTICES.md).
- **R9**: Pinned upstream [`tools/api_client.py`](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/tools/api_client.py) and [`tools/server/views.py`](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/tools/server/views.py), inspected read-only for request encoding, authentication, and audio response behavior.
