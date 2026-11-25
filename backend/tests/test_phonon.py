from __future__ import annotations

import socket
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler

import pytest

from app.phonon import (
    PhononAudioTooLarge,
    PhononEngine,
    PhononFailure,
    PhononTimeout,
    PhononUnavailable,
)
from phonon_test_support import FakeOpener, FakeResponse, phonon_settings


def test_transport_disables_ambient_proxies_and_redirects(monkeypatch, settings_factory):
    import app.phonon as phonon

    captured = {}

    class OpenOnly:
        def open(self, *_args, **_kwargs):
            raise AssertionError("constructor must not contact the endpoint")

    def build_opener(*handlers):
        captured["handlers"] = handlers
        return OpenOnly()

    monkeypatch.setattr(phonon, "build_opener", build_opener)
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid")
    engine = PhononEngine(phonon_settings(settings_factory))

    proxy = next(handler for handler in captured["handlers"] if isinstance(handler, ProxyHandler))
    assert proxy.proxies == {}
    assert any(type(handler).__name__ == "_NoRedirect" for handler in captured["handlers"])
    assert engine.settings.phonon_enabled


def test_redirect_response_is_rejected_without_following_location(settings_factory):
    redirect = HTTPError(
        "http://127.0.0.1:11434/v1/audio/speech",
        302,
        "redirect",
        {"Location": "http://private.invalid"},
        None,
    )
    opener = FakeOpener([redirect])
    engine = PhononEngine(phonon_settings(settings_factory), opener=opener)

    with pytest.raises(PhononUnavailable):
        engine.synthesize_pcm("hello", "en-US", "fixture-en-voice")

    assert len(opener.calls) == 1


def test_pcm_response_reads_are_bounded(settings_factory):
    settings = phonon_settings(settings_factory, max_temp_bytes=48)
    opener = FakeOpener([FakeResponse(b"\x00\x00" * 3)])
    engine = PhononEngine(settings, opener=opener)

    with pytest.raises(PhononAudioTooLarge):
        engine.synthesize_pcm("hello", "en-US", "fixture-en-voice")

    assert opener.calls[0][0].get_method() == "POST"


def test_cancellation_is_checked_while_reading(settings_factory):
    import threading

    cancellation = threading.Event()
    reads = []

    def cancel_after_first_read():
        reads.append(True)
        cancellation.set()

    response = FakeResponse(b"\x00\x00" * 4, on_read=cancel_after_first_read)
    engine = PhononEngine(
        phonon_settings(settings_factory),
        opener=FakeOpener([response]),
    )

    with pytest.raises(PhononFailure):
        engine.synthesize_pcm(
            "hello",
            "en-US",
            "fixture-en-voice",
            cancel_event=cancellation,
        )

    assert reads
    assert response.closed


@pytest.mark.parametrize("error", [socket.timeout(), TimeoutError(), URLError(socket.timeout())])
def test_transport_timeout_is_mapped_without_endpoint_details(settings_factory, error):
    engine = PhononEngine(
        phonon_settings(settings_factory),
        opener=FakeOpener([error]),
    )

    with pytest.raises(PhononTimeout) as raised:
        engine.synthesize_pcm("private text", "en-US", "fixture-en-voice")

    assert "private text" not in str(raised.value)
    assert "127.0.0.1" not in str(raised.value)


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        (b"", "audio/pcm"),
        (b"\x00", "audio/pcm"),
        (b"\x00\x00", "application/json"),
    ],
)
def test_malformed_pcm_responses_fail_safely(settings_factory, body, content_type):
    engine = PhononEngine(
        phonon_settings(settings_factory),
        opener=FakeOpener([FakeResponse(body, content_type=content_type)]),
    )

    with pytest.raises(PhononUnavailable):
        engine.synthesize_pcm("private text", "en-US", "fixture-en-voice")
