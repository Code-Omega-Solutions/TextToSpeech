# Data model

## Endpoint configuration

- `origin`: normalized HTTP(S) origin with no credentials, path, query, or fragment.
- `saved_origin`: the last successfully persisted origin.
- `revision`: monotonically increasing opaque generation used to reject stale discovery responses.
- `source`: `startup` or `file`, for precedence and operator diagnostics.
- `file_path`: container-side JSON path, configurable only by startup settings.

Validation rejects blank, malformed, credential-bearing, non-origin, and unauthorized destinations. A failed save never changes `saved_origin`.

## Service capabilities

- `state`: `supported`, `unsupported`, `authentication-failed`, `unreachable`, `invalid-catalog`, or `empty-catalog`.
- `engines`: supported engine identifiers scoped to the current endpoint revision.
- `voices`: language-scoped voice identifiers scoped to the selected engine and revision.

Only `supported` exposes selectors. `unsupported` permits legacy speech using omitted model/voice fields. All other states clear choices and show an actionable status.

## Save result

- `active_origin`: the persisted origin returned after success.
- `revision`: the new endpoint generation.
- `error`: safe operator-facing reason on failure.

The API never returns credentials or speech content.
