# Speech API contract

> Historical contract: automatic detection fallback is updated by
> [language detection fallback](../../004-language-detection-fallback/contracts/speech.md).

This document defines the browser-to-proxy and proxy-to-backend HTTP contract
for the macOS speech backend. The backend paths and payload names preserve the
identifiers in the feature specification. Frontend routes are the existing
proxy routes documented by the frontend.

## Routes

| Browser method and path | Backend method and path | Contract |
| --- | --- | --- |
| `GET /api/healthz` | `GET /healthz` | Credential-free liveness check. |
| `GET /api/readyz` | `GET /readyz` | Credential-free synthesis-readiness check. |
| `POST /api/v1/audio/speech` | `POST /v1/audio/speech` | JSON speech request; successful response is binary audio. |

The proxy allows only these routes. The speech route accepts `POST` only. It
replaces any browser-provided upstream `Authorization` header with its
server-configured backend credential. The credential is not sent to or exposed
in the browser. The browser does not call the backend paths directly.

## Speech request

Send `Content-Type: application/json` with a JSON object:

| Field | Required | Type and allowed values | Default / behavior |
| --- | --- | --- | --- |
| `input` | Yes | String; non-whitespace; at most 5,000 UTF-16 code units | Speech text. Unpaired surrogates are rejected. |
| `model` | No | String; only `macos-say` | `macos-say` |
| `language` | No | `de-DE`, `en-US`, `en-GB`, `de`, or `en` | Omitted means auto-detection, subject to the rule below. |
| `voice` | No | String of at most 128 characters | Ignored compatibility field. |
| `response_format` | No | `mp3` or `wav` | `mp3` |
| `speed` | No | Finite number from `0.5` through `2.0`, inclusive | `1` |

Unknown fields and whitespace-only `input` are rejected. Explicit supported
`language` values bypass detection. With `language` omitted, fewer than 20
Unicode alphabetic characters use the configured default (`en-US` initially);
otherwise local language detection accepts German or English and rejects other
languages.

The proxy and backend each enforce a maximum encoded request body of 32 KiB
while reading it; neither relies on `Content-Length`. The `input` character
limit is separate from this encoded-byte limit.

## Speech response

A successful request returns nonempty binary audio, not JSON or a persisted
URL. `response_format: mp3` returns `audio/mpeg` with
`Content-Disposition: inline; filename="speech.mp3"`. The MP3 encoding is
128 kbps CBR. `response_format: wav` returns `audio/wav` with
`Content-Disposition: inline; filename="speech.wav"`; WAV is mono, 44.1 kHz,
16-bit PCM.

## Errors

| HTTP status | Meaning |
| --- | --- |
| `401` | Missing or invalid backend bearer credential. |
| `413` | Encoded request body or generated audio exceeds its limit. |
| `422` | Invalid request, unsupported detected language, or too many speech segments. |
| `500` | Unexpected synthesis failure. |
| `503` | Synthesis capacity is exhausted or a required prerequisite is unavailable. |
| `504` | The shared synthesis-operation deadline elapsed. |

HTTP errors use a JSON string `detail` when available. Error details and
diagnostics must use safe categories and must not expose credentials, input
text, raw request bodies, raw subprocess output, or private machine paths.

## Health and readiness

`GET /healthz` and `GET /readyz` do not require authentication. Liveness may
remain healthy when synthesis is not available. Readiness verifies configuration
and credential availability, required executables, and required voices without
generating speech; it reports `503` when not ready. These endpoints do not
reveal environment values, host paths, credentials, or a full software
inventory. No response-body schema beyond these guarantees is specified here.

## Operational limits relevant to clients

- At most two synthesis operations run concurrently by default; there is no
  unbounded queue.
- A synthesis operation has a shared 60-second deadline.
- Generated audio is limited to 25 MiB.
- Speech is segmented on paragraph and sentence boundaries, with 0.4-second
  sentence pauses, 1.2-second paragraph pauses, and at most 100 segments.
- The default base speech rate is 180 words per minute; `speed` scales it.
