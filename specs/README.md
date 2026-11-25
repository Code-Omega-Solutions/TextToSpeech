# Specifications and living capabilities

## Current behavior versus proposed changes

[living-specs.yml](../living-specs.yml) is the repository's capability registry
for these implemented areas:

| Capability | Living specification | Status |
| --- | --- | --- |
| Browser speech generation | [Speech generation](../capabilities/speech-generation/speech-generation.spec.md) | Draft adoption of implemented behavior |
| Local development and container serving | [Frontend serving](../capabilities/frontend-serving/frontend-serving.spec.md) | Draft adoption of implemented behavior |
| Frontend image publication | [Image publishing](../capabilities/frontend-image-publishing/frontend-image-publishing.spec.md) | Draft adoption of implemented behavior |
| macOS backend synthesis | [Backend synthesis](../capabilities/backend-synthesis/backend-synthesis.spec.md) | Draft adoption of recovered source behavior; native runtime not qualified |
| Private VibeVoice evaluation | [VibeVoice evaluation](../capabilities/vibevoice-evaluation/vibevoice-evaluation.spec.md) | Draft; local evaluator and mocked evidence, not native model qualification |
| Project reuse and third-party notices | [Project licensing](../capabilities/project-licensing/project-licensing.spec.md) | Draft adoption of proposed custom attribution terms; legal and rights review pending |

The [project constitution](../.specify/memory/constitution.md) is the durable
Spec Kit policy. Stock Spec Kit does not validate this repository-specific
registry or its coverage maps.

The [backend living spec](../capabilities/backend-synthesis/backend-synthesis.spec.md)
records behavior implemented in [backend](../backend/) and traced to its mocked
tests in the companion [coverage map](../capabilities/backend-synthesis/backend-synthesis.coverage.md).
Its draft/adopted markers remain until the requirements are reviewed against the
code and evidence. The [backend feature specification](001-macos-backend/spec.md)
and [requirements checklist](001-macos-backend/checklists/requirements.md)
describe remaining proposed work and release gates; they do not imply that
native platform qualification or a deployment process exists. A read-only
prerequisite checker, an explicitly approved locked-environment setup helper,
and an unregistered per-user service example are available; they do not install
system prerequisites, register services, or change running systems.

The [private VibeVoice evaluation](../capabilities/vibevoice-evaluation/vibevoice-evaluation.spec.md)
is a separate, optional tool. Its report and audio remain local and owner-only;
its tests use fakes and do not qualify models or target hardware.

The [Fish Speech documentary feasibility feature](004-fish-speech-feasibility/spec.md)
records Option B's permission and capacity screening. Its
[outcome](004-fish-speech-feasibility/outcome.md) is blocked pending intended-use,
rights, voice, and authorized-machine evidence. Completing its documentary
checks does not approve model downloads, installation, host inspection,
synthesis, service integration, production use, or redistribution.

The [selectable speech engines prototype](005-selectable-speech-engines/spec.md)
adds an engine registry and authenticated discovery contract while preserving
the existing speech API. Its Fish prototype behavior is historical; the
current replacement direction and safe retirement contract are recorded in
[feature 007 — replace Fish with Phonon](007-replace-phonon/spec.md).

The [gated Fish backend enablement feature](007-fish-backend-enablement/spec.md)
and its [quickstart](007-fish-backend-enablement/quickstart.md) are retained as
historical records of an earlier private prototype and its gates. They do not
describe the current serving runtime: the Fish adapter, managed process, and
launcher have been removed, while the generic prototype recreation/runbook
safeguards remain. Historical results are not Phonon asset approval or current
deployment authorization.

The [historical Fish voice-preparation guide](../backend/voice-preparation.md)
documents authorized acquisition and WAV/transcript preparation without
distributing assets. An optional private companion repository holds sanitized
documentation, public source metadata and explicitly authorized non-sensitive
checkpoint backups with source/license/hash records; voice datasets, personal
material, credentials and approvals stay in authorized local private storage
outside both checkouts. Private hosting does not
clear dataset re-hosting, voice-use or generated-output privacy restrictions,
and does not close feature 007's remaining gates.

