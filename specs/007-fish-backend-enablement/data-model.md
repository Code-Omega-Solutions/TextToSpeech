# Resource Policy Entities

## Optional worker configuration

Opt-in flag, reviewed local argv, loopback origin/credential, peak-memory budget,
host reserve, idle timeout, and restart cooldown. Defaults: policy off,
16 GiB worker budget, 12 GiB reserve, 30-second idle/cooldown. The managed policy
requires at least two overall request permits. Invalid or missing measurements
are denial, not zero memory consumption.

## Worker lifecycle

`stopped -> starting -> ready -> stopped`; pressure/failure leads to
`cooldown -> stopped`. A busy neural request denies another neural request but
does not deny native synthesis. The supervisor owns only its created process
group and must verify termination before allowing restart. No resident worker
memory is credited toward the host reserve.

## Synthesis result

Existing audio/media type/filename fields are unchanged. Native substitution
sets actual backend to `macos-say`, fallback to true, and a safe reason code.
Logs and discovery must not expose argv, paths, credentials, text or recordings.

## Reference assets

Remain gated, private external data. An approved runtime launcher must configure
local reference IDs and transcripts separately. Public Fish-cloud IDs are not
local assets; this feature's policy does not import them.
