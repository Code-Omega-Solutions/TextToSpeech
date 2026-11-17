# Backend synthesis - Living Spec

> [DRAFT] Adopted from the recovered backend implementation and its mocked tests.
> This documents source behavior, not native macOS qualification or deployment.

## Purpose

Provide a bounded HTTP API for German and English speech synthesis using the
host's macOS `say` voices and ffmpeg, with binary MP3 or WAV responses.

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
<!-- touches: backend/app/config.py, backend/app/models.py, backend/app/engines.py, backend/app/fish_speech.py, backend/app/services.py, backend/app/routers.py, backend/tests/test_config.py, backend/tests/test_models.py, backend/tests/test_engines.py, backend/tests/test_fish_speech.py, backend/tests/test_engine_catalog.py -->

The serving application SHALL use a fixed registry of configured speech
engines. The `model` field SHALL select an enabled engine; omitting it SHALL
select the configured default. A request using legacy `vibevoice` SHALL return
503 without synthesis or fallback. An unknown, disabled, or unavailable engine
SHALL return a safe unavailable response and SHALL NOT silently select another
engine. Authenticated `GET /v1/audio/engines` SHALL list public engine IDs,
availability, supported English/German locales, and public voice IDs without
private paths or credentials. Fish Speech SHALL remain disabled unless a
loopback service origin and server-side credential are configured.

#### Scenario: an enabled engine is selected

- **WHEN** an authenticated request selects an enabled engine or omits `model`
- **THEN** the selected engine or configured default handles the request and
  response metadata identifies the engine that produced the audio.

#### Scenario: an unavailable engine is selected

- **WHEN** a request selects an unknown, disabled, or unavailable engine,
  including legacy `vibevoice`
- **THEN** it returns a safe 503 without reaching synthesis or silently
  substituting another engine.

#### Scenario: engine discovery is requested

- **WHEN** an unauthenticated caller requests the engine catalog
- **THEN** the service returns 401.
- **WHEN** an authenticated caller requests the engine catalog
- **THEN** the service returns configured public engine, availability,
  supported-language, and voice metadata without private configuration.

#### Scenario: Fish service is not configured

- **WHEN** Fish is disabled or its loopback endpoint or credential is absent
- **THEN** Fish reports unavailable and the macOS speech path remains usable.

#### Scenario: discovery does not leak runtime configuration

- **WHEN** the engine catalog is returned
- **THEN** it contains no credentials, filesystem paths, remote origins, or
  private host details.

#### Scenario: a configured backend is overridden by the request

- **WHEN** an authenticated request selects an enabled backend
- **THEN** the service dispatches that backend and returns the backend that actually produced the audio.

#### Scenario: legacy VibeVoice selection is retired

- **WHEN** a request explicitly selects the legacy `vibevoice` identifier
- **THEN** it receives a safe 503 before synthesis admission, without fallback, while the configured default engine remains available to other requests.

### Speech requests are validated against the supported contract
<!-- touches: backend/app/models.py, backend/app/routers.py, backend/tests/test_models.py, backend/tests/test_api.py -->

The speech route SHALL accept `POST /v1/audio/speech` with trimmed nonempty
`input` up to 5,000 UTF-16 code units, optional `model` selecting `macos-say`
`fish-speech`, or the legacy `vibevoice` identifier,
optional language (`de`, `de-DE`, `en`, `en-US`, or `en-GB`), optional bounded
`voice` hint, `response_format` of `mp3` or `wav`, and finite speed from 0.5
through 2.0. The backend default is `macos-say` unless an operator explicitly
configures an enabled `fish-speech` deployment. Legacy `vibevoice` requests
return a safe 503 and are not routed to another engine. MP3 and speed 1.0 remain
the request defaults. Unknown fields and
invalid values are rejected with a safe 422 response. The backend SHALL enforce
a 32 KiB encoded request-body limit while streaming, independent of
`Content-Length`.

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
<!-- touches: backend/app/services.py, backend/app/voices.py, backend/app/models.py, backend/app/config.py, backend/app/engines.py, backend/app/fish_speech.py, backend/tests/test_services.py, backend/tests/test_models.py, backend/tests/test_config.py, backend/tests/test_api.py, backend/tests/test_engines.py, backend/tests/test_fish_speech.py, backend/tests/test_engine_catalog.py, backend/tests/test_voices.py -->

