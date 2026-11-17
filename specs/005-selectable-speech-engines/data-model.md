# Data Model: Selectable Speech Engines Prototype

This model describes planned behavior. It does not record an implementation,
artifact approval, local qualification, or deployment approval.

## Speech Engine

A speech engine is a provider registered by the backend and invoked through the
shared synthesis contract.

| Field | Meaning and validation |
| --- | --- |
| `identifier` | Stable public engine identifier used by the existing `model` request field. It must identify a registered engine. |
| `enabled` | Whether the operator has configured the engine for selection. Unconfigured or disabled engines cannot synthesize. |
| `availability` | One of `unconfigured`, `checking`, `available`, or `unavailable`. Readiness is evaluated independently per engine. |
| `supported_languages` | The engine's supported English and/or German language identifiers. A request language must be supported by the selected engine. |
| `public_voice_identifiers` | Voice identifiers safe to expose through authenticated discovery. A requested voice must be advertised for the selected language and engine. |

`macos-say` is the baseline engine where its host prerequisites exist. The
optional `fish-speech` adapter targets a separately managed local inference
service; its endpoint or credential must be configured for use and private
runtime details are not part of discovery. The legacy `vibevoice` identifier
is retained only to produce the established safe unavailable response. It is
not registered as a runnable engine, loaded, or redirected to the default.

## Engine Selection and Speech Operation

The existing speech request remains the public input. Its `model`, `language`,
`voice`, `speed`, and requested audio format retain their current meanings and
validation. Omitting `model` resolves to the single configured default engine;
an explicit `model` resolves only to that enabled engine. Unknown, disabled,
unavailable, unsupported-language, or unsupported-voice selections fail with
the existing safe error behavior. A failure never changes the selected engine
implicitly.

The shared engine operation preserves the request's language, voice, speed,
and format, plus cancellation, timeout, and bounded error behavior. The
provider result contains generated audio and the actual engine identity. Any
fallback is allowed only by an explicitly configured fallback policy, and the
existing response metadata identifies the engine that generated the audio and
whether fallback occurred. Existing routes, authentication, request/response
shape, headers, limits, and MP3/WAV behavior remain compatible.

Authenticated, read-only discovery reports configured engine identifiers,
availability, supported languages, and public voice identifiers. It excludes
filesystem paths, credentials, and private host details. The speech interface
may offer only engine/language/voice combinations returned by discovery and
continues to submit them through the existing `model` and `voice` fields.

### Engine availability transitions

```text
unconfigured -> checking
checking -> available       when readiness checks pass
checking -> unavailable    when a required dependency or approval gate is unmet
available -> unavailable   when the engine becomes unreachable or fails validation
unavailable -> checking    after configuration is corrected and the service restarts
```

An absent optional engine does not make another engine unavailable or block
service readiness. A Fish engine cannot become available until its exact
candidate artifact set has passed the review gate below and its configured
runtime is ready.

## Fish Candidate Artifact Set

An artifact set binds the reviewed candidate together so approval cannot be
transferred to different files or terms.

| Field | Meaning and validation |
| --- | --- |
| `variant` | The exact Fish Speech variant under comparison, such as Drama 3 or S2-Pro. Selection is deferred until comparison and review are complete. |
| `checkpoint` | Exact model checkpoint identity. Weights are not downloaded, installed, or enabled before review acceptance. |
| `codec` | Exact codec artifact identity, reviewed with the checkpoint. |
| `runtime_packages` | Exact runtime package set required by the candidate, reviewed before installation. |
| `voice_assets` | Any voice assets or references and their provenance. No voice asset is enabled without accepted provenance and applicable terms. |
| `source_revision` | Source revision associated with the candidate and evidence. |
| `applicable_terms` | Terms applicable to the exact checkpoint, codec, packages, and voices for the intended private use. Private use is not itself evidence of permission. |
| `review_status` | `pending`, `accepted`, or `rejected`. Acceptance applies only to this exact set and intended use. |

Changing any artifact, provenance, applicable terms, or intended use requires
review of the changed set before it is enabled. A pending or rejected set
cannot be downloaded, installed, or enabled by the prototype.

## Fish Variant Evaluation Record

One record compares each considered Fish variant. It connects to an exact
artifact set but does not itself approve or select that set.

| Field | Meaning and validation |
| --- | --- |
| `variant` | Variant being compared; must correspond to the artifact set and evidence entries. |
| `upstream_evidence` | Published model size, platform/resource requirements, and English/German evidence, each attributed to its upstream source and revision. These remain vendor claims, not local measurements. |
| `local_results` | Locally measured quality, performance, resource use, or readiness. Each result is labeled as local. It remains unavailable until the relevant test is explicitly approved and run. |
| `terms_and_provenance_status` | Review status for exact artifacts and voice provenance. It must not be inferred from a general license or a different artifact revision. |
| `selection_status` | No variant is selected or enabled while comparison or required rights review is incomplete. |

Upstream claims and local results are separate evidence classes and must not be
merged, substituted for one another, or presented as equivalent. Local target
observations remain local evidence; private host identifiers and configuration
do not belong in the record.

## Deployment Approval

Deployment approval authorizes a separate prototype service, not modification
of the existing healthy service.

| Field | Meaning and validation |
| --- | --- |
| `target_identity_verified` | Whether the target identity has been verified, including host-key verification. False blocks remote changes. |
| `key_authentication_verified` | Whether authorized key authentication has been verified without introducing an unapproved key or host-key change. False blocks remote changes. |
| `prerequisites_checked` | Read-only checks of target OS, runtime, engine assets, service manager, and approved network exposure. Missing or unsupported prerequisites keep deployment blocked until explicitly approved remediation. |
| `candidate_artifacts_approved` | Whether every Fish artifact intended for deployment has accepted exact terms and provenance review. False prevents Fish weights, codecs, runtime packages, and voices from being installed or enabled. |
| `service_boundary_approved` | Whether the named prototype service and its separately approved port/network boundary are authorized. The existing service remains untouched. |
| `deployment_status` | `blocked`, `approved`, or `deployed`. `deployed` is reachable only after all applicable gates pass and the prototype is added in parallel. |

Deployment transitions from `blocked` to `approved` only after target identity,
access, prerequisites, artifact review, and service/network boundary are
approved. It transitions to `deployed` only after the separate service is
installed and its approved health, readiness, and authenticated English/German
speech checks pass. Any unmet gate keeps it blocked; no existing service,
firewall, key, host-key, or runtime configuration is changed as a workaround.
