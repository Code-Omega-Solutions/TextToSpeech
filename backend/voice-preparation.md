# Prepare private Fish voice references

This guide describes local preparation, not permission to clone a voice or
enable Fish. No recordings, transcripts, model weights, speaker identifiers,
or real approval manifests are distributed with this project. The optional
Fish path remains gated; native macOS `say` does not need these assets.

## Separate documentation from assets

| Location | Contents |
| --- | --- |
| Public project | Application code, this guide, synthetic examples and public upstream links |
| Optional private companion repository | Reviewed, sanitized documentation, public source metadata, and explicitly authorized non-sensitive checkpoint backups with source/license/hash records |
| Local private storage outside both checkouts | Authorized archives, recordings, transcripts, weights, approval records and evaluation results |
| Protected credential storage | The existing backend token, never Git or browser assets |

A private GitHub repository is still hosted by another party and may be
accessible to organization members, administrators, apps and integrations.
Private visibility does not grant re-hosting, redistribution, or voice-use
rights. Do not upload voice datasets, recordings, transcripts, personal material,
credentials or unreviewed assets to either repository, Git LFS, releases,
packages, CI artifacts/caches, issues or attachments. An explicitly authorized
private checkpoint backup is separate: archive only permitted non-sensitive
model/decoder/support files, retain their source and license notices, and verify
the exact bytes with SHA-256. A `.gitignore`
cannot protect forced adds, already tracked files, Git history, or uploads
outside Git. Review staged changes before publishing.

The companion repository uses a default-deny ignore file for Git contents.
Large checkpoint backups may be stored as explicit private Release assets,
not in public Git history. It has no automatic asset sync, submodule, CI, or
deployment connection to this project. Each operator obtains authorized voice
data directly from its source and prepares it locally; restoring an archived
checkpoint does not authorize or approve a voice.

## Required external recovery archive

The repositories alone do not retain the voice datasets or reference candidates.
For the prepared installation, preserve the operator-created local archive
`TextToSpeech-recovery-inputs-2026-11-18.zip` and its adjacent `.zip.sha256`
file in the operator's private encrypted backup system. Do not upload either
the archive or its voice data to a repository or Release.

The archive contains both original Common Voice downloads, the five pinned Fish
checkpoint files, four preliminary MP3/`.lab` candidate pairs, source/license
notes, `RESTORE.md`, `MANIFEST.json` and `verify.py`. The ZIP itself is
unencrypted and must be treated as private. Preserve the recovery keys
independently, confirm backup completion and test restoring the archive.
After restoring and extracting into private storage outside Git, run
`python3 verify.py` from the extracted root before using any files.

This preserves downloaded inputs, not a fully rebuildable or offline system.
It excludes credentials, runtime source/MPS patches, dependency packages and
actual approvals; repository changes must also be committed/pushed separately.
The archived candidates do not carry subsequent local conversion or approval
records, and the original dataset metadata remains private even inside an
encrypted backup. Local backup is not voice-use or generated-output clearance.

## Review the exact terms first

Fish source, model/decoder weights, reference recordings and generated outputs
are separate review subjects:

