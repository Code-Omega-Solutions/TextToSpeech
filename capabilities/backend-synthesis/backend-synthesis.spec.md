# Backend synthesis - Living Spec

> [DRAFT] Adopted from the recovered backend implementation and its mocked tests.
> This documents source behavior, not native macOS qualification or deployment.

## Purpose

Provide a bounded HTTP API for German and English speech synthesis using the
host's macOS `say` voices and ffmpeg, with binary MP3 or WAV responses.

## Requirements

### Speech generation is authenticated by default
<!-- touches: backend/app/config.py, backend/app/routers.py, backend/tests/test_api.py, backend/tests/test_config.py -->
<!-- adopted: backend/app/config.py, backend/app/routers.py, backend/tests/test_api.py, backend/tests/test_config.py -->

The service SHALL require a nonempty `TTS_API_KEY` and a matching Bearer token
for speech generation by default. `TTS_AUTH_ENABLED=false` explicitly disables
this check. Health and readiness routes do not require authentication.

#### Scenario: a speech request has no valid bearer token
- **WHEN** authentication is enabled and a request omits or supplies an invalid token
- **THEN** the service returns 401 with a Bearer authentication challenge before synthesis.

#### Scenario: authentication is explicitly disabled
- **WHEN** `TTS_AUTH_ENABLED` is false and no API key is configured
- **THEN** a valid speech request can proceed without an Authorization header.

### Speech requests are validated against the supported contract
<!-- touches: backend/app/models.py, backend/app/routers.py, backend/tests/test_models.py, backend/tests/test_api.py -->
<!-- adopted: backend/app/models.py, backend/app/routers.py, backend/tests/test_models.py, backend/tests/test_api.py -->

The speech route SHALL accept `POST /v1/audio/speech` with trimmed nonempty
`input` up to 5,000 characters, optional `model` fixed to `macos-say`, optional
language (`de`, `de-DE`, `en`, `en-US`, or `en-GB`), optional bounded `voice`
hint, `response_format` of `mp3` or `wav`, and speed from 0.5 through 2.0.
Defaults are `macos-say`, MP3, and speed 1.0. Unknown fields and invalid values
are rejected with a safe 422 response. The optional voice hint is accepted but
does not select the synthesis voice.

#### Scenario: a request contains an invalid field or value
- **WHEN** the request has an unsupported language, format, model, speed, extra field, or invalid input
- **THEN** the service returns 422 without exposing submitted text in the error.

#### Scenario: a request succeeds
- **WHEN** a valid request is synthesized
- **THEN** the service returns binary audio with the matching MP3/WAV media type and filename.

### Language is explicit or detected from German and English text
<!-- touches: backend/app/language.py, backend/app/models.py, backend/app/config.py, backend/tests/test_language.py, backend/tests/test_models.py -->
<!-- adopted: backend/app/language.py, backend/app/models.py, backend/app/config.py, backend/tests/test_language.py, backend/tests/test_models.py -->

Explicit supported locales SHALL bypass detection. Otherwise, inputs with fewer
than the configured minimum alphabetic characters SHALL use
`TTS_DEFAULT_LANGUAGE`; longer inputs SHALL use `langid` and resolve German to
`de-DE` and English to `en-US`. Unsupported detected languages return 422 and
require an explicit supported override.

#### Scenario: text is too short for detection
- **WHEN** input has fewer alphabetic characters than `TTS_MIN_DETECTION_CHARS`
- **THEN** the configured default language is selected without calling the detector.

#### Scenario: detection selects an unsupported language
- **WHEN** automatic detection does not identify German or English
- **THEN** the service returns 422 and asks for a supported language override.

### Synthesis uses configured system voices and bounded subprocesses
<!-- touches: backend/app/services.py, backend/app/voices.py, backend/app/config.py, backend/tests/test_services.py, backend/tests/test_voices.py -->
<!-- adopted: backend/app/services.py, backend/app/voices.py, backend/app/config.py, backend/tests/test_services.py, backend/tests/test_voices.py -->

The service SHALL use configured macOS voices, scale the configured base
words-per-minute rate by request speed, and use ffmpeg to produce mono 44.1 kHz
PCM WAV or 128 kbps MP3. It SHALL preserve sentence and paragraph pauses, reject
more than 100 speech segments, limit simultaneous synthesis without queueing,
enforce a total request timeout and generated-audio byte limit, and remove
per-request temporary files after completion or failure.

#### Scenario: capacity or a synthesis prerequisite is unavailable
- **WHEN** all synthesis permits are occupied or a required executable or voice is unavailable
- **THEN** the service rejects the request with 503 without starting unbounded queued work.

#### Scenario: synthesis exceeds a configured bound
- **WHEN** speech generation exceeds its deadline, segment count, or output-size limit
- **THEN** the service returns the corresponding bounded error and cleans up request temporary files.

### Health and readiness report distinct service states
<!-- touches: backend/app/routers.py, backend/app/voices.py, backend/tests/test_api.py, backend/tests/test_voices.py -->
<!-- adopted: backend/app/routers.py, backend/app/voices.py, backend/tests/test_api.py, backend/tests/test_voices.py -->

`GET /healthz` SHALL report process liveness without probing executables.
`GET /readyz` SHALL report readiness only when `say`, ffmpeg, and the configured
German and US English voices are available. UK English is optional for readiness.

#### Scenario: a required runtime dependency is unavailable
- **WHEN** readiness checks cannot find a required executable or voice
- **THEN** `/readyz` returns 503 while `/healthz` remains an independent liveness check.

### Errors and logs avoid speech text and credentials
<!-- touches: backend/app/main.py, backend/app/routers.py, backend/tests/test_api.py -->
<!-- adopted: backend/app/main.py, backend/app/routers.py, backend/tests/test_api.py -->

The service SHALL return safe validation and synthesis errors, assign request IDs,
and log operational metadata without including submitted speech text, bearer
credentials, or raw subprocess output.

#### Scenario: validation or synthesis fails
- **WHEN** a request fails validation or the runtime reports a synthesis failure
- **THEN** the response and logs contain safe diagnostics and do not disclose the request text or token.

## Uncovered

- Root reuse and attribution terms are defined separately in the
  [project licensing living spec](../project-licensing/project-licensing.spec.md);
  they do not establish native qualification or third-party redistribution rights.
- The frontend proxy does not currently inject a backend credential. The backend
  requires authentication by default, so integration requires an explicitly
  authorized arrangement; disabling backend auth is not a substitute for
  authenticated proxy-to-backend access on an untrusted network.
- The source and mocked suite do not establish native macOS/voice/ffmpeg
  qualification, installation or prerequisite-check workflows, protected-file
  credential provisioning, service management, or a supported OS matrix.
- The 5,000-character input and 25 MiB output limits do not provide the proposed
  coordinated 32 KiB request-body enforcement at both proxy and backend.
