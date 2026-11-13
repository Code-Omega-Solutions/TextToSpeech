# Research: macOS speech backend

These are implementation decisions, not evidence of macOS qualification or
permission to install software. The existing backend and its mocked tests are
the starting point.

## Prerequisites and installation

**Decision:** Implement a standard-library Python command separate from the
application import. Inspection is read-only and bounded. Setup proposes a
specific change plan and requires explicit acceptance. Setup requires an
existing compatible Python interpreter, `uv`, and ffmpeg. Missing or incompatible
tools produce blockers and documented official installation instructions.
Setup does not invoke Homebrew or install machine-level tools. After the
operator prepares them separately, setup creates or reuses the dedicated
user-owned environment and installs locked application dependencies.

The diagnostic command itself needs Python 3.11 or newer. Documented bounded,
read-only preflight steps check bootstrap interpreter availability before
invocation. Without it, preflight reports the blocker and instructions; the
Python checker and structured diagnostics do not run. Once it is available,
the checker can assess a separate configured backend interpreter.

**Rationale:** Existing project dependencies are already locked with `uv`.
Keeping machine-level tool preparation outside setup preserves its dedicated
environment boundary and avoids changing unrelated tools. A missing required
OS-managed voice remains a manual blocking step. Separating interpreter
preflight from the Python checker avoids claiming that it can run without Python.

**Alternatives considered:** Installing into system Python risks unrelated
applications. Automatically bootstrapping a package manager would exceed
consent. Native support and publisher verification must be checked on authorized
Macs before making support claims; a package that cannot be verified must not be
installed.

## Audio and credentials

**Decision:** Keep the existing macOS `say` and ffmpeg pipeline, explicitly
verify the selected executable's MP3 and PCM capabilities, and retain the
configured voices. Accept exactly one credential source, environment or a
protected file; conflicting sources fail closed. Provision credentials only
with explicit consent and never overwrite an existing credential.

**Rationale:** This preserves the recovered API without introducing another
engine or exposing a secret to the browser or a process argument.

**Alternatives considered:** Shipping Apple voices would cross a redistribution
boundary. An undeclared ffmpeg provider or a silent fallback would make the
installed environment irreproducible.

## Request and temporary storage bounds

**Decision:** Count UTF-16 code units after rejecting unpaired surrogates, and
bound encoded bodies while reading on both backend and frontend. Use a private
per-request directory with a configurable 256 MiB temporary budget and the
existing 25 MiB response limit; enforce limits while files are produced.

**Rationale:** Python string length differs from the browser's UTF-16 length,
and Content-Length cannot be trusted. The temporary budget is a separate
ceiling for intermediate audio; requests exceeding it fail safely.

**Alternatives considered:** Limiting only the final response can exhaust disk.
Trusting a declared body length permits chunked or misleading requests.

## Frontend integration

**Decision:** Keep the existing three-route allowlist. Add server-side secret
loading and Authorization replacement to Vite development/preview and the Nginx
container. The container consumes a read-only secret file and creates any
required rendered configuration in a private runtime location.

**Rationale:** Browser requests and assets remain unchanged and cannot select
the credential. The shared secret secures only the proxy-to-backend hop.

**Alternatives considered:** Browser-provided credentials expose the backend
secret. Disabling backend authentication to make the proxy work fails the
security requirements.

## Qualification

**Decision:** Run isolated mocked backend and proxy tests on Linux. Treat
authorized native runs on macOS 13 or later for both Intel and Apple Silicon
as separate release gates, recording actual OS, Python, package manager, ffmpeg,
and voice versions.

**Rationale:** Mocks do not establish native synthesis, installation, or
audio-encoding behavior. Legal approval, source rights, dependency licensing,
and release-history review are additional independent release gates.
