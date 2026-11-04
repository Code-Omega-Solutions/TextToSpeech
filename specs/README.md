# Specifications and living capabilities

## Current behavior versus proposed changes

[living-specs.yml](../living-specs.yml) enables Spec Kit Companion living specs
and registers these implemented capabilities:

| Capability | Living specification | Status |
| --- | --- | --- |
| Browser speech generation | [Speech generation](../capabilities/speech-generation/speech-generation.spec.md) | Draft adoption of implemented behavior |
| Local development and container serving | [Frontend serving](../capabilities/frontend-serving/frontend-serving.spec.md) | Draft adoption of implemented behavior |
| Frontend image publication | [Image publishing](../capabilities/frontend-image-publishing/frontend-image-publishing.spec.md) | Draft adoption of implemented behavior |
| macOS backend synthesis | [Backend synthesis](../capabilities/backend-synthesis/backend-synthesis.spec.md) | Draft adoption of recovered source behavior; native runtime not qualified |
| Project reuse and third-party notices | [Project licensing](../capabilities/project-licensing/project-licensing.spec.md) | Draft adoption of proposed custom attribution terms; legal and rights review pending |

The [backend living spec](../capabilities/backend-synthesis/backend-synthesis.spec.md)
records behavior implemented in [backend](../backend/) and traced to its mocked
tests in the companion [coverage map](../capabilities/backend-synthesis/backend-synthesis.coverage.md).
Its draft/adopted markers remain until the requirements are reviewed against the
code and evidence. The [backend feature specification](001-macos-backend/spec.md)
and [requirements checklist](001-macos-backend/checklists/requirements.md)
describe remaining proposed work and release gates; they do not imply that the
installer, deployment process, or native platform qualification exists.

The backend enforces bearer authentication by default, but the frontend proxy
does not inject a backend credential. The proxy also retains its existing 16 KiB
request-body limit; the proposed coordinated 32 KiB limits and authenticated
proxy-to-backend integration are not implemented. Keep backend authentication
distinct from proxy authentication when changing or describing either surface.

The root [LICENSE](../LICENSE) is a proposed custom attribution license, not an
OSI-approved standard license or legal advice. Its use is subject to legal
approval and confirmation of rights to recovered materials. The [third-party notice](../THIRD_PARTY_NOTICES.md) records the lockfile audit
and container distribution boundaries. The rebuilt frontend image retains
Debian package copyright/license files, embeds a runtime package inventory and
the [written source offer](../SOURCE_OFFER.md), and exposes OCI source/revision
and notice-location labels. The offer requires actual source fulfillment by
the publisher; image metadata or an inventory alone is not source delivery.
The next successful publish is configured to remove older Alpine-based
versions from GHCR, but cannot recall copies already downloaded. Neither
document relicenses third-party packages, Apple speech components, or external
runtime tools.

## Local tooling

This setup was validated with Spec Kit `1.2.4.dev0`, Companion `0.25.0`,
and Python 3.12. Companion scripts use the Python standard library.
The registry and specifications are versionable; generated tooling under
`.specify` remains ignored and contains no durable requirements.

For a fresh checkout, install Spec Kit using its
[official instructions](https://github.com/github/spec-kit), then initialize
shared tooling from the repository root and install Companion:

```powershell
specify init --here --integration none --script ps --non-interactive --force
specify extension add companion --version 0.25.0
```

The initialization command is for a checkout without existing local Spec Kit
customization. Do not force-initialize over customized local tooling.
Review downloaded tooling before installation. Use a compatible release if the
tested development version or extension version is unavailable; rerun validation
after upgrades. No application service installation or restart is involved.

Use an installed Python 3 interpreter below (`python3` on many macOS/Linux hosts):

```powershell
python .specify\extensions\companion\scripts\living_validate.py --json
python .specify\extensions\companion\scripts\resolve-spec-paths.py --changed frontend/app.js --json
python .specify\extensions\companion\scripts\resolve-spec-paths.py --changed backend/app/routers.py --json
python .specify\extensions\companion\scripts\resolve-spec-paths.py --headings speech-generation --json
python .specify\extensions\companion\scripts\resolve-spec-paths.py --headings backend-synthesis --json
python .specify\extensions\companion\scripts\check-coverage.py --json
python .specify\extensions\companion\scripts\drift.py --working --json
python -m unittest discover -s checks/tests -v
git diff --check
```

Shape validation reports findings in JSON but does not return a failing exit code
for every finding. Inspect error/warning counts and skipped-file reasons; exit
status alone is not a quality gate. The release-integrity unit checks protect
required license/attribution wording and the explicit third-party-audit boundary;
they are not legal or ownership verification.

## Keeping specifications alive

1. Resolve changed files to their registered capabilities before changing behavior.
2. Edit the affected requirement and its WHEN/THEN scenarios with the code change.
   Preserve unrelated requirements. Keep `touches` markers aligned with code.
3. Validate shape and coverage. Test observable behavior separately; shape validation
   does not prove an implementation satisfies its specification.
4. Review adopted requirements against code and tests before removing their
   `adopted` markers and draft banners.
5. Commit the code and matching living-spec changes together. Drift checks require
   a committed living-spec baseline; initial uncommitted drafts may be skipped.

Sibling coverage documents map existing test files to requirements. These are
traceability links, not execution results or assertion-completeness guarantees.
The backend tests mock macOS executables and do not establish native runtime
qualification. Image-publication requirements deliberately remain unmapped until
regression tests exist for their behavior.

With an optional Companion-enabled agent integration, its living-sync command
can assist updates. Plain CLI/Python validation works without adding agent prompts
or custom instructions to this repository.

Backend planning should update the backend and affected frontend capabilities
together when integration behavior changes. Keep legal approval of the custom
license, recovered-source rights, third-party review, native qualification, and
deployment authorization as explicit gates.

## Public-information boundary

Use synthetic examples, relative paths and configuration-variable names.
Do not copy production environment values, private addresses, personal paths,
raw service definitions, runtime logs, audio, databases or recovery archives into
specifications. A reference to a secret setting is not the secret value.

Review new and changed specifications before publication and review the
reachable history before a public release. Do not push checkpoint refs or
ignored local tooling/state. This documentation does not authorize a commit,
push, package installation on a remote machine, or deployment.
