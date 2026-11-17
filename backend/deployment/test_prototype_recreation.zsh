#!/bin/zsh

# Exercise both EXIT-trap paths without touching launchd or production.

set -eu

SCRIPT_DIR="${0:A:h}"
RECREATION_SCRIPT="$SCRIPT_DIR/prototype-recreation.zsh"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/tts-prototype-recreation-test.XXXXXX")"

cleanup() {
  rm -rf "$TEST_ROOT"
}
trap cleanup EXIT

assert_file_contains() {
  grep -F "$2" "$1" >/dev/null
}

write_fake_launchctl() {
  local fake_bin="$1"
  local state_file="$2"
  local log_file="$3"
  local fail_verify="$4"

  mkdir -p "$fake_bin"
  print -r -- '#!/bin/sh' > "$fake_bin/launchctl"
  print -r -- 'set -u' >> "$fake_bin/launchctl"
  print -r -- 'state_file="$FAKE_LAUNCHCTL_STATE"' >> "$fake_bin/launchctl"
  print -r -- 'log_file="$FAKE_LAUNCHCTL_LOG"' >> "$fake_bin/launchctl"
  print -r -- 'printf "%s\n" "$*" >> "$log_file"' >> "$fake_bin/launchctl"
  print -r -- 'command_name="${1:-}"' >> "$fake_bin/launchctl"
  print -r -- 'case "$command_name" in' >> "$fake_bin/launchctl"
  print -r -- '  print)' >> "$fake_bin/launchctl"
  print -r -- '    label="${2##*/}"' >> "$fake_bin/launchctl"
  print -r -- '    grep -Fx "$label" "$state_file" >/dev/null' >> "$fake_bin/launchctl"
  print -r -- '    ;;' >> "$fake_bin/launchctl"
  print -r -- '  bootout)' >> "$fake_bin/launchctl"
  print -r -- '    label="${2##*/}"' >> "$fake_bin/launchctl"
  print -r -- '    grep -Fxv "$label" "$state_file" > "$state_file.tmp" || :' >> "$fake_bin/launchctl"
  print -r -- '    mv "$state_file.tmp" "$state_file"' >> "$fake_bin/launchctl"
  print -r -- '    ;;' >> "$fake_bin/launchctl"
  print -r -- '  bootstrap)' >> "$fake_bin/launchctl"
  print -r -- '    plist="$3"' >> "$fake_bin/launchctl"
  print -r -- '    label="$(sed -n "/<key>Label<\\/key>/{n;s#.*<string>\\([^<]*\\)</string>.*#\\1#p;}" "$plist")"' >> "$fake_bin/launchctl"
  print -r -- '    grep -Fx "$label" "$state_file" >/dev/null || printf "%s\n" "$label" >> "$state_file"' >> "$fake_bin/launchctl"
  print -r -- '    ;;' >> "$fake_bin/launchctl"
  print -r -- '  kickstart)' >> "$fake_bin/launchctl"
  print -r -- '    if [ "${FAKE_LAUNCHCTL_FAIL_KICKSTART:-0}" = 1 ] && [ ! -e "$FAKE_LAUNCHCTL_FAILED" ]; then' >> "$fake_bin/launchctl"
  print -r -- '      : > "$FAKE_LAUNCHCTL_FAILED"' >> "$fake_bin/launchctl"
  print -r -- '      exit 1' >> "$fake_bin/launchctl"
  print -r -- '    fi' >> "$fake_bin/launchctl"
  print -r -- '    ;;' >> "$fake_bin/launchctl"
  print -r -- '  *) exit 2 ;;' >> "$fake_bin/launchctl"
  print -r -- 'esac' >> "$fake_bin/launchctl"
  chmod +x "$fake_bin/launchctl"
  : > "$log_file"
  : > "$fail_verify"
}

write_plist() {
  local path="$1"
  local label="$2"
  print -r -- '<?xml version="1.0" encoding="UTF-8"?>' > "$path"
  print -r -- '<plist version="1.0"><dict>' >> "$path"
  print -r -- '<key>Label</key>' >> "$path"
  print -r -- '<string>'"$label"'</string>' >> "$path"
  print -r -- '</dict></plist>' >> "$path"
}

run_case() {
  local name="$1"
  local verifier_exit="$2"
  local case_root="$TEST_ROOT/$name"
  local fake_bin="$case_root/bin"
  local state_file="$case_root/state"
  local log_file="$case_root/launchctl.log"
  local failed_file="$case_root/failed"
  local backend_plist="$case_root/backend.plist"
  local ui_plist="$case_root/ui.plist"
  local verifier="$case_root/verify.sh"
  local original_backend original_ui result

  mkdir -p "$case_root"
  write_plist "$backend_plist" "com.example.private-speech-studio-prototype"
  write_plist "$ui_plist" "com.example.private-speech-studio-ui"
  print -r -- "com.example.private-speech-studio-prototype" > "$state_file"
  print -r -- "com.example.private-speech-studio-ui" >> "$state_file"
  original_backend="$(<"$backend_plist")"
  original_ui="$(<"$ui_plist")"

  print -r -- '#!/bin/sh' > "$verifier"
  if [ "$verifier_exit" -eq 0 ]; then
    print -r -- 'exit 0' >> "$verifier"
  else
    print -r -- 'printf "%s\n" "mutated" > "$BACKEND_PLIST"' >> "$verifier"
    print -r -- 'exit 1' >> "$verifier"
  fi
  chmod +x "$verifier"
  write_fake_launchctl "$fake_bin" "$state_file" "$log_file" "$failed_file"

  set +e
  PATH="$fake_bin:$PATH" \
    FAKE_LAUNCHCTL_STATE="$state_file" \
    FAKE_LAUNCHCTL_LOG="$log_file" \
    FAKE_LAUNCHCTL_FAIL_KICKSTART=0 \
    FAKE_LAUNCHCTL_FAILED="$failed_file" \
    BACKEND_LABEL="com.example.private-speech-studio-prototype" \
    UI_LABEL="com.example.private-speech-studio-ui" \
    BACKEND_PLIST="$backend_plist" \
    UI_PLIST="$ui_plist" \
    PROTECTED_DIR="$case_root/protected" \
    VERIFY_SCRIPT="$verifier" \
    zsh "$RECREATION_SCRIPT"
  result=$?
  set -e

  if [ "$verifier_exit" -eq 0 ]; then
    [ "$result" -eq 0 ] || return 1
  else
    [ "$result" -ne 0 ] || return 1
  fi
  [ ! -e "$case_root/protected" ] || return 1
  [ "$(cat "$backend_plist")" = "$original_backend" ] || return 1
  [ "$(cat "$ui_plist")" = "$original_ui" ] || return 1
  grep -Fx "com.example.private-speech-studio-prototype" "$state_file" >/dev/null
  grep -Fx "com.example.private-speech-studio-ui" "$state_file" >/dev/null
  if [ "$verifier_exit" -ne 0 ]; then
    assert_file_contains "$log_file" "bootout gui/"
    assert_file_contains "$log_file" "bootstrap gui/"
  fi
}

[ -x "$RECREATION_SCRIPT" ] || {
  printf '%s\n' "recreation helper must be executable" >&2
  exit 1
}
zsh -n "$RECREATION_SCRIPT"
run_case success 0
run_case forced-failure 1
printf '%s\n' "prototype recreation zsh success/forced-failure tests passed"
