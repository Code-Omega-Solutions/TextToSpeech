# Feature Specification: Private VibeVoice Evaluation

**Status**: Completed
**Created**: 2026-11-15
**Source**: Idea assessment `tts-ms-vibe-code-backend`

## User Scenarios & Testing

### User Story 1 - Compare speech quality (Priority: P1)

As the product owner, I want to listen to the existing speech method and a feasible VibeVoice variant using the same English and German texts, so I can decide whether the new method improves the private system's speech.

**Why this priority**: The comparison answers the core question without requiring deployment.

**Independent Test**: Run an approved private evaluation on a suitable machine, listen to paired samples, and record ratings and observations for each available configuration.

**Acceptance Scenarios**:

1. **Given** a permitted and feasible variant and five permitted sample texts per language, **When** the evaluation is run, **Then** the product owner can listen to the variant and the existing method reading the same texts and record a 1–10 rating for each sample.
2. **Given** ratings for a configuration, **When** the results are reviewed, **Then** the report shows the individual ratings, the average by language and configuration, and the product owner's observations.
3. **Given** a variant or language cannot be safely or appropriately evaluated, **When** the results are reviewed, **Then** the report identifies the missing comparison and its reason rather than presenting it as successful.

### User Story 2 - Assess real-system feasibility (Priority: P1)

As the product owner, I want to know the resource costs and conditions of an evaluation on the candidate machines, so I can judge whether the improvement is practical.

**Why this priority**: Voice quality alone cannot establish that the approach is suitable for the available hardware.

**Independent Test**: Inspect the approved target's resources, run a permitted evaluation, and review its resource and timing results alongside any unmeasured values.

**Acceptance Scenarios**:

1. **Given** an approved target and a chosen storage volume, **When** its suitability is assessed, **Then** the report records available space, memory, platform details, relevant requirements and the time of inspection.
2. **Given** a completed evaluation run, **When** its results are reviewed, **Then** the report records installed footprint, peak memory where measurable, and generation time, or identifies each unavailable measurement and why.
3. **Given** inadequate capacity, unclear permission, or an unavailable authorized implementation, **When** the evaluation would require that prerequisite, **Then** the affected run is not performed and the report records the blocker.

### User Story 3 - Decide whether to retain the prototype (Priority: P2)

As the product owner, I want an isolated and removable prototype and an evidence report, so I can keep it, use only parts of it, or remove it after reviewing the results.

**Why this priority**: The evaluation should not commit the existing service to a new method.

**Independent Test**: Disable or remove the prototype using its documented boundary and verify that the existing speech method remains available.

**Acceptance Scenarios**:

1. **Given** the prototype is disabled or removed, **When** the existing speech method is used, **Then** it continues to operate under its existing contract.
2. **Given** the comparison and feasibility report, **When** the product owner reviews it, **Then** they can record a decision to retain, partially retain, remove, or seek an alternative without an automatic numeric pass threshold.

## Edge Cases

- Empty, invalid, or unsupported text must produce a clear failure rather than a misleading sample or score.
- A model, voice, or language may be unavailable, experimental, or unsuitable; record the limitation and do not substitute a different configuration without identifying it.
- If generation fails, is cancelled, or exceeds agreed resource bounds, stop the affected run and label incomplete results; do not score partial audio as a successful sample.
- If capacity or permissions change after inspection, reassess before performing a write or run on the target.
- Missing ratings or unmeasurable resource values remain explicitly incomplete and are not treated as zero or as a passing result.

## Requirements

### Functional Requirements

- **FR-001**: The evaluation MUST offer an isolated, optional prototype for comparing VibeVoice speech with the existing macOS speech method.
- **FR-002**: The prototype MUST be removable or disableable without changing the existing method's behavior or contract.
- **FR-003**: The evaluation MUST use the same five permitted texts per language for each feasible configuration and the baseline.
- **FR-004**: The evaluation MUST support private listening and individual 1–10 product-owner ratings for English and German samples where feasible.
- **FR-005**: The report MUST show individual ratings, averages by language and configuration, and qualitative observations.
- **FR-006**: The evaluation MUST identify the exact model variant, voice, language, machine, and configuration for every result.
- **FR-007**: The evaluation MUST investigate both identified VibeVoice TTS variants and report any unavailable or unauthorized implementation without claiming a comparison was performed.
- **FR-008**: The evaluation MUST report storage, memory, platform details, and applicable requirements for each candidate machine, including the inspection time and the intended storage volume when known.
- **FR-009**: The evaluation MUST record installed footprint, peak memory where measurable, and generation time for each evaluated configuration, identifying unavailable measurements and their reasons.
- **FR-010**: Before a target-machine download, installation, or service change, the operator MUST obtain explicit approval for that action and destination.
- **FR-011**: Before using a model, dependency, voice, or sample text, the evaluation MUST document the applicable terms and determine whether the intended private research use is permitted; unresolved permission MUST block the affected use.
- **FR-012**: The evaluation MUST record missing, failed, unsafe, or unavailable comparisons and the reason for each.
- **FR-013**: The evaluation MUST keep sample texts, generated audio, and results private unless a separate publication decision authorizes disclosure.
- **FR-014**: The evaluation MUST provide the product owner with a recordable decision to retain, partially retain, remove, or seek an alternative.
- **FR-015**: The evaluation MUST stop an affected run on failure, cancellation, or an agreed resource limit and report the incomplete result.

