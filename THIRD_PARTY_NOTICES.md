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

The [backend uv lockfile](./backend/uv.lock) contains 32 third-party package
records across 31 package names (the remaining lock record is the project
itself; NumPy has platform-specific variants). The lockfile is the pinned
package/version/source inventory, not a bundle of every package's license
text. The reviewed licenses are permissive or copyleft-with-conditions,
including MIT, BSD variants, Apache-2.0, PSF-2.0, Zlib, CC0-1.0, and MPL-2.0
(`certifi`). `langid==1.1.6` is reported as generic BSD by
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

## Optional VibeVoice worker (release blocked)

The optional worker runtime is isolated in
`backend/vibevoice_worker/pyproject.toml` and pinned in
`backend/vibevoice_worker/uv.lock` (69 resolved package records). The exact
package artifacts and their license notices have not yet been audited. Do not
install or distribute the worker yet. The implementation source reference is
[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice) at
`0063f5b175d07c0a7d0aab2c5806bee9aa15f2a1`. The repository's MIT license
requires retaining its copyright and license notice. The selected
`VibeVoice-Realtime-0.5B` model card also identifies MIT, but separately limits
its intended use to research and development, discourages commercial or
real-world use without further work, and states responsible-use restrictions.
The MIT label alone is not release approval or confirmation that a proposed
deployment is permitted.

The reviewed `en-Carter_man`, `de-Spk1_woman`, and `de-Spk0_man` presets depend
on bundled or separately obtained model voice assets. Their exact artifact
provenance and applicable terms have not been independently established. The
model documentation describes German as experimental or unsupported depending
on the referenced revision; German deployment therefore also remains subject
to host and voice qualification. The runtime lock's exact package artifacts,
licenses, and notices must be audited before installation or redistribution.

Keep VibeVoice disabled unless the model and voice artifact provenance, exact
runtime inventory, supported-host behavior, intended-use terms, and required
owner/legal approvals have all been reviewed for the specific deployment.
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
