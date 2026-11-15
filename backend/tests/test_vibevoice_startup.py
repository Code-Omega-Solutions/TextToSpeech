from fastapi.testclient import TestClient

from app.main import create_app


def prepare_macos_readiness(monkeypatch):
    monkeypatch.setattr("app.routers.shutil.which", lambda _path: "/fake/executable")
    monkeypatch.setattr(
        "app.routers.available_codecs",
        lambda *_args, **_kwargs: {"libmp3lame", "pcm_s16le"},
    )
    monkeypatch.setattr(
        "app.routers.available_voices",
        lambda *_args, **_kwargs: {"Anna", "Samantha"},
    )


def test_readiness_does_not_require_optional_worker_assets(settings, monkeypatch):
    prepare_macos_readiness(monkeypatch)
    app = create_app(settings)
    response = TestClient(app).get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["x-vibevoice-status"] == "disabled"


def test_missing_worker_assets_are_reported_without_blocking_readiness(
    settings_factory, monkeypatch
):
    prepare_macos_readiness(monkeypatch)
    settings = settings_factory(
        vibevoice_enabled=True,
        vibevoice_qualified=True,
        vibevoice_worker_peak_memory_bytes=100,
        higher_priority_memory_reserve_bytes=50,
    )
    response = TestClient(create_app(settings)).get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["x-vibevoice-status"] == "unavailable"


def test_application_shutdown_stops_optional_worker(settings, monkeypatch):
    prepare_macos_readiness(monkeypatch)
    app = create_app(settings)
    stopped = []
    monkeypatch.setattr(app.state.speech_service.vibevoice_worker, "stop", lambda: stopped.append(True))

    with TestClient(app) as client:
        assert client.get("/readyz").status_code == 200
        assert stopped == []

    assert stopped == [True]


def test_application_shutdown_terminates_a_resident_worker(settings):
    app = create_app(settings)

    class ResidentProcess:
        returncode = None
        terminated = False

        def poll(self):
            return self.returncode

        def terminate(self):
            self.terminated = True
            self.returncode = -15

        def wait(self, timeout=None):
            return self.returncode

    process = ResidentProcess()
    app.state.speech_service.vibevoice_worker._process = process
    with TestClient(app):
        assert process.terminated is False
    assert process.terminated is True
