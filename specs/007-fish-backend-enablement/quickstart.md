# Resource Policy Validation

## Local checks

Run from `backend/` in an existing supported development environment:

```sh
uv run --locked pytest tests/test_fish_process.py tests/test_engines.py tests/test_config.py tests/test_api.py tests/test_fish_speech.py tests/test_vibevoice_memory.py
```

Expect resource denial, pressure during load/active/idle operation, probe failure,
cooldown, cancellation, and native language fallback tests to pass. These are
mocked checks, not native runtime or speech-quality qualification.

## Recorded local evidence: 2026-11-17

The affected regression command completed with **175 passed** under Python 3.12
on Linux, using the existing locked dependency set:

```sh
uv run --python 3.12 --locked --no-sync pytest -ra tests/test_fish_process.py tests/test_engines.py tests/test_config.py tests/test_api.py tests/test_services.py tests/test_speech_contract.py tests/test_engine_catalog.py tests/test_fish_speech.py tests/test_vibevoice_memory.py tests/test_vibevoice_startup.py
```

Config and lifecycle/fallback tests were observed failing before the corresponding
implementation, then passing. The suite includes real disposable Linux process
sessions for graceful/forced termination and reaping, plus a disposable loopback
TCP listener; inference, native voice execution and resource-pressure scenarios
remain mocked. No shared service was stopped or reconfigured.

Tracked diff whitespace checks passed; the new feature artifacts were checked
for private host/address details. No dependency manifest or lockfile changed.
No native macOS/model benchmark or listening qualification was run, because exact
runtime/codec/checkpoint and bilingual-reference approval remain open. No model
was downloaded and no repository-managed Fish worker was enabled. Iteration 9 used the existing
strict, key-authenticated SSH path for sanitized target inspection and a
prototype-only service operation; production was contacted only for
authenticated before/after health and speech checks and was not restarted.
The server-side proxy and Fish configuration reuse the protected backend bearer
credential rather than requiring an additional operator or Fish secret.

## Iteration 11 native deployment and rollback evidence

The authorized Apple Silicon macOS target was reached with the existing strict,
non-interactive SSH policy. No host-key trust, production launch agent,
production plist, token file, or production process was changed. The stale
prototype definition remains quarantined under a non-loadable name and
disabled; no new startup definition was introduced.

The current prototype-only deployment matched the checked-in SHA-256 values
for the launcher, runbook, recreation helper, recreation test, and template:

```text
fish_worker_launcher.py       25df2f4489596853613e12f7518505fc1271f121af5db31b6251f06151f85b3e
prototype-operations.md       9d1371c1e05e0ba2c51bf19d43f5a082efb394685b05f68aa30cef00fba7fb1c
prototype-recreation.zsh      e562aaa397e31bea560bc84f927c63acf9543c6e29ed7500e9731aeef8a9cb42
test_prototype_recreation.zsh a3ca799b113d4faeda59d9d4f2bd0f0b34a089af612c9663aa8c59857ad132ce
prototype template            70981e28e355dc00937579c969f57f59a89594b6529a47b8f37ec3b71c02bb86
```

The generated private prototype plist was verified separately by hash
(`1ab99657b2eac21bb94a8e807ff5fbfa871bd68645509fd91e2ff4c322f5d440`) without
recording its private paths or credential value. Its live flags remained
`TTS_FISH_ENABLED=false`, `TTS_FISH_ARTIFACTS_APPROVED=false`,
`TTS_FISH_REFERENCES_APPROVED=false`, with no worker command.

Native `zsh -n` passed for both scripts. The executable fake-launchctl test
passed its success and forced-failure cases. The live helper then recreated
only the prototype and UI labels. Baseline, post-recreation, and post-rollback
production/prototype readiness returned HTTP 200. Authenticated WAV requests
returned HTTP 200 from both services with `macos-say`, no fallback, a valid
RIFF header, and 238,630-byte responses. The prototype rejected an
unauthenticated speech request with HTTP 401. The protected verifier reported
UI target discovery HTTP 200 with only opaque `Production` and `Prototype`
choices, and unauthorized configuration returned HTTP 401.

A live forced-failure verifier returned status 1; the protected prototype
configuration hash was restored exactly and both prototype/UI services
returned. Production readiness, authenticated WAV speech, and its launchd
process identity remained unchanged. No production restart, replacement,
credential readout, generated audio, or private target path was recorded.

