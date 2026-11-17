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

if [ -z "${TTS_API_KEY_FILE:-}" ] || [ ! -f "$TTS_API_KEY_FILE" ] || [ -L "$TTS_API_KEY_FILE" ] || [ ! -r "$TTS_API_KEY_FILE" ]; then
    echo "A readable regular TTS_API_KEY_FILE secret is required." >&2
    exit 1
fi

credential_size=$(wc -c < "$TTS_API_KEY_FILE" | tr -d '[:space:]')
credential_lines=$(wc -l < "$TTS_API_KEY_FILE" | tr -d '[:space:]')
case "$credential_size:$credential_lines" in
    *[!0-9:]*|:*)
        echo "TTS_API_KEY_FILE is invalid." >&2
        exit 1
        ;;
esac
if [ "$credential_size" -gt 4097 ] || [ "$credential_lines" -gt 1 ]; then
    echo "TTS_API_KEY_FILE is invalid." >&2
    exit 1
fi

TTS_API_KEY=$(cat "$TTS_API_KEY_FILE")
newline='
'
carriage_return=$(printf '\r')
case "$TTS_API_KEY" in
    ""|*"$newline"*|*"$carriage_return"*)
        echo "TTS_API_KEY_FILE is invalid." >&2
        exit 1
        ;;
esac

umask 077
export TTS_API_KEY
unset TTS_API_KEY_FILE
export NGINX_ENVSUBST_FILTER='^(TTS_UPSTREAM_URL|TTS_API_KEY)$'
# Keep a syntactically valid Nginx configuration available for operators and
# diagnostics; the dynamic Node runtime below owns the live API routing.
/docker-entrypoint.sh nginx -t >/dev/null
exec node /runtime/server.js