## Key Entities

- **Evaluation configuration**: A speech method, model variant where applicable, voice, language, and target machine.
- **Sample**: A permitted source text, its language and attribution, and corresponding generated audio for each evaluated configuration.
- **Evaluation result**: A configuration's ratings, observations, resource measurements, timings, and any missing data or blockers.
- **Product-owner decision**: The outcome of reviewing the evidence and its rationale.

## Success Criteria

### Measurable Outcomes

- **SC-001**: For every feasible configuration, five English and five German samples are compared with the same baseline texts, or each incomplete comparison is reported with a reason.
- **SC-002**: Every completed sample has an individual 1–10 rating, and each configuration-language pair with ratings has an average and observations recorded.
- **SC-003**: Both candidate machines and both identified model variants appear in the report, with measured results or explicit reasons they could not be evaluated.
- **SC-004**: Every evaluated configuration has installed footprint, peak memory, and generation time recorded, or an explicit reason for each missing measurement.
- **SC-005**: Disabling or removing the prototype leaves the existing speech method usable, and the product owner can record one of the stated decisions.
- **SC-006**: No model, dependency, voice, or sample text is used before its relevant terms have been documented and the intended use determined to be permitted.

## Assumptions

- This is a private research evaluation, not authorization to deploy, modify a running service, or publish generated audio or results.
- The primary candidate is evaluated first; the secondary candidate is assessed and tested only when authorized and feasible.
- German support may be experimental, and the older variant may lack an authorized implementation. Such limitations are findings, not requirements to recover unavailable code.
- The product owner decides whether the result is worthwhile; no numeric rating threshold determines that decision.
- Two-person conversation, production integration, automatic fallback, and comparisons with additional models are outside this evaluation.
- Wikipedia is a proposed sample source. Individual text rights and attribution obligations remain to be checked before use.

## Evaluation Outcome and Integration Decision

The product owner completed the English and German listening reviews and selected
VibeVoice Realtime 0.5B for backend integration.

| Language and voice | Existing voice average | VibeVoice voice average |
| --- | ---: | ---: |
| English, male | Samantha: 5.60 | Carter: 7.40 |
| German, female | Anna: 5.60 | Spk1: 7.60 |
| German, male | Eddy: 1.00 | Spk0: 5.40 |

Use Carter as the English default and Spk1 as the German default. Keep Spk0
available as an optional German voice. These are the reviewed presets with the
highest ratings for their language and gender grouping.

A separate warm-process benchmark loaded one shared model and cached the English
and both German voice prompts. It measured five samples per voice after one
warm-up per voice. Mean generation times were 3.286 seconds for English, 3.832
seconds for German female, and 3.095 seconds for German male. The corresponding
real-time factors were 0.884, 0.913, and 0.942. Compared with the earlier
per-sample cold-start runs, this was approximately 2.3–2.6 times faster, but
still slower than macOS `say`.

The one-process benchmark measured 7.28 GiB peak process RSS, 6.29 GiB peak
MPS driver allocation, and 5.09 GiB current MPS allocation after generation.
Available system memory fell from approximately 19.53 GiB to 12.71 GiB during
the run. English and German use the same model weights, so a single shared
instance is sufficient. The benchmark process exited after measurement.

The model loader reported 276 newly initialized acoustic-tokenizer encoder
tensors. The inspected streaming inference path decodes generated speech and
does not use that encoder. The measured footprint includes it, so production
integration should omit unused model components and verify the resulting
memory use. German support remains experimental, and these short listening and
performance samples do not qualify other hardware or workloads.

The integration should allow an operator to select the speech backend, keep
VibeVoice lower priority than other inference workloads, release its resident
memory when needed, and fall back to `say` when VibeVoice cannot safely run.
This decision does not change the evaluation tool into a production component.