The deployed UI was opened in a browser. Selecting WAV and generating a
synthetic sentence produced the visible `Ready to listen.` state and a
downloadable audio blob. The expected legacy engine-discovery request returned
404 and the UI reported that service defaults would be used; no credential or
upstream origin appeared in the page data. The Fish artifact, codec, reference,
and managed-neural qualification gates remain closed, so this evidence claims
native fallback and deployment safety only, not Fish output or voice approval.

## Iteration 7 fail-closed deployment state

The checked-in prototype launch template now keeps neural Fish disabled until
both exact artifact approval and the complete four-way qualified reference
catalog are available. It sets `TTS_FISH_ENABLED=false` and does not provide a
worker command, source root, checkpoint root, or Fish listener. Native
language-preserving fallback remains the only executable prototype path.

The repository-managed launcher independently requires an approval manifest
with pinned source/model revisions, exact model-file and codec hashes, and
recorded source/model/codec terms before it can exec a worker. Missing or
invalid approval fails closed. No approved manifest or four-way consented
German/English male/female reference set is present in this repository.
Consequently, no Fish neural output is claimed as qualified in this iteration.

The remote target was not changed in this iteration because no authorized
deployment session was available in this checkout. Before any future rollout, disable the stale unmanaged prototype launch
definition (and quarantine its file when the operator can identify it safely),
then
recreate only the repository-managed prototype backend and persistent UI.
Repeat prototype-only startup, readiness, native fallback, rollback, and
production-preservation checks; do not report those checks as complete until
they are observed on the native target.

## Gated native evaluation

Do not install or activate a runtime from this guide without separately
reviewing exact checkpoint/codec/runtime terms and reference permissions.
The historical iteration-6 deployment was a private, non-redistributed
prototype using
authorized local artifacts; credentials and local paths stay out of git.

After separate rollout approval:

1. Establish native baseline readiness and authenticated German/English speech.
2. With the optional engine disabled, enable the fallback policy on the prototype
   only and verify valid neural/legacy selections return native speech in the
   requested language with fallback headers.
3. Configure the reviewed managed launcher and local artifacts. Verify cold-start
   admission leaves the approved reserve, respects worker limits, and never
   starts an external or second worker.
4. With injected resource-denial measurements (not artificial load on shared
   services), verify worker termination and native fallback while idle and active.
5. Verify cancellation, cooldown, idle unloading, shutdown cleanup, and continued
   baseline readiness. Stop if termination or headroom cannot be verified.
6. Only then make bounded synthetic native/model comparisons and review
   pronunciation, completeness and acceptable quality with the operator.

The initial 16 GiB worker/12 GiB reserve excludes Drama 3's currently reported
peak. If smaller candidates cannot qualify, obtain an explicit revised runtime
decision before using the conditional 8 GiB option.

## Iteration 5 sanitized deployment record

The designated Apple Silicon target was reached with the required strict
key-authenticated SSH policy. Read-only inspection confirmed production on
port 8000, the isolated prototype on port 8001, and Fish on prototype-loopback
port 8002. Only the prototype launch agents were recreated. Production health,
readiness, and authenticated speech remained successful before and after.

The private deployment pinned Fish source revision
`7902e408c85b37193ce3f3c2361ca3c76be0d533`, model revision
`275a984d33c33659e39eed41ff5bcd6e67517f4c`, model SHA-256
`918dc960372cc1b77bbafb14c48ef7a1634ecf75d4eb85b78607223b780d6001`, and
codec SHA-256
`01b81dbf753224a156c3fe139b88bf0b9a0f54b11bee864f95e66511c3ccd754`.
The source is Apache-2.0; upstream identifies model weights as CC BY-NC-SA 4.0.
Artifacts stay private and are not committed or redistributed. Public codec
release terms and reference cloning consent remain open release gates.

Authenticated Fish requests produced playable mono 44.1 kHz WAV for German and
English with both public references. Observed response sizes were 397,356,
340,012, 262,188, and 385,068 bytes; observed elapsed times were 46.4, 40.0,
31.8, and 45.4 seconds respectively. All four responses reported Fish as the
actual backend and no fallback. An unauthenticated prototype speech request
returned 401. No subjective listening acceptance was performed.

