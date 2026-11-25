from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.config import Settings, load_phonon_approval
from app.services import SpeechService, SynthesisUnavailable


def valid_approval_document():
    def model(tag):
        return {
            "tag": tag,
            "source_url": "https://models.invalid/source",
            "source_revision": "fixture-revision",
            "terms_url": "https://models.invalid/terms",
            "terms_revision": "fixture-terms-revision",
            "terms_status": "approved",
            "license": "fixture-only",
        }

    def voice(identifier):
        return {
            "ids": [identifier],
            "default": identifier,
            "source_url": "https://voices.invalid/source",
            "source_revision": "fixture-voice-revision",
            "terms_url": "https://voices.invalid/terms",
            "terms_revision": "fixture-voice-terms",
            "terms_status": "approved",
        }

    return {
        "status": "approved",
        "intended_use": "private-noncommercial",
        "models": {
            "en-US": model("fixture-model-en"),
            "de-DE": model("fixture-model-de"),
        },
        "voices": {
            "en-US": voice("fixture-en-voice"),
            "de-DE": voice("fixture-de-voice"),
        },
    }


def test_approval_loader_accepts_only_complete_operator_reviewed_fixture(tmp_path):
    approval_file = tmp_path / "approval.json"
    approval_file.write_text(json.dumps(valid_approval_document()), encoding="utf-8")
    approval_file.chmod(0o600)

    approval = load_phonon_approval(str(approval_file))

    assert approval is not None
    assert approval.models_by_language["en-US"] == "fixture-model-en"
    assert approval.voices_by_language["de-DE"] == ("fixture-de-voice",)


@pytest.mark.parametrize(
    "change",
    [
        lambda document: document.update(status="draft"),
        lambda document: document.pop("models"),
        lambda document: document["models"]["de-DE"].update(terms_status="unreviewed"),
        lambda document: document["voices"]["en-US"].update(ids=[]),
        lambda document: document["voices"]["de-DE"].update(default="not-listed"),
    ],
)
def test_incomplete_or_unapproved_record_is_fail_closed(tmp_path, change):
    document = valid_approval_document()
    change(document)
    approval_file = tmp_path / "approval.json"
    approval_file.write_text(json.dumps(document), encoding="utf-8")

    assert load_phonon_approval(str(approval_file)) is None


@pytest.mark.skipif(
    __import__("os").name == "nt",
    reason="This runner does not grant the Windows symlink privilege",
)
def test_approval_symlink_is_not_accepted(tmp_path):
    target = tmp_path / "approval.json"
    target.write_text(json.dumps(valid_approval_document()), encoding="utf-8")
    target.chmod(0o600)
    link = tmp_path / "approval-link.json"
    link.symlink_to(target)

    assert load_phonon_approval(str(link)) is None


def test_no_approval_never_attempts_endpoint_or_enables_engine(settings_factory):
    settings = settings_factory(
        phonon_enabled=True,
        phonon_server_url="http://127.0.0.1:11434",
        phonon_approval=None,
    )
    service = SpeechService(settings)
    calls = []
    service.phonon_engine._opener = lambda *_args, **_kwargs: calls.append(True)

    info = next(
        entry for entry in service.engine_registry.catalog() if entry["id"] == "phonon"
    )
    assert info == {
        "id": "phonon",
        "available": False,
        "languages": [],
        "voices": {},
    }
    with pytest.raises(SynthesisUnavailable):
        service.synthesize_reserved("hello", "en-US", 1, "wav", backend="phonon")
    assert calls == []


@pytest.mark.parametrize(
    "url",
    [
        "http://192.0.2.10:11434",
        "http://example.invalid",
        "http://127.0.0.1:11434/path",
        "http://user:pass@127.0.0.1:11434",
        "http://127.0.0.1:11434?token=secret",
    ],
)
def test_unsafe_phonon_endpoint_forms_are_rejected(monkeypatch, url):
    monkeypatch.setenv("TTS_API_KEY", "unit-test-api-key")
    monkeypatch.setenv("TTS_PHONON_SERVER_URL", url)

    with pytest.raises(ValidationError):
        Settings.from_env()