The [UI endpoint configuration feature](006-ui-endpoint-configuration/ui-endpoint-configuration.spec.md)
proposes a configuration tab, capability-aware engine and voice controls, legacy
speech compatibility, and documented file-backed container persistence. It is
pending specification review and does not establish deployed routing or
authorize changes to a live service.

Two additional draft feature specifications separate the proposed
[local speech prototype](002-local-speech-prototype/spec.md) from the
[publishable voice-cloning interface](003-voice-cloning-ui/spec.md). Their
specifications may be reviewed for publication; the prototype implementation,
models, reference recordings and private evaluation results must remain outside
publishable repository contents until a separate decision authorizes them. The
interface must preserve ordinary speech generation without the prototype.

The backend enforces bearer authentication by default. The Vite and Nginx
proxies now read a server-side credential and replace the upstream authorization
header; neither exposes the credential to browser assets. The backend and both
proxies enforce a streamed 32 KiB encoded-request limit. Keep proxy-to-backend
authentication distinct from browser-user authentication: loopback binding is
not client access control, and TLS/access controls remain a separately reviewed
network-boundary responsibility.

The [language detection fallback feature](004-language-detection-fallback/spec.md)
describes the change from rejecting unsupported automatic detections to using
en-US. The backend living specification records the current behavior.

The root [LICENSE](../LICENSE) is a proposed custom attribution license, not an
OSI-approved standard license or legal advice. Its use is subject to legal
approval and confirmation of rights to recovered materials. It applies only to
project-owned material; third-party dependencies and runtime components retain
their own licenses. The [third-party notice](../THIRD_PARTY_NOTICES.md) uses
lockfiles and the built image's package/version/source inventory to describe
distribution scope. The rebuilt frontend image retains Debian package
copyright/license files, includes the [written source offer](../SOURCE_OFFER.md),
and exposes OCI source/revision and notice-location labels. The offer requires
actual source fulfillment by the publisher; image metadata or an inventory
alone is not source delivery. The publishing workflow removes older GHCR
versions after a successful publish, but deletion cannot recall copies already
downloaded or redistributed. Neither the notice nor the workflow grants legal
approval or relicenses third-party packages, Apple speech components, or
external runtime tools.

## Local tooling

The Copilot skills, project constitution, Companion configuration, and
`.specify/extensions.yml` lifecycle-hook configuration are tracked. Selected
Bash helpers are also tracked to preserve repository fixes. Other generated
scripts, templates, extension packages, and per-checkout integration metadata
under `.specify` remain local and must be installed separately.

