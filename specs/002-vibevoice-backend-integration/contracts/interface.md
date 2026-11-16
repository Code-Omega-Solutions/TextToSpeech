# VibeVoice Backend Integration Interface Contract

## Public speech API

The feature extends the existing authenticated speech endpoint; it does not add
a route:

| Method and route | Contract |
|---|---|
| `POST /v1/audio/speech` | Accept a JSON `SpeechRequest`; return audio bytes in the requested format. |

Authentication remains the existing bearer-token contract. Requests pass
authentication and validation before backend admission or model loading.

### Request schema

```json
{
  "input": "Text to speak",
  "model": "vibevoice",
  "language": "en-US",
  "voice": "en-Carter_man",
  "response_format": "mp3",
  "speed": 1.0
}
```

| Field | Type | Contract |
| --- | --- | --- |
| `input` | string | Required, nonempty, at most 5,000 UTF-16 code units. |
| `model` | string | Optional backend selector. `macos-say` selects the existing macOS speech backend; `vibevoice` selects VibeVoice. When omitted, the operator-configured default applies. The selected VibeVoice model is always VibeVoice Realtime 0.5B. |
| `language` | string or `null` | Optional. Existing supported language tags and aliases remain accepted: `de-DE`, `en-US`, `en-GB`, `de`, and `en`. The normalized locale is used for backend routing. VibeVoice supports the reviewed English and experimental German presets only in an explicitly enabled private research-only deployment; other supported locales use macOS speech. |
| `voice` | string or `null` | Optional. For VibeVoice, accepted values are `en-Carter_man`, `de-Spk1_woman`, and `de-Spk0_man`; the value must match the resolved locale. An omitted or blank value selects Carter for English or Spk1 for German research requests. German requests use macOS speech when research-only mode is disabled. |
| `response_format` | string | Optional; `mp3` or `wav`. Defaults to `mp3`. |
| `speed` | number | Optional; inclusive range `0.5`–`2.0`. Defaults to `1.0`; existing speed behavior is preserved. |

Unknown fields are rejected. A blank `voice` is treated as omitted. An invalid
or language-incompatible VibeVoice voice is rejected before synthesis and
produces no audio. VibeVoice enablement
requires the operator's explicit research-only setting. When it is disabled, a
German VibeVoice selection is routed through macOS speech and reports
`X-Speech-Backend: macos-say` and `X-Speech-Fallback: true`.

### Response

A successful response is the audio payload, not a JSON envelope:

| Requested format | Media type | Filename |
| --- | --- | --- |
| `mp3` | `audio/mpeg` | `speech.mp3` |
| `wav` | `audio/wav` | `speech.wav` |

Responses retain `Content-Disposition: inline; filename="…"` and
`X-Content-Type-Options: nosniff`. The response includes
`X-Speech-Backend: vibevoice` or `X-Speech-Backend: macos-say` to identify the
backend that actually generated the audio. If VibeVoice falls back to macOS
speech, the header is `macos-say`; a requested-versus-actual mismatch indicates
fallback. Partial VibeVoice output is never returned.

### Errors and bounds

The existing safe error contract remains in effect:

| Status | Meaning |
| --- | --- |
| `401` | Missing or invalid bearer token when authentication is enabled. |
| `413` | Request body or generated audio exceeds the configured size limit. |
| `422` | Invalid request, unsupported voice/locale pairing, or more than 100 speech segments. |
| `500` | Synthesis failure; response does not expose input text, credentials, or private model paths. |
| `503` | Synthesis unavailable or bounded synthesis capacity unavailable. |
| `504` | Speech generation exceeded its time limit. |

Existing request, output, timeout, cancellation, and synthesis-capacity bounds
apply to both backends. If VibeVoice cannot safely start or continue, its
resources are released and macOS speech may be attempted at most once when
available. If both backends fail, the service returns an error with no partial
audio. Requests are not queued without bound and do not create duplicate model
instances.

`/healthz` remains a process-liveness check. `/readyz` remains ready when
macOS speech prerequisites are available, even if VibeVoice is disabled,
yielded, or missing its optional runtime or assets.

The memory gate uses the host's available-memory observation and an operator
configured reserve. Cold admission requires available memory for both the
measured worker peak budget and the reserve. For a resident worker, reserve
checks add back the worker's measured resident memory so the worker does not
count its own footprint as external pressure. The worker is evicted when
external available memory falls below the reserve. This remains a
capacity-based signal, not process-aware workload coordination. If target-host
qualification cannot establish that the gate reliably protects higher-priority
workloads, VibeVoice must remain disabled and macOS speech remains the fallback.

## Private worker protocol

The API process communicates with its optional, persistent worker over private
standard streams using one JSON object per line. This is an internal protocol,
not a client API. Protocol output uses stdout; diagnostics use stderr. Each
request names a unique WAV artifact within its request-scoped temporary
directory. The parent bounds protocol lines and artifact size and enforces the
request timeout.

Request fields are `request_id`, `text`, `locale`, `voice`, and `output_path`.
The worker returns one response line with the matching `request_id`, a
`status` of `ok` or `error`, and an optional safe error `reason`. On success,
the parent validates and reads the WAV artifact, then returns or converts it
through the existing audio path. The worker does not return audio bytes on
stdout, log speech text, or include private artifact paths in diagnostics.

The worker serializes inference and uses one shared resident model for English
and German research requests. Terminating it is the memory-release mechanism; worker startup,
model loading, failure, and yielding are not exposed as additional public API
routes.

The worker's private process receives a research-only marker from the
application and refuses to initialize without it. This marks scope; it is not
production approval or permission to redistribute model assets or generated
audio.

## Identifiers carried from the feature specification

The VibeVoice voice preset identifiers are `en-Carter_man`,
`de-Spk1_woman`, and `de-Spk0_man`, active only in research-only mode.
Requirement and success-criterion
identifiers are also retained verbatim for consumer and test traceability:

| Requirements | Success criteria |
|---|---|
| `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `FR-007`, `FR-008`, `FR-009`, `FR-010`, `FR-011`, `FR-012`, `FR-013`, `FR-014`, `FR-015`, `FR-016`, `FR-017` | `SC-001`, `SC-002`, `SC-003`, `SC-004`, `SC-005`, `SC-006`, `SC-007`, `SC-008`, `SC-009` |
