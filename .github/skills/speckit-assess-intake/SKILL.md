---
name: speckit-assess-intake
description: Capture and normalize an idea into a Spec Kit assessment intake note.
compatibility: Requires a Spec Kit project with the assess extension installed.
metadata:
  author: spec-kit-core
  source: extension:assess
---

# Assess an Idea: Intake

This skill exposes the assess extension's `speckit.assess.intake` command using
GitHub Copilot's hyphenated skill syntax.

Before acting, read and follow the complete canonical command at
`.specify/extensions/assess/commands/speckit.assess.intake.md`. Treat the
triggering message and `$ARGUMENTS` as the user's input. The canonical command
is authoritative for its workflow, path-safety checks, artifact handling, and
reporting requirements. If the command file is missing, stop and report that
the assess extension is not installed correctly.
