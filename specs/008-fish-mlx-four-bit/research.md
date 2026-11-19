# Research: Fish 1.5 MLX candidate

## Decision: preserve the approved model

The approved source is Fish 1.5 DualAR at commit `3a2287807c8379c13cd5a0eee30d8054eb6a3efe`. It has 24 slow and 4 fast transformer layers, 8 codebooks, 1024 codebook entries and a 102048-token vocabulary. Its semantic checkpoint is BF16; the Firefly codec remains FP32 in the current MPS runtime. The pinned source has no MLX implementation.

The user approved a standalone port rather than model substitution. Public MLX Fish implementations examined target S1-mini or S2 Pro: [mlx-fish-speech](https://github.com/zxc524580210/mlx-fish-speech/tree/1185df40efabc6965e681af4d72e3970ed929f86), [fish-speech-mlx](https://github.com/gafiatulin/fish-speech-mlx/tree/b0c8e534960b18cd40688a85f852a6cb56af066d), and [Parrot](https://github.com/kwonho87/parrot/tree/c52b51f73ca58c87c6fcdffd68c3cd0158a83a16). Their newer checkpoints and prompt/tokenizer conventions are not evidence of Fish 1.5 compatibility.

## Decision: real packed quantization, isolated approval

[MLX 0.32.4 quantization](https://github.com/ml-explore/mlx/blob/v0.32.4/python/mlx/nn/layers/quantized.py) supports affine 4-bit grouped weights and `quantized_matmul`. Group size 64 is a candidate choice, not a quality finding. Keep embeddings and output projections initially in higher precision to reduce risk; verify actual tensor names, shapes, serialized types and numerical behavior. Existing PyTorch MPS casting and the pinned CUDA-specific int4 tool are not MLX inference.

MLX's affine representation packs eight 4-bit values per `uint32` and stores per-group scales and biases. Quantization parameters must also be recorded separately and the corresponding quantized layer structure instantiated before strict loading. The actual approved local config has `tie_word_embeddings=false`; generic upstream defaults are not evidence of this checkpoint's behavior. Local pinned-source inspection confirms adjacent-pair rotary math and the eight-pass fast codebook loop. The installed source revision was verified locally but the public upstream API did not resolve that SHA, so provenance must rely on the already-approved exact local tree and be independently reviewed rather than inferred from the upstream tag.

Fish source and model/codec rights remain distinct. The exact model revision's model card labels its weights CC-BY-NC-SA-4.0; codec weights reside in the same model repository. Existing reference rights and approval gates continue to apply. Derived artifacts and new dependencies require their own exact inventory and approval, not modification of existing production manifests.

## Decision: reuse managed worker safety

The existing supervisor owns one loopback worker, monitors memory, controls deadlines and cancellation, and supports background preload and native fallback. The candidate must use the same boundary and preserve the original Fish MessagePack/WAV contract. The original source server uses PyTorch semantic generation and the original Firefly codec; MLX must provide the semantic computation rather than relabel that server.

## Qualification

The earlier short warm-up is not an end-to-end benchmark. MLX is lazy: synchronize materialized outputs before recording timings. No claim is made about speed, German/English quality, memory under load, or native inference until independently measured on Apple Silicon with approved references and permitted text.
