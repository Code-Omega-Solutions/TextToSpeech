from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.config import Settings
from app.routers import build_health_router, build_router
from app.services import SpeechService


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings.from_env()
    speech_service = SpeechService(configured)
    application = FastAPI(
        title="Bilingual macOS Speech Service",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.settings = configured
    application.state.speech_service = speech_service

    @application.middleware("http")
    async def request_logging(request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.monotonic()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            logging.getLogger(__name__).info(
                "http request request_id=%s method=%s path=%s duration_ms=%d status=%d",
                request_id,
                request.method,
                request.url.path,
                round((time.monotonic() - started) * 1000),
                status_code,
            )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "Invalid request."})

    application.include_router(build_health_router(configured))
    application.include_router(build_router(configured, speech_service))
    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=app.state.settings.host, port=app.state.settings.port)