- The reviewed Fish source commit is
  `7902e408c85b37193ce3f3c2361ca3c76be0d533`
  ([upstream source](https://github.com/fishaudio/fish-speech/tree/7902e408c85b37193ce3f3c2361ca3c76be0d533)).
  Local patches require their own review and an exact clean source-tree binding.
- Fish 1.5 model revision
  `275a984d33c33659e39eed41ff5bcd6e67517f4c`
  ([model card](https://huggingface.co/fishaudio/fish-speech-1.5/blob/275a984d33c33659e39eed41ff5bcd6e67517f4c/README.md))
  labels the weights CC BY-NC-SA 4.0. Review the exact model and decoder
  terms, noncommercial limitation, attribution and applicable ShareAlike
  obligations; do not assume the source license covers the weights or outputs.
- Common Voice Spontaneous Speech 5.0
  [German](https://mozilladatacollective.com/datasets/cmu5mc2sn00s5mi07udtq2864)
  and [English](https://mozilladatacollective.com/datasets/cmu5nqn1h00vwmi07b4dbk085)
  cards identify `sps-corpus-5.0-2026-09-11` and CC0-1.0, but also prohibit
  re-hosting/re-sharing the dataset and attempts to identify speakers.
  Their stated intended applications do not by themselves establish approval
  for voice cloning. Accept and review the current platform/download agreements
  directly; CC0 alone is not blanket clearance of privacy or personality rights.
- The previously reviewed MDC consumer terms require machine-generated output
  disclosure and outputs not containing personal data. Whether a
  voice-conditioned output meets that condition remains unresolved here.
  Keep external sharing gated pending appropriate clarification. Private storage
  and noncommercial intent do not answer that question.

Download only through the authorized upstream flow after accepting its terms.
Do not bypass gated downloads or identify contributors. If the intended use
is not permitted, use another authorized source or make new recordings with
appropriately scoped speaker permission; doing so still needs reference
qualification and may require a deliberate update to the current dataset-bound
validator. Do not fabricate Common Voice provenance for another source.

## Prepare the local layout

On the macOS runtime host, create an owner-only data root outside every Git
checkout, including the clean Fish source tree. Use an operator-selected
absolute location and restrict its parent as well. Keep encrypted backups
and retention/deletion rules appropriate to the data. The layout is:

```text
local-private-root/
  downloads/
  checkpoints/
  approvals/
  references/
    de-female/
      reference.wav
      reference.lab
    de-male/
      reference.wav
      reference.lab
    en-female/
      reference.wav
      reference.lab
    en-male/
      reference.wav
      reference.lab
  evaluation/
```

Only the four named directories belong under `references/`, and each must
contain exactly one WAV and its same-stem `.lab` transcript. Keep original
MP3s, archive metadata, draft manifests and evaluation files elsewhere.
Do not retain contributor identifiers in logs or Git, or correlate them with
external identities. Language/gender labels are local profile names, not an
assertion of a person's identity or bilingual capability.

## Convert and review four candidates

Select one suitable recording per requested language and dataset-declared
gender category. Metadata screening is not listening approval. Prefer clean
single-speaker speech of suitable duration with a validated transcript; listen
for background voices, clipping, noise and incorrect text. Review the transcript
and audio for personal information without attempting to identify the speaker.
Preserve the spoken wording; do not replace the transcript with a translation.

For each operator-selected local MP3, macOS `afconvert` can produce a
mono, 44.1 kHz, 16-bit PCM WAV. For example, after replacing these illustrative
paths with authorized local paths:

```sh
/usr/bin/afconvert -f WAVE -d LEI16@44100 -c 1 \
  "/absolute/local/input.mp3" \
  "/absolute/local-private-root/references/de-female/reference.wav"
```

Create `reference.lab` beside it as UTF-8 text matching the audio. Repeat for
the other three IDs. Keep all files local and owner-readable only. Inspect the
WAV format and duration, listen to each converted file, and confirm the exact
transcript before any approval. Conversion success is not voice-quality or
legal acceptance.

## Record local approvals without publishing them

Use the existing
[`load_qualified_reference_catalog`](app/fish_speech.py) contract rather than
inventing another loader. A draft reference manifest should start with
`"status": "pending"` and must not be used to enable Fish. Only after review,
the approved manifest contains exactly four records with:

- `id`, `language`, `gender`: `de-female`/`de-DE`/`female`,
  `de-male`/`de-DE`/`male`, `en-female`/`en-US`/`female`,
  `en-male`/`en-US`/`male`.
- `dataset_id`, `dataset_release`, `source_url`, `source_revision`,
  `source_license`: the actual selected source; the current validator accepts
  only the two linked dataset IDs, release `sps-corpus-5.0-2026-09-11`,
  and `CC0-1.0`.
- `terms_url`, `terms_revision`, `permission_basis`, `terms_status`,
  `intended_use`: exact reviewed terms, with `dataset-terms-accepted`,
  `approved`, and `private-noncommercial` only when those statements are true.
- `audio_path`, `lab_path`: relative paths such as
  `references/de-female/reference.wav` and
  `references/de-female/reference.lab`.
- `audio_sha256`, `lab_sha256`: lowercase SHA-256 values of the exact final
  WAV/transcript bytes, calculated locally after conversion and review.

Do not copy an approval from another installation or mark records approved
merely because hashes validate. The separate artifact approval also binds the
clean source revision/tree, runtime entrypoint/arguments, every model file,
decoder and exact terms. Store both manifests locally, not in either repository.

## Connect only after the remaining gates pass

The existing settings take absolute local paths:

| Setting | Local purpose |
| --- | --- |
| `TTS_FISH_REFERENCE_ROOT` | The data root containing `references/` |
| `TTS_FISH_REFERENCE_MANIFEST` | Reviewed four-reference manifest |
| `TTS_FISH_ARTIFACT_MANIFEST` | Reviewed source/runtime/model/decoder manifest |
| `TTS_FISH_SOURCE_ROOT` | Separate clean, pinned Fish source checkout |
| `TTS_FISH_CHECKPOINT_ROOT` | Approved local checkpoint directory |

Keep `TTS_FISH_ENABLED`, `TTS_FISH_ARTIFACTS_APPROVED`, and
`TTS_FISH_REFERENCES_APPROVED` false until their respective reviews are complete.
Do not change authentication: the protected existing backend token is reused,
not copied into repositories or replaced by another key.

Creating the companion repository does not enable Fish, approve a voice,
authorize a deployment, or qualify native memory/latency/quality. Follow
[the runtime policy](README.md#opt-in-headroom-first-native-fallback) and
[feature 007's qualification procedure](../specs/007-fish-backend-enablement/quickstart.md)
only after the remaining gates and deployment authorization are satisfied.
Preserve production and language-correct native `say` fallback independently.
