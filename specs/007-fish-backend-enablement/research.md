# Fish Enablement Research

**Reviewed**: 2026-11-17
**Status**: Local policy design implemented; native runtime/artifact acceptance blocked

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
