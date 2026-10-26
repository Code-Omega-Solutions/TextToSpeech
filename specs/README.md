# Specifications and living capabilities

## Current behavior versus proposed changes

[living-specs.yml](../living-specs.yml) enables Spec Kit Companion living specs
and registers these implemented capabilities:

| Capability | Living specification | Status |
| --- | --- | --- |
| Browser speech generation | [Speech generation](../capabilities/speech-generation/speech-generation.spec.md) | Draft adoption of implemented behavior |
| Local development and container serving | [Frontend serving](../capabilities/frontend-serving/frontend-serving.spec.md) | Draft adoption of implemented behavior |
| Frontend image publication | [Image publishing](../capabilities/frontend-image-publishing/frontend-image-publishing.spec.md) | Draft adoption of implemented behavior |

The [improved backend feature](001-macos-backend/spec.md) and its
[requirements checklist](001-macos-backend/checklists/requirements.md) describe
proposed work, not shipped behavior. Do not register an implemented backend
capability or fold these requirements into current behavior until implementation
and validation provide evidence.

Notably, the proposed backend requires authenticated server-side integration and
coordinated 32 KiB request limits. Current serving remains unauthenticated at
the proxy-integration layer with a 16 KiB Nginx limit. Living specs preserve that
distinction rather than declaring future safeguards already delivered.

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
python .specify\extensions\companion\scripts\resolve-spec-paths.py --headings speech-generation --json
python .specify\extensions\companion\scripts\check-coverage.py --json
python .specify\extensions\companion\scripts\drift.py --working --json
```

Shape validation reports findings in JSON but does not return a failing exit code
for every finding. Inspect error/warning counts and skipped-file reasons; exit
status alone is not a quality gate.

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
Image-publication requirements deliberately remain unmapped until regression
tests exist for their behavior.

With an optional Companion-enabled agent integration, its living-sync command
can assist updates. Plain CLI/Python validation works without adding agent prompts
or custom instructions to this repository.

Backend planning should identify changes to existing frontend capabilities and
define a separate backend capability only when its implementation exists.
Keep license approval and deployment authorization as explicit gates.

## Public-information boundary

Use synthetic examples, relative paths and configuration-variable names.
Do not copy production environment values, private addresses, personal paths,
raw service definitions, runtime logs, audio, databases or recovery archives into
specifications. A reference to a secret setting is not the secret value.

Review new and changed specifications before publication and review the
reachable history before a public release. Do not push checkpoint refs or
ignored local tooling/state. This documentation does not authorize a commit,
push, package installation on a remote machine, or deployment.
