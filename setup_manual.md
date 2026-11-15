# Basic Memory Setup

## Scope and Identity

- Workspace project ID: `texttospeech`, derived from the repository directory name.
- Caller host ID: `thinkpad-t14`.
- OS and execution boundary: Linux over SSH; recorder shell supplied as `bash`.
- Isolation model: logical separation by project and explicit routing only. This is not an access-control boundary.

## Runtime and Registration

- Basic Memory: 1.0.0.
- `uv`: 0.9.28.
- Installation source: `uv tool`; launcher: `/home/pgfeller/.local/bin/basic-memory`.
- Registration was checked with `basic-memory project list --local --json`.
- General project: `general`, canonical root `/home/pgfeller/.local/share/basic-memory/general`.
- Workspace project: `project-texttospeech`, canonical root `/home/pgfeller/Documents/GitHub/TextToSpeech/.memory/basic-memory`.
- Host project: `machine-texttospeech-thinkpad-t14`, canonical root `/home/pgfeller/.local/share/basic-memory/projects/texttospeech/machine/thinkpad-t14/memory`.
- All three roots are distinct. The workspace root is ignored by Git. Both new projects were empty when registered; no notes were written.

## MCP Configuration

- Configuration source: workspace-root `.mcp.json`, using the native `mcpServers` format.
- The pre-existing `orchestrator` entry was preserved. No user-level or editor-compatibility MCP settings were read or changed.
- `basic-memory-general` launches `basic-memory mcp --project general`.
- `basic-memory-project-texttospeech` launches `basic-memory mcp --project project-texttospeech`.
- `basic-memory-machine-texttospeech-thinkpad-t14` launches `basic-memory mcp --project machine-texttospeech-thinkpad-t14`.
- JSON parsing and route arguments were validated locally. This validates configuration syntax only, not client loading.

## Scope Checks

| Scope | Registration | Initialization | Discovery | Routing |
| --- | --- | --- | --- | --- |
| general | passed | unverified | unverified | unverified |
| project | passed | unverified | unverified | unverified |
| host | passed | unverified | unverified | unverified |

Registration passed using the local project registry and canonical roots. Initialization, discovery, and routing remain unverified because the live VS Code MCP client has not reloaded the new entries and no Basic Memory tools are available in the current client session. Configuration alone is not evidence that the servers started or that scoped calls work.

Next, start or restart the three `basic-memory-*` servers using VS Code's MCP controls. For each initialized server, verify its discovered tool schema, then make a read-only root listing call using the explicit project argument supported by that schema. Record only success or error status; do not capture note names or contents.

## Recorder and Isolation

`machine_knowledge_plugin.py` produces a stdout-only preview. Syntax and input validation checks passed. A preview on the declared SSH host reported only observation time, OS, release, architecture, caller-supplied host/shell/boundary, and boolean PATH lookups. Positive and negative lookups passed without executing the target commands. The preview was not saved or ingested.

No unauthorized cross-project read was attempted. Strict isolation is unverified and must not be claimed: separate roots and project-pinned launch arguments do not restrict a process that can access all roots. No canary note was created.

## Backup and Approval Notes

Back up Markdown note files in the three project roots and the workspace `.mcp.json` configuration. Do not copy a live SQLite database as a backup. No package installation, user-level MCP edit, OS permission change, archived-memory access, or memory-note write was performed during setup.
