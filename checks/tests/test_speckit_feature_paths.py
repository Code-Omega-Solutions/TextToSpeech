import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".specify/scripts/bash"


class SpecKitFeaturePathTests(unittest.TestCase):
    def setUp(self):
        self.bash = shutil.which("bash")
        if not self.bash:
            self.skipTest("Bash is unavailable")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.scripts = self.root / ".specify/scripts/bash"
        self.scripts.mkdir(parents=True)
        for name in ("common.sh", "check-prerequisites.sh", "setup-plan.sh", "setup-tasks.sh"):
            shutil.copyfile(SCRIPTS / name, self.scripts / name)
        self.templates = self.root / ".specify/templates"
        self.templates.mkdir()
        (self.templates / "plan-template.md").write_text("Plan template\n", encoding="utf-8")
        (self.templates / "tasks-template.md").write_text("Tasks template\n", encoding="utf-8")
        self.relative = "specs/007 path $value; [feature]"
        self.feature = self.root / self.relative
        self.feature.mkdir(parents=True)
        (self.feature / "spec.md").write_text("Specification\n", encoding="utf-8")
        self.environment = os.environ.copy()
        for key in ("SPECIFY_INIT_DIR", "SPECIFY_FEATURE_DIRECTORY", "SPECIFY_FEATURE",
                    "SPECIFY_FEATURE_NO_PERSIST"):
            self.environment.pop(key, None)
        self.environment["SPECIFY_FEATURE_DIRECTORY"] = self.relative

    def run_script(self, name, *args, env=None):
        return subprocess.run(
            [self.bash, str(self.scripts / name), *args],
            cwd=self.root, env=env or self.environment, capture_output=True, text=True,
        )

    def test_setup_and_prerequisite_paths_preserve_special_characters(self):
        plan = self.run_script("setup-plan.sh", "--json")
        self.assertEqual(plan.returncode, 0, plan.stderr)
        self.assertEqual(Path(json.loads(plan.stdout)["FEATURE_DIR"]), self.feature)
        self.assertEqual((self.feature / "plan.md").read_text(), "Plan template\n")
        tasks = self.run_script("setup-tasks.sh", "--json")
        self.assertEqual(tasks.returncode, 0, tasks.stderr)
        self.assertEqual(Path(json.loads(tasks.stdout)["FEATURE_DIR"]), self.feature)
        (self.feature / "tasks.md").write_text("Tasks\n", encoding="utf-8")
        check = self.run_script(
            "check-prerequisites.sh", "--json", "--require-spec", "--require-tasks", "--include-tasks"
        )
        self.assertEqual(check.returncode, 0, check.stderr)
        result = json.loads(check.stdout)
        self.assertEqual(Path(result["FEATURE_DIR"]), self.feature)
        self.assertIn("tasks.md", result["AVAILABLE_DOCS"])
        self.assertEqual(json.loads((self.root / ".specify/feature.json").read_text())["feature_directory"],
                         self.relative)

    def test_no_persist_overrides_and_missing_feature_fail_closed(self):
        feature_json = self.root / ".specify/feature.json"
        original = json.dumps({"feature_directory": "specs/previous"})
        feature_json.write_text(original, encoding="utf-8")
        result = self.run_script("check-prerequisites.sh", "--json", "--paths-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(json.loads(result.stdout)["FEATURE_DIR"]), self.feature)
        self.assertEqual(feature_json.read_text(), original)
        (self.feature / "plan.md").write_text("Plan\n", encoding="utf-8")
        env = self.environment | {"SPECIFY_FEATURE_NO_PERSIST": "1"}
        result = self.run_script("check-prerequisites.sh", "--json", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(feature_json.read_text(), original)
        feature_json.unlink()
        env.pop("SPECIFY_FEATURE_DIRECTORY")
        result = self.run_script("check-prerequisites.sh", "--json", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Failed to resolve feature paths", result.stderr)
        self.assertFalse(feature_json.exists())


if __name__ == "__main__":
    unittest.main()
