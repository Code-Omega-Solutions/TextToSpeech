# Feature Specification: UI Endpoint Configuration

**Created**: 2026-11-17
**Status**: Draft, proposed behavior
**Input**: Add a configuration tab for the speech-service endpoint, hide unsupported engine and voice selectors, and document file-backed configuration persistence across container image updates.

## User Scenarios & Testing

### User Story 1 - Choose the intended speech service (Priority: P1)

As an evaluator, I can use the configured speech-service endpoint in the same
interface. An authorized operator changes that endpoint through the protected
server-side configuration workflow, without putting a backend credential in a
browser.

**Why this priority**: Evaluating the wrong service defeats the purpose of the prototype interface.

**Independent Test**: Switch between two controlled services with distinguishable responses and confirm subsequent speech and connection checks use only the saved destination.

**Acceptance Scenarios**:

1. **Given** a working configured service, **When** I open the configuration tab, **Then** I see that routing is operator-managed and no credential input is offered.
2. **Given** a permitted, reachable replacement service, **When** I save its endpoint, **Then** the interface confirms the save, refreshes connection and speech-option information, and sends subsequent speech requests to that service.
3. **Given** an invalid or unauthorized destination or a failed configuration write, **When** I try to save, **Then** an actionable error appears and the previous saved endpoint remains active.

### User Story 2 - Use only supported speech options (Priority: P1)

As a speech user, I see engine and voice selectors only when the selected service supports those choices. A service without discovery remains usable through its established speech defaults.

**Why this priority**: Empty dropdowns must not prevent ordinary speech generation against an otherwise compatible service.

**Independent Test**: Exercise a service with discovery, a legacy service without discovery, and a service with a failing discovery response.

**Acceptance Scenarios**:

1. **Given** a service advertising usable engines and voices, **When** its options load, **Then** the interface shows supported choices and generation uses the selected engine and applicable voice.
2. **Given** a speech-compatible service that explicitly does not support discovery, **When** its capabilities are checked, **Then** unsupported selectors are absent and speech generation works with compatible defaults.
3. **Given** an authentication failure, timeout, malformed catalog, or supported but empty catalog, **When** discovery finishes, **Then** a distinct actionable status appears, no stale choices remain, and the interface does not silently classify the service as legacy.

### User Story 3 - Retain configuration across image replacement (Priority: P2)

As a container operator, I can locate and persist the saved configuration so an image update does not reset the selected endpoint.

**Why this priority**: A working endpoint choice should survive routine maintenance without being entered again.

**Independent Test**: Follow the documented storage instructions, save a nondefault endpoint, replace the container using the same persisted storage, and verify the saved endpoint remains active from a fresh browser session.

**Acceptance Scenarios**:

1. **Given** an operator preparing persistent storage, **When** they read the deployment documentation, **Then** they find the exact configuration-file location, writable mount target, required permissions, and a synthetic Compose example.
2. **Given** saved configuration on persisted storage, **When** the container is recreated with a replacement image, **Then** the interface loads the same endpoint without browser-local settings or image edits.
3. **Given** missing, corrupt, or unwritable configuration storage, **When** the service starts or an operator saves a change, **Then** it reports the condition explicitly and does not claim an unsaved endpoint is durable.

## Edge Cases

- An endpoint is blank, malformed, contains embedded credentials, or targets a destination outside the operator's permitted scope.
- A saved endpoint becomes unreachable after saving. Report its failure without silently switching back to a different service.
- A discovery response from the previous endpoint arrives after an endpoint switch. It must not restore old options or connection state.
- An engine has no voices for the selected language. Do not invent choices; retain automatic-language and service-default-voice behavior where supported.
- A speech request is in flight during a configuration change. It must not be replayed automatically against the new service.
- Two browser sessions edit shared settings. Each save must produce a complete valid configuration, never a partial file.
- Saved configuration conflicts with startup settings, or persisted storage is absent after container recreation. Document precedence and distinguish a documented initial default from recovery after corruption.

## Requirements

### Functional Requirements

