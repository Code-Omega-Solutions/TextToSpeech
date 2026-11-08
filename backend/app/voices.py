from __future__ import annotations

import subprocess

from app.config import Settings


class VoiceInventoryError(Exception):
    """The host voice list could not be queried safely."""


class VoiceInventoryTimeout(VoiceInventoryError):
    """The host voice list did not respond before its timeout."""


def configured_voices(settings: Settings) -> dict[str, str]:
    return {
        "de-DE": settings.voice_de_de,
        "en-US": settings.voice_en_us,
        "en-GB": settings.voice_en_gb,
    }


def required_voices(settings: Settings) -> dict[str, str]:
    voices = configured_voices(settings)
    return {locale: voices[locale] for locale in ("de-DE", "en-US")}


def available_voices(say_path: str, timeout: float = 5.0) -> set[str]:
    try:
        result = subprocess.run(
            [say_path, "-v", "?"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise VoiceInventoryTimeout from exc
    except OSError as exc:
        raise VoiceInventoryError from exc
    if result.returncode != 0:
        raise VoiceInventoryError
    names: set[str] = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if fields:
            names.add(fields[0])
    return names


def voice_available(configured_name: str, available: set[str]) -> bool:
    if configured_name in available:
        return True
    # The documented German default includes the localized label as well as
    # the voice identifier that `say -v '?'` reports.
    identifier = configured_name.split(maxsplit=1)[0]
    return identifier in available


def resolve_voice(language: str, settings: Settings, available: set[str]) -> str:
    voice = configured_voices(settings)[language]
    if voice in available:
        return voice
    identifier = voice.split(maxsplit=1)[0]
    if identifier in available:
        return identifier
    raise LookupError(language)
