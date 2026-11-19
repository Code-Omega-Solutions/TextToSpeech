# Third-party notices and license audit

The root [LICENSE](./LICENSE) is a proposed custom attribution license for
project-owned materials only. It does not replace, extend, or relicense
third-party software, content, or system components. Each released source tree
or binary/image must be inventoried against its own lockfiles and package
metadata, and redistributed with the applicable copyright notices, license
texts, and source offers.

## Frontend container image

The runtime image is based on the Debian Trixie variant of the official Nginx
image. The final image contains a Debian package/version/source inventory at
`/usr/share/doc/texttospeech-frontend/RUNTIME-PACKAGES.txt`. This image-level
metadata is the inventory for that built runtime; the base-image name or the
source lockfiles alone are not a substitute for checking the exact release.
Debian package copyright and license notices are preserved under
`/usr/share/doc/*/copyright`. The Debian copyright files include the notices
and license terms for corresponding packages. Do not remove or replace them
when redistributing the image.

For components whose terms require source availability, the
[written source offer](./SOURCE_OFFER.md) provides a request channel and
fulfillment terms. The offer is copied into each newly built image. Preserve
the offer and all package copyright files when redistributing the image.

The previously published Alpine image
`sha256:7415ab30306c25b4df0cb02f9f51eaf1b5a8027a1ab705bbd5bcf9d56edf1727`
contained 71 Alpine packages but did not include complete package-level
copyright/license files or a source offer. Its compliance is not verified; do
not redistribute that legacy digest. A supplemental source offer is now
recorded in [SOURCE_OFFER.md](./SOURCE_OFFER.md). The publishing workflow is
configured to retain only the newest version after a successful publication,
which is intended to remove that legacy registry version. Registry deletion
cannot recall copies already downloaded or redistributed and does not
retroactively cure missing notices.

The Node.js build stage and npm development dependencies are not copied into
the runtime image. The final image's deployed files and Nginx runtime are the
relevant container distribution scope; each build's Debian inventory and
package copyright files must remain available with it. macOS `/usr/bin/say`
and installed system voices are supplied by Apple and are not part of this
repository or relicensed here.

## Backend lockfile

