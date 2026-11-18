# Optional Basic Memory setup

Basic Memory is optional and separate from the repository's `memory-store` sync workflow. Follow the [Basic Memory quickstart](https://docs.basicmemory.com/) to install the CLI on the machine that runs your Copilot session.

## Register local projects

Run `basic-memory project list --local --json` first. Reuse an existing project only if it points to the intended folder; do not overwrite or move an existing registration. For missing projects, use `basic-memory project add --local <name> <path>`. Registration indexes existing files, so use empty folders for new projects.

| Scope | Project name | Root |
| --- | --- | --- |
| General | `general` | A local folder outside the checkout |
| Project | `project-TextToSpeech` | `.basic-memory/project-TextToSpeech` inside the checkout (git-ignored) |
| Host | `machine-TextToSpeech-<host-id>` | A separate local folder outside the checkout |

Use distinct, non-nested roots. Use a stable, opaque host ID unique to the environment running the client; don't put raw machine identifiers, local paths, or memory notes in Git.

## Connect Copilot

In VS Code, select the Copilot harness and open **Chat: Open Customizations** > **MCP Servers**. Add the servers to **Copilot Global** (the local user configuration), not the tracked workspace `.mcp.json`. Merge the following example into the existing `mcpServers` object; don't replace unrelated entries. Replace `<host-id>` with the same ID used during registration. If the harness cannot find `basic-memory` on its PATH, use the local executable's absolute path in your user configuration only.

```json
{
  "mcpServers": {
    "basic-memory-general": {
      "type": "stdio",
      "command": "basic-memory",
      "args": ["mcp", "--project", "general"]
    },
    "basic-memory-project-TextToSpeech": {
      "type": "stdio",
      "command": "basic-memory",
      "args": ["mcp", "--project", "project-TextToSpeech"]
    },
    "basic-memory-host-TextToSpeech": {
      "type": "stdio",
      "command": "basic-memory",
      "args": ["mcp", "--project", "machine-TextToSpeech-<host-id>"]
    }
  }
}
```

Use **MCP: List Servers** to start each server. For each scope, confirm that Copilot connects, discovers the tools, and succeeds at a read-only call specifying the intended `project`. Separate folders and project arguments help prevent accidental mixing; they don't enforce access control.

## Preview machine knowledge

Run `python machine_knowledge_plugin.py --help` for usage. The script prints a preview to standard output: it doesn't run the commands it looks up, write notes, or change configuration. Back up note files and configuration separately; don't use a copy of a live SQLite database as a backup.
