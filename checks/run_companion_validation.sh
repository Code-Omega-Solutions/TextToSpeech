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
      tests/test_fish_worker_launcher.py \
      tests/test_fish_deployment_template.py \
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

if command -v zsh >/dev/null 2>&1; then
  zsh backend/deployment/test_prototype_recreation.zsh
else
  printf '%s\n' \
    "native zsh recreation tests unavailable in this environment; run them on the authorized macOS target" \
    >&2
fi