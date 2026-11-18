"""Fish 1.5 autoregressive sampling using the MLX DualAR model."""

from __future__ import annotations

from typing import Any


def sample(mx: Any, logits: Any, previous: list[int] | None, temperature: float,
           top_p: float, repetition_penalty: float) -> int:
    if not 0 < temperature < 2 or not 0 < top_p <= 1 or not 0 < repetition_penalty < 2:
        raise ValueError("Invalid Fish sampling parameters")
    if previous:
        indices = mx.array(previous, dtype=mx.int32)
        values = logits[indices]
        logits[indices] = mx.where(
            values < 0, values * repetition_penalty, values / repetition_penalty
        )
    order = mx.argsort(-logits)
    ranked = logits[order]
    cumulative = mx.cumsum(mx.softmax(ranked.astype(mx.float32), axis=-1))
    remove = (cumulative > top_p) & (mx.arange(ranked.shape[0]) > 0)
    filtered = mx.where(remove, -float("inf"), ranked) / max(temperature, 1e-5)
    selected = mx.random.categorical(filtered)
    result = order[selected]
    mx.eval(result)
    return int(result.item())


def generate(*, model: Any, prompt: Any, max_new_tokens: int,
             decode_one_token: Any = None, **sampling: Any) -> Any:
    import torch

    del decode_one_token
    mx = model.mx
    if prompt.ndim != 2 or prompt.shape[0] != 9:
        raise ValueError("Fish prompt must contain nine token streams")
    prompt_length = prompt.shape[1]
    if prompt_length < 1 or prompt_length >= 8192:
        raise ValueError("Fish prompt length is invalid")
    count = min(max_new_tokens or 8192 - prompt_length, 8192 - prompt_length)
    if count <= 0:
        raise ValueError("Fish generation length is invalid")
    params = {
        key: float(value.item() if hasattr(value, "item") else value)
        for key, value in sampling.items()
        if key in {"temperature", "top_p", "repetition_penalty"}
    }
    if set(params) != {"temperature", "top_p", "repetition_penalty"}:
        raise ValueError("Fish sampling parameters are incomplete")
    model.reset()
    current = mx.array(prompt.detach().cpu().numpy())
    generated: list[list[int]] = []
    previous: list[list[int]] = [[] for _ in range(9)]
    end = model.tokenizer.get_token_id("<|im_end|>")

    for step in range(count):
        logits, hidden = model.slow(current)
        window = None
        if step:
            window = [
                (values[-16:] if len(values) >= 16 else values + [0] * (16 - len(values)))
                for values in previous
            ]
        token = sample(mx, logits, None if window is None else window[0], **params)
        model.fast_cache = [None] * 4
        model.fast(hidden)
        first = max(0, token - model.tokenizer.semantic_begin_id)
        if first >= 1024:
            raise ValueError("Fish semantic token is outside the codebook")
        codebooks = [token, first]
        embedding = model.tensors["fast_embeddings.weight"][first]
        for index in range(1, 8):
            logits = model.fast(embedding)
            code = sample(mx, logits, None if window is None else window[index + 1], **params)
            codebooks.append(code)
            embedding = model.tensors["fast_embeddings.weight"][code]
        generated.append(codebooks)
        if step:
            for index, value in enumerate(codebooks):
                previous[index].append(value)
        current = mx.array(codebooks, dtype=mx.int32).reshape(9, 1)
        if step and token == end:
            break
    output = torch.tensor(generated, dtype=prompt.dtype, device=prompt.device).T
    return torch.cat((prompt, output), dim=1)
