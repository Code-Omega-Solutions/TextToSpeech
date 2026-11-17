# Prototype-only macOS operations

This runbook is intentionally sanitized. Replace angle-bracketed values only
on the authorized native target; never commit the replacements.

## Remove stale unmanaged startup

The unload wait below is mandatory. A successful `bootout` command is not
enough: do not bootstrap or recreate a service until its exact label is absent
from `launchctl print`. The loop is deliberately bounded at 40 attempts
(250 ms each, 10 seconds total); a timeout is a stop condition.

1. Record the managed production label and do not pass it to any command below.
2. List the user launch agents and identify the stale prototype definition by
   its prototype-only label and port 8001. Do not infer identity from a process
   name alone.
3. Disable and quarantine the stale definition before recreating the managed
   one. Use the exact label and exact plist path identified in step 2:

   ```sh
   launchctl disable "gui/$(id -u)/<LEGACY_PROTOTYPE_LABEL>"
   launchctl bootout "gui/$(id -u)/<LEGACY_PROTOTYPE_LABEL>" 2>/dev/null || true
   for attempt in $(seq 1 40); do
     if ! launchctl print \
       "gui/$(id -u)/<LEGACY_PROTOTYPE_LABEL>" >/dev/null 2>&1; then
       break
     fi
     [ "$attempt" -lt 40 ] || {
       echo "legacy prototype did not unload within 10 seconds" >&2
       exit 1
     }
     sleep 0.25
   done
   launchctl print-disabled "gui/$(id -u)" |
     grep -F "<LEGACY_PROTOTYPE_LABEL>" | grep -F "=> disabled" >/dev/null
   mv "<LEGACY_PLIST>" "<LEGACY_PLIST>.quarantined"
   test ! -e "<LEGACY_PLIST>"
   test -e "<LEGACY_PLIST>.quarantined"
   ```

4. Confirm that the legacy label is disabled, its `.plist` is no longer in the
   loadable launch-agent directory, and no unmanaged listener owns the
   prototype port. The quarantine suffix must not end in `.plist`, so a future
   login scan cannot load the stale definition. Do not stop or reload the
   production label.

If the legacy label or its prototype-only port cannot be verified, stop. Do not
use a broad `kill`, process-name termination, or wildcard launchctl command.

## Deterministic prototype/UI recreation

Use protected, reviewed copies of the repository-managed backend and persistent
UI launch definitions. First capture each current managed definition for
rollback. Boot out only the prototype backend and UI labels, and wait for both
labels to disappear before bootstrapping either definition:

```sh
launchctl bootout "gui/$(id -u)/<MANAGED_PROTOTYPE_LABEL>"
launchctl bootout "gui/$(id -u)/<MANAGED_UI_LABEL>"
for label in "<MANAGED_PROTOTYPE_LABEL>" "<MANAGED_UI_LABEL>"; do
  for attempt in $(seq 1 40); do
    if ! launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then
      break
    fi
    [ "$attempt" -lt 40 ] || {
      echo "managed label did not unload within 10 seconds" >&2
      exit 1
    }
    sleep 0.25
  done
done
launchctl bootstrap "gui/$(id -u)" "<BACKEND_PLIST>"
launchctl bootstrap "gui/$(id -u)" "<UI_PLIST>"
launchctl kickstart -k "gui/$(id -u)/<MANAGED_PROTOTYPE_LABEL>"
launchctl kickstart -k "gui/$(id -u)/<MANAGED_UI_LABEL>"
```

Verify prototype readiness, authenticated native fallback, UI root, opaque
target selection, unauthorized configuration rejection, and production health
and authenticated speech before and after the operation. Only after exact
artifact terms and four-way consented references are accepted may the
prototype template be replaced with a reviewed Fish-enabled configuration.

## Rollback

If any prototype or UI check fails, boot out only the two managed prototype
labels, wait for both exact labels to disappear using the same bounded loop,
restore the protected copies, bootstrap them again, and repeat the same checks.
Do not continue after a wait timeout. Production remains untouched throughout.
Record only sanitized status and HTTP outcomes; never record host identities,
addresses, paths, credentials, raw inventories, or generated audio.
