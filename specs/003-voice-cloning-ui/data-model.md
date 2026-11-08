# Data Model: Voice Cloning Interface

These are transient client-side concepts, not database schemas or existing
server models. The proposed wire format is in
[the contract](contracts/capability-and-synthesis.md).

## Capability

- `state`: `checking`, `available`, `unavailable`, or `unknown`.
- When available: protocol version, nonempty accepted MIME types, positive
  max reference bytes within the UI cap, and service status.
- Discovery failure, disabled proxy routes, unsupported version, malformed
  fields or unsupported service: cloning unavailable/unknown; normal synthesis
  remains enabled. Do not treat successful health as cloning availability.

## Reference selection

- One in-memory `File`, name for local display, size, MIME type and validity;
  no sample content, name or path in logs or diagnostics.
- Authorization confirmation belongs to the current file, defaults false and
  resets on replacement, removal, clear and end of session. It is the user's
  assertion, not verified consent.
- Accept only service-advertised formats within both service and UI limits;
  reject zero-length, unsupported, oversized and locally detectable corrupt
  input with an accessible explanation. Server validation remains authoritative.
- Removing, clearing or replacing releases file and preview handles and revokes
  any associated object URL; no claim is made about server-side deletion.

## Request

- Mode: ordinary (default) or explicitly selected clone; current text, selected
  format, speed and optional explicit language are snapshotted at submission.
- Clone additionally requires available capability, current valid reference and
  current confirmation. Only clone sends the reference and affirmation.
- One in-flight request at a time; clearing/resetting or changing the reference
  invalidates the relevant result. Abort on cancellation/disposal where
  possible, and use request identity to ignore late completions even if abort
  races. Existing ordinary submission remains possible after errors.

## Generation result

- Nonempty audio blob and object URL; selected output format; engine status
  `candidate`, `native-fallback`, or `unknown`; a known or unknown reason.
- Only an explicit, internally consistent reported native fallback may show
  fallback; tell users it is not the selected cloned voice. Candidate is
  identified only when explicitly reported. Incomplete/invalid metadata is
  unknown rather than inferred. Missing reason remains explicitly unknown.
- Clear previous output before a new request; failed, cancelled or empty
  responses never display stale or partial output as the new result. Revoke
  old URLs on replacement, clear and disposal.

## State transitions

`checking -> available | unavailable | unknown`; rechecks may transition
between these states. `no reference -> selected/unconfirmed -> confirmed ->
submitting -> result | error`; replace/remove/clear resets confirmation.
If availability changes during submission, use only the completed response's
reported status. An obsolete request cannot restore a removed reference or
overwrite newer UI state. Errors permit retry and never disable ordinary mode.
