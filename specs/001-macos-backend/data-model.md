# Data Model: Publishable macOS Speech Backend

This model describes the proposed feature contract, not proof that the recovered
baseline already implements it. Speech text and generated audio are transient;
the feature introduces no history, account, or persisted-speech entities.

## Entities

### Runtime Configuration

Validated settings loaded by the backend and its server-side proxy.

| Field | Constraints / meaning |
|---|---|
| `host`, `port` | Bind address and configured port. Default exposure is loopback; an occupied port is a blocker, not a reason to select another port. |
| `default_locale` | Supported locale used for short or ambiguous input; initially `en-US`. |
| `voice_map` | Executable voice names for `de-DE`, `en-US`, and optional `en-GB`; German and US English are required for readiness. |
| `say_executable`, `ffmpeg_executable` | Configured executable locations. ffmpeg must actually support MP3 encoding and WAV output. Invoke without a shell. |
| `base_rate_wpm` | Positive configured speech rate; defaults to 180 words per minute. Request speed scales this rate. |
| `request_body_limit_bytes` | 32 KiB maximum, enforced while streaming by both proxy and backend. |
| `text_limit_utf16_units` | 5,000 UTF-16 code units. |
| `max_segments` | Maximum 100 speech segments. |
| `max_concurrent_synthesis` | At most two by default; no unbounded waiting queue. |
| `operation_timeout_seconds` | Shared 60-second synthesis deadline by default, including child operations. |
| `audio_response_limit_bytes` | Maximum 25 MiB. |
| `temporary_disk_budget_bytes` | Finite aggregate/intermediate storage budget; initially 256 MiB per the research decision. |
| `credential_source` | Exactly one of an environment-provided credential or a protected credential file. The value itself is not part of public configuration or diagnostics. |

Configuration validation rejects unsupported locales/formats, invalid
executable or credential settings, conflicting credential sources, and
out-of-range resource limits. A missing or empty required credential fails
closed. The proxy uses its own server-side credential reference and fixed
upstream/route allowlist; it must replace any client-supplied Authorization
header and never expose its credential to browser code.

### Speech Request

One validated, non-persistent request to `POST /v1/audio/speech`.

| Field | Constraints / meaning |
|---|---|
| `input` | Required non-whitespace text; at most 5,000 UTF-16 code units. Reject unpaired surrogates. |
| `model` | Optional; if supplied, must equal `macos-say`. |
| `language` | Optional locale or alias: `de-DE`, `en-US`, `en-GB`, `de`, or `en`. Explicit supported values bypass detection. |
| `voice` | Optional compatibility field, ignored for voice selection, at most 128 characters. |
| `response_format` | `mp3` by default, or `wav`. |
| `speed` | Finite number from 0.5 through 2.0 inclusive; defaults to 1. |
| encoded body | Maximum 32 KiB, measured as bytes while reading; do not rely on `Content-Length`. Unknown JSON fields and malformed JSON are rejected. |

When `language` is absent, text with fewer than 20 Unicode alphabetic
characters uses `default_locale`. Otherwise local language identification
accepts German or English and rejects unsupported detected languages with 422.
The aliases `de` and `en` normalize to `de-DE` and `en-US`, respectively.

### Speech Segment

A transient portion of a request's text, split along paragraph and sentence
boundaries for synthesis.

| Field | Constraints / meaning |
|---|---|
| `text` | Text for one segment, held only in private per-request temporary storage. |
| `pause_after_seconds` | 0.4 seconds between sentences and 1.2 seconds between paragraphs, as applicable. |
| `sequence` | Stable request-local order; total segment count must not exceed 100. |

Segmentation must account for abbreviations, decimals, line breaks, and quoted
sentence endings. Segments are not persisted.

### Synthesis Operation

The bounded processing lifecycle for one authenticated request.

| Field | Constraints / meaning |
|---|---|
| `request_id` | Opaque correlation identifier safe for operational logs. |
| `locale`, `voice` | Resolved supported locale and configured voice. UK English is optional; missing it does not block default readiness. |
| `format`, `speed` | Validated output format and requested speed applied to the configured base rate. |
| `deadline` | One deadline shared across segmentation, speech subprocesses, conversion, and response production. |
| `permit` | One of the bounded synthesis slots; acquired without an unbounded queue and always released. |
| `workspace` | Private, collision-safe, per-request temporary directory subject to the temporary-disk budget. |
| `children` | Only subprocesses owned by this operation; launched without a shell and terminated on timeout/cancellation. |

User text is never interpolated into a command. Temporary text/audio and owned
children are cleaned up on success, error, timeout, and cancellation; no
process-wide or name-based termination is allowed.

### Synthesis Result

Transient binary response returned to the caller; no URL or persisted audio.

| Field | Constraints / meaning |
|---|---|
| `audio` | Non-empty encoded bytes, no more than 25 MiB. |
| `media_type` | `audio/mpeg` for MP3 or `audio/wav` for WAV. |
| `filename` | `speech.mp3` or `speech.wav` disposition filename. |
| `request_id` | Correlates the response/diagnostics without exposing text or credentials. |
| encoding | MP3 is 128 kbps CBR; WAV is mono, 44.1 kHz, 16-bit PCM. |

