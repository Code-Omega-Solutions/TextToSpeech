---
name: speckit-assess-research
description: Gather and assess evidence for an idea in a Spec Kit assessment.
compatibility: Requires a Spec Kit project with the assess extension installed.
metadata:
  author: spec-kit-core
  source: extension:assess
---

# Assess an Idea: Research

This skill exposes the assess extension's `speckit.assess.research` command
using GitHub Copilot's hyphenated skill syntax.

Before acting, read and follow the complete canonical command at
`.specify/extensions/assess/commands/speckit.assess.research.md`. Treat the
triggering message and `$ARGUMENTS` as the user's input. The canonical command
is authoritative for its workflow, path-safety checks, evidence standards,
artifact handling, and reporting requirements. If the command file is missing,
stop and report that the assess extension is not installed correctly.
