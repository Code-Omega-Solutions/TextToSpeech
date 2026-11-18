# Resource Policy Entities

## Optional worker configuration

Opt-in flag, reviewed local argv, loopback origin/credential, peak-memory budget,
host reserve, idle timeout, and restart cooldown. Defaults: policy off,
16 GiB worker budget, 12 GiB reserve, 30-second idle/cooldown. The managed policy
also accepts an optional positive startup allowance no greater than the worker
budget; unset retains full-budget cold start. This admission estimate is
independent of the continuously enforced reserve and runtime RSS ceiling.
The managed policy requires at least two overall request permits.
Invalid or missing measurements
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

The approved catalog contains exactly four language-specific profiles:
`de-male`, `de-female`, `en-male`, and `en-female`. Each profile binds one
reference recording to its transcript and must satisfy:

- locale and public profile ID;
- language and dataset-declared gender category, without inferring identity;
- dataset ID, release, CC0 license, and accepted-agreement permission basis;
- private WAV and transcript paths plus their individual SHA-256 hashes;
- validated duration, sample format, transcript match, and listening-review
  status;
- private approval status and intended-use scope.

Keep dataset contributor identifiers, original archives, source transcripts,
accepted-agreement evidence, and selected reference audio outside the
repository. Do not derive a contributor's external identity or redistribute
source dataset files. Store references in a private data root separate from the
clean Fish source checkout; the worker uses this data root as its working
directory for Fish's relative `references/<id>` lookup. The operator's
noncommercial-use attestation and the accepted dataset terms must be recorded
privately and must not be presented as resolving the MDC restriction on
personal data in generated outputs.

## Generated audio sharing

Generated audio is a separate output from both model artifacts and source
references. Any output intended for downstream sharing must be disclosed as
machine-generated and must not contain personal data under the applicable MDC
terms. Because voice-conditioned synthesis may preserve identifiable speaker
characteristics, sharing remains disabled until that condition is reviewed;
the operator's consent attestation does not override the platform terms.
