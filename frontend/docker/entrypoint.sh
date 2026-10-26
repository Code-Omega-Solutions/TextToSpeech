#!/bin/sh
set -eu

if [ -z "${TTS_UPSTREAM_URL:-}" ]; then
    echo "TTS_UPSTREAM_URL is required; configure the authorized speech service origin." >&2
    exit 1
fi

if ! printf '%s\n' "$TTS_UPSTREAM_URL" | grep -Eq '^https?://([A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*|[0-9]{1,3}(\.[0-9]{1,3}){3})(:[0-9]{1,5})?$'; then
    echo "TTS_UPSTREAM_URL must be an HTTP(S) origin with no path, credentials, query, or fragment." >&2
    exit 1
fi

exec /docker-entrypoint.sh "$@"