### Prerequisite Check Item and Report

A bounded, read-only inspection produces one item per prerequisite and a
machine- and human-readable report. It must not import the application,
synthesize audio, download, install, create an environment, alter
configuration, generate a credential, or register a service.

| Item field | Constraints / meaning |
|---|---|
| `id` | Stable diagnostic identifier. |
| `dependency` | Prerequisite being checked, such as supported macOS/architecture, `say`, Python, environment tooling, ffmpeg codec, voice, configuration, credential accessibility, destination access, disk space, or port. |
| `status` | `pass`, `warn`, or `fail`. Required missing/incompatible prerequisites are blockers; optional UK-English voice absence is a warning. |
| `detected_version` | Safe version or capability detail when available; never a secret. |
| `reason`, `remediation` | Safe explanation and actionable operator instruction, without private paths or raw command output. |

The report contains the items and overall readiness. Exit status is 0 when
ready, 1 for actionable blockers, and 2 for invalid invocation or incomplete
diagnostics. Every check is bounded and non-interactive. Unsupported OS,
macOS release, or unqualified architecture refuses installation without
changes. A prerequisite report is distinct from HTTP health: endpoints do not
reveal the full software inventory.

### Installation Plan and Installation Result

An installation plan records proposed changes for one operator-approved,
user-owned destination. It is presented before execution; explicit acceptance
is required, including unattended operation.

| Plan/result field | Constraints / meaning |
|---|---|
| `destination` | Approved, user-owned installation location; do not overwrite an existing incompatible managed environment without a separate deliberate replacement action. |
| `proposed_changes` | Exact missing prerequisites/actions, using approved documented distribution channels or an explicitly approved package manager. |
| `accepted` | Must be explicitly true before changes begin. No implicit consent or privileged escalation. |
| `steps` | Ordered installation steps and per-step completion/failure state. |
| `pending_manual_steps` | Required user actions such as OS-managed voice installation; their presence means setup is incomplete. |
| `verification` | Fresh prerequisite/readiness results after installation. |
| `failure_category` | Safe diagnostic category; distinguishes completed work from pending/failed work without raw output or secret values. |

Setup is serialized per destination and idempotent. Repeat setup on a complete
installation makes no changes. On interruption, only newly created temporary
artifacts may be removed; existing environments, credentials, services, and
running service state are preserved. Package-manager bootstrap, privileged
actions, service registration/start/restart, upgrades, rotation, remote access,
and uninstall are not implicit setup steps.

## Relationships

- A `Runtime Configuration` supplies defaults, limits, executable/voice
  mappings, and a credential reference to each `Synthesis Operation`.
- A `Speech Request` is authenticated and validated before language detection;
  it resolves to one locale/voice and one ordered collection of `Speech Segment`
  instances.
- One `Synthesis Operation` owns the request's permit, private workspace, and
  child processes, and produces at most one `Synthesis Result`.
- A `Prerequisite Report` aggregates `Prerequisite Check Item` records and
  determines whether setup/readiness is blocked or ready.
- An accepted `Installation Plan` is executed into an `Installation Result`;
  that result includes a fresh prerequisite report and any outstanding manual
  steps.
- The frontend proxy accepts only the existing three `/api/` routes and maps
  them to fixed backend endpoints; it does not create or alter the browser's
  speech request contract.

## State Transitions

### Check and readiness

Each check item progresses from not-run to `pass`, `warn`, or `fail`; a timed
out or otherwise incomplete diagnostic is represented as an incomplete report,
not as ready. Overall readiness is ready only when every required dependency
passes and configuration/credentials are valid. Optional UK-English absence
may warn without blocking default readiness. HTTP liveness may remain healthy
while synthesis readiness is unavailable; `/readyz` then returns 503.

### Installation

`proposed → accepted → executing → verified` is the successful path. A plan
cannot enter `executing` without explicit acceptance. Execution may instead
end as `incomplete` when manual steps remain, or `failed` when an operation
fails or is interrupted. Both outcomes report completed work accurately and
require a fresh check before claiming readiness; neither authorizes destructive
rollback of pre-existing state.

### Speech request

`received → authenticated → validated → capacity-reserved → synthesized →
responded` is the success path. Authentication failure terminates with 401
before detection/synthesis; validation failure returns 413 or 422 as
appropriate. Capacity exhaustion or missing prerequisites returns 503,
deadline expiry returns 504, and unexpected synthesis failure returns 500.
Every terminal path releases any acquired permit, terminates owned children,
and removes request-local temporary files.

## Contract references

The preserved API routes, request/response semantics, limits, error codes, and
authentication behavior are specified in `spec.md` under FR-010–FR-022. The
implementation choices and initial resource defaults are detailed in
`plan.md` and `research.md`.
