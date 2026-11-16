# Data Model: VibeVoice Backend Integration

This model describes the request, configuration, resource-admission, worker,
voice, and response data introduced or reshaped by the feature. Existing speech
request protections and response limits remain authoritative; this document
does not redefine their numeric values.

## Entities

### Speech backend configuration

Operator-controlled settings that select the default backend and determine
whether VibeVoice can be admitted.

| Field | Type | Validation and meaning |
| --- | --- | --- |
| `host` | bind address | Defaults to loopback. `0.0.0.0` is permitted for an explicitly authorized private Open WebUI deployment; bearer authentication remains required, and the listener must not be exposed to untrusted networks over plaintext HTTP. |
| `default_backend` | `macos-say \| vibevoice` | Must name a supported backend. VibeVoice is the default only on a qualified host when enabled; otherwise the operator may select `macos-say`. |
| `vibevoice_enabled` | boolean | When false, VibeVoice is unavailable and must not be loaded. |
| `vibevoice_research_only` | boolean | Must be explicitly true before VibeVoice can be enabled. It records that this private deployment is authorized for research and development only, not routine production use or redistribution. |
| `worker_peak_memory_budget` | configured memory quantity | Required to admit VibeVoice; must be an operator-provided measured budget, not an assumed universal threshold. |
| `higher_priority_memory_reserve` | configured memory quantity | Required to admit VibeVoice; represents memory left available to higher-priority workloads. |
| `resource_probe` | `vm_stat`-based probe | Must provide a trustworthy available-memory observation. An unavailable or untrustworthy probe fails closed to macOS speech. |
| `worker_timeout` | duration | Bounds worker operations. |
| `worker_line_limit` | size limit | Bounds each JSON-lines protocol message. |
| `worker_audio_limit` | size limit | Bounds the worker WAV artifact and remains subject to existing output limits. |

The worker's peak budget and higher-priority reserve must both be configured.
Admission is allowed only when the available-memory observation covers the
worker budget plus the reserve. Available memory below the reserve means
VibeVoice must yield and remain unavailable until capacity recovers. This is a
capacity-based signal, not process-aware coordination; target-host qualification
must establish that it protects higher-priority workloads. Missing research-only
acknowledgment, unknown settings, failed probes, or unavailable worker/runtime/
assets make VibeVoice unavailable; they do not prevent macOS speech from starting.

### Speech request

A caller's authenticated synthesis request. The existing API request shape,
authentication, speed behavior, cancellation, and input limits remain in force.

| Field | Type | Validation and meaning |
| --- | --- | --- |
| `input` | string | Subject to existing input validation and size limits. Sensitive; must not appear in logs or error responses. |
| `model` | optional `macos-say \| vibevoice` | Optional per-request override. If omitted, use `default_backend`. An override is permitted only when that backend is enabled. |
| `language` | existing language value, including automatic detection | Preserve existing language detection and supported language behavior. VibeVoice presets are available for English and German only when research-only mode is explicitly enabled; other languages use macOS speech. |
| `voice` | optional voice-preset identifier | If omitted or blank for VibeVoice, resolve the default from the detected or selected language. A supplied voice must be known and compatible with the resolved language; reject invalid or incompatible choices before synthesis. |
| `response_format` | `mp3 \| wav` | Preserve existing supported formats, corresponding media types, and output limits. |
| `speed` | existing speed value | Preserve existing validation and backend behavior; do not broaden the supported range as part of this feature. |
| `cancellation` | existing cancellation signal | Must stop work and release the request's capacity; partial audio must not be returned. |

Authentication and request validation occur before model loading or synthesis.
An explicit `macos-say` request must not start or load the VibeVoice worker.

### Voice preset

An immutable catalog entry that maps a supported locale to a VibeVoice voice.

| Identifier | Language | Gender label | Default |
| --- | --- | --- | --- |
| `en-Carter_man` | English | male | Yes, for English VibeVoice requests |
| `de-Spk1_woman` | German | female | Yes, for German research requests |
| `de-Spk0_man` | German | male | No; optional for German research requests |

Validation rules:

- Voice identifiers must resolve to an entry in this catalog.
- The preset language must match the request's selected or detected language.
- A blank voice value is treated as omitted so OpenAI-compatible clients can use
  automatic language-based preset selection.
- Unknown or language-incompatible selections are rejected before synthesis and
  produce no audio.
- VibeVoice-specific presets may be used only when `vibevoice_research_only`
  is enabled. Without that setting, the worker remains unavailable and the
  service uses macOS speech.
- VibeVoice uses the reviewed Realtime 0.5B model with one shared resident
  weight set for English and German research requests. Other languages continue
  through macOS speech.

### Resource observation and admission decision

An ephemeral observation used to decide whether VibeVoice may load, remain
resident, or must yield.

| Field | Type | Validation and meaning |
| --- | --- | --- |
| `available_memory` | memory quantity or unknown | Obtained through the existing `vm_stat`-based approach. For a resident worker, add back its measured resident memory so the pressure value reflects other workloads; unknown or untrustworthy values deny VibeVoice admission. |
| `worker_peak_memory_budget` | memory quantity | Must be configured and measured for the optimized decoder-only worker. |
| `higher_priority_memory_reserve` | memory quantity | Must be configured by the operator. |
| `decision` | `admit \| deny \| yield` | `admit` requires available memory for both configured quantities. `deny` selects macOS speech without loading. `yield` evicts the resident worker and prevents new VibeVoice work while available memory remains below the reserve. |
| `reason` | safe reason code | Used for diagnostics; must not include speech text, credentials, or private model paths. |

