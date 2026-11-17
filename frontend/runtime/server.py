"""Dependency-free persistent UI server for the approved speech boundary.

The normal developer experience remains Vite.  This small runtime exists for
the macOS user-agent deployment where Node is intentionally not required.  It
serves the built assets and implements the same allowlisted, server-side
credential proxy as the Vite runtime.
"""

from __future__ import annotations

import hmac
import http.client
import json
import mimetypes
import os
import re
import secrets
import stat
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


MAX_PROXY_BODY_BYTES = 32 * 1024
MAX_PROXY_RESPONSE_BYTES = 100 * 1024 * 1024
ORIGIN_PATTERN = re.compile(
    r"^https?://([A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*|[0-9]{1,3}(\.[0-9]{1,3}){3})(:[0-9]{1,5})?$"
)
ROUTES = {
    "/api/healthz": ("GET", 10),
    "/api/readyz": ("GET", 15),
    "/api/v1/audio/engines": ("GET", 15),
    "/api/v1/audio/speech": ("POST", 75),
}
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class ConfigurationError(RuntimeError):
    """The operator did not provide a safe UI configuration."""


class RequestBodyError(ConfigurationError):
    """The client supplied a missing or oversized request body."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def validate_origin(value: str | None) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ConfigurationError("An approved HTTP(S) speech origin is required.")
    if not ORIGIN_PATTERN.fullmatch(value):
        raise ConfigurationError("Speech origins must not contain paths or credentials.")
    parsed = urlsplit(value)
    if parsed.path == "/":
        raise ConfigurationError("Speech origins must not contain paths or credentials.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ConfigurationError("Speech origin port is invalid.") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ConfigurationError("Speech origin port is invalid.")
    return value


def _env_origins(env: dict[str, str]) -> set[str]:
    raw = env.get("TTS_ALLOWED_UPSTREAMS") or env.get("TTS_UPSTREAM_URL")
    if not raw:
        raise ConfigurationError("TTS_UPSTREAM_URL is required.")
    return {validate_origin(item.strip()) for item in raw.split(",") if item.strip()}


def load_approved_targets(env: dict[str, str]) -> dict[str, dict[str, str]]:
    production = env.get("TTS_TARGET_PRODUCTION_URL") or env.get("TTS_UPSTREAM_URL")
    if not production:
        raise ConfigurationError("TTS_UPSTREAM_URL is required.")
    targets: object = {
        "production": {"label": "Production", "origin": production}
    }
    if env.get("TTS_PROTOTYPE_UPSTREAM_URL"):
        targets["prototype"] = {
            "label": "Prototype",
            "origin": env["TTS_PROTOTYPE_UPSTREAM_URL"],
        }
    if env.get("TTS_TARGETS_JSON") is not None:
        try:
            targets = json.loads(env["TTS_TARGETS_JSON"])
        except json.JSONDecodeError as exc:
            raise ConfigurationError("TTS_TARGETS_JSON must be valid JSON.") from exc
    if not isinstance(targets, dict) or not targets:
        raise ConfigurationError("TTS_TARGETS_JSON must be an object.")
    allowed = _env_origins(env)
    result: dict[str, dict[str, str]] = {}
    for identifier, value in targets.items():
        if (
            not isinstance(identifier, str)
            or not identifier
            or len(identifier) > 32
            or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in identifier)
            or not isinstance(value, dict)
        ):
            raise ConfigurationError("TTS_TARGETS_JSON contains an invalid target.")
        origin = validate_origin(value.get("origin"))
        if origin not in allowed:
            raise ConfigurationError("Every target must be operator-approved.")
        label = value.get("label")
        result[identifier] = {
            "label": label.strip() if isinstance(label, str) and label.strip() else identifier,
            "origin": origin,
        }
    return result


def endpoint_config_path(env: dict[str, str]) -> Path:
    return Path(env.get("TTS_ENDPOINT_CONFIG_FILE", "/var/lib/private-speech-studio/endpoint.json"))


def load_configured_origin(env: dict[str, str]) -> str:
    fallback = validate_origin(env.get("TTS_UPSTREAM_URL"))
    path = endpoint_config_path(env)
    if not path.exists():
        return fallback
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return validate_origin(payload["origin"])
    except (OSError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ConfigurationError("The endpoint configuration is corrupt or unreadable.") from exc


def save_configured_origin(origin: str, env: dict[str, str]) -> str:
    origin = validate_origin(origin)
    path = endpoint_config_path(env)
    temporary = path.with_name(f"{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        path.parent.chmod(0o700)
        temporary.write_text(json.dumps({"origin": origin}) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ConfigurationError("The endpoint configuration could not be saved.") from exc
    return origin


def read_proxy_credential(env: dict[str, str]) -> str:
    direct = env.get("TTS_API_KEY")
    path_value = env.get("TTS_API_KEY_FILE")
    if direct is not None and path_value is not None:
        raise ConfigurationError("Configure only one backend credential source.")
    if direct is not None:
        if not direct.strip() or "\r" in direct or "\n" in direct:
            raise ConfigurationError("The backend credential is invalid.")
        return direct
    if not path_value:
        raise ConfigurationError("A protected backend credential source is required.")
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path_value, flags)
        details = os.fstat(descriptor)
        uid = os.getuid() if hasattr(os, "getuid") else details.st_uid
        if (
            not stat.S_ISREG(details.st_mode)
            or details.st_uid != uid
            or details.st_mode & 0o077
            or details.st_size > 4096
        ):
            raise ConfigurationError("The backend credential file is unavailable or not protected.")
        value = os.read(descriptor, 4097).decode("utf-8").removesuffix("\n")
        if not value.strip() or "\r" in value or "\n" in value:
            raise ConfigurationError("The backend credential file is invalid.")
        return value
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError("The backend credential file is unavailable or not protected.") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


class _SessionTargets:
    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._lock = threading.Lock()

    def create(self, target: str) -> str:
        identifier = secrets.token_urlsafe(18)
        with self._lock:
            if len(self._values) >= 1024:
                self._values.pop(next(iter(self._values)))
            self._values[identifier] = target
        return identifier

    def get(self, identifier: str | None) -> str | None:
        if not identifier:
            return None
        with self._lock:
            return self._values.get(identifier)


class SpeechUIHandler(BaseHTTPRequestHandler):
    server_version = "PrivateSpeechStudio/1.0"

    @property
    def ui_server(self) -> "SpeechUIServer":
        return self.server  # type: ignore[return-value]

    def log_message(self, _format: str, *_args: object) -> None:
        # Do not log request paths, query strings, cookies, or upstream details.
        return

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_HEAD(self) -> None:
        self._dispatch("HEAD")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PUT(self) -> None:
        self._dispatch("PUT")

    def _dispatch(self, method: str) -> None:
        parsed = urlsplit(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self._api(method, path, parsed.query)
        else:
            if method not in {"GET", "HEAD"}:
                self._send_json(405, {"detail": "Method not allowed."})
            else:
                self._static(path, head=method == "HEAD")

    def _api(self, method: str, path: str, query: str) -> None:
        if path == "/api/targets":
            if method != "GET":
                self._send_json(403, {"detail": "Target discovery requires GET."})
                return
            targets, selected = self._selected_target()
            self._send_json(
                200,
                {
                    "targets": [
                        {"id": identifier, "label": value["label"]}
                        for identifier, value in targets.items()
                    ],
                    "selected": selected,
                },
            )
            return
        if path == "/api/target":
            if method != "POST":
                self._send_json(403, {"detail": "Target selection requires POST."})
                return
            try:
                payload = json.loads(self._read_body().decode("utf-8"))
                targets = load_approved_targets(self.ui_server.env)
                identifier = payload.get("id") if isinstance(payload, dict) else None
                if not isinstance(identifier, str) or identifier not in targets:
                    self._send_json(403, {"detail": "That target is not operator-approved."})
                    return
                session = self.ui_server.sessions.create(identifier)
                self.send_response(204)
                self.send_header("Set-Cookie", f"tts_target={session}; HttpOnly; SameSite=Lax; Path=/")
                self.end_headers()
            except RequestBodyError as exc:
                self._send_json(exc.status, {"detail": exc.detail})
            except (ConfigurationError, UnicodeError, json.JSONDecodeError):
                self._send_json(400, {"detail": "The target selection is invalid."})
            return
        if path == "/api/configuration":
            credential = self.ui_server.credential
            presented = self.headers.get("Authorization", "")
            if not credential or not hmac.compare_digest(
                presented.removeprefix("Bearer ").strip(), credential
            ):
                self._send_json(401, {"detail": "Operator authorization is required."})
                return
            if method == "GET":
                try:
                    load_configured_origin(self.ui_server.env)
                    self._send_json(200, {"configured": True})
                except ConfigurationError as exc:
                    self._send_json(503, {"detail": str(exc)})
                return
            if method != "PUT":
                self._send_json(403, {"detail": "Configuration requires GET or PUT."})
                return
            try:
                payload = json.loads(self._read_body().decode("utf-8"))
                origin = validate_origin(payload.get("origin") if isinstance(payload, dict) else None)
                if origin not in _env_origins(self.ui_server.env):
                    self._send_json(403, {"detail": "That destination is not operator-approved."})
                    return
                save_configured_origin(origin, self.ui_server.env)
                self._send_json(200, {"saved": True})
            except RequestBodyError as exc:
                self._send_json(exc.status, {"detail": exc.detail})
            except (ConfigurationError, UnicodeError, json.JSONDecodeError):
                self._send_json(400, {"detail": "The endpoint configuration is invalid."})
            return
        route = ROUTES.get(path)
        if route is None:
            self._send_json(404, {"detail": "Unknown API endpoint."})
            return
        expected_method, timeout = route
        if method != expected_method:
            self._send_json(403, {"detail": f"{expected_method} required."})
            return
        try:
            targets, _selected = self._selected_target()
            target_origin = targets[_selected]["origin"]  # type: ignore[index]
            body = self._read_body() if method == "POST" else b""
            self._proxy(target_origin, path.removeprefix("/api"), query, body, timeout)
        except RequestBodyError as exc:
            self._send_json(exc.status, {"detail": exc.detail})
        except ConfigurationError:
            self._send_json(503, {"detail": "The configured speech service is unavailable."})
        except (OSError, http.client.HTTPException):
            self._send_json(502, {"detail": "The configured speech service could not be reached."})

    def _selected_target(self) -> tuple[dict[str, dict[str, str]], str]:
        targets = load_approved_targets(self.ui_server.env)
        cookie = self.headers.get("Cookie", "")
        session = next(
            (
                item.split("=", 1)[1]
                for item in cookie.split(";")
                if item.strip().startswith("tts_target=")
            ),
            None,
        )
        selected = self.ui_server.sessions.get(session)
        if selected in targets:
            return targets, selected
        configured = load_configured_origin(self.ui_server.env)
        for identifier, value in targets.items():
            if value["origin"] == configured:
                return targets, identifier
        raise ConfigurationError("The configured speech service is not approved.")

    def _read_body(self) -> bytes:
        declared = self.headers.get("Content-Length")
        if declared is None or not declared.isdecimal():
            raise RequestBodyError(411, "A bounded request body is required.")
        size = int(declared)
        if size > MAX_PROXY_BODY_BYTES:
            raise RequestBodyError(413, "Request body exceeds the 32 KiB limit.")
        body = self.rfile.read(size)
        if len(body) != size:
            raise OSError("incomplete request body")
        return body

    def _proxy(self, origin: str, path: str, query: str, body: bytes, timeout: int) -> None:
        parsed = urlsplit(origin)
        connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        connection = connection_class(parsed.hostname, parsed.port, timeout=timeout)
        try:
            target = path + (f"?{query}" if query else "")
            headers = {"Authorization": f"Bearer {self.ui_server.credential}"}
            if body:
                headers["Content-Type"] = self.headers.get("Content-Type", "application/octet-stream")
                headers["Content-Length"] = str(len(body))
            connection.request("POST" if body else "GET", target, body=body or None, headers=headers)
            response = connection.getresponse()
            payload = response.read(MAX_PROXY_RESPONSE_BYTES + 1)
            if len(payload) > MAX_PROXY_RESPONSE_BYTES:
                self._send_json(502, {"detail": "The speech response exceeded the configured limit."})
                return
            self.send_response(response.status)
            for name, value in response.getheaders():
                if name.lower() not in HOP_BY_HOP_HEADERS and name.lower() != "set-cookie":
                    self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)
        finally:
            connection.close()

    def _static(self, path: str, *, head: bool) -> None:
        relative = "index.html" if path in {"", "/"} else path.removeprefix("/")
        root = self.ui_server.static_root.resolve()
        candidate = (root / relative).resolve()
        if root not in candidate.parents and candidate != root:
            self._send_json(404, {"detail": "Not found."})
            return
        if not candidate.is_file():
            self._send_json(404, {"detail": "Not found."})
            return
        payload = candidate.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(candidate))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        if not head:
            self.wfile.write(payload)

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


class SpeechUIServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], static_root: Path, env: dict[str, str]):
        self.static_root = static_root
        self.env = env
        self.credential = read_proxy_credential(env)
        self.sessions = _SessionTargets()
        super().__init__(address, SpeechUIHandler)


def main() -> None:
    env = dict(os.environ)
    root = Path(env.get("TTS_UI_ROOT", "dist")).resolve()
    if not root.is_dir():
        raise SystemExit("TTS_UI_ROOT is unavailable")
    host = env.get("TTS_UI_HOST", "127.0.0.1")
    try:
        port = int(env.get("TTS_UI_PORT", "5173"))
    except ValueError as exc:
        raise SystemExit("TTS_UI_PORT is invalid") from exc
    if not 1 <= port <= 65535:
        raise SystemExit("TTS_UI_PORT is invalid")
    load_approved_targets(env)
    load_configured_origin(env)
    server = SpeechUIServer((host, port), root, env)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
