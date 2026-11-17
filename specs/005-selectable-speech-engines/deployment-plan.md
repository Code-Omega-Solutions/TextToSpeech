# Parallel Prototype Deployment Plan

**Status**: deployed for macOS baseline; Fish remains disabled
**Deployment mode**: side-by-side; preserve the existing healthy service
**Candidate model**: none selected

## Verified Preflight

- SSH public-key authentication succeeded after the operator interactively
  verified and accepted the target's host key. The host name, address, login
  name, and key fingerprint are intentionally omitted from this tracked file.
- Read-only target inspection confirmed a macOS Apple Silicon host with the
  required configured German and US English `say` voices.
- With the user's approval, Homebrew, Python 3.12.16, `uv` 0.13.8, and `ffmpeg`
   9.0.2 were installed in the standard Apple Silicon Homebrew prefix. No shell
   profile, application service, credential, port, firewall, or runtime
   configuration for the existing service was changed.
- The backend dependencies were synchronized from the committed lockfile into
   the dedicated prototype environment.
- A separate per-user LaunchAgent is running with authentication enabled,
   Fish disabled, and the approved parallel listener. Its credential is stored
   in an owner-only file and is not included in this repository or memory note.
- Health and readiness return 200. Catalog access requires bearer authentication.
   Authenticated English and German WAV requests return audio from `macos-say`;
   legacy `vibevoice` and disabled `fish-speech` selections return 503.
- A healthy speech service already listens on the current deployment port. It
  remains unchanged; no process, service, firewall, key, credential, port, or
  runtime configuration was modified.
- No Fish model, weights, codec, voice assets, or inference server were
  downloaded, installed, or enabled. Exact checkpoint and voice terms remain
  unreviewed.

These observations establish operation of the macOS baseline prototype only.
They do not qualify Fish, authorize its artifacts, or establish that a specific
Fish variant will run acceptably.

## Remaining Follow-Up

- Open WebUI runs on a separate private-network device. Its client configuration
  has not been changed. Configure it through the owner's normal secret manager
  with the prototype base URL and the protected API key, without copying the
  key into this repository or chat.
- Before enabling Fish, review the exact checkpoint, codec, runtime packages,
  applicable terms, and voice provenance. Leave Fish disabled if any gate is
  unresolved; the macOS baseline continues to serve English and German.
- Compare the pinned Fish variants and obtain separately approved local quality,
  latency, and resource tests before selecting or installing any weights.

The installed prototype is separate from the existing service. Do not change,
stop, or replace that service as part of this deployment. Never request or store
passwords, API keys, or private-key contents in this repository. If a later
change needs a new SSH key or service boundary, review and approve that exact
change before acting.

## Deployment Verification

- The host key was accepted after interactive fingerprint review; public-key
  authentication then succeeded for the confirmed account.
- Read-only checks confirmed the parallel port was unused before deployment.
- The existing service remains healthy on its original listener.
- The prototype has bearer authentication, authenticated discovery, safe
  unavailable responses, and successful synthetic English/German WAV checks.
- Fish is disabled; no Fish model, voice, or codec assets were downloaded or
  installed.

## Current Outcome

The macOS-only prototype is deployed and verified in parallel. Fish model
assessment and installation remain blocked on exact terms/provenance and
approved local evaluation. Open WebUI still needs its client-side configuration
updated separately using the protected credential.
