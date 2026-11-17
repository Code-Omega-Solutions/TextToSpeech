#!/usr/bin/env bash
set -euo pipefail

case "${OSTYPE:-}" in
  msys*|cygwin*|win32*)
    uv run --directory backend --locked pytest -c pyproject.toml \
      tests/test_api.py \
      tests/test_config.py \
      tests/test_models.py \
      tests/test_services.py \
      tests/test_speech_contract.py \
      tests/test_engines.py \
      tests/test_fish_speech.py \
      tests/test_engine_catalog.py \
      tests/test_voices.py \
      tests/test_vibevoice_startup.py \
      tests/test_vibevoice_retirement.py \
      -k 'not credential_file and not empty_credential and not credential_symlink' \
      -q
    ;;
  *)
    uv run --directory backend --locked pytest -c pyproject.toml tests -q
    ;;
esac

TTS_UPSTREAM_URL=http://127.0.0.1:9 \
TTS_API_KEY=validation-only-placeholder \
  npm --prefix frontend test

python3 -m unittest discover -s checks/tests -v