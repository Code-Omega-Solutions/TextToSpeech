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