- **FR-001**: The interface MUST provide a labeled, keyboard-operable configuration tab explaining that endpoint routing is operator-managed.
- **FR-002**: The browser MUST NOT provide a backend-token input or send a backend credential; authorized endpoint changes use the protected server-side workflow.
- **FR-003**: The system MUST reject invalid endpoint values with a visible reason before changing active configuration.
- **FR-004**: A successful save MUST make subsequent connection, discovery, and speech requests use the saved endpoint without rebuilding the frontend image.
- **FR-005**: An endpoint change MUST discard previous capability selections and ignore late discovery responses belonging to the previous endpoint.
- **FR-006**: The system MUST display engine and voice selectors only for choices supported by the active service and applicable language.
- **FR-007**: A service explicitly lacking discovery MUST remain usable for speech with documented compatible defaults and without unsupported selectors.
- **FR-008**: The interface MUST distinguish unsupported discovery from authentication, connectivity, malformed-response, and empty-catalog failures.
- **FR-009**: Configuration-save failures MUST preserve the last successfully saved endpoint and report that the attempted change was not saved.
- **FR-010**: The system MUST store the shared endpoint configuration in a container-side file that can be persisted independently of the image.
- **FR-011**: Saved configuration MUST survive browser reload, service restart, and container replacement when the documented persistent storage is retained.
- **FR-012**: Deployment documentation MUST state the exact file path, mount target, permissions, initialization behavior, and precedence between saved and startup configuration, with a working synthetic Compose example.
- **FR-013**: The system MUST keep backend credentials server-side and prevent endpoint edits from forwarding them to an operator-unauthorized destination.
- **FR-014**: Configuration changes MUST be restricted to the authorized operator access boundary rather than granting arbitrary public clients control of shared routing.
- **FR-015**: The feature MUST preserve existing text and audio privacy, request limits, language behavior, and playback/download behavior.

### Key Entities

- **Endpoint configuration**: The shared active service destination, its saved state, and any pending unsaved edit. It contains no speech text, audio, or browser-visible credential.
- **Service capabilities**: Endpoint-specific discovery support, available engines, and applicable voices. Unknown, unsupported, failed, and supported-but-empty are distinct states.
- **Persistent configuration file**: The durable representation of endpoint configuration, owned by the serving instance and retained through an operator-managed mount.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An evaluator can use the configured destination without browser credential setup; an authorized operator can change it server-side without rebuilding an image.
- **SC-002**: All controlled-service switching cases route subsequent connection checks, discovery, and generation exclusively to the saved destination.
- **SC-003**: Both a discovery-enabled service and a compatible legacy service produce playable, downloadable speech; unsupported selectors are absent in the legacy case.
- **SC-004**: Every tested invalid endpoint, unauthorized destination, failed save, and discovery failure produces an explicit status without showing stale selectable choices.
- **SC-005**: Following only the persistence documentation preserves a saved nondefault endpoint through one restart and one container replacement, verified in a fresh browser session.
- **SC-006**: All configuration actions are operable by keyboard, with labeled controls and announced save/error status at desktop and mobile layouts.

## Assumptions

- Configuration is shared by the frontend serving instance, not a per-browser preference. Changing it affects subsequent requests from all users of that instance.
- Existing startup configuration supplies the initial endpoint when no saved file exists. Valid saved configuration takes precedence thereafter; corruption is an error, not permission to silently use another endpoint.
- Endpoint input remains an HTTP(S) origin without embedded credentials, path, query, or fragment, consistent with current serving constraints.
- Explicit unsupported-discovery responses permit legacy mode. Authentication failures, timeouts, invalid responses, and an empty supported catalog do not establish lack of support.
- Existing speech-compatible services accept their established default engine/model behavior without voice discovery. Planning must verify that contract against repository evidence rather than inventing a model identifier.
- Endpoint switching requires an operator-approved destination and compatible server-side authentication. This feature does not introduce a general-purpose proxy or a new identity-management system.
- The browser does not display the configured destination or accept operator credentials. Authorized endpoint changes use a protected administration workflow outside browser assets.
- Existing living specifications currently block generation on failed or empty discovery. Legacy compatibility is a proposed targeted change, not already implemented behavior.
- The reported deployed routing and suspected production port are unverified. No live installation inspection, restart, or deployment is authorized by this specification.
- Backend engine installation, model enablement, voice cloning, production migration, and changes to existing model/voice release gates are outside scope.
