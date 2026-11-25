# Feature Specification: Replace Fish Speech with Ollama Phonon

**Feature Branch**: `007-replace-phonon`

**Created**: 2026-11-24

**Status**: Completed — live qualification and convergence completed

**Input**: User-requested specification based on the selected assessment direction: remove Fish Speech completely, replace it with Ollama Phonon for English and German, retain native macOS `say`, preserve established speech behavior while removing the fixed text-character limit, split text when a model's capacity is exceeded, prefer MP3 streaming if feasible, and create a follow-up if expectations are not met after productive use.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate English and German speech with Phonon (Priority: P1)

As a speech-service user, I want to request English or German speech through the replacement engine using the controls I already rely on, so I can use a suitable alternative to Fish without changing my established workflow.

**Why this priority**: Replacing Fish is the purpose of the feature, and both languages are in the selected scope.

**Independent Test**: Submit representative authorized English and German requests using supported voices and the existing speech controls; verify that complete audio in the requested format is returned with accurate response metadata.

**Acceptance Scenarios**:

1. **Given** an approved Phonon model and voice are available for the requested language, **When** a valid request uses an existing supported speed and output format, **Then** the user receives complete speech using the selected voice and speed, in the requested format, and the response identifies the engine that produced it.
2. **Given** a request is within the existing encoded-request size bound but exceeds the selected model's per-input capacity, **When** it is submitted, **Then** all requested text is spoken in order without omission or truncation.
3. **Given** Phonon or the requested voice is unavailable, **When** a request selects it, **Then** the user receives a clear, privacy-safe failure and the service does not silently substitute another engine.
4. **Given** client-facing MP3 streaming can preserve existing response guarantees, **When** the user requests speech, **Then** MP3 audio is delivered incrementally; otherwise the user receives the established complete-response behavior.

---

### User Story 2 - Continue using native macOS speech (Priority: P1)

As a user who relies on the native macOS speech option, I want it to remain available after Fish is removed, so the replacement does not take away the currently productive option.

**Why this priority**: The selected direction explicitly retains native `say` as the available alternative.

**Independent Test**: Submit requests through the native speech option before and after the migration and compare the accepted controls, audio behavior, and response metadata.

**Acceptance Scenarios**:

1. **Given** a valid request for native macOS speech, **When** it is submitted after Fish has been removed, **Then** native speech remains selectable and returns the established response behavior.
2. **Given** the native speech option is unavailable on a system, **When** a user selects it, **Then** the service reports that state without claiming another engine produced the audio.

---

### User Story 3 - Retire Fish without surprising existing clients (Priority: P1)

As the service operator, I want Fish completely removed while existing clients receive a deliberate response to old Fish selections, so the migration does not leave an unused engine or silently change client behavior.

**Why this priority**: Complete removal is the selected scope, but legacy clients need a predictable migration path.

**Independent Test**: Check the service's advertised choices and submit requests using both current choices and the retired Fish selection.

**Acceptance Scenarios**:

1. **Given** the replacement is active, **When** a user checks available speech choices, **Then** Fish is no longer offered and Phonon and native macOS speech remain available where supported.
2. **Given** a client sends the retired `fish-speech` selection, **When** the service receives the request, **Then** it returns a safe unavailable response and does not route the request to Phonon or the configured default.

### User Story 4 - Use the replacement from the browser (Priority: P1)

As a browser user, I want to select an available speech engine and use longer text, so the interface exposes the replacement without silently discarding my input.

**Why this priority**: The browser is a primary client of the updated service.

**Independent Test**: Select the available Phonon engine for each supported language, submit supported text including more than 5,000 units, and inspect the returned audio and actual-engine disclosure.

**Acceptance Scenarios**:

1. **Given** Phonon is advertised for English or German, **When** a user selects it and an advertised voice, **Then** the browser submits those selections and displays the returned audio and actual engine.
2. **Given** text exceeds 5,000 units but the complete encoded request fits the existing size bound, **When** the user types or pastes and submits it, **Then** the full text is sent without truncation.
3. **Given** the complete encoded request exceeds the existing size bound, **When** the user submits it, **Then** the interface retains the text and explains the limit without sending the request.
4. **Given** an engine is unavailable or does not support a selected language, **When** the choices are refreshed, **Then** it is not offered for that selection; native speech remains the initial choice when available.

### Edge Cases

