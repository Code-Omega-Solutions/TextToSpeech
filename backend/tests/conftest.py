import os
from dataclasses import replace

import pytest

from app.config import Settings


os.environ.setdefault("TTS_API_KEY", "unit-test-api-key")


@pytest.fixture
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture
def settings_factory(settings):
    def build(**overrides):
        return replace(settings, **overrides)

    return build
