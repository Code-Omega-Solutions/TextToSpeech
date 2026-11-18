# Fish 1.5 MLX candidate

**Experimental; not deployed or qualified.** The candidate converts only the
already approved Fish 1.5 DualAR checkpoint. It packs 140 attention and
feed-forward matrices as MLX affine 4-bit (group size 64); embeddings, output
heads and other weights remain FP16. The original Firefly codec stays in its
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
backend's environment. Do not modify or restart the current production service.
Changing code, dependencies, artifacts or the reviewed runtime invalidates the
binding and requires a fresh review.

## Evidence and outstanding gates

On Apple Silicon, the approved checkpoint was converted twice independently
to the same 674,469,198-byte packed safetensors SHA-256
`f6a2528c23281cd67d4768b29af4c8678aaa746d7bd75646037ac1ef9358e05b`.
Strict reload found 483 entries including 140 packed matrices. Synthetic-token
MLX execution and numerical comparisons against PyTorch with the same
dequantized weights exercised slow and fast inference and caches. This is not
an audio or quality test. The generated review-required approval was rejected
at startup as intended.

No candidate end-to-end WAV, consented-reference speech, synchronized
representative performance benchmark, English/German quality assessment,
worst-case memory qualification, rights clearance for redistribution, or
deployment approval has been established. Any speech validation requires
separate authorization and an independently reviewed candidate approval.
MLX computations are lazy; synchronize with `mx.eval` before timing.