The [backend uv lockfile](./backend/uv.lock) contains 37 third-party package
records across 36 package names (the remaining lock record is the project
itself; NumPy has platform-specific variants). The lockfile is the pinned
package/version/source inventory, not a bundle of every package's license
text. The reviewed licenses are permissive or copyleft-with-conditions,
including MIT, BSD variants, Apache-2.0, PSF-2.0, Zlib, CC0-1.0, and MPL-2.0
(`certifi`). The new locked packages are `msgpack==1.2.4` (Apache-2.0),
`httpx2==2.16.2` (BSD-3-Clause), `httpcore2==2.16.2` (BSD-3-Clause),
`httpx2-jsfetch==1.0` (BSD-3-Clause), and `truststore==0.10.5` (MIT), based
on the exact PyPI release metadata. PyPI metadata is not a substitute for
reviewing the installed artifacts' license texts and notices before
redistribution. `langid==1.1.6` is reported as generic BSD by
[PyPI](https://pypi.org/project/langid/1.1.6/); the upstream repository's
[license text](https://github.com/saffsd/langid.py/blob/master/LICENSE) has the
two BSD redistribution conditions. The exact release tag was not independently
confirmed. Verify obligations against the exact release artifacts and retain
the package's copyright notice, conditions, license, and disclaimer when
redistributing it.

No identified lockfile license bars commercial or non-commercial use. This
finding does not establish that the project has rights to every recovered
source file, nor does the proposed root license relicense any dependency.

## Frontend npm lockfile

The [frontend npm lockfile](./frontend/package-lock.json) contains 43
package-version records: 25 MIT, 4 Apache-2.0, 1 BSD-3-Clause, 1 ISC, and 12
MPL-2.0. These packages are installed in the Docker build stage and are not
copied into the final runtime image. If the build environment or packages are
redistributed separately, preserve their required copyright and license
notices; MPL-covered files remain subject to MPL-2.0.

## Other runtime components

`ffmpeg` is an external backend runtime prerequisite and is not included in
this source tree. Its license and build configuration depend on the
distribution selected by the operator. Review that distribution's package
metadata and notices before bundling or redistributing it. Do the same for
other separately installed runtime components; the project license does not
cover them.

## Experimental MLX dependency (not a working worker)

The proposed Fish candidate pins `mlx==0.32.4` and `mlx-metal==0.32.4` in
`backend/deployment/fish_mlx-requirements.txt`, with hashes for Python 3.12
macOS arm64 wheels. The [MLX source license at v0.32.4](https://github.com/ml-explore/mlx/blob/v0.32.4/LICENSE)
is MIT, copyright Apple Inc. The exact wheel contents and notices have not been
fully audited for redistribution. This dependency pin is not a working Fish
runtime or approval to deploy; Fish model, codec and reference terms remain
separate gates.

## Optional VibeVoice worker (release blocked)

The optional worker runtime is isolated in
`backend/vibevoice_worker/pyproject.toml` and pinned in
`backend/vibevoice_worker/uv.lock` (69 resolved package records). The exact
package artifacts and their license notices have not yet been audited. The
operator authorized installation on the private R&D host only; this does not
clear the artifacts for redistribution. Do not distribute the worker. The
implementation source reference is
[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice) at
`0063f5b175d07c0a7d0aab2c5806bee9aa15f2a1`. The repository's MIT license
requires retaining its copyright and license notice. The selected
`VibeVoice-Realtime-0.5B` model revision
`6bce5f06044837fe6d2c5d7a71a84f0416bd57e4` identifies MIT. Its model card
limits direct intended use to research, says the model is intended for English
speech only, and lists unsupported languages as out of scope. It discourages
commercial or real-world use without further testing and development, and
states responsible-use restrictions. The card also claims that generated audio
contains an audible AI disclaimer and an imperceptible watermark; the integrated
worker must verify that the exact checkpoint preserves these safeguards. The
model revision must be pinned and recorded with the deployed artifact. The MIT
label alone is not release approval or confirmation that a proposed deployment
is permitted. The operator has authorized private R&D use only; this is not
legal approval, Microsoft permission, or a basis for production or
redistribution claims. German is experimental and unsupported in the reviewed
model card, so do not present German VibeVoice as a supported production use.

At source commit `0063f5b175d07c0a7d0aab2c5806bee9aa15f2a1`, the selected voice
files are present under `demo/voices/streaming_model/`: `en-carter_man.pt`
(blob `1d795ef667e6641eecb8b22452bb853b089bfdbe`), `de-Spk1_woman.pt`
(blob `c67e669e718639e1d7e451330e3122eb8a0ac071`), and `de-Spk0_man.pt`
(blob `740731426768eb1902ede9276c9e1f33fb8bd37f`). This identifies their
source artifacts, but neither their filenames nor the repository's MIT license
establishes consent or provenance for the represented voices. The owner has
authorized these bundled presets for private R&D only. This does not establish
third-party consent, legal clearance, production support, or permission to
redistribute the voice files or generated audio. German generation remains an
unsupported experiment under the reviewed model card. Do not clone or
impersonate a real person without explicit consent.

The pinned source's `demo/download_experimental_voices.sh` links an additional
`experimental_voices_de.tar.gz` GitHub attachment. A non-extracting listing
identified `de-Spk2_woman.pt`, `de-Spk3_man.pt`, `de-Spk4_woman.pt`,
`de-Spk5_man.pt`, and `de-Spk6_man.pt` under `de/`. The upstream inference
example recursively scans the voice directory for `.pt` files, so these prompts
are structurally compatible with that loader. The integrated worker does not
currently load them: its preset catalog and file lookup support only the three
listed bundled prompts. The download script provides no archive checksum or
separate license, voice-consent, or provenance record. These experimental files
do not make German an officially supported use of the English-only model.

PyPI JSON metadata for the 68 external versions in the worker lock reports
`soxr==1.1.0` as `LGPL-2.1-or-later`, `certifi==2026.10.23` with an MPL-2.0
classifier, and `tqdm==4.67.1` with MIT and MPL-2.0 classifiers. Twelve locked
NVIDIA CUDA packages declare `Other/Proprietary` metadata; the thirteenth,
`nvidia-cusparselt-cu12==0.6.2`, has only freeform license metadata. All 13 are
conditional `torch==2.6.0` dependencies for Linux x86_64, not the macOS worker
target. Five other packages expose only freeform metadata:
`charset-normalizer==3.5.2`, `decorator==5.3.1`, `llvmlite==0.44.0`,
`psutil==7.2.2`, and `nvidia-cusparselt-cu12==0.6.2`. PyPI metadata and
classifiers are not substitutes for inspecting the exact distributions,
bundled notices, or corresponding source. Those artifact-level reviews remain
required before production use or redistribution. The owner-authorized local
R&D install does not clear these release gates.

Keep VibeVoice disabled outside the explicitly authorized private R&D scope, and
do not enable a deployment until model and voice provenance, exact runtime
inventory, host behavior, safeguards, and intended-use terms have been reviewed.
These are release gates, not a statement of legal approval.

## Release status

The lockfile audit found no dependency license that requires making this
source repository private. Repository visibility is separate from compliance
for a binary or container distribution. Before public release, obtain explicit
legal/ownership approval of the proposed custom project license, verify rights
to recovered source, review the reachable repository history, and verify
third-party notices and source-offer fulfillment for the exact artifact.
Publication and deletion of old registry versions are not release approval;
deletion cannot recall copies already downloaded. This inventory documents
obligations and artifacts; it is not legal advice or a substitute for verifying
each release image and its source-offer fulfillment process.