The service SHALL use configured macOS voices and honor an explicitly selected
installed public voice; an unrecognized legacy voice hint SHALL retain the
configured default. It SHALL scale the configured base words-per-minute rate
by request speed and use ffmpeg to produce mono 44.1 kHz
PCM WAV or 128 kbps MP3. Fish Speech SHALL run as an optional separately
managed loopback service. Its adapter SHALL use bounded MessagePack requests,
the configured server-side bearer key, a finite timeout, response-size limits,
and validated WAV output. Fish WAV output SHALL use the existing bounded
conversion path for requested MP3/WAV format and speed. Fish SHALL remain
unavailable until configured and approved; it SHALL NOT download weights or
voice assets at startup. Fish failures SHALL return a safe unavailable or
bounded failure response and SHALL NOT silently fall back to another engine.
The serving application SHALL NOT construct or start the VibeVoice worker;
private VibeVoice evaluation tooling remains separate.

Serving engines SHALL preserve request, output, timeout, temporary-storage,
concurrency, cancellation, and private-data logging bounds. A response SHALL
identify the engine that generated it and any explicitly configured fallback.

#### Scenario: a selected macOS voice is honored

- **WHEN** a caller selects an installed public macOS voice for the resolved locale
- **THEN** the service uses that voice, while an unrecognized legacy hint keeps the configured default.

#### Scenario: Fish audio is converted within existing bounds

- **WHEN** Fish returns valid bounded WAV audio for an MP3, WAV, or speed-adjusted request
- **THEN** the existing conversion path returns the requested format within configured output, time, and temporary-storage limits.

#### Scenario: the Fish service fails

- **WHEN** the loopback Fish service is unavailable, times out, is cancelled, exceeds limits, or returns invalid audio
- **THEN** partial audio is discarded and no unconfigured fallback engine is used.

#### Scenario: a legacy VibeVoice request arrives

- **WHEN** a request selects `vibevoice` after the serving worker is retired
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

### Health and readiness report distinct service states
<!-- touches: backend/app/routers.py, backend/app/voices.py, backend/app/engines.py, backend/tests/test_api.py, backend/tests/test_voices.py, backend/tests/test_vibevoice_startup.py -->

`GET /healthz` SHALL report process liveness without probing executables.
`GET /readyz` SHALL report readiness only when `say`, ffmpeg's required MP3 and
WAV encoders, and the configured German and US English voices are available.
Optional Fish availability SHALL be reported separately and SHALL NOT change
readiness of the macOS baseline. UK English is optional for baseline readiness.
`X-Fish-Speech-Status` SHALL report whether the configured Fish service is
disabled, available, or unavailable without exposing private paths.
`X-VibeVoice-Status` remains `disabled` for response compatibility; serving
readiness SHALL NOT construct or probe a VibeVoice worker.

#### Scenario: a readiness prerequisite is unavailable

- **WHEN** `say`, a required ffmpeg encoder, or a configured German or US English voice is unavailable
- **THEN** `/readyz` returns 503 while `/healthz` remains an independent liveness check.

### Errors and logs avoid speech text and credentials
<!-- touches: backend/app/main.py, backend/app/routers.py, backend/tests/test_api.py -->

The service SHALL return safe validation and synthesis errors, identify the
actual backend in successful response metadata, assign request IDs, and log
backend, locale, response format, duration, and safe failure reason. Responses and logs SHALL exclude
submitted speech text, bearer credentials, raw request bodies, raw subprocess
output, query strings, and private machine paths.

#### Scenario: validation or synthesis fails

- **WHEN** validation or synthesis fails for a request containing speech text, credentials, or a query string
- **THEN** the response and correlated logs contain a request ID and safe diagnostics without those values, raw subprocess output, or private paths.

## Uncovered

- Root reuse and attribution terms are defined separately in the
  [project licensing living spec](../project-licensing/project-licensing.spec.md);
  they do not establish native qualification or third-party redistribution rights.
- The source and mocked suite do not establish native macOS/voice/ffmpeg
  qualification, publisher verification, service management, or a supported OS
  matrix. Prerequisite inspection, locked dependency setup, and protected-file
  credential loading are implemented but still require native qualification.
