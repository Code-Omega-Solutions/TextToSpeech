# Feature Specification: Fish Speech MLX 4-bit candidate

**Feature Branch**: `pgfeller-mlx-fish-4bit`

**Created**: 2026-11-18

**Status**: Draft

**Input**: Implement an opt-in Apple Silicon Fish Speech 1.5 MLX 4-bit candidate, preserving approved voices, existing APIs, preload, and native fallback without deployment.

## User Scenarios & Testing

### User Story 1 - Prepare an approved candidate (Priority: P1)

An operator derives a quantized semantic model from the approved Fish Speech 1.5 checkpoint while retaining the approved higher-precision codec and voice references.

**Why this priority**: A candidate must preserve the identity, rights, and compatibility of the existing model before it can be evaluated.

**Independent Test**: Convert an approved checkpoint in isolation, verify the result and its provenance, and reject altered or incomplete artifacts before launch.

**Acceptance Scenarios**:

1. **Given** approved Fish 1.5 source and checkpoint, **When** an operator prepares a candidate, **Then** the candidate uses packed 4-bit semantic matrices and retains the existing codec and tokenizer.
2. **Given** missing approval, mismatched source, altered derived weights, or incompatible model configuration, **When** preparation or startup is attempted, **Then** it fails safely without changing approved trees.

### User Story 2 - Opt in without disrupting native speech (Priority: P1)

An operator can explicitly select the candidate as the owned Fish worker without changing request formats, voice selection, authentication, or the native baseline.

**Why this priority**: The candidate must not silently replace the existing service or weaken resource and privacy protections.

**Independent Test**: Exercise candidate dispatch and worker failures with existing API and supervisor tests.

**Acceptance Scenarios**:

1. **Given** explicit approval and candidate selection, **When** a valid Fish request is made, **Then** the existing voice and response contracts remain unchanged.
2. **Given** a busy, failing, cancelled, or resource-denied candidate, **When** a request is processed, **Then** existing ownership, deadlines, cancellation, fallback, cooldown, and safe diagnostics apply.
3. **Given** preload is enabled, **When** the backend starts, **Then** the candidate follows the existing nonblocking preload and retention policy.

### User Story 3 - Qualify the candidate (Priority: P2)

An operator can distinguish functional evidence from Apple Silicon performance, bilingual quality, rights, and deployment qualification.

**Why this priority**: Quantization and mocked tests do not establish acceptable quality, speed, or permission to deploy.

**Independent Test**: Review conversion, native inference and measurement evidence alongside explicit unresolved gates.

**Acceptance Scenarios**:

1. **Given** a permitted isolated test, **When** inference is measured, **Then** timings synchronize lazy execution and report the tested workload and hardware accurately.
2. **Given** unverified performance, voice quality, rights, or production approval, **When** the candidate is documented, **Then** those limitations remain explicit and deployment is not implied.

### Edge Cases

- An incompatible tokenizer, shape, codebook count, or cache configuration must be rejected rather than silently remapped.
- Failure or cancellation must not adopt, terminate, or otherwise affect an unrelated process.
- The candidate must not download models, expose reference content, or modify approved source or checkpoint trees.
- Native-only Windows and Linux usage must not require MLX.

## Requirements

### Functional Requirements

- **FR-001**: The candidate MUST derive its semantic model exclusively from the approved Fish Speech 1.5 checkpoint and preserve the existing tokenizer, codebook behavior, and higher-precision Firefly codec.
- **FR-002**: Conversion MUST produce and load actual MLX packed 4-bit semantic matrices with explicit group size and documented excluded layers.
- **FR-003**: The candidate MUST require a separate exact approval binding for source, runtime, original and derived artifacts, codec, terms, and approved references.
- **FR-004**: Candidate storage and dependencies MUST be isolated from approved source and checkpoint trees and MUST NOT auto-download models.
- **FR-005**: Candidate selection MUST be explicit and MUST preserve existing API identifiers, request/response shapes, voice behavior, and safe backend/fallback diagnostics.
- **FR-006**: Managed ownership, deadlines, cancellation, memory controls, cooldown, preload, and native fallback MUST remain effective for the candidate.
- **FR-007**: MLX dependencies MUST remain optional and platform-appropriate.
- **FR-008**: Validation MUST cover conversion, loading, dispatch, transport, lifecycle, and failure behavior; native inference and bilingual quality MUST be reported separately from mocked evidence.
- **FR-009**: No production service, configuration, approved artifact, or deployment may be changed by this work.
- **FR-010**: Benchmarking beyond bounded approved-reference and generic-text validation requires separate permission.

### Key Entities

- **Approved source artifacts**: The pinned Fish source, semantic checkpoint, codec, tokenizer, and their terms and hashes.
- **Derived candidate**: Isolated packed semantic weights and runtime, with exact provenance and approval binding.
- **Qualified references**: The four existing approved German and English voice reference pairs and their consent and dataset terms.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An authorized operator can prepare and start one candidate from the existing checkpoint without downloading a replacement model or changing approved trees.
- **SC-002**: Existing request, fallback, and preload behavior remains covered by focused regression tests, including candidate failure and rejection paths.
- **SC-003**: All four approved voice profiles remain selectable with unchanged public identifiers; English and German quality is qualified separately on actual hardware.
- **SC-004**: Reports distinguish synchronized native timing, quality, and memory evidence from unverified claims; no performance improvement is presumed.

## Assumptions

- The user approved a standalone faithful Fish 1.5 port after existing MLX projects were found to target newer models.
- The candidate is private and experimental; conversion is not deployment approval or a waiver of model and voice rights.
- Synthesis and benchmarking require the existing privacy, memory, approval, and consent boundaries.
