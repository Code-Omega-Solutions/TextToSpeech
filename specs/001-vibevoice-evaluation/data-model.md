# Data Model: Private VibeVoice Evaluation

This model describes the private, local evaluation artifacts. It does not change
the production speech API or authorize downloads, installation, service changes,
publication, or use of any model, voice, or text. The report is persisted locally
as JSON; operator-supplied texts, generated audio, credentials, and results are
not checked into the repository.

## Entities

### Evaluation run

One explicitly initiated evaluation, with a manifest and report.

| Field | Type | Validation |
| --- | --- | --- |
| `run_id` | string | Unique and stable within the local report store. |
| `created_at` | timestamp | ISO 8601 timestamp with timezone. |
| `operator` | string, optional | Private local identifier or display name; do not store credentials. |
| `manifest_path` | local path | Operator-supplied manifest; must resolve to an approved local input and contain no credentials. |
| `output_directory` | local path | Operator-supplied dedicated destination outside the repository; must be user-owned and inaccessible to group/other users. |
| `state` | enum | One of `preflight`, `ready`, `generating`, `reviewing`, `complete`, `blocked`, `failed`, `cancelled`. |
| `resource_limits` | object | Agreed run bounds, when applicable; generation must stop when a bound is reached. |
| `configuration_ids` | list of IDs | References configurations selected for this run; must include the baseline for each intended comparison. |
| `sample_ids` | list of IDs | References permitted sample texts selected for this run. |
| `decision_id` | ID, optional | References the product-owner decision recorded after evidence review. |

### Candidate machine and inspection

Each candidate machine has a read-only inspection record for the intended
evaluation target and storage volume.

| Field | Type | Validation |
| --- | --- | --- |
| `machine_id` | string | Stable identifier that does not expose a private address or unnecessary personal data. |
| `platform` | string | Record observed OS, hardware/architecture, and relevant platform details; do not infer qualification. |
| `inspected_at` | timestamp | ISO 8601 timestamp with timezone; re-inspect if capacity or permissions change. |
| `intended_storage_volume` | string, optional | Identify the volume when known without recording sensitive mount details. |
| `available_storage_bytes` | integer, optional | Non-negative measured value; missing measurements require a reason. |
| `available_memory_bytes` | integer, optional | Non-negative measured value; missing measurements require a reason. |
| `requirements` | list of strings | Applicable runtime/model requirements and their observed status. |
| `permissions_status` | enum | `approved`, `unclear`, or `denied`; unclear or denied permission blocks the affected action. |
| `limitations` | list of strings | Include reasons for unknown or unsuitable platform/capacity observations. |

### Terms and authorization record

Records whether the specific material and action are permitted, separately
from the product owner's later evaluation decision.

| Field | Type | Validation |
| --- | --- | --- |
| `authorization_id` | string | Unique within the run. |
| `material_type` | enum | `model`, `implementation`, `dependency`, `voice`, or `sample_text`. |
| `material_identity` | string | Exact variant/version/source or text attribution sufficient to identify what was reviewed. |
| `terms_reference` | string | Reference to the applicable terms and review evidence; do not treat a model-card license alone as clearance of implementation/dependencies. |
| `intended_use` | string | State the proposed private research use. |
| `status` | enum | `permitted`, `unresolved`, or `not_permitted`. |
| `reviewed_at` | timestamp, optional | Required when status is `permitted` or `not_permitted`. |
| `approved_action` | string, optional | Explicitly identify approved download, installation, or service-change action and destination when such an action is needed. |
| `approver` | string, optional | Record the operator/authority who approved the action, without credentials. |

An unresolved or not-permitted record blocks only the affected material/action;
the evaluator must not proceed by silently substituting another model, voice,
dependency, or text.

### Speech configuration

Identifies one method and its exact evaluation conditions.

| Field | Type | Validation |
| --- | --- | --- |
| `configuration_id` | string | Unique within the run. |
| `method` | enum | `existing_macos` or `vibevoice`. |
| `model_variant` | string, optional | Required for VibeVoice; record the exact variant, including `VibeVoice-TTS-1.5B` or `VibeVoice-Realtime-0.5B` when assessed. |
| `voice` | string | Exact voice identity; do not substitute without a distinct configuration. |
| `language` | string | BCP 47 language tag, e.g. `en` or `de`; record experimental/unsupported status rather than assuming feasibility. |
| `machine_id` | ID | References the candidate machine used. |
| `adapter_identity` | string, optional | Exact already-installed, authorized adapter/runtime identity for VibeVoice. |
| `terms_authorization_ids` | list of IDs | References permitted records for all applicable model, implementation, dependency, and voice materials. |
| `availability` | enum | `available`, `unavailable`, `unauthorized`, or `untested`. |
| `limitation_reason` | string, optional | Required when unavailable, unauthorized, or untested; a non-available configuration cannot claim generated results. |

The baseline configuration represents the existing authenticated local
`POST /v1/audio/speech` contract. If it is unavailable, record the blocker;
do not call macOS speech directly or change/register the production service as
a substitute.

### Sample text

One operator-supplied source text used consistently across paired configurations.

| Field | Type | Validation |
| --- | --- | --- |
| `sample_id` | string | Unique within the manifest. |
| `language` | string | BCP 47 tag; must match the intended configuration language. |
| `text` | string | Non-empty and valid for the selected method; keep in private local storage. |
| `attribution` | string | Identifies source/author and any required attribution. |
| `terms_authorization_id` | ID | References a permitted sample-text terms record. |
| `permitted` | boolean | Must be `true` before use; false or unresolved permission blocks generation. |

