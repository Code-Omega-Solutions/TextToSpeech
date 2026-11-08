import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LicenseIntegrityTests(unittest.TestCase):
    def assert_text_contains(self, expected, actual):
        self.assertTrue(expected in actual, f"required publication text missing: {expected!r}")

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

    def test_distribution_inventory_preserves_each_component_boundary(self):
        notice_text = " ".join(
            (ROOT / "THIRD_PARTY_NOTICES.md")
            .read_text(encoding="utf-8")
            .split()
        )

        self.assert_text_contains("for project-owned materials only", notice_text)
        self.assert_text_contains("does not replace, extend, or relicense", notice_text)
        self.assert_text_contains("package/version/source inventory", notice_text)
        self.assert_text_contains("copyright files", notice_text)
        self.assert_text_contains("source offer", notice_text)
        self.assert_text_contains("macOS `/usr/bin/say`", notice_text)
        self.assert_text_contains("not included in this source tree", notice_text)

    def test_publication_documents_keep_legal_source_and_qualification_gates(self):
        backend_readme = " ".join(
            (ROOT / "backend/README.md").read_text(encoding="utf-8").split()
        )
        specs_readme = " ".join(
            (ROOT / "specs/README.md").read_text(encoding="utf-8").split()
        )
        notice_text = " ".join(
            (ROOT / "THIRD_PARTY_NOTICES.md")
            .read_text(encoding="utf-8")
            .split()
        )

        self.assert_text_contains("not evidence of native macOS qualification", backend_readme)
        self.assert_text_contains("does not authorize release", backend_readme)
        self.assert_text_contains("rights to recovered source", backend_readme)
        self.assert_text_contains("reachable history", specs_readme)
        self.assert_text_contains("legal approval", specs_readme)
        self.assert_text_contains("recovered-source rights", specs_readme)
        self.assert_text_contains("cannot recall copies already downloaded", notice_text)
        self.assert_text_contains("not legal advice", notice_text)


if __name__ == "__main__":
    unittest.main()
