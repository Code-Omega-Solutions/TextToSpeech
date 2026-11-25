# Backend synthesis - Living Spec

> [DRAFT] Adopted from the recovered backend implementation and its mocked tests.
> This documents source behavior, not native macOS qualification or deployment.

## Purpose

Provide a bounded HTTP API for German and English speech synthesis using the
host's macOS `say` voices and ffmpeg, with binary MP3 or WAV responses. Phonon
is an optional, disabled-by-default engine. Fish is retired and has no runtime
adapter, managed worker, or launcher.

## Requirements

### Speech generation is authenticated by default
<!-- touches: backend/app/config.py, backend/app/routers.py, backend/tests/test_api.py, backend/tests/test_config.py -->

The service SHALL require one nonempty credential from `TTS_API_KEY` or a
read-only protected `TTS_API_KEY_FILE` by default. Configuring both sources
SHALL prevent startup. `TTS_AUTH_ENABLED=false` disables authentication.
Health and readiness routes do not require authentication. Responses and logs
SHALL not disclose credential values or credential-file paths.

#### Scenario: a speech request uses a protected credential file

- **WHEN** authentication is enabled, only the protected credential file is configured, and a request presents its matching bearer token
- **THEN** the service authenticates the request without disclosing the file contents or path.

#### Scenario: credential sources conflict

- **WHEN** both credential sources are configured
- **THEN** startup fails before serving requests and diagnostics disclose neither value.

#### Scenario: a speech request has no valid bearer token

- **WHEN** authentication is enabled and a speech request omits or supplies an invalid token
- **THEN** the service returns 401 before synthesis.

#### Scenario: health and readiness are checked without authentication

- **WHEN** a caller requests health or readiness without a bearer token
- **THEN** the route reports its service state without an authentication challenge.

#### Scenario: authentication is explicitly disabled

- **WHEN** `TTS_AUTH_ENABLED` is false and no credential is configured
- **THEN** a valid speech request can proceed without an Authorization header.

### Speech engines are selected explicitly and discovered
<!-- touches: backend/app/config.py, backend/app/models.py, backend/app/engines.py, backend/app/phonon.py, backend/app/services.py, backend/app/routers.py, backend/tests/test_config.py, backend/tests/test_models.py, backend/tests/test_engines.py, backend/tests/test_engine_catalog.py, backend/tests/test_fish_retirement.py, backend/tests/test_phonon_approval.py, backend/tests/test_phonon_availability.py -->

The serving application SHALL use a fixed registry of configured speech
engines. The `model` field SHALL select an enabled engine; omitting it SHALL
select the configured default. Phonon SHALL be disabled unless explicitly
configured with reviewed model/voice approval and a trusted loopback service
endpoint. Each approved model SHALL have an immutable SHA-256 digest that
matches installed service metadata before discovery or synthesis; synthesis
SHALL address the immutable model manifest on a compatible Ollama service. A request
using retired `fish-speech` or legacy `vibevoice` SHALL
return a safe 503 before synthesis admission, without fallback. Unknown,
disabled, or unavailable engines SHALL return a safe unavailable response and
SHALL NOT silently select another engine. Authenticated
`GET /v1/audio/engines` SHALL list only configured public engine IDs,
availability, supported locales, and public voice IDs without private paths or
credentials. The catalog SHALL NOT advertise Fish.

#### Scenario: an enabled engine is selected

- **WHEN** an authenticated request selects an enabled engine or omits `model`
- **THEN** the selected engine or configured default handles the request and
  response metadata identifies the engine that produced the audio.

#### Scenario: an unavailable engine is selected

- **WHEN** the default strict policy is active and a request selects an unknown, disabled, or unavailable engine,
  including legacy `vibevoice`
- **THEN** it returns a safe 503 without reaching synthesis or silently
  substituting another engine.

#### Scenario: engine discovery is requested

