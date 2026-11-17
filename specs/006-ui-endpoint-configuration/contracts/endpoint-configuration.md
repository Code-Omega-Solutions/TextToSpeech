# Endpoint configuration contract

## Server-side API

- `GET /api/configuration`: returns the active origin for an authorized operator.
- `PUT /api/configuration`: accepts `{ "origin": "https://service.example.test" }`, validates authorization and policy, atomically persists, and returns the saved origin.
- `GET /api/v1/audio/engines`: remains endpoint-scoped and reports explicit discovery state.
- `GET /api/healthz`: remains endpoint-scoped.
- `POST /api/v1/audio/speech`: remains the existing bounded speech contract.

All configuration routes require the existing operator authorization boundary. Error responses are safe strings and never include credentials.

## UI identifiers

The configuration tab is keyboard-operable and exposes a labeled
`configuration-tab`, informational `configuration-status`, and
`discovery-status`. It does not expose an endpoint editor or backend-token input;
the protected server-side API remains the only configuration mutation path.
