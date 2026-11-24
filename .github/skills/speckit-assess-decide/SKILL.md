---
name: speckit-assess-decide
description: Decide whether an assessed idea should proceed, be clarified, or stop.
compatibility: Requires a Spec Kit project with the assess extension installed.
metadata:
  author: spec-kit-core
  source: extension:assess
---

# Assess an Idea: Decide

This skill exposes the assess extension's `speckit.assess.decide` command using
GitHub Copilot's hyphenated skill syntax.

Before acting, read and follow the complete canonical command at
`.specify/extensions/assess/commands/speckit.assess.decide.md`. Treat the
triggering message and `$ARGUMENTS` as the user's input. The canonical command
is authoritative for its workflow, path-safety checks, evidence standards,
artifact handling, overwrite protections, and reporting requirements. If the
command file is missing, stop and report that the assess extension is not
installed correctly.
