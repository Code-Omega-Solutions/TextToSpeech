# Speech API Contract: Replace Fish Speech with Ollama Phonon

This feature preserves the backend's existing public HTTP API and adds the `phonon` engine selection.

## `GET /v1/audio/engines`

Requires the existing bearer authentication. Returns public metadata for `macos-say` and `phonon` when configured. Phonon voices are limited to the approved language-specific catalog. The retired `fish-speech` engine is absent. The response does not expose endpoint URLs, local paths, model digests, credentials, or other private configuration.

## `POST /v1/audio/speech`

Requires the existing bearer authentication and the existing 32 KiB encoded-request limit.

| Field | Contract |
|---|---|
| `input` | Required nonempty speech text. No fixed 5,000-UTF-16-unit limit. The request-body bound still applies. |
| `model` | Optional engine selection. Supports `phonon` and `macos-say`; the retired `fish-speech` value receives a safe 503 rather than being redirected. |
| `language` | Optional existing language value or alias. Phonon is offered only for configured English and German locales. |
| `voice` | Optional approved voice ID compatible with the selected language and model. An unknown or unapproved Phonon voice fails safely. |
| `response_format` | `mp3` or `wav`; default remains `mp3`. |
| `speed` | Finite number from 0.5 through 2.0; default remains `1.0`. |

A successful response remains complete-response binary audio with the existing media type, filename, and headers identifying the actual engine and fallback state. A Phonon selection never silently falls back to native speech. Errors use the existing safe validation, unavailable, timeout, capacity, output-size, and synthesis-failure responses.

## Health and readiness

Baseline readiness continues to reflect the native macOS speech service and its existing prerequisites. Phonon absence does not make the service unready. The authenticated engine catalog reports Phonon availability separately; health and catalog output do not reveal its private endpoint or model paths.
