from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import Settings
from app.routers import build_health_router, build_router
from app.services import SpeechService


_MAX_REQUEST_BODY_BYTES = 32 * 1024
_SAFE_HTTP_PATHS = {"/healthz", "/readyz", "/v1/audio/speech"}


class RequestBoundaryMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.monotonic()
        status_code = 500
        path = scope.get("path", "")
        safe_path = path if path in _SAFE_HTTP_PATHS else "/other"

        async def send_with_request_id(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", ()))
                if not any(name.lower() == b"x-request-id" for name, _ in headers):
                    headers.append((b"x-request-id", request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        async def reject(status: int, detail: str):
            body = ('{"detail":"' + detail + '"}').encode("utf-8")
            await send_with_request_id(
                {
                    "type": "http.response.start",
                    "status": status,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send_with_request_id(
                {"type": "http.response.body", "body": body, "more_body": False}
            )

        async def replay_body(body: bytes):
            pending = True

            async def replay_receive():
                nonlocal pending
                if pending:
                    pending = False
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            await self.app(scope, replay_receive, send_with_request_id)

        try:
            if path == "/v1/audio/speech" and scope.get("method") == "POST":
                content_lengths = [
                    value
                    for name, value in scope.get("headers", ())
                    if name.lower() == b"content-length"
                ]
                if len(content_lengths) > 1 and len(set(content_lengths)) > 1:
                    await reject(400, "Invalid request.")
                    return
                if content_lengths:
                    try:
                        declared_length = int(content_lengths[0])
                    except ValueError:
                        await reject(400, "Invalid request.")
                        return
                    if declared_length < 0:
                        await reject(400, "Invalid request.")
                        return
                    if declared_length > _MAX_REQUEST_BODY_BYTES:
                        await reject(413, "Request body exceeds the 32 KiB limit.")
                        return

                chunks = []
                body_size = 0
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    body_size += len(chunk)
                    if body_size > _MAX_REQUEST_BODY_BYTES:
                        await reject(413, "Request body exceeds the 32 KiB limit.")
                        return
                    chunks.append(chunk)
                    if not message.get("more_body", False):
                        break
                await replay_body(b"".join(chunks))
            else:
                await self.app(scope, receive, send_with_request_id)
        finally:
            logging.getLogger(__name__).info(
                "http request request_id=%s method=%s path=%s duration_ms=%d status=%d",
                request_id,
                scope.get("method", "UNKNOWN"),
                safe_path,
                round((time.monotonic() - started) * 1000),
                status_code,
            )


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

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "Invalid request."})

    application.include_router(build_health_router(configured))
    application.include_router(build_router(configured, speech_service))
    application.add_middleware(RequestBoundaryMiddleware)
    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=app.state.settings.host, port=app.state.settings.port)
