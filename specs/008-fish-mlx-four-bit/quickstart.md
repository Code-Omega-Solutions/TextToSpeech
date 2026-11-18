# Fish 1.5 MLX candidate

**Experimental; not broadly qualified.** The candidate converts only the
already approved Fish 1.5 DualAR checkpoint. It packs 100 attention and
feed-forward matrices as MLX affine 4-bit (group size 64); the first eight
slow layers, embeddings, output heads and other weights remain FP16. The
original Firefly codec stays in its
existing higher-precision PyTorch MPS path. The default Fish runtime remains
PyTorch; native `say`, API contracts, managed lifecycle and fallback remain in
place. Preload loads the candidate but does not generate warm-up speech.

## Preparation and review

Use macOS arm64 with Python 3.12 and the existing approved Fish environment.
Review the Fish source, checkpoint, codec, reference consent, MLX dependencies
and applicable terms first. Do not copy or modify approved trees. Install the
pinned MLX wheels into a **separate** private site directory using the
hash-locked `backend/deployment/fish_mlx-requirements.txt`; do not install into
the approved Fish environment or globally. Configure the existing approved
`TTS_FISH_*` source, checkpoint, reference, manifest and approval environment
variables, and set `TTS_FISH_MLX_SITE_ROOT` to that separate site directory.
Keep credentials and private reference material out of logs and examples.

With `PYTHON` pointing to the existing approved Fish virtualenv interpreter and
`BACKEND` to this candidate checkout's backend, run in a controlled environment:

```sh
"$PYTHON" -I -S -B "$BACKEND/deployment/fish_mlx/bootstrap.py" \
  --prepare "$PRIVATE_NEW_CANDIDATE_DIR"
export TTS_FISH_MLX_CANDIDATE_ROOT="$PRIVATE_NEW_CANDIDATE_DIR"
"$PYTHON" -I -S -B "$BACKEND/deployment/fish_mlx/bootstrap.py" \
  --review-output "$PRIVATE_NEW_REVIEW_FILE"
```

Both output paths must be absolute and new, outside protected trees. Conversion
is offline, checks the approved inputs and available memory, validates the
configuration and tensor inventory, then saves and reloads packed weights.
An interrupted conversion can leave a partial candidate directory; remove only
that specific private directory before retrying. The review file begins with
`review-required`: see `backend/deployment/fish_mlx/APPROVAL.md`. After a human
has reviewed and approved the exact binding and rights, set its status to
`approved`, keep it owner-controlled and not group/world writable, and set
`TTS_FISH_MLX_APPROVAL_MANIFEST` to its path and `TTS_FISH_MLX_APPROVED=true`.
Never treat conversion or these instructions as approval.

For a separately authorized isolated test backend, set `TTS_FISH_RUNTIME=mlx4`,
enable the existing managed/opportunistic Fish settings and use a JSON argv
`TTS_FISH_WORKER_COMMAND` containing the exact candidate interpreter,
`-I`, `-S`, `-B`, and this checkout's `backend/deployment/fish_mlx/bootstrap.py`.
Configure the candidate paths and the unchanged original Fish approvals in that
backend's environment. Activation of a production service requires a separate
authorization and a rollback plan.
Changing code, dependencies, artifacts or the reviewed runtime invalidates the
binding and requires a fresh review.

## Evidence and outstanding gates

On Apple Silicon, the mixed-precision conversion produced an 846,296,200-byte
packed safetensors file with SHA-256
`5aa0746f626a4d2a89b8c720be6dc275d78eb9a65b2c54871ee743dc2374866a`.
Strict reload found 403 entries including 100 packed matrices. Reference-
conditioned, teacher-forced comparisons against PyTorch using the same
dequantized weights closely matched slow and fast logits. The original fully
quantized candidate sometimes ran to the token limit; retaining eight early
layers in FP16 improved the bounded cases. This is not a quality guarantee.
Generation now fails rather than returning audio if it reaches its token limit.

With the approved Fish source and tokenizer, a separate no-audio test exercised
the upstream prompt encoder and generation queue using synthetic codebook
tokens, both with and without a synthetic prompt. Mocked tests also exercise
managed dispatch, MessagePack request shape, startup exit and safe fallback
headers; mocked WAV/codec behavior is not end-to-end WAV evidence. The
optional `test_fish_mlx_upstream.py` requires explicitly setting
`TTS_FISH_MLX_SYNTHETIC_BRIDGE_TEST=1` and the approved source/checkpoint
paths in an isolated offline environment; it never loads reference audio or
produces speech.

With explicit authorization and a private hash-bound approval, four short
English/German requests produced valid WAVs in an isolated worker. Cold
readiness was 6.223 seconds; complete request-to-WAV times were 0.815–1.044
seconds for 1.161–2.322 seconds of audio. The process-group peak RSS sampled
2.40 GB and available memory stayed above 19.34 GB. On the same short inputs,
the original PyTorch worker took 3.053–4.646 seconds after 11.185 seconds cold
readiness, with 0.789–1.300 seconds of audio; sampling streams differ even with
equal seeds. A separate managed-backend test verified preload survived 32
seconds idle, English and German returned Fish headers without fallback in
0.990 and 0.988 seconds respectively, and the worker exited on shutdown.
Request-to-WAV timings include materialized audio; individual reference,
prefill, generation and codec phases were not timed.

After explicit deployment authorization, an exact-label rollout retained the
preloaded worker for 32 seconds and passed same-origin proxy readiness and
catalog checks. Short proxy requests returned Fish without fallback: English
1.057 seconds for 1.068 seconds of audio; German 1.575 seconds for 1.811 seconds
of audio. A first launchd bootstrap failed; the original service was restored
and verified before an isolated launchd restart test and guarded retry. A
private original-service backup supports rollback.

These are a few bounded requests, not representative or worst-case benchmarks.
No perceptual English/German quality assessment, worst-case memory qualification
or redistribution rights clearance has been established. MLX computations are
lazy; synchronize with `mx.eval` before timing individual phases.
