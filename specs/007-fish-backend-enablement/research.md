# Fish Enablement Research

**Reviewed**: 2026-11-17
**Status**: Private four-voice managed inference observed with opt-in startup
allowance; broader lifecycle/quality qualification remains open

## Optimistic startup follow-up

The operator authorized a more aggressive, revisable cold-start threshold
relying on continued monitoring and yielding. The new positive
`TTS_FISH_STARTUP_MEMORY_BYTES` overrides only cold-start allowance and cannot
exceed the runtime worker budget. Unset retains conservative admission.
The isolated private prototype now uses 4 GiB startup allowance plus the
unchanged 12 GiB reserve (16 GiB total admission threshold), keeping the
16 GiB worker RSS ceiling, 0.25-second monitor and 30-second idle/cooldown.
This is an optimistic trial rather than a measured guarantee against spikes.

All four short synthetic reference selections now returned valid Fish WAV
with `X-Speech-Backend: fish-speech` and no fallback. The cold request took
27.01 seconds; subsequent requests took 8.07, 17.04 and 10.89 seconds.
Across 181 approximately half-second samples, minimum available memory was
13.08 GiB and peak owned-group RSS was 3.00 GiB. One worker group was observed;
after the idle window its listener and owned child session were absent.
These sampled values do not include a proven Metal allocation peak or qualify
long inputs, pressure termination, restart/cancellation, or subjective quality.
Production retained its listener identity and readiness.

The eight new cases failed before implementation; all 132 targeted native
tests then passed in a separate candidate tree before deployment. The local
Windows runner was blocked by an existing virtualenv `lib64` access error;
native verification used the already-installed locked environment instead.
Deployment initially encountered launchd's asynchronous unload/bootstrap
transition; the old prototype was restored, and the final cutover waited for
the exact old listener/label to disappear and bounded the bootstrap retry.
Only the designated prototype was restarted; no production definition changed.

## Earlier private enablement result (superseded by startup follow-up)

This supersedes the pending preparation state below. The operator listened to
all four converted WAVs, checked their transcripts, and explicitly approved
private evaluation. The exact four-profile reference manifest now validates;
assets and approval records remain private.

The two-file MPS patch was reviewed as token-tensor dtype matching. A separate
clean source snapshot preserves every tracked original working-tree file
byte-for-byte, including those changes, while leaving the original checkout
untouched. Its local revision is
`3a2287807c8379c13cd5a0eee30d8054eb6a3efe`, with upstream provenance
`7902e408c85b37193ce3f3c2361ca3c76be0d533`. The launcher validated the
deterministic source digest, all five previously recorded checkpoint hashes,
the runtime entrypoint and fixed MPS/half/offline loopback contract against an
owner-only approval manifest. Source terms remain Apache-2.0; the pinned model
card records CC BY-NC-SA 4.0 for model/decoder weights. The operator attests
requirements are fulfilled for private noncommercial use; this is not an
independent legal or redistribution clearance. The fresh card-access 403
limitation recorded earlier remains.

Native targeted tests passed (124 tests), and the clean source's API entrypoint
import/options check passed without starting inference. The authorized isolated
prototype and UI were switched to the staged build, retaining the shared backend
credential. Only the exact legacy prototype Fish service was disabled, unloaded
and quarantined; production retained its process identity, configuration hashes,
readiness and authenticated speech.

After legacy retirement, the deployed probe still measured about 17.3 GiB
available. Its real configured admission check returned `fish_memory_reserve`
against the unchanged 12 GiB reserve plus 16 GiB budget. Four authenticated
reference selections produced valid native WAV with fallback metadata, not
Fish output. Neither weights-inference compatibility, managed lifecycle nor
neural voice quality is qualified. Do not bypass this gate or stop unrelated
workloads. Detailed bounded results are in [quickstart.md](quickstart.md).

## Earlier private enablement preparation follow-up (superseded)

On 2026-11-18 the operator authorized enabling Fish in the isolated private
environment. The existing runtime passed an MPS token-dtype `torch.isin`
smoke check. Four candidate pairs were converted privately on the authorized
Mac into mono 44.1 kHz PCM16 WAV/UTF-8 transcript pairs and bound by hashes
in a draft manifest. Format, duration and owner-only permissions passed;
human listening/transcript review is still pending, so the manifest remains
unapproved and the catalog was not changed.

Both backend readiness checks remained HTTP 200 and production retained its
original process identity. No service or credential changes occurred. The
external legacy Fish listener remains present; it cannot be adopted by the
managed worker. Available memory with that worker resident was 17.34 GiB,
below the fixed 28 GiB cold-start admission threshold. Preparation does not
qualify a managed runtime or justify weakening the headroom policy.

## Headroom-First Follow-Up

