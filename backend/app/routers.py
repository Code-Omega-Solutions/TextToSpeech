from __future__ import annotations

import asyncio
import hmac
import logging
import shutil
import threading
import time

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.language import resolve_language
from app.models import SpeechRequest
from app.services import (
    AudioTooLarge,
    SpeechService,
    SynthesisCapacityExceeded,
    SynthesisFailure,
    SpeechSegmentLimitExceeded,
    SynthesisTimeout,
    SynthesisUnavailable,
    available_codecs,
)
from app.voices import (
    VoiceInventoryError,
    available_voices,
    required_voices,
    voice_available,
)


logger = logging.getLogger(__name__)
router = APIRouter()


def _authenticate(authorization: str | None, settings: Settings) -> None:
    if not settings.auth_enabled:
        return
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, separator, token = authorization.partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not token
        or settings.api_key is None
        or not hmac.compare_digest(token.encode("utf-8"), settings.api_key.encode("utf-8"))
    ):
        raise HTTPException(
            status_code=401,
            detail="A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def build_router(settings: Settings, speech_service: SpeechService) -> APIRouter:
    api = APIRouter()

    @api.post("/v1/audio/speech")
    async def create_speech(
        payload: SpeechRequest,
        request: Request,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> Response:
        started = time.monotonic()
        selected_language: str | None = None
        selected_backend = payload.model or settings.default_backend
        actual_backend = selected_backend
        failure_reason = "none"
        status_code = 500
        try:
            _authenticate(authorization, settings)
            selected_language = resolve_language(payload, settings)
            if selected_backend == "vibevoice":
                if not settings.vibevoice_enabled:
                    raise HTTPException(status_code=422, detail="Invalid request.")
                if payload.voice is not None:
                    voice_languages = {
                        "en-Carter_man": "en",
                        "de-Spk1_woman": "de",
                        "de-Spk0_man": "de",
                    }
                    voice_language = voice_languages.get(payload.voice)
                    if voice_language is None or not selected_language.startswith(voice_language):
                        raise HTTPException(status_code=422, detail="Invalid request.")
            if not speech_service.try_acquire():
                raise SynthesisCapacityExceeded
            cancel_event = threading.Event()
            try:
                synthesis = asyncio.create_task(
                    run_in_threadpool(
                        speech_service.synthesize_reserved,
                        payload.input,
                        selected_language,
                        payload.speed,
                        payload.response_format,
                        cancel_event,
                        selected_backend,
                        payload.voice,
                    )
                )
                try:
                    result = await asyncio.shield(synthesis)
                except asyncio.CancelledError:
                    cancel_event.set()
                    try:
                        await asyncio.shield(synthesis)
                    except Exception:
                        pass
                    raise
            finally:
                speech_service.release_permit()
            status_code = 200
            actual_backend = result.actual_backend
            failure_reason = result.failure_reason or "none"
            return Response(
                content=result.audio,
                media_type=result.media_type,
                headers={
                    "Content-Disposition": f'inline; filename="{result.filename}"',
                    "X-Content-Type-Options": "nosniff",
                    "X-Speech-Backend": result.actual_backend,
                    "X-Speech-Fallback": str(result.fallback).lower(),
                },
            )
        except HTTPException as exc:
            status_code = exc.status_code
            raise
        except SpeechSegmentLimitExceeded as exc:
            status_code = 422
            raise HTTPException(
                status_code=422,
                detail="Speech input must contain no more than 100 sentence segments.",
            ) from exc
        except AudioTooLarge as exc:
            status_code = 413
            raise HTTPException(
                status_code=413, detail="Generated audio exceeds the configured size limit."
            ) from exc
        except SynthesisCapacityExceeded as exc:
            status_code = 503
            raise HTTPException(status_code=503, detail="Speech synthesis capacity is unavailable.") from exc
        except SynthesisUnavailable as exc:
            status_code = 503
            raise HTTPException(status_code=503, detail="Speech synthesis is unavailable.") from exc
        except SynthesisTimeout as exc:
            status_code = 504
            raise HTTPException(status_code=504, detail="Speech generation exceeded its time limit.") from exc
        except SynthesisFailure as exc:
            status_code = 500
            failure_reason = type(exc).__name__
            logger.error(
                "speech synthesis failed request_id=%s error_type=%s",
                request.state.request_id,
                type(exc).__name__,
            )
            raise HTTPException(status_code=500, detail="Speech generation failed.") from exc
        except Exception as exc:
            status_code = 500
            failure_reason = type(exc).__name__
            logger.error(
                "speech synthesis failed request_id=%s error_type=%s",
                request.state.request_id,
                type(exc).__name__,
            )
            raise HTTPException(status_code=500, detail="An internal error occurred.") from exc
        finally:
            logger.info(
                "speech request request_id=%s duration_ms=%d backend=%s locale=%s format=%s reason=%s status=%d",
                request.state.request_id,
                round((time.monotonic() - started) * 1000),
                actual_backend,
                selected_language or "unresolved",
                payload.response_format,
                failure_reason,
                status_code,
            )

    return api


def build_health_router(settings: Settings, vibevoice_worker=None) -> APIRouter:
    health = APIRouter()

    @health.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @health.get("/readyz")
    async def readyz() -> Response:
        if settings.auth_enabled and not settings.api_key:
            return JSONResponse(status_code=503, content={"detail": "Authentication configuration unavailable."})
        if shutil.which(settings.say_path) is None:
            return JSONResponse(status_code=503, content={"detail": "say executable unavailable."})
        if shutil.which(settings.ffmpeg_path) is None:
            return JSONResponse(status_code=503, content={"detail": "ffmpeg executable unavailable."})
        try:
            codecs = await run_in_threadpool(available_codecs, settings.ffmpeg_path)
        except SynthesisUnavailable:
            return JSONResponse(status_code=503, content={"detail": "Audio codecs unavailable."})
        if not {"libmp3lame", "pcm_s16le"}.issubset(codecs):
            return JSONResponse(status_code=503, content={"detail": "Required audio codecs unavailable."})
        try:
            voices = await run_in_threadpool(available_voices, settings.say_path)
        except VoiceInventoryError:
            return JSONResponse(status_code=503, content={"detail": "Voice inventory unavailable."})
        needed_voices = required_voices(settings)
        if not all(
            voice_available(needed_voices[locale], voices) for locale in ("de-DE", "en-US")
        ):
            return JSONResponse(status_code=503, content={"detail": "Required speech voices unavailable."})
        return JSONResponse(
            status_code=200,
            content={"status": "ready"},
            headers={
                "X-VibeVoice-Status": (
                    vibevoice_worker.status if vibevoice_worker is not None else "disabled"
                )
            },
        )

    return health
