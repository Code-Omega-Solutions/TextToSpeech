import pytest
from fastapi.testclient import TestClient

from app.engines import EngineDescriptor, EngineRegistration, EngineRegistry
from app.main import create_app


def test_engine_catalog_requires_bearer_auth(settings):
    response = TestClient(create_app(settings)).get("/v1/audio/engines")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("fish_runtime", ["pytorch", "mlx4"])
def test_engine_catalog_is_public_metadata_only(settings_factory, fish_runtime):
    settings = settings_factory(fish_runtime=fish_runtime)
    app = create_app(settings)
    app.state.speech_service.engine_registry = EngineRegistry(
        (
            EngineRegistration(
                EngineDescriptor(
                    "fish-speech",
                    ("de-DE", "en-US"),
                    {"de-DE": ("de-reference",), "en-US": ("en-reference",)},
                ),
                lambda: True,
                lambda: True,
                lambda *_args: None,
            ),
        )
    )

    response = TestClient(app).get(
        "/v1/audio/engines",
        headers={"Authorization": f"Bearer {settings.api_key}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "engines": [
            {
                "id": "fish-speech",
                "available": True,
                "fish_runtime": fish_runtime,
                "languages": ["de-DE", "en-US"],
                "voices": {"de-DE": ["de-reference"], "en-US": ["en-reference"]},
            }
        ]
    }
    assert "/private/" not in response.text
    assert settings.api_key not in response.text