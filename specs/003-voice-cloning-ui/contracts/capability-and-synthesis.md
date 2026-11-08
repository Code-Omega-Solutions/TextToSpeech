# Proposed Capability and Synthesis Contract

**Status: provisional, not implemented or agreed.** This is the UI plan's
integration proposal for the separate prototype owner to accept or revise.
No live integration, default enablement or publication claim follows from it.
Mocks can exercise this proposal independently; integration requires both sides
to agree and test the same version, bounds, authentication and retention policy.

## Legacy compatibility

`POST /api/v1/audio/speech` stays unchanged: JSON `input`,
`response_format` (`mp3` or `wav`), numeric `speed`, and `language` only for
an explicit selection. Auto mode omits language. Existing response audio and
errors remain valid; no optional fields or reference go on this route. The
legacy encoded body limit remains 32 KiB. Existing health checks and ordinary
generation must not wait on or depend on discovery.

## Optional capability

Proposed `GET /api/v1/capabilities` maps to upstream `/v1/capabilities`
through the same-origin proxy. Only an enabled, exact version-1 response with
valid values enables the clone choice:

```json
{
  "version": 1,
  "cloning": {
    "available": true,
    "accepted_media_types": ["audio/wav"],
    "max_reference_bytes": 2097152
  }
}
```

`available: false` disables cloning; the remaining fields may be omitted then.
When true, the MIME list is nonempty and the maximum is a positive integer no
greater than 2,097,152 bytes. Example values are synthetic, not a service
promise. Unknown versions, invalid/missing fields, disabled routes, 404, auth
failure, timeout and network failure fail closed for cloning, visibly identify
unavailability or unknown status, and leave ordinary generation usable.
Never cache an availability claim indefinitely; the service is authoritative
at submission time.

## Optional cloning request

Proposed `POST /api/v1/audio/speech/clone`, proxied to
`/v1/audio/speech/clone`, uses `multipart/form-data` containing:

| Field | Type | Meaning |
| --- | --- | --- |
| `input` | UTF-8 text | Existing input rules, including 5,000 UTF-16 units |
| `response_format` | text | `mp3` or `wav` |
| `speed` | decimal text | Existing range 0.5 through 2.0 |
| `language` | optional text | Existing explicit locale; absent for auto |
| `reference` | file | One nonempty advertised MIME type, bounded by advertised and UI limits |
| `authorization_confirmed` | text | Literal `true` for the current selection |

This affirmation is not proof of consent. Do not submit a file without an
explicit clone choice and confirmation. Apply a hard 2,097,152-byte file cap
and 3,145,728-byte total encoded multipart cap, including all fields and
boundaries; reject rather than truncate. Check file size/type and detectable
corruption locally, and require server validation. These caps are proposed and
must be agreed; an unsupported or smaller service limit wins. The current
backend neither accepts this request nor implements this endpoint.

## Response and errors

For a complete successful clone request, return a nonempty audio body with the
requested audio media type and these proposed headers:

| Header | Allowed values / meaning |
| --- | --- |
| `X-Speech-Contract-Version` | `1` |
| `X-Speech-Engine` | `candidate` or `native` |
| `X-Speech-Fallback` | `none` or `native` |
| `X-Speech-Fallback-Reason` | Optional registered token such as `memory-pressure` |

`candidate` with `none` identifies candidate output; `native` with `native`
identifies native fallback and must visibly state the clone was not preserved.
If the native reason is absent or unrecognized, show reason unknown; do not
invent one. Missing/unknown version, engine or fallback, inconsistent
combinations and invalid headers yield engine status unknown, never successful
cloning or an inferred fallback. These headers describe actual execution,
not intent. Legacy responses do not need them; ordinary results with no
metadata remain unknown.

Non-2xx, cancellation, timeout, invalid media and empty audio are failures;
never expose partial audio or stale output. Proposed error response is JSON
`{"code":"invalid_reference"}` with recognized codes `invalid_reference`,
`unauthorized_reference`, `capability_unavailable`, `upload_too_large`,
`generation_failed` and `timeout`; the UI maps recognized codes and HTTP
status to safe actionable messages, not arbitrary detail, text, file names or
service diagnostics. Unknown codes use a generic failure. Prototype failures
must not be silently relabeled as pressure fallback.

## Proxy, privacy and approval boundary

The optional proxy routes are disabled by default, individually allowlisted and
method-restricted in both Vite/preview and Nginx; same-origin requests receive
the existing server-side upstream authorization, not a browser credential.
No browser-supplied Authorization may reach upstream. Preserve CSP, upstream
validation and existing legacy limits. For the clone route enforce encoded
bytes for declared and chunked requests, cap concurrent in-flight bodies, set
timeouts and fail closed on overflow. Avoid access/body logging and avoid
persisting request bodies; if a proxy cannot avoid disk buffering, it must stay
disabled until its private storage, permissions, bounded lifecycle and cleanup
on success, failure and cancellation are explicitly reviewed and verified.
Do not claim that removing the browser selection deletes service-side data.

Contract owner must agree supported types, caps, header/route names, error
mapping, authentication, actual-engine semantics and server-side retention
and deletion before real integration. The proxy-to-service credential is not
browser-user authentication; network access controls remain a separate gate.
