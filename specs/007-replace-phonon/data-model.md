# Data Model: Replace Fish Speech with Ollama Phonon

## Speech request

The authenticated `POST /v1/audio/speech` request retains the existing `input`, `model`, `language`, `voice`, `response_format`, and `speed` fields. `input` remains nonempty and valid Unicode, but is no longer capped at 5,000 UTF-16 code units. The ASGI request boundary continues to cap the encoded body at 32 KiB. Supported output formats and speed bounds remain `mp3`/`wav` and 0.5 through 2.0.

The `model` may select `phonon` or `macos-say`. The retired `fish-speech` identifier remains recognizable only to produce a safe unavailable response; it is not registered, advertised, or routed. Unknown, disabled, or unavailable engines do not fall back.

## Phonon approval record

An operator-controlled record describes the exact Phonon deployment. It is not created by the service and is not sufficient by itself to authorize a download or deployment.

| Field | Rule |
|---|---|
| Status | Must be explicitly approved before the engine can become available. |
| Model tags and digests | Must name a configured English and German candidate and record each reviewed digest as lowercase `sha256:` followed by 64 hexadecimal digits. Runtime identity must match the installed model metadata and synthesis uses a digest-addressed manifest on Ollama 0.40.18 or later. Older records without digests are unavailable until independently reviewed and updated. |
| Model source and terms | Must record the exact upstream source/revision, license or terms URL, reviewed terms revision, and intended-use basis. |
| Voices | Must list only reviewed voice IDs compatible with their configured language and model. |
| Voice provenance | Must identify the voice source and applicable terms. If a separate voice asset is used, record its immutable identity. |
| Endpoint | Must resolve to the explicitly configured trusted service origin; the origin is never returned by the public catalog. |

An absent, malformed, incomplete, unapproved, or mismatched record yields an empty voice catalog and an unavailable Phonon engine. It does not prevent native macOS readiness.

## Speech engine

The existing engine registry continues to expose only public engine metadata.

| Engine | Availability |
|---|---|
| `macos-say` | Determined by existing executable, codec, and voice checks. |
| `phonon` | Enabled only when its approval record is valid, at least one configured model and its approved voices are present, and a compatible trusted endpoint is reachable. Discovery lists only languages with matching model identities. |
| `fish-speech` | Retired. Requests receive an unavailable response; it is absent from the registry and catalog. |

Catalog entries contain only engine ID, availability, supported languages, and approved public voice IDs. They exclude endpoint URLs, asset paths, digests, credentials, and host details.

## Generated audio

Each Phonon segment produces bounded 24 kHz mono PCM. The service validates the format and combines the segments in source order without omission. It wraps the complete PCM payload as WAV and reuses the established conversion path to apply speed and return a bounded WAV or MP3 `SynthesisResult`.

The result records the actual engine as `phonon`, `fallback` as false, and the existing filename/media-type fields. Any failure discards partial output and returns the established safe error behavior.

## Request lifecycle

1. Authenticate and validate the request and its encoded size.
2. Reject a retired Fish selection or a disabled/unavailable Phonon selection before synthesis.
3. Acquire an existing synthesis permit and divide Phonon text into ordered segments no longer than the documented model limit.
4. Collect each response under the shared deadline, cancellation, temporary-storage, segment-count, and output-size bounds.
5. Convert and return the complete result with accurate engine metadata, or discard partial output on failure.
