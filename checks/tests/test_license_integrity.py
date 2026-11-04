import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LicenseIntegrityTests(unittest.TestCase):
    def test_license_keeps_requested_reuse_and_attribution_terms(self):
        license_text = " ".join((ROOT / "LICENSE").read_text(encoding="utf-8").split())

        self.assertIn("commercial and non-commercial purposes", license_text)
        self.assertIn("modify, prepare Derivative Works", license_text)
        self.assertIn(
            "Every Derivative Work must include a reasonably prominent statement",
            license_text,
        )
        self.assertIn(
            "This software is based on TextToSpeech by Code-Omega-Solutions.",
            license_text,
        )
        self.assertIn("not an OSI-approved license", license_text)

    def test_third_party_notice_keeps_audit_boundary_explicit(self):
        notice_text = " ".join(
            (ROOT / "THIRD_PARTY_NOTICES.md")
            .read_text(encoding="utf-8")
            .split()
        )

        self.assertIn("backend/uv.lock", notice_text)
        self.assertIn("frontend/package-lock.json", notice_text)
        self.assertIn("/usr/share/doc/*/copyright", notice_text)
        self.assertIn("SOURCE_OFFER.md", notice_text)
        offer_text = " ".join(
            (ROOT / "SOURCE_OFFER.md").read_text(encoding="utf-8").split()
        )
        self.assertIn("patrik.gfeller@code-omega.ch", offer_text)
        self.assertIn("at least three years", offer_text)
        self.assertIn("complete corresponding source code", offer_text)
        self.assertIn("any recipient", offer_text)
        self.assertTrue((ROOT / "NOTICE").is_file())


if __name__ == "__main__":
    unittest.main()
