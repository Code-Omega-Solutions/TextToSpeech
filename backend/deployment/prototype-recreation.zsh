#!/bin/zsh

# Recreate only the managed prototype backend and UI launch agents.
# This file is intentionally parameterized; do not commit target paths.

set -eu

DOMAIN="${DOMAIN:-gui/$(id -u)}"
WAIT_ATTEMPTS="${WAIT_ATTEMPTS:-40}"
WAIT_SECONDS="${WAIT_SECONDS:-0.25}"
MANAGED_BACKEND_LABEL="com.example.private-speech-studio-prototype"
MANAGED_UI_LABEL="com.example.private-speech-studio-ui"
MANAGED_BACKEND_PLIST_NAME="com.example.private-speech-studio-backend.plist"
MANAGED_UI_PLIST_NAME="com.example.private-speech-studio-ui.plist"

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

assert_plist_label() {
  path="$1"
  expected="$2"
  label="$(
    if command -v plutil >/dev/null 2>&1; then
      plutil -extract Label raw -o - "$path" 2>/dev/null || :
    fi
  )"
  if [ -z "$label" ]; then
    label="$(
      sed -n '/<key>Label<\/key>/{n;s#^[[:space:]]*<string>\([^<]*\)</string>.*#\1#p;}' \
        "$path"
    )"
  fi
  [ "$label" = "$expected" ] || {
    printf '%s\n' "plist label is not an approved managed identity" >&2
    return 1
  }
}

: "${BACKEND_LABEL:?BACKEND_LABEL is required}"
: "${UI_LABEL:?UI_LABEL is required}"
: "${BACKEND_PLIST:?BACKEND_PLIST is required}"
: "${UI_PLIST:?UI_PLIST is required}"

case "$BACKEND_LABEL:$UI_LABEL" in
  "$MANAGED_BACKEND_LABEL:$MANAGED_UI_LABEL") ;;
  *)
    printf '%s\n' "labels are not the approved managed prototype pair" >&2
    exit 1
esac
[ "$BACKEND_LABEL" != "$UI_LABEL" ] || {
  printf '%s\n' "backend and UI labels must be distinct" >&2
  exit 1
}

assert_regular_file "$BACKEND_PLIST"
assert_regular_file "$UI_PLIST"
[ "${BACKEND_PLIST:t}" = "$MANAGED_BACKEND_PLIST_NAME" ] || {
  printf '%s\n' "backend plist is not the approved managed definition" >&2
  exit 1
}
[ "${UI_PLIST:t}" = "$MANAGED_UI_PLIST_NAME" ] || {
  printf '%s\n' "UI plist is not the approved managed definition" >&2
  exit 1
}
assert_plist_label "$BACKEND_PLIST" "$BACKEND_LABEL"
assert_plist_label "$UI_PLIST" "$UI_LABEL"

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
fi
chmod u+r,u-wx,go-rwx "$PROTECTED_DIR/backend.plist" "$PROTECTED_DIR/ui.plist"
assert_plist_label "$PROTECTED_DIR/backend.plist" "$BACKEND_LABEL"
assert_plist_label "$PROTECTED_DIR/ui.plist" "$UI_LABEL"

restore_plist() {
  source="$1"
  destination="$2"
  temporary="${destination}.rollback.$$"
  [ ! -e "$temporary" ] && [ ! -L "$temporary" ] || {
    printf '%s\n' "rollback temporary destination already exists" >&2
    return 1
  }
  cp -p "$source" "$temporary" || return 1
  chmod u+rw,go-rwx "$temporary" || {
    rm -f "$temporary"
    return 1
  }
  mv -f "$temporary" "$destination" || {
    rm -f "$temporary"
    return 1
  }
  assert_regular_file "$destination"
}

rollback() {
  set +e
  bootout_if_loaded "$BACKEND_LABEL" || return 1
  bootout_if_loaded "$UI_LABEL" || return 1
  restore_plist "$PROTECTED_DIR/backend.plist" "$BACKEND_PLIST" || return 1
  restore_plist "$PROTECTED_DIR/ui.plist" "$UI_PLIST" || return 1
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
