#!/bin/zsh

# Recreate only the managed prototype backend and UI launch agents.
# This file is intentionally parameterized; do not commit target paths.

set -eu

DOMAIN="${DOMAIN:-gui/$(id -u)}"
WAIT_ATTEMPTS="${WAIT_ATTEMPTS:-40}"
WAIT_SECONDS="${WAIT_SECONDS:-0.25}"

is_loaded() {
  launchctl print "$DOMAIN/$1" >/dev/null 2>&1
}

wait_absent() {
  label="$1"
  attempt=1
  while is_loaded "$label"; do
    if [ "$attempt" -ge "$WAIT_ATTEMPTS" ]; then
      printf '%s\n' "exact launch label did not unload within the bounded wait" >&2
      return 1
    fi
    sleep "$WAIT_SECONDS"
    attempt=$((attempt + 1))
  done
}

wait_present() {
  label="$1"
  attempt=1
  while ! is_loaded "$label"; do
    if [ "$attempt" -ge "$WAIT_ATTEMPTS" ]; then
      printf '%s\n' "exact launch label did not load within the bounded wait" >&2
      return 1
    fi
    sleep "$WAIT_SECONDS"
    attempt=$((attempt + 1))
  done
}

bootout_if_loaded() {
  label="$1"
  if is_loaded "$label"; then
    launchctl bootout "$DOMAIN/$label"
  fi
  wait_absent "$label"
}

assert_regular_file() {
  [ -f "$1" ] && [ ! -L "$1" ] || {
    printf '%s\n' "expected a non-symlink plist" >&2
    return 1
  }
}

: "${BACKEND_LABEL:?BACKEND_LABEL is required}"
: "${UI_LABEL:?UI_LABEL is required}"
: "${BACKEND_PLIST:?BACKEND_PLIST is required}"
: "${UI_PLIST:?UI_PLIST is required}"

case "$BACKEND_LABEL:$UI_LABEL" in
  *production*)
    printf '%s\n' "production labels are outside this prototype-only operation" >&2
    exit 1
    ;;
esac
[ "$BACKEND_LABEL" != "$UI_LABEL" ] || {
  printf '%s\n' "backend and UI labels must be distinct" >&2
  exit 1
}

assert_regular_file "$BACKEND_PLIST"
assert_regular_file "$UI_PLIST"

if [ -n "${PROTECTED_DIR:-}" ] && [ -e "$PROTECTED_DIR" ]; then
  [ -d "$PROTECTED_DIR" ] && [ ! -L "$PROTECTED_DIR" ] || {
    printf '%s\n' "protected rollback directory is unsafe" >&2
    exit 1
  }
  assert_regular_file "$PROTECTED_DIR/backend.plist"
  assert_regular_file "$PROTECTED_DIR/ui.plist"
else
  if [ -n "${PROTECTED_DIR:-}" ]; then
    mkdir -p "$PROTECTED_DIR"
  else
    PROTECTED_DIR="$(mktemp -d "${TMPDIR:-/tmp}/tts-prototype-rollback.XXXXXX")"
  fi
  cp -p "$BACKEND_PLIST" "$PROTECTED_DIR/backend.plist"
  cp -p "$UI_PLIST" "$PROTECTED_DIR/ui.plist"
  chmod u-w,g-w,o-w "$PROTECTED_DIR/backend.plist" "$PROTECTED_DIR/ui.plist"
fi

rollback() {
  set +e
  bootout_if_loaded "$BACKEND_LABEL" || return 1
  bootout_if_loaded "$UI_LABEL" || return 1
  cp -p "$PROTECTED_DIR/backend.plist" "$BACKEND_PLIST" || return 1
  cp -p "$PROTECTED_DIR/ui.plist" "$UI_PLIST" || return 1
  launchctl bootstrap "$DOMAIN" "$BACKEND_PLIST" || return 1
  launchctl bootstrap "$DOMAIN" "$UI_PLIST" || return 1
  wait_present "$BACKEND_LABEL" || return 1
  wait_present "$UI_LABEL" || return 1
  launchctl kickstart -k "$DOMAIN/$BACKEND_LABEL" || return 1
  launchctl kickstart -k "$DOMAIN/$UI_LABEL" || return 1
}

rollback_required=1
trap '
  exit_code=$?
  if [ "$rollback_required" -eq 1 ]; then
    rollback || exit_code=1
  fi
  rm -rf "$PROTECTED_DIR"
  exit "$exit_code"
' EXIT

bootout_if_loaded "$BACKEND_LABEL"
bootout_if_loaded "$UI_LABEL"
launchctl bootstrap "$DOMAIN" "$BACKEND_PLIST"
launchctl bootstrap "$DOMAIN" "$UI_PLIST"
wait_present "$BACKEND_LABEL"
wait_present "$UI_LABEL"
launchctl kickstart -k "$DOMAIN/$BACKEND_LABEL"
launchctl kickstart -k "$DOMAIN/$UI_LABEL"

if [ -n "${VERIFY_SCRIPT:-}" ]; then
  assert_regular_file "$VERIFY_SCRIPT"
  [ -x "$VERIFY_SCRIPT" ] || {
    printf '%s\n' "verification script must be executable" >&2
    exit 1
  }
  "$VERIFY_SCRIPT"
fi

rollback_required=0