- **WHEN** an unauthenticated caller requests the engine catalog
- **THEN** the service returns 401.
- **WHEN** an authenticated caller requests the engine catalog
- **THEN** the service returns configured public engine, availability,
  supported-language, and voice metadata without private configuration.

#### Scenario: Phonon remains disabled without approval

- **WHEN** Phonon has no explicitly approved model/voice record or trusted
  service endpoint
- **THEN** it remains unavailable without an endpoint request, while the
  configured native engine remains usable.

#### Scenario: Phonon service or model identity is unavailable

- **WHEN** the service is unreachable or incompatible
- **THEN** discovery reports Phonon unavailable with no voices and speech
  requests return 503 without calling the speech endpoint or falling back.
- **WHEN** an approved model is missing or its installed digest does not match
- **THEN** its language and voices are absent from discovery and speech
  requests for that language return 503 without falling back; another
  independently available language remains usable.

#### Scenario: a retired Fish selection arrives

- **WHEN** an authenticated client explicitly selects `fish-speech`
- **THEN** the speech route returns a safe 503 before synthesis admission and
  does not fall back to Phonon or the configured default.

#### Scenario: discovery does not leak runtime configuration

- **WHEN** the engine catalog is returned
- **THEN** it contains no credentials, filesystem paths, remote origins, or
  private host details.

#### Scenario: a configured backend is overridden by the request

- **WHEN** an authenticated request selects an enabled backend
- **THEN** the service dispatches that backend and returns the backend that actually produced the audio.

#### Scenario: legacy VibeVoice selection is retired

- **WHEN** the default strict policy is active and a request explicitly selects the legacy `vibevoice` identifier
- **THEN** it receives a safe 503 before synthesis admission, without fallback, while the configured default engine remains available to other requests.

### Speech requests are validated against the supported contract
<!-- touches: backend/app/models.py, backend/app/routers.py, backend/tests/test_models.py, backend/tests/test_api.py, backend/tests/test_fish_retirement.py -->

The speech route SHALL accept `POST /v1/audio/speech` with nonblank `input`
preserved exactly, optional `model` selecting `macos-say`, `phonon`, or the retired
`fish-speech`/`vibevoice` identifiers,
optional language (`de`, `de-DE`, `en`, `en-US`, or `en-GB`), optional bounded
`voice` hint, `response_format` of `mp3` or `wav`, and finite speed from 0.5
through 2.0. The backend default is `macos-say` unless an operator explicitly
configures Phonon with required approval. Retired Fish and legacy `vibevoice`
requests return a safe 503 without fallback. MP3 and speed 1.0 remain
the request defaults. Unknown fields and
invalid values are rejected with a safe 422 response. The backend SHALL enforce
a 32 KiB encoded request-body limit while streaming, independent of
`Content-Length`; there is no fixed text-unit limit.

#### Scenario: a request contains an invalid field or value

- **WHEN** a request contains an unsupported language, format, model, speed, an unknown field, or invalid input
- **THEN** the service returns 422 without exposing submitted text or starting synthesis.

#### Scenario: a streamed request exceeds the encoded body limit

- **WHEN** a request body exceeds 32 KiB, including chunked input or a misleading `Content-Length`
- **THEN** the service rejects it before parsing or synthesis.

### Language is explicit or detected from German and English text
<!-- touches: backend/app/language.py, backend/app/models.py, backend/app/config.py, backend/tests/test_language.py, backend/tests/test_models.py -->
<!-- adopted: backend/app/language.py, backend/app/models.py, backend/app/config.py, backend/tests/test_language.py, backend/tests/test_models.py -->

Explicit supported locales SHALL bypass detection. Otherwise, inputs with fewer
than the configured minimum alphabetic characters SHALL use
`TTS_DEFAULT_LANGUAGE`; longer inputs SHALL use `langid` and resolve German to
`de-DE` and English to `en-US`. Other detected languages fall back to `en-US`.
Unexpected detector failures remain errors.

