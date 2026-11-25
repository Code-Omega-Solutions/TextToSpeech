import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".specify/extensions/git/scripts"


class FeatureBranchParserTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def stage_script(self, platform, extension):
        names = (f"create-new-feature-branch.{extension}", f"git-common.{extension}")
        if not all((SCRIPTS / platform / name).is_file() for name in names):
            if platform == "powershell":
                self.skipTest("Spec Kit PowerShell extension is unavailable")
            self.fail(f"Spec Kit {platform} extension is unavailable")
        target = self.root / ".specify/extensions/git/scripts" / platform
        target.mkdir(parents=True)
        for name in names:
            shutil.copyfile(SCRIPTS / platform / name, target / name)
        return target / names[0]

    def test_bash_arguments_and_errors(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash is unavailable")
        script = self.stage_script("bash", "sh")

        def run(*args):
            return subprocess.run(
                [bash, str(script), *args], cwd=self.root, capture_output=True, text=True
            )

        for args in (
            ("--json", "--dry-run", "--number", "12", "--short-name", "ui-alignment", "Update UI"),
            ("--json", "--dry-run", "Update UI", "--short-name", "ui-alignment", "--number", "12"),
        ):
            with self.subTest(args=args):
                result = run(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["BRANCH_NAME"], "012-ui-alignment")
        for args in (("--short-name",), ("--short-name", "--json"), ("--number", "-1")):
            with self.subTest(args=args):
                self.assertNotEqual(run(*args).returncode, 0)
        created = run("--json", "--number", "12", "--short-name", "ui-alignment", "Update UI")
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertEqual(json.loads(created.stdout)["BRANCH_NAME"], "012-ui-alignment")
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=self.root, capture_output=True, text=True, check=True
        )
        self.assertEqual(branch.stdout.strip(), "012-ui-alignment")

    def test_powershell_equivalent_arguments(self):
        powershell = shutil.which("pwsh")
        if not powershell:
            self.skipTest("PowerShell is unavailable")
        script = self.stage_script("powershell", "ps1")
        result = subprocess.run(
            [powershell, "-NoProfile", "-File", str(script), "-Json", "-DryRun",
             "-Number", "12", "-ShortName", "ui-alignment", "Update UI"],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["BRANCH_NAME"], "012-ui-alignment")


if __name__ == "__main__":
    unittest.main()