The operator authorized a 12 GiB reserve and 16 GiB neural-worker budget first,
with native `say` fallback independent of neural engine/voice preference.
Investigate smaller Fish candidates before considering an 8 GiB reserve.
This supersedes strict neural-unavailability handling for the new opt-in policy,
not the default behavior of existing deployments.

[Fish Speech v1.5.0 README](https://github.com/fishaudio/fish-speech/blob/v1.5.0/README.md)
claims macOS, German/English and reference-based cross-language support. It
states Apache-licensed source and CC BY-NC-SA 4.0 model weights.
[Tagged inference documentation](https://github.com/fishaudio/fish-speech/blob/v1.5.0/docs/en/inference.md)
describes reference WAV/transcript assets, a checkpoint and a separate Firefly
codec. This makes 1.5 a screening lead, not evidence that a specific artifact
fits 16 GiB or meets local latency/quality targets.

Direct model-card and config retrieval from the authoritative weight host
returned 403, including a separate command-line fetch. No access restriction
was bypassed. Exact artifacts and terms remain unreviewed; no download or
installation is performed. The new model-independent supervisor can be
implemented and mocked without clearing those deployment gates.

The tagged [installation index](https://github.com/fishaudio/fish-speech/blob/v1.5.0/docs/en/index.md)
provides a macOS `--device mps` path and warns compilation is not officially
supported on Apple Silicon. Its generic inference guidance says 4 GB GPU
memory, not a measured total unified-memory peak. It also labels both source
and models CC BY-NC-SA 4.0, conflicting with the tagged README's source-license
claim. The tagged [LICENSE](https://github.com/fishaudio/fish-speech/blob/v1.5.0/LICENSE)
was subsequently fetched and is Apache 2.0, supporting the README's source
distinction; the installation warning is inconsistent/stale source guidance.
This does not clear the separately published weights or codec.

**Current decision**: Screen Fish 1.5 first. The earlier S2/Drama screening
decisions below are retained as history and alternatives, not the current
headroom-first runtime choice. No smaller candidate has yet been measured to
fit the budget, so the conditional weaker-reserve option has not been exercised.

## Model Candidate

**Decision**: Propose further screening of S2-Pro, not installation or enablement.

**Rationale**: The upstream README describes a 4B multilingual model supporting
reference-based voice cloning. Male and female German/English profiles do not
require four separate checkpoints. This does not establish local language
quality or hardware fitness.

**Alternatives considered**: Drama 3 is documented as 35B total/3B active with
at least 48 GB GPU memory in FP8 and NVIDIA-only operation in the upstream
runtime. That runtime is not proposed for this deployment class. The subsequent
MLX community-port finding below changes the screening options, not the
upstream runtime's requirements. Historical variants had not been reviewed in
that earlier screening; the 1.5 follow-up above now addresses that gap.

## Runtime

**Decision**: The operator fixed the target to an Apple Silicon Mac with 32 GiB
unified memory. Screen a community MLX runtime on that target, without installing
or enabling it. This supersedes the earlier Linux/NVIDIA deployment proposal.

**Rationale**: The upstream installation guide lists Linux/WSL and S2-Pro
NVIDIA or CPU operation with at least 24 GB GPU guidance. CPU support is not
evidence of acceptable latency or RAM use. Native Apple Silicon operation is
not established by that guide.

**New community evidence**: MLX-Audio's
[Drama 3 guide](https://github.com/Blaizzy/mlx-audio/blob/main/docs/models/tts/fish-drama3.md)
describes `mlx-community/fish-audio-drama-3-3bit` at roughly 18.5 GB on disk and
22.5-24 GB peak memory, explicitly intended to fit a 32 GB Mac. Its 4-bit build
is documented at roughly 22 GB on disk and 26 GB peak memory. Timing claims are
from an M3 Max, not this target; the reported quality comparison used 20 English
clips and does not qualify German pronunciation. The 3-bit build is a screening
candidate, not an approved artifact or capacity guarantee.

The guide describes MLX reference-audio generation, not compatibility with the
existing Fish `/v1/health` and MessagePack `/v1/tts` contract. Do not assume it
can replace the current adapter's server without an integration review.

**Alternatives considered**: Shared Linux CPU operation would need a bounded
capacity and workload-reserve plan. Native macOS operation would need separate
compatibility research and qualification. Neither has been approved for testing.
Absence of the NVIDIA diagnostic tool is not proof that no physical GPU exists.

Read-only inspection succeeded, but raw host inventory and private configuration
are intentionally omitted. Both existing speech listeners remained present.
No inference benchmark or load test was run.

## Voice References

**Decision**: Use two operator-supplied consented bilingual speakers, each with
German and English recordings and matching transcripts.

**Rationale**: This preserves the requested male/female identity across both
languages without assuming any community voice has cleared rights. Proposed
reference IDs are `de-male`, `de-female`, `en-male`, and `en-female`.

**Alternatives considered**: Four unrelated community voices were not selected.
Names of public speakers, model availability, or permission to listen to a
recording would not establish consent for voice cloning.

The operator subsequently requested community candidate discovery. The original
two-bilingual-speaker objective remains desired, but none of the candidates
below has established bilingual suitability or verified cloning consent.
No recordings, transcripts, or private consent evidence have been received.
Upstream's 10-30 second reference guidance is a vendor claim, not a measured
quality guarantee.

### Community Voice Shortlist

Fish pages could not be opened directly during this search. The following
names and descriptions come from indexed search snippets; destination links
were resolved through search-result redirects. These are audition leads, not
verified licenses, authentic speaker descriptions, or downloaded local assets.

| Intended profile | Community listing | Indexed description |
| --- | --- | --- |
| German male | [MALE GERMAN](https://fish.audio/m/b86c787cf5f6461f9536305e0280f004/) | Male German listing; audition for everyday announcements. |
| German female | [German female](https://fish.audio/m/54e57575c1fd47bfbdfae42c07903b95/) | German female listing; sample quality not assessed. |
| English male | [Everyday English Narrator](https://fish.audio/m/3e8337eb23ac4036a6b88d74d1ec5779/) | Indexed as male, middle-aged narration. |
| English female | [British Narrator](https://fish.audio/m/7aa4b4afe2574815a72ea7c20e3ca0a5/) | Indexed as female, middle-aged British narration. |

No evidence establishes that these are two bilingual speakers or that reference
audio and transcripts are exportable. A Fish cloud model ID is not a local
reference asset; passing it to a local inference server does not download the
associated voice. Do not synthesize with, scrape recordings from, or install
these listings without terms, provenance, and local-use review.

For locally usable reference material, a stronger German male screening lead is
[Thorsten-Voice](https://github.com/thorstenMueller/Thorsten-Voice): the creator
explicitly contributes his voice for TTS and publishes the
[44 kHz recording dataset](https://huggingface.co/datasets/Thorsten-Voice/TV-44kHz-Full)
as CC0. This is stronger source evidence, not final cloning/usage clearance or
proof that English cross-language generation sounds native.

Additional recording-source leads, not selected voices:

- [OpenSLR SLR83](https://www.openslr.org/83/) provides transcribed volunteer male
  and female English recordings under CC BY-SA 4.0. Select a speaker only after
  reviewing attribution, share-alike implications, and cloning consent.
- [LJ Speech](https://keithito.com/LJ-Speech-Dataset/) provides a single female
  English speaker with transcripts and a public-domain statement. Its 22.05 kHz,
  MP3-derived source is less attractive than clean full-bandwidth recordings.
  Public-domain recording status alone does not establish cloning consent.

No German female recording source with equally strong explicit TTS contribution
evidence was verified in this bounded search. Leave that slot unapproved rather
than invent a cleared voice or assume a celebrity/community clone is permitted.

## Terms and Revisions

**Decision**: Keep artifact acceptance blocked.

**Earlier S2/Drama rationale**: The source README distinguishes Fish Audio Community License
materials from S2-Pro weights under the Fish Audio Research License. Fetching
the S2-Pro model-card content returned HTTP 403. Full applicable checkpoint and
codec terms were not obtained, and no exact artifact revision was accepted.
Private noncommercial use alone does not clear these gates.

**Alternatives considered**: Do not infer weight permissions from the source
license, change models to avoid review, or treat a blocked document fetch as
successful review.

The public sources below were fetched from mutable upstream branches during
screening. Pin reviewed revisions and retrieve the authoritative full artifact
terms before any deployment decision.

## Public Sources

- [Fish Speech README](https://github.com/fishaudio/fish-speech/blob/main/README.md):
  model sizes, voice-reference guidance, and license distinction.
- [Installation guide](https://github.com/fishaudio/fish-speech/blob/main/docs/en/install.md):
  documented platform, accelerator, and memory guidance.
- [S2-Pro model card](https://huggingface.co/fishaudio/s2-pro):
  authoritative artifact review entry point; content retrieval was blocked.
- [Prior comparison](../005-selectable-speech-engines/fish-variant-comparison.md):
  earlier pinned comparison and unresolved approval gates.
- [MLX-Audio README](https://github.com/Blaizzy/mlx-audio/blob/main/README.md) and
  [Drama 3 runtime guide](https://github.com/Blaizzy/mlx-audio/blob/main/docs/models/tts/fish-drama3.md):
  community Apple Silicon runtime and quantization claims. Mutable source;
  exact release/commit and converted artifact terms remain to be pinned.

## Unresolved Inputs

- A qualified runtime on the confirmed Mac and an approved loopback integration
  compatible with the existing adapter.
- Exact pinned checkpoint, codec, and runtime revisions and applicable terms.
- Private bilingual speaker references, transcripts, and consent/provenance.
- Native measurements against the now-approved 12 GiB reserve/16 GiB budget,
  plus agreed listening acceptance thresholds.

These inputs block artifact installation, launcher/reference integration and
native evaluation, not the model-independent policy in [plan.md](plan.md).
The local design and task list deliberately leave those gated tasks open.

## Iteration 11 research and native evidence

The tagged Fish Speech v1.5.0 README and inference guide were re-reviewed from
their public GitHub sources. They state that the source is Apache-licensed,
model weights are CC BY-NC-SA 4.0, inference uses a separate Firefly decoder
checkpoint, and reference audio is paired with reference text. The guide's
workflow and the README's 10–30-second voice-sample guidance do not establish
speaker consent, bilingual identity, or a release decision for any local
recording. The authoritative exact model metadata remains unavailable from
this environment; no access restriction was bypassed and no weight was
downloaded.

FFmpeg's official legal page was re-reviewed. It distinguishes the default
LGPL terms from optional GPL/non-free components and lists source/build and
distribution obligations for redistribution. This is general codec guidance,
not an approval of the private target binary or a substitute for an immutable
codec revision and terms record. OpenSLR SLR83 was also re-reviewed: it
documents volunteer English dialect recordings, WAV/transcript data, and
Attribution-ShareAlike 4.0 terms. That provenance and dataset license still do
not establish cloning consent, bilingual identity, or the exact four
Fish-consumed pairs required by this feature. No reference manifest, voice ID,
or Fish output was created or advertised.

The authorized target was checked using the current prototype-only launcher,
native-only plist, and bounded zsh helper. Exact checked-in hashes and the
generated private plist hash are recorded in the iteration-11 quickstart, not
as artifact approval. The managed flags remain fail-closed and the worker
command remains absent. Native authenticated WAV fallback, browser playback,
protected-copy rollback, and production preservation passed; exact
artifact/codec/reference and managed-neural gates remain open.

## Iteration 12 rollback and deployment evidence boundary

The prototype-only helper was corrected locally to bind the exact managed
prototype/UI labels and plist names, validate each plist `Label`, and restore
protected copies through an atomic same-directory rename with owner-only
writable mode. Its fake-launchctl test now runs two consecutive forced
rollbacks and checks restored content and modes. The Companion validation
assertion uses the Git executable mode on Windows while retaining the native
zsh executable check.

No live deployment is claimed for this iteration. The current builder session
does not expose the authorized SSH target/path or deployment credential, so no
remote service, token, launchd definition, or production process was touched.
The historical iteration-11 runbook hash is explicitly superseded because it
does not identify the current checked-in runbook. Current hashes and rollback
evidence must be refreshed only after an independent authorized live run.
Exact runtime/model/codec terms, clean approved artifacts, four consented
reference pairs, Fish outputs, and managed-neural lifecycle evidence remain
unresolved; no access restriction or consent gap was bypassed.

## Iteration 10 fail-closed hardening evidence

The managed launcher now rejects any source checkout with tracked, untracked,
or ignored files, including the previously tolerated `references/` exception.
The approval manifest must be a non-symlink, non-group/world-writable POSIX
file and must bind the tracked `tools/api_server.py` entrypoint hash plus the
fixed loopback `tts`/MPS/one-worker/decoder contract. Model-tree coverage,
codec hashing, canonical relative paths, and source-tree hashing remain
independently checked before `exec`; no terms, model revision, codec revision,
or reference permission is inferred by this change. Focused launcher tests
cover dirty-source rejection and runtime-entrypoint mismatch.

The sanitized prototype runbook is now one idempotent bounded sequence. It
conditionally boots out only exact managed labels, waits up to 10 seconds for
each label to disappear before any bootstrap, captures owner-protected
prototype/UI copies, and uses an exit-trap rollback that restores those copies
if any subsequent check fails. Re-running after a successful stale quarantine
does not fail merely because the legacy label is already unloaded. The
sequence still preserves the non-`.plist` stale quarantine and excludes the
production label.

No new authorized native execution is claimed in this iteration: this builder
environment has no authorized SSH target/path available to run the sanitized
sequence, and no production or secret operation was attempted. The previous
independent run remains the authoritative evidence that the old unguarded
recreation snippet failed before rollback. Exact artifact/codec terms, a clean
approved source checkout, four consented WAV/`.lab` pairs, managed neural
outputs, and live lifecycle measurements remain blocked. Fish stays disabled
and no model, codec, reference, or terms were downloaded or fabricated.

## Iteration 9 authoritative and deployment evidence

The public, tagged Fish 1.5.0 README and inference guide were re-reviewed
through their GitHub sources. They document the source/model license
distinction, multilingual/reference-audio workflow, checkpoint layout, and
Firefly decoder path. The authoritative S2-Pro artifact page remained
unreadable with HTTP 403 from this environment. No alternate credentials,
mirror, scraping workaround, or access-control bypass was used.

The authorized target's local Fish source and checkpoint locations were
inspected without copying them into this repository. The source checkout is not
clean, and the local codec's runtime presence does not supply an immutable
codec revision or accepted terms. Therefore no exact approval manifest can
legitimately bind the clean source tree, every model file, the codec file, and
their applicable terms. The managed launcher and prototype configuration remain
fail-closed; no repository-managed Fish worker was enabled and no artifact was
downloaded.

Public reference research was also pursued without downloading or scraping
voice material. Thorsten-Voice documents an explicit German TTS contribution
and publishes a CC0 dataset, making it a strong German-male provenance lead.
It does not provide the requested two bilingual speakers or four exact
Fish-consumed WAV/`.lab` pairs. Other public recording datasets and Fish
community listings do not establish cloning consent, bilingual identity, or
exportable local references. No celebrity or community clone is approved.
The four-way reference manifest consequently remains absent.

The same authorized session identified one stale prototype launch definition
with the prototype port and automatic startup enabled. It was disabled by its
exact label, booted out with a bounded 10-second unload wait, and quarantined
under a non-`.plist` name. The persisted disabled state and absence of the
loadable file were verified. Protected managed backend/UI definitions were
recreated and restored with the same bounded wait; production health,
authenticated speech, and launchd process identity were preserved. This closes
the stale-startup/runbook defect only. It does not establish native neural
qualification, four Fish outputs, or managed neural lifecycle evidence.

## Iteration 7 approval and deployment evidence

The exact artifact gate was rechecked against authoritative public sources.
The pinned Fish source revision and tagged documentation remain readable and
identify Apache-2.0 source, CC BY-NC-SA 4.0 model weights, a separate Firefly
codec, and local WAV/transcript references. The authoritative model-card and
configuration endpoints still return HTTP 403 from this environment. No
restriction was bypassed, and no model or codec terms were inferred from the
source license. The exact model/codec approval manifest therefore remains
absent.

The repository-managed launcher now requires a local approval manifest before
it can exec. The manifest must pin source and model revisions, identify every
model file with a hash, match the codec hash, and record exact source/model/
codec terms. The prototype launch template sets both approval gates false,
does not provide a worker command or artifact roots, and keeps native fallback
available. Neural deployment is consequently disabled rather than accepted.

The voice review likewise remains unqualified. Thorsten-Voice provides strong
German male TTS-contribution and CC0 dataset evidence; OpenSLR SLR83 and
LJ Speech provide public recording/transcript terms but do not establish
explicit voice-cloning consent. None supplies the complete exact WAV/transcript
matrix with verified consent for German/English male/female use. No celebrity
or community voice is advertised, and no reference asset is committed.

No live native Fish output, managed-worker lifecycle, stale-launch-agent
cleanup, or prototype/UI recreation is claimed for this iteration. A future
authorized target session must disable the unmanaged prototype definition,
recreate only the managed prototype and persistent UI, and observe actual Fish
output (not fallback) plus admission, pressure, probe failure, cancellation,
deadline, cooldown, idle unload, cleanup, sampling, and native fallback before
acceptance. Production must remain untouched.

## Iteration 6 deployment evidence

The sanitized deployment record below supersedes the earlier "not deployed"
notes while preserving the unresolved approval gates. The designated target
was reached with the required non-interactive, key-authenticated SSH policy;
host identity, private paths, credentials, raw inventories, and audio files
remain out of this repository.

- The target is Apple Silicon macOS. Production remains on port 8000, the
  repository-managed prototype backend is on loopback port 8001, and the Fish
  worker contract is loopback-only on port 8002. The persistent UI is on its
  approved service boundary at port 5173. Production was not restarted,
  replaced, reconfigured, or terminated.
- The authorized local Fish source and checkpoint remain pinned to the
  previously recorded source/model revisions and SHA-256 values above. The
  deployed Python runtime reports 3.12.15. The local codec reports FFmpeg
  9.0.2; its build has neither non-free components nor the `--enable-gpl`
  configuration flag. FFmpeg's own license output includes component notices,
  and the authoritative [FFmpeg legal page](https://ffmpeg.org/legal.html)
  was consulted. This is sufficient for private, non-redistributed use only;
  a redistributable codec manifest is not claimed.
- The repository-managed launcher is active and runs one offline worker
  through the existing local Fish environment. Its admission policy requires
  the 12 GiB reserve plus the 16 GiB worker budget, rejects startup when the
  sampled available memory cannot satisfy both, and never adopts or terminates
  the pre-existing worker on port 8002. A Fish-selected request returned
  native `macos-say` audio with `X-Speech-Fallback: true`; the external worker
  listener identity was unchanged. This is live evidence of safe denial and
  language-preserving fallback, not evidence that neural admission fits.
- The UI is now a persistent dependency-free service with a launch-agent
  boundary. Browser verification selected the opaque `Prototype` target,
  generated playable native audio, and received HTTP 401 for an unauthorized
  operator configuration request. An unapproved target returned HTTP 403.
  Browser data exposed only `Production` and `Prototype`; origins and
  credentials stayed server-side. The production backend does not expose
  engine discovery, so its expected 404 is treated as service-default
  behavior; the prototype catalog is available.
- Prototype-only launch-agent recreation was exercised for both backend and UI.
  A protected rollback copy of both launch configurations was created before
  recreation. After recreation, the UI root, prototype readiness, prototype
  authenticated speech, production health, and production authenticated speech
  all returned HTTP 200. No production service was touched.

No reference voice is advertised by the deployed catalog. The exact
recording, transcript, provenance, and cloning-consent evidence for the
requested male/female German/English matrix is still absent, so the four-way
reference criterion remains blocked. No public listing or dataset license is
being treated as cloning consent. Subjective listening acceptance is likewise
pending operator review.

## Iteration 1 deployment gate

The newly designated deployment target was inspected with the existing
non-interactive, strict-host-key SSH policy. The authorized probe did not
establish a connection, so its operating system, service roles, free ports,
and native-fallback capability remain unknown. No host configuration was
changed and no production service was contacted or restarted. The existing
authorized Mac was likewise not reachable from this checkout.

The prototype policy now reuses the protected backend bearer credential for
Fish and for the frontend's privileged endpoint configuration authorization;
no separate Fish or operator token is required. This preserves an explicit
bearer check and the exact upstream allowlist. It does not constitute a live
deployment or native qualification.

## Iteration 5 live prototype evidence

**Recorded**: 2026-11-17. This section contains sanitized evidence from the
designated Apple Silicon deployment target. It intentionally omits the host
name, address, filesystem paths, bearer value, process inventories, and audio
artifacts.

Read-only discovery succeeded. The target is an Apple Silicon macOS host with
the existing production backend on port 8000 and an isolated prototype backend
on port 8001. Fish listens only on the prototype host's loopback port 8002.
The production listener remained running throughout; it was not restarted,
reconfigured, replaced, or terminated.

### Pinned artifacts and terms

The private prototype uses the following immutable public revisions:

- Fish source: `7902e408c85b37193ce3f3c2361ca3c76be0d533`.
- Fish model revision: `275a984d33c33659e39eed41ff5bcd6e67517f4c`.
- Model SHA-256: `918dc960372cc1b77bbafb14c48ef7a1634ecf75d4eb85b78607223b780d6001`.
- Codec SHA-256: `01b81dbf753224a156c3fe139b88bf0b9a0f54b11bee864f95e66511c3ccd754`.

The pinned source license is Apache-2.0. The upstream source documentation
states that model weights are CC BY-NC-SA 4.0. The model and codec remain
private, non-redistributed prototype artifacts; this repository does not
bundle them or make a redistribution claim. Codec release-term evidence is
still not suitable for a public artifact decision, so T004 remains open even
though the private deployment uses fixed hashes. No hosted inference or
unreviewed voice download was used.

### References and live outputs

The deployed catalog exposes only two reviewed public reference IDs:
`public-male-thorsten` (Thorsten-Voice's original TTS contribution, CC0
dataset source) and `public-female-slr83` (OpenSLR SLR83 volunteer recording,
CC BY-SA 4.0 source). They are private prototype screening references, not a
claim that either speaker is bilingual or that cross-language identity is
native. Cloning-consent and redistribution review remain open; T005 is not
closed.

Authenticated prototype requests returned HTTP 200 for all four combinations
below. Each response was mono, 44.1 kHz PCM WAV, reported
`X-Speech-Backend: fish-speech` and `X-Speech-Fallback: false`, and was
validated as playable WAV:

| Locale | Reference | Bytes | Audio | Elapsed |
| --- | --- | ---: | ---: | ---: |
| de-DE | public-male-thorsten | 397,356 | 4.50 s | 46.4 s |
| de-DE | public-female-slr83 | 340,012 | 3.85 s | 40.0 s |
| en-US | public-male-thorsten | 262,188 | 2.97 s | 31.8 s |
| en-US | public-female-slr83 | 385,068 | 4.37 s | 45.4 s |

These are synthetic checks only. No subjective listening acceptance was
performed, so pronunciation, completeness, and identity quality remain
pending. The prototype rejected an unauthenticated speech request with HTTP
401. Production health, readiness, and authenticated speech were successful
before and after the prototype rollout.

The standalone browser UI was verified through a local loopback proxy against
the two remote services because the target host has neither Docker nor Node.
The browser displayed opaque `Production` and `Prototype` choices, discovered
Fish and both references, submitted a German Fish request, and produced a
playable audio blob. An unauthorised privileged configuration request returned
HTTP 401. Browser text and resource URLs contained neither the backend origin
nor credentials. The proxy now forwards the request content type required by
FastAPI; its Windows standalone server also serves the root document correctly.

### Lifecycle and rollback boundary

The external loopback Fish worker is live, but it is not the repository's
managed `FishProcess` worker. A prototype-only pause of that owned worker
therefore produced the expected bounded HTTP 504 rather than a native fallback;
the worker was resumed and the prototype returned to HTTP 200 readiness and
Fish speech. Enabling opportunistic fallback is intentionally not claimed:
the backend requires a reviewed local managed-worker argv before enabling that
policy, and the external launcher does not provide one. No artificial memory
pressure was generated, no shared process was terminated, and no native
admission, idle unload, cooldown, cancellation, or RSS isolation claim is
made. T010 remains open.

Prototype launch-agent recreation and rollback were exercised only for the
prototype service. After restoring its original external-worker policy,
readiness and authenticated Fish speech returned HTTP 200. Production stayed
untouched. These results establish deployment and rollback evidence, not
completion of the remaining artifact, reference, or managed-lifecycle gates.

## Iteration 12: Exact artifacts and Common Voice datasets

The operator clarified four language-specific speakers (one female and one
male for each language), noncommercial use, private model/reference artifacts,
and noncommercial sharing of generated speech. The operator attests permission
for that intended voice use. The original two-bilingual-speaker preference is
superseded; no cross-language speaker identity is to be inferred.

### Fish artifact terms

The authorized Mac is reachable over the existing pinned SSH key. The installed
model and decoder hashes match the files listed by the exact Hugging Face model
revision
[`275a984d33c33659e39eed41ff5bcd6e67517f4c`](https://huggingface.co/fishaudio/fish-speech-1.5/tree/275a984d33c33659e39eed41ff5bcd6e67517f4c).
The revision's model card labels the model `CC-BY-NC-SA-4.0`, states the
noncommercial-only usage condition in its gated-use field, and applies its
license to the model weights. The Firefly decoder file is a weight in this
same pinned model repository and has the recorded hash below. This supports
reviewing it under the same model-weight terms; it is not an independent codec
license file.

- Fish source commit: `7902e408c85b37193ce3f3c2361ca3c76be0d533`
  (Apache-2.0 source).
- Model revision: `275a984d33c33659e39eed41ff5bcd6e67517f4c`;
  `model.pth` SHA-256:
  `918dc960372cc1b77bbafb14c48ef7a1634ecf75d4eb85b78607223b780d6001`.
- Firefly decoder SHA-256:
  `01b81dbf753224a156c3fe139b88bf0b9a0f54b11bee864f95e66511c3ccd754`.
- Exact card:
  [pinned model README](https://huggingface.co/fishaudio/fish-speech-1.5/blob/275a984d33c33659e39eed41ff5bcd6e67517f4c/README.md).
- Exact artifact listing:
  [pinned model revision files](https://huggingface.co/api/models/fishaudio/fish-speech-1.5/revision/275a984d33c33659e39eed41ff5bcd6e67517f4c).

The user confirmed use will be noncommercial. Model and decoder files remain
private and are not to be redistributed. CC BY-NC-SA requires attribution and
ShareAlike for adaptations that are shared. Whether voice-conditioned speech
outputs are adaptations is not established by the model card; do not make a
public licensing conclusion from the model license alone.

The installed Fish source checkout is at the pinned commit but has two local
modifications that cast semantic-token ID tensors to the existing tensor dtype
for MPS compatibility. Those changes are user work and were not reverted. The
exact source tree must be reviewed, tested, and hash-bound in the private
approval manifest before a managed worker can start.

### Common Voice reference data

The account holder reviewed and checked the same dataset-agreement flags for
both dataset downloads in MDC. Each card identifies CC0-1.0, has no additional
conditions and no special constraints, and forbids attempts to identify
speakers or re-host/re-share the dataset. The consumer terms additionally
require generated output to be disclosed as machine-generated and not to
contain personal data. Do not retain speaker identifiers in the approval
records, correlate a contributor with an external identity, or redistribute
dataset clips.

The selected source is the small spontaneous-speech release rather than the
34.82 GB German or 88.43 GB English scripted releases:

| Language | Dataset card | Release / format | Card summary |
| --- | --- | --- | --- |
| German | [Common Voice Spontaneous Speech 5.0](https://mozilladatacollective.com/datasets/cmu5mc2sn00s5mi07udtq2864) | `sps-corpus-5.0-2026-09-11`, MP3, 38.71 MB | 382 clips, 30 speakers, 108 transcribed and validated |
| English | [Common Voice Spontaneous Speech 5.0](https://mozilladatacollective.com/datasets/cmu5nqn1h00vwmi07b4dbk085) | `sps-corpus-5.0-2026-09-11`, MP3, 519.05 MB | 5,898 clips, 642 speakers, 2,474 transcribed and validated |

Both authorized archives are stored outside the repository in session-private
storage. The dataset files expose a `client_id` described as a hashed UUID and
optional self-declared gender. Local screening grouped clips only by that
dataset-provided pseudonymous field to find same-speaker segments; no IDs,
transcripts, or audio were emitted in logs or committed.

Initial non-identifying metadata screening found enough potential material in
each category. For candidates with a transcript, a positive transcript vote,
and a 5-to-30-second clip duration, the German archive has 4 female and 9 male
speaker groups; the English archive has 69 female and 51 male groups. These
are screening counts, not voice selections or quality approval. Exact clips
still need audio-quality/listening review, transcript matching, conversion to
the Fish WAV/`.lab` layout, and private hash records. Four preliminary
candidate MP3/`.lab` pairs (one per language and dataset-declared gender) have
since been extracted into session-private storage using duration, transcript
vote, and quality-tag metadata only. They have not been auditioned, transcript
reviewed, converted, or approved; they are not yet qualified references.

### Remaining release boundary

The user's permission attestation and dataset CC0 do not resolve whether a
voice-conditioned output is "personal data" under the MDC consumer terms.
Because Fish reference cloning intentionally carries speaker characteristics,
noncommercial sharing remains gated pending a defensible terms review. Local
private evaluation may prepare the references and test the isolated managed
runtime only after their exact per-clip approval record and model/source
manifest are complete; do not release or externally share generated samples
until that output constraint is resolved. Browser confirmations establish only
that the account holder checked the displayed agreements; they do not establish
broader rights or override the platform terms.

## Current implementation follow-up

The managed launcher now requires the reference root to be outside the pinned
Fish source checkout, revalidates the exact four-profile manifest at launch,
and runs Fish from the reference root with the approved source on `PYTHONPATH`.
This preserves Fish's relative reference lookup without placing private audio
in the source tree. The browser UI maps the four intended IDs to language and
gender labels and displays a machine-generated-audio disclosure; it does not
advertise those voices unless the authenticated backend catalog qualifies them.

The installed Fish checkout is at the pinned source commit. Its only tracked
changes are the two reported MPS-related patches: they construct semantic-token
ID tensors with the dtype of the existing token tensors in the embedding and
generation paths. The diff was reviewed, but no Fish-runtime or MPS test was
run; the modified checkout remains dirty and no source approval manifest was
created.

Local regression checks passed: 71 focused backend tests passed with 4
platform-specific skips, 27 additional catalog/service/deployment tests
passed, and the engine-discovery browser suite passed all 18 desktop/mobile
cases after a successful frontend build. These checks do not qualify the
modified upstream Fish source, approve the preliminary references, resolve the
MDC output restriction, or establish native macOS deployment or neural
qualification. T004, T005, T006, and T010 remain open.

## Documentation and local-asset separation

The operator approved a private companion repository for sanitized documentation
and public source metadata only, with restricted assets kept in local private
storage outside both checkouts. The companion was created privately with Actions,
issues, wiki and forking disabled; its initial tracked contents are an allowlist
ignore file, a preparation/storage README and an unapproved public-source index.
No recordings, transcripts, model weights, credentials or runtime approval files
were uploaded. The public [preparation guide](../../backend/voice-preparation.md)
explains authorized acquisition, local conversion and the existing approval gates.

The German dataset card was rechecked and still labels the data CC0-1.0 while
prohibiting re-hosting/re-sharing and attempts to identify speakers. Private
hosting therefore is not assumed to permit a dataset mirror. The local-only
asset boundary reduces accidental public disclosure and avoids a new dataset
upload, but does not settle voice-use rights, the MDC generated-output
personal-data condition, model terms, or native qualification. Existing runtime
and sharing gates remain unchanged.

### Authorized private checkpoint archival

The operator subsequently requested durable off-workstation archival and states
that license requirements are fulfilled for their private use. This is recorded
as an operator intended-use assessment, not an independent rights-clearance
verdict. Five non-sensitive checkpoint files (model, decoder, config, special
tokens and tokenizer) were copied unchanged to a private companion Release.
They total 1,466,157,080 bytes. Source-host and transfer-copy SHA-256 values match;
all seven Release assets, including checksum and archival-manifest files, also
match GitHub's server-reported SHA-256 digests and sizes. The private repository
contains exact upstream source/revision links, recorded licenses, attribution,
modification status, hashes, review limitations and restore instructions.

The exact model card/API returned HTTP 403 to this session during archival, so
the recorded weight-license basis remains the earlier exact-revision review.
No access restriction was bypassed. The model/decoder hashes match that prior
evidence; support-file hashes identify the installed bytes and were not newly
compared against upstream. This exception permits the explicitly authorized
checkpoint backup, not a dataset mirror. No voice data, transcripts, consent
records, credentials, actual approval manifest or private host configuration
was uploaded. Fish activation, complete voice restoration and native
qualification remain open; the archive is not an approved runtime.