#### Scenario: text is too short for detection

- **WHEN** input has fewer alphabetic characters than `TTS_MIN_DETECTION_CHARS`
- **THEN** the configured default language is selected without calling the detector.

#### Scenario: detection selects an unsupported language

- **WHEN** automatic detection does not identify German or English
- **THEN** the service selects `en-US` for synthesis.

### Synthesis uses configured bounded speech engines
<!-- touches: backend/app/services.py, backend/app/voices.py, backend/app/models.py, backend/app/config.py, backend/app/engines.py, backend/app/phonon.py, backend/tests/test_services.py, backend/tests/test_models.py, backend/tests/test_config.py, backend/tests/test_api.py, backend/tests/test_engines.py, backend/tests/test_engine_catalog.py, backend/tests/test_voices.py, backend/tests/test_phonon.py, backend/tests/test_phonon_api.py, backend/tests/test_phonon_approval.py, backend/tests/test_phonon_availability.py, backend/tests/test_phonon_segmentation.py, backend/tests/test_phonon_streaming.py, backend/tests/test_phonon_response_metadata.py -->

The service SHALL use configured macOS voices and honor an explicitly selected
installed public voice; an unrecognized legacy voice hint SHALL retain the
configured default. It SHALL scale the configured base words-per-minute rate
by request speed and use ffmpeg to produce mono 44.1 kHz
PCM WAV or 128 kbps MP3. Phonon SHALL be disabled by default and SHALL require
an explicitly approved model/voice record and a trusted loopback service
endpoint before use. Its adapter SHALL use bounded requests, a finite timeout,
bounded PCM reads, and ordered capacity-aware segmentation. Phonon output SHALL
use the existing bounded conversion path for requested MP3/WAV format and
speed. The service SHALL NOT download model or voice assets. Phonon failures
SHALL return a safe unavailable or bounded failure response and SHALL NOT
silently fall back to another engine.
The serving application SHALL NOT construct or start the VibeVoice worker;
private VibeVoice evaluation tooling remains separate.

Serving engines SHALL preserve request, output, timeout, temporary-storage,
concurrency, cancellation, and private-data logging bounds. A response SHALL
identify the engine that generated it and any explicitly configured fallback.

#### Scenario: a selected macOS voice is honored

- **WHEN** a caller selects an installed public macOS voice for the resolved locale
- **THEN** the service uses that voice, while an unrecognized legacy hint keeps the configured default.

#### Scenario: approved Phonon audio is converted within existing bounds

- **WHEN** Phonon returns valid bounded PCM audio for an MP3, WAV, or speed-adjusted request
- **THEN** the existing conversion path returns the requested format within configured output, time, and temporary-storage limits.

#### Scenario: Phonon text exceeds one model request's capacity

- **WHEN** request text exceeds the selected model's supported per-request size
- **THEN** the adapter submits bounded segments in order, preserving every
  input character including whitespace, and returns complete audio subject to
  service request and output limits.

#### Scenario: Phonon is disabled or fails

- **WHEN** Phonon is disabled, unavailable, times out, is cancelled, exceeds limits, or returns invalid audio
- **THEN** partial audio is discarded and no unconfigured fallback engine is used.

#### Scenario: a legacy VibeVoice request arrives

- **WHEN** the strict policy is active and a request selects `vibevoice` after the serving worker is retired
- **THEN** the route returns the safe unavailable response before synthesis admission and does not construct or invoke the worker.

#### Scenario: synthesis prerequisites or capacity are unavailable

- **WHEN** all synthesis permits are occupied or a required executable or voice is unavailable
- **THEN** the service rejects the request with 503 without queuing it.

#### Scenario: synthesis is cancelled or exceeds a resource bound

- **WHEN** a request is cancelled or exceeds its deadline, segment, output-size, or temporary-disk limit
- **THEN** the service returns a bounded error, makes partial audio unavailable, and frees capacity for later requests.

