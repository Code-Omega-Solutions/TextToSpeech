# macOS speech backend

This directory contains the recovered Python backend source and its tests.
Virtual environments, environment files, runtime data, and host-specific launch
scripts are intentionally excluded. The source has not yet been qualified for
deployment; do not treat recovery as authorization to change the running service.

## Development

The backend requires macOS, Python 3.11 or newer, the system `say` command, and
`ffmpeg` on `PATH`. Use `uv` to create an isolated development environment and
run the mocked unit tests:

```powershell
uv sync --dev
uv run pytest
```

For local macOS development, set `TTS_API_KEY` in the process environment and
start the service with `uv run python -m app.main`. Authentication is enabled
by default, and the service binds to loopback unless configured otherwise.

See the [backend feature specification](../specs/001-macos-backend/spec.md) for
the proposed qualification, security, and release requirements.

The repository's [proposed custom attribution license](../LICENSE) and
[third-party notices](../THIRD_PARTY_NOTICES.md) are subject to legal and
ownership review. The lockfile audit found no dependency license that prohibits
public source distribution, but it does not establish rights to recovered
source or clear the separately published frontend image. The custom license is
not an OSI-approved standard license; do not treat its presence as completed
release clearance.
