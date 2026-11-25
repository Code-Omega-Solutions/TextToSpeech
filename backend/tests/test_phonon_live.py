from __future__ import annotations

import os

import pytest

from app.config import Settings
from app.phonon import PhononEngine


pytestmark = pytest.mark.skipif(
    os.environ.get("TTS_PHONON_LIVE_QUALIFICATION") != "1",
    reason="explicit live qualification opt-in is required",
)


def test_live_english_and_german_use_only_preapproved_installed_models(monkeypatch):
    settings = Settings.from_env()
    if not settings.phonon_enabled or settings.phonon_approval is None:
        pytest.skip("Phonon is not explicitly enabled with a reviewed approval record")
    if not settings.phonon_server_url:
        pytest.skip("No explicitly configured local endpoint")
    engine = PhononEngine(settings)
    installed = engine.installed_models()
    required = set(settings.phonon_approval.models_by_language.values())
    assert required.issubset(installed), (
        "approved models must already be installed; this test never pulls assets"
    )
    for language in ("en-US", "de-DE"):
        voice = settings.phonon_approval.default_voices_by_language[language]
        pcm = engine.synthesize_pcm(
            "This is a short approved live qualification sample.",
            language,
            voice,
        )
        assert pcm
