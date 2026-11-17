# Prototype-only macOS operations

This runbook is intentionally sanitized. Replace angle-bracketed values only
on the authorized native target; never commit the replacements.

## Remove stale unmanaged startup

1. Record the managed production label and do not pass it to any command below.
2. List the user launch agents and identify the stale prototype definition by
   its prototype-only label and port 8001. Do not infer identity from a process
   name alone.
3. Disable the stale definition before recreating the managed one:

   ```sh
   launchctl disable "gui/$(id -u)/<LEGACY_PROTOTYPE_LABEL>"
   launchctl bootout "gui/$(id -u)/<LEGACY_PROTOTYPE_LABEL>" 2>/dev/null || true
   ```

4. Confirm that the legacy label is disabled and that no unmanaged listener
   owns the prototype port. Do not stop or reload the production label.

If the legacy label or its prototype-only port cannot be verified, stop. Do not
use a broad `kill`, process-name termination, or wildcard launchctl command.

## Deterministic prototype/UI recreation

Use protected, reviewed copies of the repository-managed backend and persistent
UI launch definitions. First capture each current managed definition for
rollback, then boot out only the prototype backend and UI labels:

```sh
launchctl bootout "gui/$(id -u)/<MANAGED_PROTOTYPE_LABEL>"
launchctl bootout "gui/$(id -u)/<MANAGED_UI_LABEL>"
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
labels, restore the protected copies, bootstrap them again, and repeat the
same checks. Production remains untouched throughout. Record only sanitized
status and HTTP outcomes; never record host identities, addresses, paths,
credentials, raw inventories, or generated audio.