For each feasible language comparison, the manifest supplies exactly five
permitted texts. Each baseline and candidate configuration in that comparison
uses the same five sample IDs. Empty, invalid, unsupported, or unauthorized
texts are rejected or blocked with a reason, never replaced silently.

### Sample result

The result of attempting one configuration on one sample. It preserves
incomplete outcomes as first-class records.

| Field | Type | Validation |
| --- | --- | --- |
| `sample_result_id` | string | Unique within the run. |
| `run_id` | ID | References the evaluation run. |
| `configuration_id` | ID | References the exact speech configuration. |
| `sample_id` | ID | References the shared source text. |
| `status` | enum | `pending`, `completed`, `failed`, `cancelled`, `blocked`, or `incomplete`. |
| `audio_path` | local path, optional | Private local generated audio with owner-only access; required only for a completed generation. |
| `generation_time_ms` | integer, optional | Non-negative elapsed time; missing value requires a measurement reason. |
| `rating` | integer, optional | Product-owner rating from 1 through 10; allowed only for completed, listened-to audio. |
| `observation` | string, optional | Qualitative listening observation; retain locally. |
| `reason` | string, optional | Required for failed, cancelled, blocked, or incomplete status and for unavailable measurements. |

Partial audio after a failed, cancelled, or over-limit generation is marked
unscorable and cannot receive a successful sample rating. Do not encode missing
ratings or measurements as zero.

### Configuration measurements

Run-level measurements attached to an evaluated configuration and its target
machine.

| Field | Type | Validation |
| --- | --- | --- |
| `configuration_id` | ID | References the measured configuration. |
| `installed_footprint_bytes` | integer, optional | Non-negative; report reason if unavailable. |
| `peak_memory_bytes` | integer, optional | Non-negative; report reason if unavailable/unmeasurable. |
| `measurement_method` | string, optional | Describe how the value was observed. |
| `missing_measurement_reasons` | map | Each unavailable required measurement has a specific reason. |

### Comparison issue

Explains any absent or unsuccessful comparison without implying success.

| Field | Type | Validation |
| --- | --- | --- |
| `issue_id` | string | Unique within the run. |
| `configuration_id` | ID, optional | References the affected configuration when known. |
| `sample_id` | ID, optional | References the affected sample when applicable. |
| `category` | enum | `unavailable`, `unauthorized`, `capacity`, `permission`, `unsupported_language`, `failed`, `cancelled`, or `resource_limit`. |
| `reason` | string | Required, specific explanation of the missing/failed/unsafe comparison. |
| `recorded_at` | timestamp | ISO 8601 timestamp with timezone. |

### Product-owner decision

The recorded outcome of reviewing the evidence; it is not an automatic score
threshold or a run execution status.

| Field | Type | Validation |
| --- | --- | --- |
| `decision_id` | string | Unique within the report. |
| `outcome` | enum | `retain`, `partially_retain`, `remove`, or `seek_alternative`. |
| `rationale` | string | Required; explain the decision in light of quality, feasibility, and limitations. |
| `decided_at` | timestamp | ISO 8601 timestamp with timezone. |
| `decided_by` | string | Product-owner identifier/display name. |

## Relationships and report calculations

- An evaluation run has one or more machine inspections, configurations,
  sample texts, sample results, and comparison issues.
- A configuration references exactly one machine and a set of applicable
  terms/authorization records. A VibeVoice configuration identifies one exact
  model variant and adapter; a baseline configuration identifies the existing
  speech method.
- A sample result links one run, one configuration, and one sample text. The
  same sample ID is reused across each paired baseline/candidate comparison.
- Each configuration has zero or one measurement record; missing values remain
  absent and carry explicit reasons.
- A completed sample result may have one rating. The report average is the
  arithmetic mean of present ratings, grouped by language and configuration;
  show the rating count and do not compute an average for an empty group.
- The report includes per-sample ratings, qualitative observations, inspection
  evidence, configuration measurements, and every comparison issue. A missing,
  failed, blocked, or unauthorized result is never represented as a successful
  comparison.
- One optional product-owner decision references the reviewed run. Recording it
  does not alter model permissions or authorize deployment/publication.

## Run state transitions

| From | To | Condition |
| --- | --- | --- |
| `preflight` | `ready` | Manifest is valid; sample and material terms are documented and permitted; required capacity and action approvals are confirmed; authorized adapters are already available. |
| `preflight` | `blocked` | A required permission is unclear/denied, a required adapter is unavailable/unauthorized, or capacity/prerequisites prevent a safe run. Record the reason; do not perform the affected action. |
| `ready` | `generating` | Operator explicitly starts the approved evaluation. |
| `generating` | `reviewing` | Generation attempts have stopped normally; completed samples are ready for private listening and rating, while non-completed samples retain their status/reason. |
| `generating` | `failed` / `cancelled` | An affected run fails, is cancelled, or exceeds an agreed resource bound; stop it and mark partial output unscorable. |
| `reviewing` | `complete` | Evidence and any available ratings/observations are saved; missing values remain explicit. The product-owner decision may be recorded with the report. |

No transition downloads or installs a model, modifies/registers/restarts the
existing service, publishes data, or deploys the prototype implicitly. Those
actions require their own explicit approval and destination as required by the
specification.
