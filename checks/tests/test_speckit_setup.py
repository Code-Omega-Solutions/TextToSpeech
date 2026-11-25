import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from checks import check_speckit_setup as checker


class SpecKitSetupTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for relative_path in checker.REQUIRED_FILES:
            path = self.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        self.settings = self.root / ".vscode/settings.json"
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(json.dumps({"chat.useAgentSkills": True}), encoding="utf-8")
        self.integration = self.root / ".specify/integration.json"
        self.integration.write_text(
            json.dumps({"installed_integrations": ["copilot"]}), encoding="utf-8"
        )
        self.which = patch.object(checker.shutil, "which", return_value="specify").start()
        self.addCleanup(patch.stopall)
        self.real_run = subprocess.run
        self.run = patch.object(
            checker.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(["specify", "--version"], 0),
        ).start()

    def test_healthy_setup_is_read_only_and_only_probes_cli_version(self):
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(checker.check_setup(self.root), [])
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.run.assert_called_once_with(
            ["specify", "--version"], cwd=self.root, capture_output=True, timeout=10, check=False
        )

    def test_missing_cli_reports_path_issue_without_running_it(self):
        self.which.return_value = None
        self.assertIn("missing from PATH", " ".join(checker.check_setup(self.root)))
        self.run.assert_not_called()

    def test_broken_and_timed_out_cli_are_reported(self):
        self.run.return_value.returncode = 1
        self.assertIn("--version' fails", " ".join(checker.check_setup(self.root)))
        for error in (OSError("missing executable"), subprocess.TimeoutExpired("specify", 10)):
            with self.subTest(error=type(error).__name__):
                self.run.side_effect = error
                self.assertIn("cannot start", " ".join(checker.check_setup(self.root)))

    def test_missing_or_empty_scaffold_file_is_named(self):
        path = self.root / ".specify/scripts/bash/check-prerequisites.sh"
        path.write_text("", encoding="utf-8")
        self.assertIn(str(path.relative_to(self.root)).replace("\\", "/"), " ".join(checker.check_setup(self.root)))
        path.unlink()
        self.assertIn("check-prerequisites.sh", " ".join(checker.check_setup(self.root)))

    def test_disabled_or_invalid_settings_are_reported(self):
        for value in ({"chat.useAgentSkills": False}, [], None):
            with self.subTest(value=value):
                self.settings.write_text(json.dumps(value), encoding="utf-8")
                self.assertIn("chat.useAgentSkills", " ".join(checker.check_setup(self.root)))
        self.settings.write_text("not JSON", encoding="utf-8")
        self.assertIn("Cannot read workspace", " ".join(checker.check_setup(self.root)))

    def test_missing_or_malformed_integration_metadata_is_reported(self):
        for value in ({}, {"installed_integrations": None}, {"installed_integrations": "copilot"}, []):
            with self.subTest(value=value):
                self.integration.write_text(json.dumps(value), encoding="utf-8")
                self.assertIn("not registered", " ".join(checker.check_setup(self.root)))
        self.integration.unlink()
        self.assertIn("Missing or invalid local integration", " ".join(checker.check_setup(self.root)))

    def test_incomplete_checkout_has_actionable_nonzero_result_without_writes(self):
        self.which.return_value = None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with patch.object(checker, "ROOT", root), contextlib.redirect_stdout(output):
                self.assertEqual(checker.main(), 1)
            self.assertEqual(list(root.iterdir()), [])
            self.assertIn("specs/README.md", output.getvalue())
            self.assertIn("did not install or modify anything", output.getvalue())

    def test_workspace_task_runs_on_open_without_forcing_automatic_task_consent(self):
        root = Path(__file__).resolve().parents[2]
        tasks = json.loads((root / ".vscode/tasks.json").read_text(encoding="utf-8"))
        task = next(item for item in tasks["tasks"] if item["label"] == "Spec Kit: Check Local Setup")
        self.assertEqual(task["type"], "process")
        self.assertEqual(task["runOptions"]["runOn"], "folderOpen")
        self.assertEqual(task["runOptions"]["instanceLimit"], 1)
        self.assertEqual(task["args"], ["${workspaceFolder}/checks/check_speckit_setup.py"])
        settings = json.loads((root / ".vscode/settings.json").read_text(encoding="utf-8"))
        self.assertNotIn("task.allowAutomaticTasks", settings)

    def test_project_hooks_are_shareable_but_local_speckit_state_is_ignored(self):
        root = Path(__file__).resolve().parents[2]
        for path, ignored in (
            (".specify/extensions.yml", False),
            (".github/skills/speckit-git-commit/SKILL.md", False),
            (".specify/feature.json", True),
            (".specify/extensions/companion/scripts/write-context.py", True),
            (".specify/assessments/private-assessment/intake.md", True),
        ):
            with self.subTest(path=path):
                result = self.real_run(
                    ["git", "check-ignore", "--no-index", "-q", path],
                    cwd=root,
                    check=False,
                )
                self.assertEqual(result.returncode, 0 if ignored else 1)


if __name__ == "__main__":
    unittest.main()