The service does not modify or stop image-generation or Ollama workloads. If it
cannot reliably assess memory or honor the configured reserve, it uses macOS
speech rather than allowing VibeVoice to compete blindly.

### VibeVoice worker

One optional persistent child process owned by the speech service. Its runtime
and model dependencies are isolated from the API process.

| Field | Type | Validation and meaning |
| --- | --- | --- |
| `state` | worker lifecycle state | One of `unloaded`, `loading`, `ready`, `generating`, `yielding`, or `failed`; transitions are defined below. |
| `model_variant` | model identifier | Must be the reviewed VibeVoice Realtime 0.5B variant. |
| `model_weights` | one shared resident set | Shared across English and German research requests; no duplicate language-specific model copies. |
| `decoder` | speech decoder | Load and validate only speech-generation components. Do not construct the unused acoustic encoder. |
| `voice_prompt_cache` | cache allocations | May contain only prompts needed for supported presets; all prompt-cache allocations are released when the worker yields or stops. |
| `active_request` | optional request identifier | At most one request is generated at a time by the serialized worker. |
| `protocol_streams` | private stdin/stdout/stderr | One JSON request and response per line on stdin/stdout; protocol output only on stdout and diagnostics on stderr. |
| `worker_process` | child-process handle | Termination is the authoritative mechanism for releasing model and accelerator allocations. |

Worker requests use a unique WAV path inside a per-request private temporary
directory. The path and artifact are bounded and validated by the backend;
partial artifacts are discarded on failure, cancellation, or fallback. The
worker does not download assets, and it is not started until a request passes
authentication, validation, admission, and bounded-capacity checks.

### Synthesis result and audio artifact

The result returned through the existing speech response contract, regardless
of which backend generated it.

| Field | Type | Validation and meaning |
| --- | --- | --- |
| `audio` | bounded audio bytes | Must be complete and valid for the requested format. Never include partial VibeVoice output after fallback. |
| `format` | `mp3 \| wav` | Must match the requested supported format. WAV is passed through; MP3 is produced using the existing backend conversion path. |
| `media_type` | existing response media type | Must correspond to the returned audio format. |
| `actual_backend` | `macos-say \| vibevoice` | Identifies the backend that actually generated the returned audio, not merely the requested/default backend. Expose it through the response header defined in the interface contract. |
| `fallback` | boolean | True when a VibeVoice selection was served by macOS speech. |
| `failure_reason` | optional safe reason code | May describe an availability, resource, timeout, cancellation, or worker failure without private request data or model paths. |

If fallback is needed, the service discards any partial VibeVoice audio and
attempts macOS speech at most once when available. If no backend or required
encoder can produce a complete response, return the existing-style clear
availability error and no audio.

## Relationships

- A speech request resolves one effective backend from its override or the
  configured default.
- A speech request may reference one voice preset. The preset's language must
  match the request's resolved language.
- An English or German VibeVoice request requires research-only mode, an enabled
  backend, a successful resource admission decision, and available bounded
  worker capacity.
- German requests outside research-only mode use macOS speech without worker
  admission.
- The speech service owns zero or one VibeVoice worker; the worker owns one
  shared model-weight set and its currently permitted voice-prompt cache.
- A worker serially processes admitted VibeVoice requests. Requests beyond the
  configured bounded capacity are rejected or handled through macOS speech;
  they must not accumulate in an unbounded queue.
- A synthesis result identifies the backend that produced its single complete
  audio artifact and its requested output format.
- A VibeVoice failure or yield may lead to one macOS fallback attempt. It never
  creates a second fallback attempt or combines partial artifacts from two
  backends.

## State transitions

### Worker lifecycle

| Current state | Event / guard | Next state | Required effect |
| --- | --- | --- | --- |
| `unloaded` | Request passes validation, capacity, and memory admission | `loading` | Start the isolated worker lazily; do not download assets. |
| `loading` | Worker and decoder load successfully | `ready` | Retain one shared model and only required voice prompts. |
| `loading` | Worker, assets, runtime, or capacity unavailable | `failed` | Clean up partial worker resources; serve macOS speech when available. |
| `ready` | Request admitted to the serialized worker | `generating` | Generate one bounded request. |
| `generating` | Generation succeeds and no yield is required | `ready` | Validate the complete bounded WAV artifact and continue retaining the worker. |
| `ready` | Reserve crossed or higher-priority claim requires memory | `yielding` | Stop admitting VibeVoice work and terminate the worker. |
| `generating` | Pressure or cancellation requires eviction | `yielding` | Stop unsafe work, discard partial output, and terminate the worker. |
| `yielding` | Worker exits and allocations are released | `unloaded` | Clear model, decoder, and voice-prompt cache state. |
| `failed` | Failed worker resources are cleaned up | `unloaded` | Clear partial worker state; later requests may retry only after admission succeeds. |

While pressure remains, each new VibeVoice request is denied and uses macOS
speech when available; the worker is not reloaded. German requests outside
research-only mode always use macOS speech. When the higher-priority
need ends and configured capacity is available, a later admitted request may
transition the worker from `unloaded` to `loading` again. Service readiness is
independent of VibeVoice residency: macOS speech remains ready when its own
prerequisites are met.

### Request handling

`received -> validated -> admitted -> generating -> completed` is the normal
path. Invalid, unauthenticated, over-limit, unsupported-voice, or
unsupported-format requests are rejected before model loading. If VibeVoice
cannot start or continue, the request moves to `fallback` after partial
VibeVoice output is discarded, then makes at most one macOS synthesis attempt.
Cancellation or timeout stops work and releases bounded capacity. The request
ends as either a complete result from one actual backend or an error with no
audio.
