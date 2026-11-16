"""Check documentary screening claims, not model or host qualification."""

from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit


FEATURE_DIR = Path(__file__).resolve().parent
REPO_ROOT = FEATURE_DIR.parent.parent
REVISION = "0f8a12e8a651062fdee9c33a894bdccd3a8513f1"


class DocumentaryScreeningTests(unittest.TestCase):
    def report(self, name: str) -> str:
        return (FEATURE_DIR / name).read_text(encoding="utf-8")

    def test_fr001_permission_separation(self):
        report = self.report("permission-screening.md")
        for text in (
            "**Permission status**: blocked",
            "**Intended use**: unresolved",
            "**Voice rights**: unresolved",
            "Fish Audio Community License",
            "Fish Audio Research License",
            "Weight terms",
            "unverified",
            REVISION,
            "## Required Inputs",
        ):
            self.assertIn(text, report)

    def test_fr002_capacity_separation(self):
        report = self.report("capacity-screening.md")
        self.assertIn("**Host qualification**: blocked", report)
        self.assertIn("## Upstream Guidance", report)
        self.assertIn("48 GB", report)
        self.assertIn("24 GB", report)
        for measurement in (
            "Available storage",
            "Available RAM",
            "Available VRAM",
            "Peak runtime memory",
            "Higher-priority reserve",
            "Time to first audio",
            "Total synthesis time",
        ):
            self.assertIn(f"| {measurement} | not measured |", report)

    def test_fr003_blocked_outcome(self):
        report = self.report("outcome.md")
        for text in (
            "**Documentary status**: complete",
            "**Overall feasibility**: blocked",
            "**Permission**: blocked",
            "**Capacity**: blocked",
            "| English | not evaluated | not measured |",
            "| German | not evaluated | not measured |",
        ):
            self.assertIn(text, report)
        for number in range(1, 9):
            self.assertIn(f"**Q{number}**", report)

    def test_fr004_operations_withheld(self):
        report = self.report("outcome.md")
        for operation in (
            "Model downloads",
            "Package installation",
            "Host inspection",
            "Synthesis",
            "Spending",
            "Service changes",
        ):
            self.assertIn(f"| {operation} | not authorized; not performed |", report)
        self.assertIn("Separate operator approval", report)
        self.assertIn("Stop", report)

    def test_fr005_evidence_and_boundaries(self):
        for name in (
            "permission-screening.md",
            "capacity-screening.md",
            "outcome.md",
        ):
            report = self.report(name)
            self.assertIn("## Evidence", report)
            self.assertTrue(report.endswith("\n"))
            self.assertFalse(report.endswith("\n\n"))
            links = re.findall(r"\]\(([^)]+)\)", report)
            self.assertTrue(links, name)
            for link in links:
                parsed = urlsplit(link)
                if parsed.scheme:
                    self.assertEqual(parsed.scheme, "https")
                    self.assertIn(
                        parsed.hostname,
                        {"github.com", "raw.githubusercontent.com", "api.github.com", "huggingface.co"},
                    )
                    self.assertIsNone(parsed.username)
                    self.assertIsNone(parsed.password)
                    self.assertFalse(parsed.query)
                else:
                    target = (FEATURE_DIR / parsed.path).resolve()
                    self.assertTrue(target.is_relative_to(REPO_ROOT))
                    self.assertTrue(target.exists(), link)
                    if parsed.fragment:
                        headings = re.findall(
                            r"^#+\s+(.+)$", target.read_text(encoding="utf-8"), re.MULTILINE
                        )
                        anchors = {
                            re.sub(r"\s", "-", re.sub(r"[^a-z0-9_\-\s]", "", heading.lower()))
                            for heading in headings
                        }
                        self.assertIn(parsed.fragment, anchors, link)
            self.assertNotRegex(report, r"(?i)Bearer\s+[a-z0-9._~-]{12,}")
            self.assertNotRegex(report, r"\b(?:10|127)\.\d+\.\d+\.\d+\b")
        outcome = self.report("outcome.md")
        self.assertIn("No private speech, audio, credentials, or operational details", outcome)
        self.assertIn("not legal approval or platform qualification", " ".join(outcome.split()))


if __name__ == "__main__":
    unittest.main()