For a fresh checkout, install Spec Kit using its
[official instructions](https://github.com/github/spec-kit), then initialize
shared tooling from the repository root:

```powershell
specify init --here --script ps --non-interactive --force
```

Non-interactive initialization defaults to Copilot. `--force` merges scaffold
files into a nonempty checkout and may overwrite conflicts; inspect existing
`.specify` and `.github/skills` files first, and do not force over customized
tooling. Keep the constitution tracked when updating the generated scaffold.
Spec Kit initialization does not install or restart application services.
The tracked extension configuration names the project's hooks; install the
named extensions locally before running them. Inspect installation changes
before accepting updates to the tracked configuration or customized helpers.

### Repairing a partial scaffold

If stock helpers such as the convergence prerequisite checker are missing,
generate a clean scaffold with the installed CLI and copy only missing files.
In Git Bash, this preserves the constitution, extension configuration, feature
state, and existing Copilot skills instead of forcing initialization over them:

```bash
scratch=$(mktemp -d)
specify init "$scratch/scaffold" --script sh --integration copilot --non-interactive --ignore-agent-tools
cp -an "$scratch/scaffold/.specify/." .specify/
bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
bash .specify/scripts/bash/resolve-template.sh spec-template --json
```

Use an active feature with a nonempty spec, plan, and task list for the first
check. Untracked scaffold files remain local tooling and must be installed on
each machine; do not overwrite the tracked helper fixes. Optional `jq` must work
if selected by the Bash helpers; a stale launcher can exist on PATH while its
executable is missing. Check `jq --version` when diagnosing JSON errors. The
repaired local helper falls back when that probe fails.

Copilot skill discovery also requires `chat.useAgentSkills` to be enabled in
the workspace settings. Reload the VS Code window after enabling it if existing
skills are not yet listed. Changing this setting does not rewrite the skills.

### Workspace-open setup check

The versioned [VS Code task](../.vscode/tasks.json) runs the read-only
[local setup checker](../checks/check_speckit_setup.py) whenever this workspace
opens, including on another machine. It checks CLI responsiveness, required
stock/Companion files, Copilot integration metadata, and workspace skill settings.
It does not need an active feature, install tooling, or run a workflow.

On first use, trust the workspace and allow its automatic tasks when VS Code
prompts. If automatic tasks were previously disabled, use **Tasks: Manage
Automatic Tasks in Folder** to enable them. Workspace files do not override that
consent. Python must be available as `python` on Windows or `python3` on macOS/Linux.

Failures appear in the **Spec Kit: Check Local Setup** task terminal with the
missing items and a reference to the repair instructions above. Run it manually
with **Tasks: Run Task**, or from the repository root:

```bash
python3 checks/check_speckit_setup.py
```

Use `python` instead on Windows when running outside Git Bash. A successful
setup check confirms tooling availability, not model or platform qualification.

The Companion VS Code extension and the Spec Kit extension are separate.
The checked-in Companion skills correspond to Spec Kit Companion 0.28.0,
which requires Spec Kit 1.2.5.dev0 or newer. Install that extension from its
official release:

```sh
specify extension add companion --from https://github.com/alfredoperez/speckit-companion/releases/download/speckit-ext-v0.28.0/companion-0.28.0.zip
specify extension list
python3 .specify/extensions/companion/scripts/write-context.py --help
```

Review the source confirmation before accepting it. The generated extension
and its scripts are ignored local tooling, so install them separately in each
checkout. Do not use `--force` over an existing installation without reviewing
its configuration and changes. Companion records future workflow steps; it
cannot reconstruct missing historical timestamps. These scripts do not replace
reviewing registry shape and coverage alongside the repository's tests.

```powershell
python3 -m unittest discover -s checks/tests -v
git diff --check
```

These release-integrity tests protect required license/attribution wording,
distribution boundaries, and explicit release-gate wording; they are not legal
or ownership verification.

## Keeping specifications alive

1. Resolve changed files to their registered capabilities before changing behavior.
2. Edit the affected requirement and its WHEN/THEN scenarios with the code change.
   Preserve unrelated requirements. Keep `touches` markers aligned with code.
3. Review registry paths and coverage maps, then run focused behavior tests.
   Documentation and coverage links do not prove an implementation satisfies
   its specification.
4. Review adopted requirements against code and tests before removing their
   `adopted` markers and draft banners.
5. Commit the code and matching living-spec changes together. Drift checks require
   a committed living-spec baseline; initial uncommitted drafts may be skipped.

Sibling coverage documents map existing test files to requirements. These are
traceability links, not execution results or assertion-completeness guarantees.
The backend tests mock macOS executables and do not establish native runtime
qualification. Image-publication requirements deliberately remain unmapped until
regression tests exist for their behavior.

The Companion VS Code extension is optional and does not replace repository
tests or review of the registry and coverage maps.

Backend planning should update the backend and affected frontend capabilities
together when integration behavior changes. Keep legal approval of the custom
license, recovered-source rights, third-party review, exact-artifact
source-offer fulfillment, native qualification, and deployment/release
authorization as explicit gates. Mocked Linux checks do not satisfy native
qualification. Review changed publication content and the reachable history
before a public release; cleanup of registry versions is not a substitute.

## Public-information boundary

Use synthetic examples, relative paths and configuration-variable names.
Do not copy production environment values, private addresses, personal paths,
raw service definitions, runtime logs, audio, databases or recovery archives into
specifications. A reference to a secret setting is not the secret value.

Review new and changed specifications before publication and review the
reachable history before a public release. Do not push checkpoint refs or
ignored local tooling/state. This documentation does not authorize a commit,
push, package installation on a remote machine, or deployment.
