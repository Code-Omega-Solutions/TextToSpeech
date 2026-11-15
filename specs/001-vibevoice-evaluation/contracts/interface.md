# Evaluation Interface Contract

## Scope

This contract describes the private VibeVoice evaluation prototype only. It adds no production speech route, configuration, or service lifecycle behavior. The prototype is optional and removable/disableable; the existing speech method retains its contract.

## Operator entry and execution boundary

Run the tool from `backend/` with `python3 -m evaluation.vibevoice.cli`:

| Command | Behavior |
|---|---|
| `inspect --manifest <path>` | Validate the private manifest and perform read-only checks of the local machine, model adapters, and output destination. Report each blocker and its reason. |
| `run --manifest <path> --output-dir <path> --approve-run` | Generate only permitted, feasible comparisons and write local audio and a JSON report. The explicit flag approves this evaluation run; it does not authorize downloads, installation, service changes, or publication. |
| `serve --report <path>` | Serve the report's local review UI on `127.0.0.1` using an available local port. |

The operator supplies the private sample manifest and output directory. Execution may use only already-installed, approved model adapters, as bounded subprocesses without a shell; the prototype does not download or install models automatically. Invalid arguments or malformed input return a nonzero exit status. A valid inspection or run that records blockers returns a report with those blockers and does not claim that the affected comparison succeeded.

The output directory must be a dedicated, user-owned path outside the repository with owner-only access. Reject an unsafe existing destination instead of changing its permissions implicitly.

The baseline is the existing authenticated `POST /v1/audio/speech` endpoint. It is not replaced or modified. If it or an approved adapter is unavailable, the comparison is recorded as blocked, not substituted.

## Local review UI and routes

Bind the review server to `127.0.0.1` only. Do not accept a bind-address override. Preserve these routes and consumer/test-facing screen identifiers:

| Route | Screen identifier | Contract |
|---|---|---|
| `GET /listening-review` | `listening-review` | Paired playback for the same sample across configurations; show configuration identity and allow an individual 1–10 rating and qualitative observation. |
| `GET /results-summary` | `results-summary` | Show individual ratings, averages by language and configuration, observations, machine/resource evidence, reasons for missing results, and the product-owner decision. |

These are local UI routes, not production API routes. The local server exposes only the following run-scoped data operations:

| Route | Request / response |
|---|---|
| `GET /api/run` | Return the selected run's configuration, sample, status, and safe metadata needed by the UI. Do not return credentials or arbitrary filesystem paths. |
| `GET /api/audio/{sample_result_id}` | Return audio only for a completed result belonging to the selected run. Resolve by result ID, never by a caller-supplied path. |
| `PUT /api/ratings/{sample_result_id}` | Accept `{ "rating": 1..10, "observation": "..." }` only for completed, listened-to audio; persist atomically to the local JSON report. |
| `PUT /api/decision` | Accept `{ "outcome": "retain|partially_retain|remove|seek_alternative", "rationale": "..." }`; persist the product owner's decision locally. |
| `GET /api/report` | Return the report with individual ratings, averages, measurements, and explicit reasons for missing or incomplete data. |

Write operations must validate the request origin and a run-scoped session token. Audio, sample text, and results remain local and private unless a separate publication decision authorizes disclosure.

## Result data contract

Each evaluation configuration identifies its speech method, exact model variant where applicable, voice, language, target machine, and configuration. Each sample records its permitted source text and language/attribution, plus the corresponding generated audio for each evaluated configuration. Results record individual product-owner ratings (1–10), qualitative observations, averages by language and configuration, resource measurements, timings, missing-data reasons, and blockers. The product-owner decision is recordable as retain, partially retain, remove, or seek an alternative; there is no automatic numeric pass threshold.

Track the candidate identifiers exactly as specified: `VibeVoice-TTS-1.5B` and `VibeVoice-Realtime-0.5B`. Language support, model availability, and authorization are not implied by these names.

The input manifest must identify exactly five permitted sample IDs per evaluated language and include the text, language, source/attribution, and permission status for each. Every feasible baseline and candidate configuration for that language uses the same IDs. The persisted JSON report retains failed, blocked, cancelled, and incomplete outcomes with a reason; missing ratings and measurements are absent, never zero.

## Required feature identifiers

The following requirement identifiers are carried forward verbatim from the feature specification: `FR-001`, `FR-002`, `FR-003`, `FR-004`, `FR-005`, `FR-006`, `FR-007`, `FR-008`, `FR-009`, `FR-010`, `FR-011`, `FR-012`, `FR-013`, `FR-014`, and `FR-015`.

## Verbatim constraints

- model, voice, dependency, and sample-text terms must be assessed before use
- preserve existing service and require approval for target-machine changes
- No production deployment, service changes, or automatic fallback
- No two-person conversation or broader model search
