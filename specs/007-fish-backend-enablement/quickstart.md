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
was downloaded, no runtime launcher was installed, and nothing was deployed.
The authorized read-only SSH probe for the newly designated target could not
connect under strict host-key checking, so target OS, roles, free ports, and
native fallback remain unverified. Production was not contacted or restarted.
The server-side proxy and Fish configuration reuse the protected backend bearer
credential rather than requiring an additional operator or Fish secret.

## Gated native evaluation

Do not install or activate a runtime from this guide. First review exact
checkpoint/codec/runtime terms, the authenticated local launcher, reference
provenance and resource budget. Keep credentials and local paths out of git.

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

The external Fish worker is not the repository-managed `FishProcess` worker.
Pausing only that owned prototype worker caused a bounded 504 rather than
native fallback; resuming it restored readiness and Fish speech. Opportunistic
fallback, native admission, idle unloading, cooldown, cancellation, pressure
handling, and hard unified-memory isolation therefore remain unqualified. Do
not enable opportunistic mode without a reviewed local worker command and real
resource evidence. This leaves T004, T005, T006, and T010 open as appropriate
to the unresolved artifact/reference/managed-lifecycle gates.

### Prototype rollback

To roll back the prototype only, stop the prototype launch agent, restore the
previous prototype environment and checkout, then recreate that launch agent
and verify authenticated `/readyz` and one Fish request. Do not stop or
reload the production launch agent. Iteration 5 exercised prototype-only
recreation and restoration; readiness and Fish speech returned HTTP 200.
Never record the host identity, credential, private paths, raw inventories, or
generated audio in this repository.
