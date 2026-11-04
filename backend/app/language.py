from collections.abc import Callable

from fastapi import HTTPException
import langid

from app.config import Settings
from app.models import SpeechRequest


def detect_language(text: str) -> str:
    detected, _score = langid.classify(text)
    if detected == "de":
        return "de-DE"
    if detected == "en":
        return "en-US"
    raise HTTPException(
        status_code=422,
        detail="Only German and English are supported; supply a supported language override.",
    )


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
        if detected in {"de-DE", "en-US"}:
            return detected
        if detected not in {"de", "en"}:
            raise HTTPException(
                status_code=422,
                detail="Only German and English are supported; supply a supported language override.",
            )
        return "de-DE" if detected == "de" else "en-US"
    return detect_language(request.input)
