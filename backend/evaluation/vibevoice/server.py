from __future__ import annotations

import hmac
import html
import secrets
import threading
from copy import deepcopy
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from evaluation.vibevoice.report import (
    load_report,
    resolve_audio_path,
    save_report,
    update_decision,
    update_rating,
)


DEFAULT_HOST = "127.0.0.1"


class RatingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: StrictInt = Field(ge=1, le=10)
    observation: str = Field(default="", max_length=4000)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["retain", "partially_retain", "remove", "seek_alternative"]
    rationale: str = Field(min_length=1, max_length=4000)


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def _local_review_page(page_name: str, session_token: str) -> HTMLResponse:
    page_path = Path(__file__).with_name(page_name)
    try:
        page = page_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail="The local evaluation review page is unavailable."
        ) from exc
    nonce = secrets.token_urlsafe(18)
    page = page.replace("__SESSION_TOKEN__", html.escape(session_token, quote=True))
    page = page.replace("__CSP_NONCE__", nonce)
    return HTMLResponse(
        page,
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; "
                f"script-src 'nonce-{nonce}'; "
                f"style-src 'nonce-{nonce}'; "
                "connect-src 'self'; "
                "media-src 'self' blob:; "
                "base-uri 'none'; "
                "form-action 'self'; "
                "frame-ancestors 'none'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


def create_app(report_path: str | Path, *, session_token: str) -> FastAPI:
    path = Path(report_path)
    if path.name != "report.json":
        raise ValueError("the report file must be named report.json")
    if not isinstance(session_token, str) or len(session_token) < 32:
        raise ValueError("session_token must contain at least 32 characters")
    load_report(path)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.report_path = path
    app.state.session_token = session_token
    app.state.report_lock = threading.RLock()
    app.state.listened_results = set()

    def authorize(request: Request, supplied_token: str | None) -> None:
        origin = request.headers.get("origin")
        if origin is None or not _is_same_origin(origin, str(request.base_url)):
            raise HTTPException(status_code=403, detail="A same-origin request is required.")
        if supplied_token is None or not hmac.compare_digest(
            supplied_token, app.state.session_token
        ):
            raise HTTPException(status_code=401, detail="A valid run session token is required.")

    def read_report() -> dict:
        try:
            return load_report(app.state.report_path)
        except (OSError, ValueError, PermissionError) as exc:
            raise HTTPException(status_code=500, detail="The local evaluation report is unavailable.") from exc

    def safe_report(report: dict) -> dict:
        safe = deepcopy(report)
        _remove_private_paths(safe)
        return safe

    @app.get("/listening-review", response_class=HTMLResponse)
    def get_listening_review() -> HTMLResponse:
        return _local_review_page("listening.html", app.state.session_token)

    @app.get("/results-summary", response_class=HTMLResponse)
    def get_results_summary() -> HTMLResponse:
        return _local_review_page("summary.html", app.state.session_token)

    @app.get("/api/run")
    def get_run(
        request: Request,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> dict:
        authorize(request, x_session_token)
        report = read_report()
        safe = safe_report(report)
        return {
            "run_id": report["run_id"],
            "created_at": report["created_at"],
            "state": report["state"],
            "configuration_ids": report["configuration_ids"],
            "sample_ids": report["sample_ids"],
            "configurations": safe["configurations"],
            "samples": safe["samples"],
            "results": safe["results"],
        }

    @app.get("/api/report")
    def get_report(
        request: Request,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> dict:
        authorize(request, x_session_token)
        return safe_report(read_report())

    @app.get("/api/audio/{sample_result_id}")
    def get_audio(
        sample_result_id: str,
        request: Request,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> FileResponse:
        authorize(request, x_session_token)
        report = read_report()
        try:
            audio_path = resolve_audio_path(report, sample_result_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Completed audio result was not found.") from exc
        app.state.listened_results.add(sample_result_id)
        media_type = "audio/wav" if audio_path.suffix.lower() == ".wav" else "application/octet-stream"
        return FileResponse(
            audio_path,
            media_type=media_type,
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    @app.put("/api/ratings/{sample_result_id}")
    def put_rating(
        sample_result_id: str,
        payload: RatingRequest,
        request: Request,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> dict:
        authorize(request, x_session_token)
        with app.state.report_lock:
            report = read_report()
            try:
                result = update_rating(
                    report,
                    sample_result_id,
                    payload.rating,
                    payload.observation,
                    listened=sample_result_id in app.state.listened_results,
                )
                save_report(report, app.state.report_path.parent)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail="Sample result was not found.") from exc
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="Sample result was not found.") from exc
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {key: value for key, value in result.items() if key != "audio_path"}

    @app.put("/api/decision")
    def put_decision(
        payload: DecisionRequest,
        request: Request,
        x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    ) -> dict:
        authorize(request, x_session_token)
        with app.state.report_lock:
            report = read_report()
            try:
                decision = update_decision(
                    report,
                    payload.outcome,
                    payload.rationale,
                )
                save_report(report, app.state.report_path.parent)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        return decision

    return app


def serve(report_path: str | Path, *, session_token: str, port: int = 8000) -> None:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    uvicorn.run(
        create_app(report_path, session_token=session_token),
        host=DEFAULT_HOST,
        port=port,
        access_log=False,
    )


def _is_same_origin(origin: str, base_url: str) -> bool:
    origin_parts = urlsplit(origin)
    base_parts = urlsplit(base_url)
    return (
        origin_parts.scheme == base_parts.scheme
        and origin_parts.netloc == base_parts.netloc
        and origin_parts.path in {"", "/"}
        and not origin_parts.query
        and not origin_parts.fragment
    )


def _remove_private_paths(value: dict | list) -> None:
    if isinstance(value, dict):
        private_keys = {
            "audio_path",
            "manifest_path",
            "output_directory",
            "intended_storage_volume",
            "adapter_identity",
        }
        for key in list(value):
            if key in private_keys or key.endswith("_path"):
                del value[key]
            else:
                child = value[key]
                if isinstance(child, (dict, list)):
                    _remove_private_paths(child)
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, (dict, list)):
                _remove_private_paths(child)