#### Scenario: a valid request completes

- **WHEN** a valid request is synthesized with an available configured voice
- **THEN** the service returns the requested audio format with the configured rate and preserved sentence and paragraph pauses.

### Historical Fish headroom-first policy (retired)

> **Historical only:** This section records the former Fish prototype policy
> and is not current serving behavior. The Fish adapter, supervisor, and
> launcher have been removed. The active engine contract above requires
> explicit availability and never falls back from a retired Fish selection.

<!-- touches: backend/app/config.py, backend/app/memory.py, backend/app/services.py, backend/app/routers.py, backend/app/main.py, backend/deployment/prototype-operations.md, backend/deployment/prototype-recreation.zsh, backend/deployment/test_prototype_recreation.zsh, backend/tests/test_config.py, backend/tests/test_engines.py, backend/tests/test_api.py, backend/tests/test_fish_deployment_template.py, backend/tests/test_speech_contract.py -->

`TTS_FISH_OPPORTUNISTIC=true` SHALL explicitly opt in to language-preserving
native fallback for valid neural selections, including retired `vibevoice`,
when optional synthesis is disabled, busy, resource-denied, unavailable or
times out within its neural budget. Unknown models and invalid/unauthenticated
requests SHALL remain rejected. Explicit native requests SHALL not start Fish.
Fallback SHALL ignore neural voice preference, use the resolved locale's native
default, preserve format/speed/output bounds and the original overall deadline,
and report `X-Speech-Backend`, `X-Speech-Fallback` and an allowlisted
`X-Speech-Fallback-Reason` (or `unknown`). Non-fallback responses omit the reason
header. Cancellation, oversized output and native failures SHALL not become
success-shaped fallbacks.

An enabled managed Fish service SHALL require a private, reviewed local argv
launcher and at least two overall request permits. Its launcher SHALL require
an exact local approval manifest for the actual clean source checkout revision
and deterministic source-tree digest, with no tracked, untracked, or ignored
files, every runtime model file, the codec file, immutable artifact revisions,
per-file hashes, applicable terms, and the tracked runtime entrypoint hash plus
fixed loopback serving contract before exec. The approval manifest itself SHALL
not be group- or world-writable on POSIX. The reference approval SHALL bind
each advertised ID to exactly `references/<id>/<stem>.wav` and its matching
`.lab` under a separate private reference-data root, reject symlinks and extra
Fish-consumed files, and record the exact CC0 dataset/release, accepted-term
permission basis, hashes, and private noncommercial intended use without
recording contributor identity. The managed launcher SHALL revalidate this
reference manifest before exec and run the Fish API with the reference-data
root as its working directory and the clean source checkout on `PYTHONPATH`.
It SHALL lazily create one
low-priority owned process session, admit one neural request, and leave native
admission independent of waiting neural requests. Defaults SHALL be a 16 GiB
worker process-group RSS budget, 12 GiB available-memory reserve, and 30-second
idle/cooldown limits. A cold start SHALL require both reserve and peak budget
by default. An explicit `TTS_FISH_STARTUP_MEMORY_BYTES` override SHALL replace
only the startup allowance, MUST be positive and no greater than the worker
budget, and SHALL NOT reduce the loaded reserve or runtime RSS ceiling.
The private operator may tune this optimistic allowance from observed behavior;
sampled monitoring cannot guarantee instantaneous yielding or prevent transient
memory pressure during load. With either admission policy,
a loaded worker SHALL not have its resident memory credited toward the reserve.

The supervisor SHALL monitor loading, active and idle workers, reject invalid
measurements, and stop only the owned process group on pressure, budget breach,
cancellation, timeout, idle expiry or shutdown. Unverified termination SHALL
disable neural restart and log an explicit safe error. Discovery SHALL not start
a model. The reviewed launcher SHALL use local approved assets without downloads;
offline library flags are not a network sandbox. Sampled host/RSS estimates
SHALL not be represented as hard physical/Metal memory isolation or native
qualification. Exact runtime/artifact/reference and deployment approval remain
separate gates.

