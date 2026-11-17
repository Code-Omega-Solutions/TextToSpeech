from collections.abc import Callable

try:
    import langid
except ImportError:  # pragma: no cover - exercised by minimal target runtimes
    langid = None

from app.config import Settings
from app.models import SpeechRequest


def detect_language(text: str) -> str:
    if langid is None:
        return _fallback_language(text)
    detected, _score = langid.classify(text)
    return _resolve_detected_language(detected)


def _fallback_language(text: str) -> str:
    """Keep native fallback usable when the optional classifier is absent."""

    german_markers = {"der", "die", "das", "und", "nicht", "ist", "ich"}
    words = {word.casefold().strip(".,!?;:") for word in text.split()}
    return "de-DE" if words & german_markers else "en-US"


def _resolve_detected_language(detected: str) -> str:
    if detected in {"de", "de-DE"}:
        return "de-DE"
    return "en-US"


def resolve_language(
    request: SpeechRequest,
    settings: Settings,
    classifier: Callable[[str], str] | None = None,
) -> str:
    if request.language is not None:
        return request.language
    alphabetic_count = sum(character.isalpha() for character in request.input)
    if alphabetic_count < settings.min_detection_chars:
        return settings.default_language
    if classifier is not None:
        detected = classifier(request.input)
        return _resolve_detected_language(detected)
    return detect_language(request.input)
