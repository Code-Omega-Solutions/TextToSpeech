# Proposed Private Prototype Contract

This contract is for a separately authorized loopback-only prototype, not a
change to the existing public service. The existing binary speech endpoint and
health/readiness semantics remain unchanged; preserve all authentication,
body/text/segment/output/disk limits, speed, locale, timeout and cancellation
behavior in `backend/app/` or reject the specific unsupported case explicitly.
Do not silently substitute defaults or truncate input.

## Local selection and status

Use the existing `POST /v1/audio/speech` JSON and binary MP3/WAV response.
For the private instance only, `X-Prototype-Engine` accepts `native` or
`candidate` (default `native`); `X-Prototype-Reference` is an opaque local
reference ID and is valid only with `candidate`. Reject invalid, missing,
unauthorized or incompatible references before generation. A candidate request
without a reference is non-cloned; the model adapter must prove it supports
that mode or return an explicit unsupported error. Private reference enrollment
is a local operator action, not a public upload API.

Every successful private speech response returns `X-TTS-Engine` (`native` or
candidate ID), `X-TTS-Voice-Condition` (`cloned` or `not-cloned`), and
`X-TTS-Fallback-Reason` (`none`, `pressure`, `insufficient-headroom`, or
`telemetry-unavailable`). A fallback from a clone always returns `native` and
`not-cloned`. Candidate load, execution or conversion failure is an explicit
failure, not a pressure fallback. If native synthesis fails after a valid
fallback, return an error, not partial audio or a success-shaped response.
For non-success responses provide sanitized reason codes and a request ID;
never disclose input, references, private paths or raw worker output.

`GET /local/v1/capabilities` on the private instance requires the same bearer
authentication as synthesis and returns candidate identifier, availability,
supported locales, formats, cloning and non-cloning support, and pressure
state. It contains no local paths, voices, recordings or resource telemetry.
Unavailable/unverified capability is reported as unavailable, not inferred.
The separate UI can use a normalized capability and response-status adapter;
it must remain usable against the existing service when this route is absent.
Loopback binding alone is not authorization; do not weaken existing auth.

The separate [UI proposal](../../003-voice-cloning-ui/contracts/capability-and-synthesis.md)
uses different routes, request shapes and response headers. These contracts are
not yet agreed or interoperable. Before any real integration, both owners must
agree and test a versioned mapping or revise both contracts, including consent,
reference retention, authentication and bounds; neither proposal is implemented.

## Pressure and termination policy

Before any real run the evaluator documents and verifies a macOS pressure
signal and a conservative available-headroom measurement, worker peak memory
method, measurement interval and a native reserve on the target. If a
reliable signal or reserve cannot be established, candidate admission is
disabled and the outcome is native fallback or an explicit failure.

The pre-registered reservation is at least the largest measured candidate
incremental peak for the approved input envelope plus 25% margin; the system
must have that reservation **and** an independently measured reserve for
native synthesis and unrelated workloads. Do not treat free cache, process RSS
alone or model cache limits as total unified-memory headroom. Unknown,
stale (>2 seconds), unavailable or internally inconsistent telemetry is unsafe.
The evaluator may choose a stricter reserve; no numeric memory guarantee is
claimed until measured. Before peak data exists, only a separately approved,
guarded calibration run with a pre-agreed hard stop can establish it.

- `NORMAL`: admit at most one candidate only when pressure is normal and
  safe headroom meets both reservations; otherwise use native or fail.
- `PRESSURE`: warning/critical pressure, insufficient headroom or telemetry
  failure blocks new candidate work. Stop an in-flight candidate on the first
  unsafe observation, terminate its process tree, wait for exit and cleanup,
  and only then attempt native fallback within the original request deadline.
  If termination, cleanup, remaining deadline or native capacity is inadequate,
  fail explicitly with no partial audio.
- `RECOVERING`: after a pressure episode, require 3 consecutive safe samples
  at least 5 seconds apart, with headroom above the admission requirement by
  an additional 10% of candidate reservation. Reset the counter on any unsafe
  or unknown sample. A subsequent request may re-enter `NORMAL`; no automatic
  work is launched.

Poll no slower than once per second while a worker runs, enforce an independent
request deadline, and use a bounded graceful stop followed by forced process
termination. Verify process exit and cleanup before releasing the single permit
or starting fallback; if this cannot be verified, keep candidate admission
disabled and surface the failure. Unload the model by terminating the dedicated
worker after each candidate request, on pressure, cancellation and shutdown.
This intentionally favors isolation over warm-model latency.

## Invariants and compatibility

Only complete, validated, bounded audio is emitted. Cancellation, timeout,
worker death, disk exhaustion, unsupported format/speed, failed conversion,
missing model or native dependency and invalid references produce explicit
failure. The shared deadline includes candidate work, termination and fallback.
Use nonblocking capacity admission with no unbounded queue. Require private
tests for each transition and outcome and native checks on the target Mac.