#### Scenario: a request omits the voice when Fish is the configured default

- **WHEN** a request selects Fish as the configured default without a voice
- **THEN** the service selects `de-female` for `de-DE` or `en-female` for `en-US`
  only if that profile is in the approved catalog; unsupported locales can
  use the native fallback under the headroom-first policy.

#### Scenario: a deployment limits German Fish to the male reference

- **WHEN** `TTS_FISH_GERMAN_MALE_ONLY` is enabled
- **THEN** German Fish discovery and default selection use only the qualified
  `de-male` profile, requests for `de-female` are rejected, and English
  selection and manifest validation remain unchanged.

#### Scenario: a valid optional selection cannot run

- **WHEN** the headroom-first policy is enabled and Fish is disabled, busy, unavailable or resource-denied, or a valid legacy neural selection is made
- **THEN** native speech uses the resolved German/English locale without the neural voice preference, reports `macos-say` and fallback metadata, and retains the original response bounds.

#### Scenario: memory pressure occurs while loading, active or idle

- **WHEN** the owned worker exceeds its budget, available memory falls below reserve, or a memory probe fails in any lifecycle phase
- **THEN** the supervisor terminates only its owned group, rejects the neural result, and requires cooldown plus sufficient cold-start headroom before restart.

#### Scenario: the exact configured memory boundary is available

- **WHEN** available memory equals reserve plus peak budget at cold start, or equals reserve while the worker is loaded and RSS is no greater than budget
- **THEN** memory admission succeeds; dropping below reserve or exceeding budget denies neural work.

#### Scenario: an operator opts in to optimistic cold-start admission

- **WHEN** a positive startup allowance below the worker budget is configured and available memory equals reserve plus that allowance
- **THEN** cold start is admitted, but loading, active and idle monitoring still enforce the unchanged reserve and worker budget, stopping only the owned worker on breach.

#### Scenario: cancellation, idle expiry or shutdown occurs

- **WHEN** an active request is cancelled or times out, or the worker idles past its limit, or the application shuts down
- **THEN** the owned worker is stopped and reaped without terminating an external listener; cancellation starts no native fallback.

#### Scenario: an external listener or unverified cleanup is encountered

- **WHEN** the target endpoint is already listening or its connection probe is uncertain before worker creation, or owned group termination cannot be verified
- **THEN** the external listener is not adopted or killed, and unverified cleanup disables further neural starts rather than assuming memory was released.

### Health and readiness report distinct service states
<!-- touches: backend/app/routers.py, backend/app/voices.py, backend/app/engines.py, backend/tests/test_api.py, backend/tests/test_fish_retirement.py, backend/tests/test_native_speech_preservation.py, backend/tests/test_voices.py, backend/tests/test_vibevoice_startup.py -->

`GET /healthz` SHALL report process liveness without probing executables.
`GET /readyz` SHALL report readiness only when `say`, ffmpeg's required MP3 and
WAV encoders, and the configured German and US English voices are available.
Readiness SHALL depend only on the macOS baseline and SHALL NOT require or probe
Fish or Phonon assets or services. UK English is optional for baseline
readiness. `X-VibeVoice-Status` remains `disabled` for response compatibility;
serving readiness SHALL NOT construct or probe a VibeVoice worker.

#### Scenario: a readiness prerequisite is unavailable

- **WHEN** `say`, a required ffmpeg encoder, or a configured German or US English voice is unavailable
- **THEN** `/readyz` returns 503 while `/healthz` remains an independent liveness check.

#### Scenario: Phonon is disabled

- **WHEN** Phonon is disabled or its local approval and service prerequisites
  are absent while the native prerequisites are available
- **THEN** `/readyz` succeeds without probing Phonon.

