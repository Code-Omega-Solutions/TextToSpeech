# macOS speech backend

This directory contains the recovered Python backend and its mocked tests.
There are no checked-in virtual environments, credentials, runtime data, or
host-specific launch scripts. Recovery and these setup helpers do not authorize
changing a running service, registering a new one, or publishing a release.

## Requirements and clean-checkout setup

The speech runtime requires macOS 13 or newer on Apple Silicon or Intel, Python
3.11 or newer, `uv`, the macOS `/usr/bin/say` command, and `ffmpeg` with the
required MP3/WAV encoders on `PATH`. The repository's mocked tests can run on
Linux; they do not qualify the native macOS runtime.

From a fresh checkout, review this guide, then run the dependency-locked setup
and mocked tests from `backend/`:

```sh
uv sync --locked --dev
uv run pytest
```

`uv sync` changes only the project's local Python environment. It does not
install macOS tools, voices, or a service, and does not change an existing
system Python or running application. The setup helper below is an optional,
separate path when an operator wants an isolated managed runtime environment.

## Read-only prerequisite check

The checker reports platform, architecture, tool, voice, configuration,
credential-access, destination, disk, and port diagnostics. It does not install
anything, write configuration, or synthesize speech. Run it from this directory:

```sh
python3 prerequisites.py
python3 prerequisites.py --json
```

Exit status `0` means all required checks passed, `1` means one or more
prerequisites need attention, and `2` means inspection could not complete.
Review each diagnostic and remediation; a successful check is not a native
qualification or release approval.

## Optional isolated setup and recovery

Setup is plan-first. Create the intended parent directory yourself, then ask for
a plan without `--accept`:

```sh
mkdir -p "$HOME/.local/share/texttospeech"
python3 setup.py --destination "$HOME/.local/share/texttospeech/backend-venv"
```

Review the action, destination, blockers, and exact plan ID printed by the
helper. Only if the plan is acceptable, explicitly accept that ID:

```sh
python3 setup.py --destination "$HOME/.local/share/texttospeech/backend-venv" --accept <PLAN_ID>
```

The helper rechecks the plan before it acts and installs only locked Python
dependencies into that dedicated destination. It will not overwrite an existing
destination or modify system Python, install `ffmpeg`, change macOS settings,
create credentials, register services, or start/stop a service. Do not approve a
plan you have not reviewed. A plan-only invocation is check-only; `--json` is
available on either invocation for machine-readable output.

If a plan is blocked, use the named remediation and rerun the checker. Missing
system tools, codecs, or voices require separate operator action through
approved channels; this helper does not install them. If a plan becomes stale,
or a prerequisite changes before acceptance, generate and review a new plan
rather than reusing an old ID. If another setup holds the destination lock, let
it finish and then rerun the plan. A compatible environment matching the current
lockfile is reported as a no-op on rerun.

On an installation failure, artifacts created by that attempt are removed and
the helper reports failure; it does not roll back or remove pre-existing
content. If dependencies installed but post-checks still find an external
prerequisite missing, the environment can remain in place and the result is
reported as incomplete. Review the diagnostics, resolve only the missing
prerequisite, rerun the read-only check, then request a fresh plan. Never point
the helper at a shared or existing environment.

## Credentials and service operation

Bearer authentication is enabled by default. Choose exactly one server-side
credential source:

- Set `TTS_API_KEY` through the process supervisor's protected environment; or
- Set `TTS_API_KEY_FILE` to an existing regular UTF-8 file owned by the service
  user, mode `0600` (no group/other access), containing a nonempty credential
  of at most 4096 bytes and optionally one trailing newline.

Do not set both variables. The backend does not create, display, rotate, or
overwrite credentials. Keep secret values outside the repository and logs. A
missing, empty, unreadable, insecure, symlink, or malformed file prevents use.
The checker reports credential accessibility without printing the secret.
Provisioning and rotation remain operator responsibilities.

The backend defaults to `127.0.0.1:8000`; do not bind it to a wider interface
unless a separately reviewed network boundary requires it. Health (`/healthz`)
is distinct from readiness (`/readyz`), which verifies runtime dependencies and
required voices. The speech endpoint is `POST /v1/audio/speech`. The existing
request limit is 5,000 UTF-16 code units; the service applies bounded request,
concurrency, timeout, output, and per-request temporary-storage limits.

German (`de-DE`) and US English (`en-US`) voices are required. Defaults are
`Anna (Deutsch (Deutschland))` and `Samantha`; British English (`en-GB`,
default voice `Daniel`) is optional. Verify the host inventory with
`/usr/bin/say -v '?'` and `python3 prerequisites.py`. If a required voice is
unavailable, install or select it through macOS voice settings, or set the
corresponding `TTS_VOICE_DE_DE`, `TTS_VOICE_EN_US`, or `TTS_VOICE_EN_GB` value
to an installed voice. Rerun the checker; an optional voice missing does not
block readiness.

`service/com.example.texttospeech.plist` is a review-only per-user launchd
example. It contains placeholders for the operator's own paths, references a
protected credential file, binds to loopback, and does not start at load. Review
and adapt it only after native qualification and deployment approval. The
repository does not register or activate it. Do not use this sample to alter a
running service.

For removal, first stop only a service that you deliberately registered, using
the service manager and identity you chose. Then remove only the dedicated
managed environment and private configuration/data you created for this
instance. Preserve shared environments, source files, credentials that are
still in use, system packages, and unrelated services. Setup does not remove
those resources.

## Qualification and release gates

Mocked Linux checks validate code paths and fixtures only. They are not evidence
of native macOS qualification, voice availability on a target host, operational
readiness, deployment authorization, or release approval. Native qualification
must be performed and reviewed on the supported macOS environment without
claiming success from mocks.

The root [proposed custom attribution license](../LICENSE) applies only to
project-owned material. Its use, rights to recovered source, third-party
notices, and release history require separate legal, ownership, and source-rights
review. A clean dependency audit does not clear recovered source or the
separately published frontend image. The custom license is not an OSI-approved
standard license; its presence does not authorize release. See the
[third-party notices](../THIRD_PARTY_NOTICES.md), [source offer](../SOURCE_OFFER.md),
and [feature specification](../specs/001-macos-backend/spec.md) for the
separate inventory and proposed gates.
