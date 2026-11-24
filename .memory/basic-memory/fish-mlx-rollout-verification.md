---
title: Fish MLX rollout verification
type: note
permalink: project-texttospeech/fish-mlx-rollout-verification
---

# Fish MLX rollout verification

- [workflow] During a Fish MLX rollout with preload enabled, backend readiness and an open worker port do not mean the neural request slot is free. Wait for the backend's preload-complete signal before using a synthesis smoke test to judge the cutover. A 200 response can still be native fallback; check the actual engine and fallback response headers. Verified during the 2026-11-20 rollout.
- [architecture] The Fish adapter requests in-memory conditioning reuse when a reference ID is supplied. The cache is keyed by reference ID and lasts only for the life of the worker; it is not a persisted speaker tensor or an audio-output cache. Shared MLX model weights are separate from voice conditioning.

- [configuration] `TTS_FISH_GERMAN_MALE_ONLY=true` restricts the backend's German Fish catalog and default to `de-male` and rejects explicit `de-female` requests. It leaves English voices and validation of the full approved reference manifest unchanged. Verified on 2026-11-20: changing this selection policy required new approval for the changed backend binding, but no regeneration of shared MLX weights.

- [workflow] Fish MLX approval binds the complete backend `app` tree, so even a language-selection-only change requires review and approval of the new app-tree binding before the worker can start. Compare the newly generated review binding with the prior approval and investigate any additional differences. Verified during the 2026-11-20 fallback rollout.