The browser UI was run through a local standalone proxy because the target has
no Node or Docker runtime. It exposed only opaque Production/Prototype choices,
discovered Fish and both references, and generated playable prototype audio.
The privileged configuration endpoint rejected an unauthorised browser request
with 401. Browser assets and resource URLs contained no backend origin or
credential. A proxy content-type forwarding defect found during this check was
fixed and covered by the frontend unit suite.

That historical external worker is not used as the current managed worker.
The iteration-6 launch configuration uses the repository-managed launcher and
keeps that pre-existing listener outside its ownership boundary. The remaining
artifact, reference, and full native-qualification gates are still open.

### Prototype rollback

To roll back the prototype only, stop the prototype launch agent, restore the
previous prototype environment and checkout, then recreate that launch agent
and verify authenticated `/readyz` and one Fish request. Do not stop or
reload the production launch agent. Iteration 5 exercised prototype-only
recreation and restoration; readiness and Fish speech returned HTTP 200.
Never record the host identity, credential, private paths, raw inventories, or
generated audio in this repository.

## Historical iteration 6 deployment record (superseded)

The designated Apple Silicon target now runs the repository-managed prototype
backend and a persistent dependency-free UI service. Production remains on its
pre-existing port and was not restarted or replaced. The prototype backend and
UI use distinct service ports; Fish is loopback-only. Both launch agents were
recreated in a prototype-only operation from protected configuration backups.

Live checks after recreation:

- prototype readiness: HTTP 200;
- prototype authenticated native speech: HTTP 200;
- production health and authenticated speech: HTTP 200;
- UI root: HTTP 200;
- opaque target discovery: HTTP 200 with only `Production` and `Prototype`;
- unapproved target selection: HTTP 403;
- unauthorized operator configuration: HTTP 401;
- Fish-selected prototype speech: HTTP 200 with actual backend `macos-say` and
  fallback `true`.

The Fish-selected request is the important live lifecycle result: the manager
refused neural admission because the 12 GiB reserve plus 16 GiB worker budget
could not be satisfied by the sampled host headroom, then produced
language-preserving native audio within the request boundary. No artificial
memory pressure was generated and no external worker was terminated. Idle
unload, cooldown, cancellation, deadline, and owned cleanup remain covered by
the focused tests; a neural success benchmark and four consented reference
voices remain unqualified.

The prototype catalog advertises no reference IDs until exact recording,
transcript, provenance, and cloning-consent evidence is supplied. The UI
therefore exposes the qualified engine boundary without promising an
unqualified voice identity. The production engine-discovery 404 is expected
for that legacy service and the UI correctly falls back to service defaults.

## Iteration 10 sanitized hardening record

The launcher and deployment runbook were hardened without changing the
fail-closed deployment state. A source tree is now rejected when Git reports
any tracked, untracked, or ignored file; the old exception for untracked
`references/` files is gone. The local approval manifest must be a non-symlink
file without group/world write permission on POSIX and must bind the exact
tracked runtime entrypoint hash and fixed loopback Fish serving contract in
addition to every model/codec file hash and pinned terms. No model, codec,
reference, or license term was invented or downloaded.

The prototype-only operations runbook now guards an already-absent
`launchctl` label, waits for exact labels to disappear before bootstrapping,
and captures protected backend/UI copies before recreation. An exit trap
restores those copies only after the same bounded unload wait if any post-load
check fails. The stale definition remains disabled and quarantined under a
non-`.plist` name; the production label is never passed to the sequence.
Focused launcher and runbook tests pass locally.

This iteration has no new native execution result. The current builder
environment does not expose an authorized SSH target/path, so the corrected
sequence was not run against the designated host and no production or secret
operation was attempted. The previous independent run's failure of the old
unguarded recreation stage remains open evidence; no deterministic live
recreation/rollback success is claimed here. Exact model/codec terms, a clean
approved source checkout, four consented WAV/`.lab` pairs, Fish outputs,
managed neural lifecycle measurements, and browser/live checks remain
unresolved gates.

## Iteration 9 sanitized deployment record

The authorized strict-SSH session reached the designated Apple Silicon macOS
target without changing host-key trust. Read-only discovery found one exact
stale user launch-agent definition for the prototype port with both
`RunAtLoad` and `KeepAlive` enabled; the repository-managed prototype label was
excluded from this identity check. Production, prototype, Fish-loopback, and UI
listeners were present on their distinct ports.

