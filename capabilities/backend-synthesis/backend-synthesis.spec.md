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

#### Scenario: a configured backend is overridden by the request

- **WHEN** an authenticated request selects an enabled backend
- **THEN** the service dispatches that backend and returns the backend that actually produced the audio.

#### Scenario: VibeVoice is disabled or not qualified

- **WHEN** a request explicitly selects VibeVoice while it is disabled, or the operator has not supplied its qualification flag and measured memory budgets
- **THEN** the request is rejected before synthesis admission and the existing macOS backend remains available.

### Speech requests are validated against the supported contract
<!-- touches: backend/app/models.py, backend/app/routers.py, backend/tests/test_models.py, backend/tests/test_api.py -->

The speech route SHALL accept `POST /v1/audio/speech` with trimmed nonempty
`input` up to 5,000 UTF-16 code units, optional `model` selecting `macos-say`
or the optional `vibevoice` backend,
optional language (`de`, `de-DE`, `en`, `en-US`, or `en-GB`), optional bounded
`voice` hint, `response_format` of `mp3` or `wav`, and finite speed from 0.5
through 2.0. The backend default is `macos-say` unless an operator explicitly
configures an enabled, qualified VibeVoice deployment. MP3 and speed 1.0 remain
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

### Synthesis uses configured voices and bounded worker processes
<!-- touches: backend/app/services.py, backend/app/voices.py, backend/app/config.py, backend/app/vibevoice.py, backend/vibevoice_worker/worker.py, backend/tests/test_services.py, backend/tests/test_vibevoice.py, backend/tests/test_vibevoice_memory.py, backend/tests/test_voices.py -->

The service SHALL use configured macOS voices, scale the configured base
words-per-minute rate by request speed, and use ffmpeg to produce mono 44.1 kHz
PCM WAV or 128 kbps MP3. The optional VibeVoice path SHALL use one persistent
isolated worker, local offline assets, the reviewed language-compatible presets,
and only its speech decoder. It SHALL be admitted only when available memory
covers the measured worker peak and higher-priority reserve; reserve pressure or
an unavailable probe SHALL terminate the worker and prevent reload until
capacity recovers. Both paths SHALL preserve request, output, timeout, and
temporary-disk bounds, without an unbounded queue. A VibeVoice failure SHALL
discard partial audio and attempt the macOS backend at most once. Cancellation
or failure SHALL stop work and release request capacity.

#### Scenario: a VibeVoice worker is admitted and later yields

- **WHEN** a VibeVoice request is admitted with sufficient measured capacity and memory later falls below the configured reserve
- **THEN** one worker serves the request, terminates on reserve crossing, and does not reload while pressure remains.

#### Scenario: VibeVoice cannot produce a complete response

- **WHEN** worker startup, generation, memory admission, or output validation fails
- **THEN** partial worker audio is discarded and macOS speech is attempted at most once when available.

#### Scenario: synthesis prerequisites or capacity are unavailable

- **WHEN** all synthesis permits are occupied or a required executable or voice is unavailable
- **THEN** the service rejects the request with 503 without queuing it.

#### Scenario: synthesis is cancelled or exceeds a resource bound

- **WHEN** a request is cancelled or exceeds its deadline, segment, output-size, or temporary-disk limit
- **THEN** the service returns a bounded error, makes partial audio unavailable, and frees capacity for later requests.

#### Scenario: a valid synthesis request completes

- **WHEN** a valid request is synthesized with an available configured voice
- **THEN** the service returns the requested audio format with the configured rate and preserved sentence and paragraph pauses.

### Health and readiness report distinct service states
<!-- touches: backend/app/routers.py, backend/app/voices.py, backend/tests/test_api.py, backend/tests/test_voices.py -->

`GET /healthz` SHALL report process liveness without probing executables.
`GET /readyz` SHALL report readiness only when `say`, ffmpeg's required MP3 and
WAV encoders, and the configured German and US English voices are available.
Optional VibeVoice assets and worker residency SHALL NOT affect readiness. UK
English is optional for readiness. `X-VibeVoice-Status` SHALL report the
optional worker state without exposing private paths.

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
