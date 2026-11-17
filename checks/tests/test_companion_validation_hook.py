import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".specify/extensions/companion/scripts"))

from companion_config import load_config, merge_hooks


class CompanionValidationHookTests(unittest.TestCase):
    def test_implement_hook_owns_validation_and_uses_checked_in_runner(self):
        config, warnings = load_config(str(ROOT / ".specify/companion.yml"))
        self.assertEqual(warnings, [])
        hooks, warnings = merge_hooks(config, "implement", ["implement-exec"])
        self.assertEqual(warnings, [])
        self.assertEqual(len(hooks), 1)
        hook = hooks[0]["hook"]
        self.assertEqual(hook["type"], "command")
        self.assertEqual(hook["run"], "bash checks/run_companion_validation.sh")
        self.assertEqual(hook["owns"], "validation")
        self.assertTrue((ROOT / "checks/run_companion_validation.sh").is_file())


if __name__ == "__main__":
    unittest.main()