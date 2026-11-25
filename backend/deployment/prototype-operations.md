# Historical prototype-only macOS operations

> **Historical deployment record:** This Fish-era runbook is retained for its
> exact-label, bounded-wait, protected-copy, and rollback safeguards. Its
> project-specific prototype procedure is not a current deployment guide and
> does not configure or authorize Phonon. Do not inspect or change a target
> service based on this document.

This runbook is intentionally sanitized. Replace angle-bracketed values only
on the authorized native target; never commit the replacements. The commands
below are one bounded, idempotent sequence: an already-unloaded label is not
treated as an error, and no bootstrap is attempted until `launchctl print`
confirms that the exact label is absent.

## Capture fallback diagnostics

For the serving launchd backend running `python -m app.main`, set
`StandardOutPath` and `StandardErrorPath` in its plist to distinct files in an
operator-owned `0700` directory. Precreate the files with mode `0600`. Back up
the original plist privately and validate the edited plist before unloading and
bootstrapping only the serving label. Preserve its environment and arguments.

The application writes INFO request diagnostics to stderr. On successful
fallback, match the response's `X-Request-ID` to the `speech request` line to
see the requested engine, actual engine, and the same safe reason as
`X-Speech-Fallback-Reason`. Check that a read-only health request appears in
the log before relying on it. Protect and rotate the log files under the
host's operator retention policy. To undo the change, restore the original
plist and reload only that label.

## Safety preflight and bounded helpers

Run the following in one POSIX shell with `set -eu`. Do not replace the exact
labels with a wildcard, a process name, or a port-only match.

```sh
set -eu

DOMAIN="gui/$(id -u)"
WAIT_ATTEMPTS=40
WAIT_SECONDS=0.25

is_loaded() {
  launchctl print "$DOMAIN/$1" >/dev/null 2>&1
}

wait_absent() {
  label="$1"
  attempt=1
  while is_loaded "$label"; do
    if [ "$attempt" -ge "$WAIT_ATTEMPTS" ]; then
      printf '%s\n' "exact launch label did not unload within 10 seconds" >&2
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
      printf '%s\n' "exact launch label did not load within 10 seconds" >&2
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
```

`bootout_if_loaded` is deliberately conditional. This fixes the common
recreation failure where `bootout` returns nonzero for a label that is already
unloaded; it still fails closed if the label remains present after the
bounded wait. Never continue after a wait timeout.

## Remove stale unmanaged startup

1. Record the managed production label and do not pass it to any command below.
2. List the user launch agents and identify the stale prototype definition by
   its prototype-only label and port 8001. Do not infer identity from a process
   name alone.
3. Use the exact label and exact plist path identified in step 2. The operation
   is safe to repeat after the stale file has already been quarantined:

   ```sh
   LEGACY_LABEL="<LEGACY_PROTOTYPE_LABEL>"
   LEGACY_PLIST="<LEGACY_PLIST>"
   LEGACY_QUARANTINE="${LEGACY_PLIST}.quarantined"

   if [ -e "$LEGACY_PLIST" ]; then
     assert_regular_file "$LEGACY_PLIST"
     launchctl disable "$DOMAIN/$LEGACY_LABEL"
     bootout_if_loaded "$LEGACY_LABEL"
     launchctl print-disabled "$DOMAIN" |
       grep -F "$LEGACY_LABEL" | grep -F "=> disabled" >/dev/null
     [ ! -e "$LEGACY_QUARANTINE" ] || {
       printf '%s\n' "stale quarantine destination already exists" >&2
       exit 1
     }
     mv "$LEGACY_PLIST" "$LEGACY_QUARANTINE"
   else
     [ -e "$LEGACY_QUARANTINE" ] || {
       printf '%s\n' "stale plist is neither loadable nor quarantined" >&2
       exit 1
     }
     if is_loaded "$LEGACY_LABEL"; then
       printf '%s\n' "quarantined stale label is still loaded" >&2
       exit 1
     fi
     launchctl print-disabled "$DOMAIN" |
       grep -F "$LEGACY_LABEL" | grep -F "=> disabled" >/dev/null
   fi

   [ ! -e "$LEGACY_PLIST" ]
   [ -e "$LEGACY_QUARANTINE" ]
   ```