- Phonon is missing, not ready, or unable to serve one of the requested languages.
- A selected voice is unknown, unapproved, or incompatible with the requested language.
- A request exceeds a model's per-input capacity but remains within the existing encoded-request size bound.
- A request exceeds the former 5,000-unit text limit but remains within the existing encoded-request size bound.
- Speech generation times out, is cancelled, returns partial audio, or produces audio that cannot be converted to the requested format.
- The target system or the path to its unauthenticated speech service is not supported or cannot be verified as private.
- Model or voice terms, source, or intended-use permission have not been reviewed.
- A Phonon request fails while native macOS speech remains available.
- Audio streaming cannot meet the existing size, error, cancellation, and privacy guarantees.
- Multibyte text, escaped characters, and selected options can make an encoded browser request exceed the body limit even when its character count is small.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The replacement MUST remove Fish as a selectable engine and MUST NOT require Fish assets or services for the speech service to start or become ready.
- **FR-002**: The replacement MUST provide Phonon speech for English and German when the approved model, voice, and target environment support the requested language.
- **FR-003**: The replacement MUST retain native macOS `say` as an available speech option where the host supports it.
- **FR-004**: The replacement MUST preserve established authentication, speed control, voice selection, MP3/WAV output, response metadata, and the existing encoded-request size safeguard. It MUST NOT retain a fixed 5,000-unit text limit.
- **FR-005**: The replacement MUST handle text beyond a selected model's per-input capacity by dividing it into supported segments and returning a complete result that preserves the text's order and content, subject to existing request, time, and audio-output safeguards.
- **FR-006**: The replacement SHOULD stream MP3 audio to the user when it can preserve the established response behavior, bounded output, cancellation, timeout, and safe-error guarantees. If it cannot, it MUST retain the current complete-response behavior and MUST NOT claim that client-facing streaming is supported.
- **FR-007**: Successful responses MUST continue to identify the engine that actually generated the audio and preserve the existing response metadata required by clients.
- **FR-008**: The service MUST retain its existing user authentication. The unauthenticated Phonon service MUST remain reachable only over a verified, trusted path and MUST NOT be exposed beyond the separately approved network boundary.
- **FR-009**: Errors and logs MUST NOT disclose speech text, credentials, or private host configuration.
- **FR-010**: Exact Phonon model and voice assets MUST NOT be used until their source, terms, provenance, and compatibility with the stated private, non-commercial intended use have been reviewed.
- **FR-011**: The replacement MUST report Phonon as unavailable when its required model or service is unavailable; it MUST NOT silently route a selected Phonon request to native macOS speech.
- **FR-012**: The replacement MUST NOT require a predefined quality threshold before productive use. If the requester reports after productive use that expectations are not met, a dedicated follow-up MUST be created; this does not waive rights, platform, privacy, or operational gates.
- **FR-013**: The browser MUST retain typed and pasted text beyond 5,000 units, submit it without truncation when the entire encoded request is within the existing limit, and explain an oversized request without sending or discarding it.
- **FR-014**: The browser MUST disclose the actual producing engine and fallback status from the response, or indicate when that metadata was not reported.
- **FR-015**: The browser MUST offer available engines and compatible voices from discovery, exclude retired or unavailable choices, and preserve native speech as its initial choice when available.

### Key Entities *(include if feature involves data)*

- **Speech request**: A user's text, language, selected speech option and voice, speed, and requested audio format.
- **Speech option**: A supported way to generate speech, either Phonon or native macOS speech, with language and voice availability.
- **Generated audio**: The returned speech, its requested format, and metadata identifying the option that produced it.
- **Evaluation result**: A record of post-use feedback and any follow-up created when the requester reports unmet expectations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Existing authentication, speed, voice selection, MP3/WAV output, required response metadata, and encoded-request size safeguards remain in effect, while a text-only request longer than 5,000 UTF-16 code units and within the existing encoded-request size bound is accepted without truncation.
- **SC-002**: Phonon produces complete, valid speech for every agreed English and German evaluation sample using an approved voice and requested output format.
- **SC-003**: After replacement, Fish is absent from the service's available choices and is not required for startup or readiness; Phonon and native macOS speech remain available where their prerequisites are met.
- **SC-004**: No model or voice with unresolved terms or provenance is used, and no unauthenticated speech service is exposed outside its approved trust boundary.
- **SC-005**: No predefined quality threshold blocks productive use; if the requester reports that expectations are not met after productive use, a dedicated follow-up is created.
- **SC-006**: Browser tests submit intact text over 5,000 units, accept a request exactly at the existing encoded-size boundary, and reject one over the boundary without losing the text.
- **SC-007**: Browser tests select Phonon for both supported languages and show the actual engine returned with the audio.

## Assumptions

- The requester states that intended use is private and non-commercial. This statement does not itself clear model or voice terms.
- At specification time, the requester reported a recent Apple Silicon Mac with Ollama on the same machine and expected the unauthenticated service to be reachable locally. Target compatibility and the local service path were subsequently verified for the authorized deployment.
- Exact English and German model tags and voice identifiers will be selected only after their terms and provenance are reviewed.
- The fixed 5,000-unit text limit is removed, but the existing encoded-request size safeguard and other bounded time/output protections remain.
- When a request exceeds a model's per-input capacity, the service divides it into supported segments and preserves all text in the result.
- Client-facing MP3 streaming is preferred only if it can be provided without weakening the established response guarantees.
- Existing `fish-speech` requests receive a safe unavailable response and are not redirected.
- No quality threshold is required before productive use; a separate follow-up is created if expectations are not fulfilled.
- The specification records a product direction; it does not authorize host inspection, model download, installation, synthesis, implementation, or changes to a running service. Those actions require separate approval.
