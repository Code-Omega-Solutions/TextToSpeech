# Feature Specification: Language detection fallback

**Feature Branch**: `pgfeller-language-detection-fallback`

**Created**: 2026-11-09

**Status**: Draft

**Input**: Use en-US as fallback when no language is specified and automatic detection cannot identify a supported language.

## User Scenarios & Testing

### User Story 1 - Synthesize when detection is inconclusive (Priority: P1)

A user submits text without a language and receives English speech when automatic detection does not identify a supported language.

**Why this priority**: An inconclusive detection should not prevent a valid speech request.

**Independent Test**: Submit a valid request with no language while detection identifies an unsupported language and verify that synthesis uses en-US.

**Acceptance Scenarios**:

1. **Given** a valid request without an explicit language, **When** detection identifies an unsupported language, **Then** synthesis uses en-US.
2. **Given** a valid request without an explicit language, **When** detection identifies German or English, **Then** synthesis uses the corresponding supported locale.

### User Story 2 - Preserve chosen languages (Priority: P1)

A user who chooses a supported language continues to receive speech in that language, regardless of the text.

**Why this priority**: Explicit choices must take precedence over automatic behavior.

**Independent Test**: Submit text with an explicit supported language and confirm that the selected language is used without detection.

**Acceptance Scenarios**:

1. **Given** a supported explicit language, **When** a valid request is submitted, **Then** that language is used without detection.
2. **Given** an unsupported explicit language, **When** a request is submitted, **Then** it remains invalid.

### Edge Cases

- Short input continues to use the configured short-input default without detection.
- Unexpected detector failures remain errors rather than being silently disguised as successful detection.
- Existing input validation, authentication, and synthesis errors remain unchanged.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST use en-US when no language is specified and detection returns an unsupported language.
- **FR-002**: The system MUST preserve German and English automatic detection results.
- **FR-003**: The system MUST honor supported explicit language choices without running detection.
- **FR-004**: The system MUST continue rejecting unsupported explicit language choices.
- **FR-005**: The system MUST preserve the configured default for input too short for detection.
- **FR-006**: The system MUST surface unexpected detector failures instead of treating them as inconclusive results.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested unsupported detection result without an explicit language selects en-US.
- **SC-002**: Every tested supported explicit or detected language retains its existing selection.
- **SC-003**: Every tested unsupported explicit language remains rejected.

## Assumptions

- A detector result outside the supported languages counts as inconclusive, not as a request to synthesize that language.
- The fallback applies to inconclusive detection, not unexpected runtime errors or short-input configuration.
- Deployment and native macOS qualification require separate authorization.