4. Confirm that the legacy label is disabled, its `.plist` is no longer in the
   loadable launch-agent directory, and no unmanaged listener owns the
   prototype port. The quarantine suffix must not end in `.plist`, so a future
   login scan cannot load the stale definition. Do not stop or reload the
   production label.

If the legacy label, port ownership, or disabled state cannot be verified,
stop. Do not use a broad `kill`, process-name termination, or wildcard
`launchctl` command.

## Deterministic prototype/UI recreation

Use the checked-in executable
`backend/deployment/prototype-recreation.zsh` as the exact bounded sequence.
It accepts only this explicit managed identity pair:

```text
backend label: com.example.private-speech-studio-prototype
backend plist: com.example.private-speech-studio-backend.plist
UI label:      com.example.private-speech-studio-ui
UI plist:      com.example.private-speech-studio-ui.plist
```

The helper also reads each plist's `Label` key and rejects a mismatch. Set the
values below after preflight; never replace the labels with production, a
different label, or a wildcard:

```sh
export BACKEND_LABEL="com.example.private-speech-studio-prototype"
export UI_LABEL="com.example.private-speech-studio-ui"
export BACKEND_PLIST="<BACKEND_PLIST>"
export UI_PLIST="<UI_PLIST>"
zsh backend/deployment/prototype-recreation.zsh
```

The helper captures owner-only protected copies before booting out either
managed label, waits for exact-label absence before each bootstrap, waits for
both labels to return, and kickstarts only those labels. If `VERIFY_SCRIPT` is
set to an executable regular file, it runs after both services return; any
nonzero result leaves `rollback_required=1`, invokes protected-copy rollback,
and preserves the original failure status. Rollback copies each protected plist
to a temporary file, restores owner-only writable mode `0600`, and atomically
renames it over the destination, so a second forced rollback can replace a
destination left read-only by an older version. The `EXIT` trap uses the
portable `exit_code` variable rather than zsh's read-only `status` parameter.
On successful checks, the helper sets `rollback_required=0` and keeps the
recreated prototype/UI configuration.

Run the approved bounded checks through a private, uncommitted executable
`VERIFY_SCRIPT`: prototype readiness and authenticated native fallback, an
explicit `response_format=wav` request with a RIFF/container check, UI root and
opaque target selection, unauthorized configuration rejection, and production
health plus authenticated speech. Record only sanitized status and HTTP
outcomes. Never put credentials, target identities, paths, or generated audio
in that verifier or this repository.

The checked-in `test_prototype_recreation.zsh` runs the success path, two
consecutive forced-failure/rollback paths, mode and content checks, and an
unapproved-label rejection against fake launchctl state without touching
launchd or production. Run it with
`zsh backend/deployment/test_prototype_recreation.zsh` on a host with zsh
before using the operational helper.

Keep the deployment template native-only. Phonon remains disabled by default;
no endpoint, model, voice asset, or approval is supplied here. This historical
sequence does not qualify any model, codec, reference, generated output, or
current Phonon deployment.

## Rollback

The helper's `EXIT` trap is the protected rollback path. It boots out only the
two managed prototype labels, waits for both exact labels to disappear,
restores the protected copies, bootstraps them again, waits for both labels to
appear, and kickstarts only those labels. A wait timeout or
restore/bootstrap failure returns nonzero and stops; production remains
untouched throughout. If the shell is interrupted before the trap runs,
repeat the same `bootout_if_loaded`, bounded wait, restore, bootstrap, and
`wait_present` steps manually before doing any other operation.