### Errors and logs avoid speech text and credentials
<!-- touches: backend/app/main.py, backend/app/routers.py, backend/tests/test_api.py, backend/tests/test_speech_contract.py -->

The service SHALL return safe validation and synthesis errors, identify the
actual backend in successful response metadata, assign request IDs, and log
requested and actual backend, fallback status, locale, response format, duration,
and safe failure reason. The standalone entry point emits these request
diagnostics at INFO. Responses and logs SHALL exclude
submitted speech text, bearer credentials, raw request bodies, raw subprocess
output, query strings, and private machine paths.

#### Scenario: validation or synthesis fails

- **WHEN** validation or synthesis fails for a request containing speech text, credentials, or a query string
- **THEN** the response and correlated logs contain a request ID and safe diagnostics without those values, raw subprocess output, or private paths.

### Historical Fish prototype evidence (retained)

> **Historical only:** The following deployment and qualification records
> describe earlier Fish prototype work; they do not describe the current
> runtime or authorize target access, asset use, or service changes.

The operator-authorized private prototype now has a hash-bound clean patched
Fish source, exact approved checkpoints/runtime binding and four converted,
operator-auditioned German/English female/male references. Its authenticated
catalog and UI expose these approved choices; production is unchanged. Current
live requests first yielded to native WAV under the default conservative
28 GiB threshold. A separately authorized 4 GiB startup allowance plus 12 GiB
reserve now admits the private worker: all four short selections returned actual
Fish WAV without fallback. Sampled minimum available memory was 13.08 GiB and
peak owned-group RSS 3.00 GiB. This does not qualify worst-case/Metal memory,
subjective voice quality or the complete native pressure/cancellation lifecycle.
See feature 007's
[current deployment evidence](../../specs/007-fish-backend-enablement/quickstart.md).
External-output sharing remains separately gated.

### Iteration 5 Fish prototype evidence (historical)

The designated Apple Silicon prototype has been deployed on a separate backend
port using the existing backend bearer mechanism and a loopback Fish service.
Four authenticated German/English male/female reference combinations returned
playable WAV with truthful Fish backend metadata; the prototype rejected an
unauthenticated request with 401. This is live deployment evidence, not a
claim of subjective quality, bilingual identity, managed-worker lifecycle,
native fallback, or hard unified-memory isolation. The exact artifact, public
reference-consent, and managed-lifecycle gates remain tracked in feature 007's
research and quickstart.

### Iteration 9 prototype-only deployment evidence (historical)

The authorized native target was inspected with strict SSH and the exact stale
prototype launch definition was disabled, booted out with a bounded unload
wait, and quarantined under a non-`.plist` name. The persisted disabled state
and absence of the loadable definition were verified. Protected managed
prototype/UI definitions were recreated and restored with the same bounded
wait, while production health, authenticated speech, and process identity
remained unchanged. This establishes safe prototype service recreation only;
it does not qualify Fish artifacts, references, neural output, or managed
neural lifecycle behavior. The checked-in template therefore remains
fail-closed.

### Iteration 10 Fish launcher deployment-safety record (historical)

The managed Fish launcher now fails closed for dirty or ignored source trees,
requires a protected approval-manifest file on POSIX, and binds the exact
tracked runtime entrypoint and loopback serving contract before exec. The
prototype operations runbook is idempotent for already-unloaded labels and
uses bounded exact-label waits plus protected-copy rollback. These changes do
not qualify a model, codec, reference, native output, or live recreation; the
authorized native sequence remains an operational gate.

## Uncovered

- Root reuse and attribution terms are defined separately in the
  [project licensing living spec](../project-licensing/project-licensing.spec.md);
  they do not establish native qualification or third-party redistribution rights.
- The source and mocked suite do not establish native macOS/voice/ffmpeg
  qualification, publisher verification, service management, or a supported OS
  matrix. Prerequisite inspection, locked dependency setup, and protected-file
  credential loading are implemented but still require native qualification.
