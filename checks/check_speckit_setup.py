"""Read-only checks for the local Spec Kit scaffold required by this repository."""

import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ".specify/scripts/bash/common.sh",
    ".specify/scripts/bash/check-prerequisites.sh",
    ".specify/scripts/bash/resolve-template.sh",
    ".specify/templates/spec-template.md",
    ".specify/templates/plan-template.md",
    ".specify/templates/tasks-template.md",
    ".specify/memory/constitution.md",
    ".specify/extensions.yml",
    ".specify/extensions/companion/scripts/write-context.py",
    ".github/skills/speckit-specify/SKILL.md",
    ".github/skills/speckit-plan/SKILL.md",
    ".github/skills/speckit-tasks/SKILL.md",
    ".github/skills/speckit-implement/SKILL.md",
    ".github/skills/speckit-converge/SKILL.md",
)


def check_setup(root: Path) -> list[str]:
    issues = []
    executable = shutil.which("specify")
    if executable is None:
        issues.append("Spec Kit CLI 'specify' is missing from PATH.")
    else:
        try:
            result = subprocess.run(
                [executable, "--version"],
                cwd=root,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                issues.append("Spec Kit CLI is on PATH but 'specify --version' fails.")
        except (OSError, subprocess.TimeoutExpired):
            issues.append("Spec Kit CLI cannot start or did not respond within 10 seconds.")

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        try:
            available = path.is_file() and path.stat().st_size > 0
        except OSError:
            available = False
        if not available:
            issues.append(f"Missing or empty setup file: {relative_path}")

    settings_path = root / ".vscode/settings.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict) or settings.get("chat.useAgentSkills") is not True:
            issues.append("Enable 'chat.useAgentSkills' in .vscode/settings.json.")
    except (OSError, UnicodeError, ValueError):
        issues.append("Cannot read workspace skill settings from .vscode/settings.json.")

    integration_path = root / ".specify/integration.json"
    try:
        integration = json.loads(integration_path.read_text(encoding="utf-8"))
        installed = integration.get("installed_integrations") if isinstance(integration, dict) else None
        if not isinstance(installed, list) or "copilot" not in installed:
            issues.append("Spec Kit's local Copilot integration is not registered.")
    except (OSError, UnicodeError, ValueError):
        issues.append("Missing or invalid local integration metadata: .specify/integration.json")

    return issues


def main() -> int:
    issues = check_setup(ROOT)
    if not issues:
        print("[OK] Spec Kit CLI, stock scaffold, Companion, and workspace skills are available.")
        print("No installation, feature creation, or workflow execution was performed.")
        return 0

    print("[FAIL] Local Spec Kit setup needs attention:")
    for issue in issues:
        print(f"  - {issue}")
    print("See specs/README.md: Local tooling / Repairing a partial scaffold.")
    print("Install the CLI from https://github.com/github/spec-kit if needed.")
    print("Do not force initialization over customized skills or the constitution.")
    print("This check did not install or modify anything.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())