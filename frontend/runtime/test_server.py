import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from server import (  # noqa: E402
    SpeechUIServer,
    ConfigurationError,
    load_approved_targets,
    load_configured_origin,
    save_configured_origin,
    validate_origin,
)


class _UpstreamHandler(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, _format, *_args):
        return

    def do_GET(self):
        self.__class__.calls.append((self.server.name, self.path, self.headers.get("Authorization")))
        body = json.dumps({"engine": self.server.name}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _upstream(name):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _UpstreamHandler)
    server.name = name
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _ui(tmp_path, production, prototype):
    production_origin = f"http://127.0.0.1:{production.server_address[1]}"
    prototype_origin = f"http://127.0.0.1:{prototype.server_address[1]}"
    env = {
        "TTS_UPSTREAM_URL": production_origin,
        "TTS_ALLOWED_UPSTREAMS": f"{production_origin},{prototype_origin}",
        "TTS_TARGETS_JSON": json.dumps(
            {
                "production": {"label": "Production", "origin": production_origin},
                "prototype": {"label": "Prototype", "origin": prototype_origin},
            }
        ),
        "TTS_API_KEY": "synthetic-ui-token",
        "TTS_ENDPOINT_CONFIG_FILE": str(tmp_path / "endpoint.json"),
    }
    root = tmp_path / "dist"
    root.mkdir()
    (root / "index.html").write_text("<main>Speech</main>", encoding="utf-8")
    server = SpeechUIServer(("127.0.0.1", 0), root, env)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, env


def _request(server, path, *, method="GET", body=None, headers=None):
    request = Request(
        f"http://127.0.0.1:{server.server_address[1]}{path}",
        method=method,
        data=body,
        headers=headers or {},
    )
    return urlopen(request)


def test_origin_and_target_configuration_is_operator_bounded(tmp_path):
    production, _ = _upstream("production")
    prototype, _ = _upstream("prototype")
    try:
        server, _thread, env = _ui(tmp_path, production, prototype)
        try:
            assert validate_origin("http://speech.example:8000") == "http://speech.example:8000"
            with pytest.raises(ConfigurationError):
                validate_origin("http://speech.example/path")
            targets = load_approved_targets(env)
            assert set(targets) == {"production", "prototype"}
            assert load_configured_origin(env) == targets["production"]["origin"]
            save_configured_origin(targets["prototype"]["origin"], env)
            assert load_configured_origin(env) == targets["prototype"]["origin"]
            assert json.loads((tmp_path / "endpoint.json").read_text())["origin"] == targets["prototype"]["origin"]
        finally:
            server.shutdown()
            server.server_close()
    finally:
        production.shutdown()
        prototype.shutdown()


def test_opaque_session_selection_and_privileged_configuration(tmp_path):
    _UpstreamHandler.calls.clear()
    production, _ = _upstream("production")
    prototype, _ = _upstream("prototype")
    server, _thread, env = _ui(tmp_path, production, prototype)
    try:
        targets = json.loads(_request(server, "/api/targets").read())
        assert targets == {
            "targets": [
                {"id": "production", "label": "Production"},
                {"id": "prototype", "label": "Prototype"},
            ],
            "selected": "production",
        }
        assert "127.0.0.1" not in json.dumps(targets)

        selection = _request(
            server,
            "/api/target",
            method="POST",
            body=b'{"id":"prototype"}',
            headers={"Content-Type": "application/json"},
        )
        cookie = selection.headers["Set-Cookie"].split(";", 1)[0]
        response = json.loads(
            _request(server, "/api/v1/audio/engines", headers={"Cookie": cookie}).read()
        )
        assert response == {"engine": "prototype"}
        assert _UpstreamHandler.calls[-1][2] == "Bearer synthetic-ui-token"

        with pytest.raises(HTTPError) as unauthorized:
            _request(server, "/api/configuration")
        assert unauthorized.value.code == 401
        configuration_headers = {
            "Authorization": "Bearer synthetic-ui-token",
            "Content-Type": "application/json",
        }
        with pytest.raises(HTTPError) as denied:
            _request(
                server,
                "/api/configuration",
                method="PUT",
                body=b'{"origin":"http://attacker.example"}',
                headers=configuration_headers,
            )
        assert denied.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        production.shutdown()
        prototype.shutdown()


def test_oversized_body_returns_one_bounded_client_error(tmp_path):
    production, _ = _upstream("production")
    prototype, _ = _upstream("prototype")
    server, _thread, _env = _ui(tmp_path, production, prototype)
    try:
        with pytest.raises(HTTPError) as error:
            _request(
                server,
                "/api/target",
                method="POST",
                body=b"x",
                headers={"Content-Length": str(32 * 1024 + 1)},
            )
        assert error.value.code == 413
    finally:
        server.shutdown()
        server.server_close()
        production.shutdown()
        prototype.shutdown()