Before the change, production health, readiness, and authenticated speech were
HTTP 200, and the managed prototype speech and UI root were HTTP 200. The
identified stale label was disabled by its exact `gui/<uid>/<label>` identity,
booted out, and given a bounded 10-second unload wait (40 × 250 ms). Its exact
plist was then moved to a non-`.plist` quarantine name. The persisted
`launchctl print-disabled` record reported `=> disabled`, the original loadable
file was absent, and no wildcard process termination or production operation
was used. This combination prevents a future launch-agent scan from loading
the stale definition; no machine reboot was performed.

Protected copies of the managed prototype and UI definitions were captured.
Both labels were recreated from those copies, with the same bounded unload wait
before each bootstrap, and then restored from the managed definitions. The
recreation and rollback checks returned prototype authenticated speech and UI
HTTP 200. Production health, readiness, and authenticated speech remained
HTTP 200; its launchd process identity was unchanged. Final listener counts
remained one each on the production, prototype, and UI ports. The stale file
remains quarantined and disabled.

This deployment evidence does **not** close the Fish gates. The managed
prototype stayed fail-closed with `TTS_FISH_ENABLED=false` and no approved
artifact or reference manifest. The tagged Fish source and inference
documentation are publicly readable, but the authoritative exact checkpoint
metadata remains HTTP 403 from this environment, and codec-specific terms for
the installed local file are not accepted as reviewed approval. The local
source checkout is not clean, so its tree cannot bind an approval manifest.
No model or codec was downloaded, no restriction was bypassed, and no managed
neural worker was enabled.

Public voice research also remains incomplete: Thorsten-Voice provides strong
German male TTS-contribution and CC0 dataset provenance, but not the requested
four exact bilingual male/female WAV/`.lab` pairs. Other public recording leads
do not establish cloning consent, bilingual identity, or local Fish-reference
exportability. No celebrity or community clone is advertised, no reference
manifest was created, and no Fish output or subjective listening acceptance is
claimed. T004, T005, T006, and T010 therefore remain open.

## Iteration 8 historical deployment record (superseded)

The authorized deployment probe confirmed an Apple Silicon macOS target with
production, prototype, and UI listeners on distinct ports. Authenticated
production health, readiness, and speech were HTTP 200 before the operation.
The prototype-only stale startup definition owning the prototype port was
identified by its exact label, but iteration 8 only unloaded it and did not
quarantine its loadable plist. That record therefore did not establish future
startup safety; iteration 9 above corrects it.

Only the managed prototype and UI were recreated from the reviewed source and
configuration. A first placeholder-template bootstrap was rejected and the
managed definitions were restored from the protected copies; the subsequent
path-corrected recreation started both services. Production was not booted out,
restarted, or replaced. Post-recreation production health, readiness, and
authenticated speech remained HTTP 200. Prototype health/readiness and
authenticated native speech were HTTP 200, while an unauthenticated speech
request returned HTTP 401. The prototype response reported `macos-say` as the
actual backend and did not claim Fish output.

The persistent UI served HTTP 200, exposed only opaque Production/Prototype
targets, returned HTTP 403 for an unapproved target, and returned HTTP 401 for
unauthorized privileged configuration. A session-selected prototype target
proxied successfully; an authorized target write survived a clean UI
recreation, then was restored to production. A transient listener race during
`kickstart` was handled by booting out and bootstrapping only the UI label;
the final UI and production target state were healthy.

The deployed Fish path remains fail-closed. The authorized local checkpoint
directory exists, but no exact artifact/terms manifest or qualified reference
manifest is available. The source checkout has two unrelated working-tree
edits, and its accessible reference tree contains two WAV files and no
matching `.lab` transcripts; no reference IDs are approved. No assets were
downloaded, no access controls were bypassed, and no four-way Fish outputs are
claimed. The exact source revision/tree, every model file, codec file, and
terms must be approved before enabling the worker. Mocked lifecycle tests cover
admission, one-worker ownership, pressure/probe failure, cancellation,
deadline, cooldown, idle unload, cleanup, and native fallback; live neural
lifecycle and four-output qualification remain open gates.
