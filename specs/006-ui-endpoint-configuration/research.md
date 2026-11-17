# Research: UI endpoint configuration

## Decision: persist one shared JSON file with atomic replacement

**Rationale:** The frontend already proxies a single configured upstream and the requirement is shared state across reload, restart, and image replacement. A container-side file mounted independently of the image provides that durability. Write a temporary file in the same directory, apply restrictive permissions, flush, and replace it atomically.

**Alternatives considered:** Browser local storage would be per-user and would not survive container replacement. Environment-only configuration cannot be changed through the authorized UI.

## Decision: retain the existing server-side credential

**Rationale:** The current proxy reads `TTS_API_KEY` or a protected file and replaces the browser Authorization header. Endpoint edits must validate against an operator allowlist and never accept or forward a browser-supplied credential.

**Alternatives considered:** Passing credentials from the browser would violate the privacy boundary. An unrestricted proxy would allow unauthorized destinations.

## Decision: use explicit capability outcomes

**Rationale:** A successful explicit unsupported-discovery response enables legacy mode. Authentication, network, invalid catalog, and supported-but-empty responses remain failures with no selectors and no legacy classification.

**Alternatives considered:** Treating every discovery failure as legacy would hide outages and stale choices.

## Decision: preserve the established legacy speech default

**Rationale:** The current backend already selects `settings.default_backend` when `model` is absent. Legacy requests omit unsupported selectors and the model field, so the existing configured backend/default voice and language behavior remain the evidence-backed contract.

**Alternatives considered:** Inventing a new model identifier or voice would be unverified and could break compatible services.
