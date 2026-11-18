"""MLX execution of the approved Fish Speech 1.5 DualAR transformer."""

from __future__ import annotations

from typing import Any


class DualAR:
    def __init__(self, mx: Any, tensors: dict[str, Any], tokenizer: Any):
        from .conversion import inspect_mlx_tensors

        inspect_mlx_tensors(tensors)
        self.mx = mx
        self.tensors = tensors
        self.tokenizer = tokenizer
        self.semantic_ids = mx.array(
            [tokenizer.get_token_id(f"<|semantic:{i}|>") for i in range(1024)]
        )
        self.slow_cache: list[tuple[Any, Any] | None] = [None] * 24
        self.fast_cache: list[tuple[Any, Any] | None] = [None] * 4

    def reset(self) -> None:
        self.slow_cache = [None] * 24
        self.fast_cache = [None] * 4

    def parameters(self):
        return iter(())

    def linear(self, x: Any, prefix: str, quantized: bool = True) -> Any:
        mx = self.mx
        weight = self.tensors[prefix + ".weight"]
        if not quantized:
            return x @ weight.T
        return mx.quantized_matmul(
            x,
            weight,
            self.tensors[prefix + ".scales"],
            self.tensors[prefix + ".biases"],
            transpose=True,
            group_size=64,
            bits=4,
            mode="affine",
        )

    def norm(self, x: Any, prefix: str) -> Any:
        mx = self.mx
        f = x.astype(mx.float32)
        normalized = f * mx.rsqrt(mx.mean(f * f, axis=-1, keepdims=True) + 1e-6)
        return normalized.astype(x.dtype) * self.tensors[prefix + ".weight"]

    def rotary(self, x: Any, offset: int) -> Any:
        mx = self.mx
        sequence = x.shape[1]
        freq = 1.0 / (1000000.0 ** (mx.arange(0, 64, 2, dtype=mx.float32) / 64))
        angle = mx.arange(offset, offset + sequence, dtype=mx.float32)[:, None] * freq
        cos = mx.cos(angle).astype(mx.bfloat16).astype(x.dtype).astype(mx.float32)
        sin = mx.sin(angle).astype(mx.bfloat16).astype(x.dtype).astype(mx.float32)
        pairs = x.astype(mx.float32).reshape(*x.shape[:-1], 32, 2)
        cos = cos[None, :, None, :]
        sin = sin[None, :, None, :]
        return mx.stack(
            (pairs[..., 0] * cos - pairs[..., 1] * sin,
             pairs[..., 1] * cos + pairs[..., 0] * sin),
            axis=-1,
        ).reshape(*x.shape).astype(x.dtype)

    def block(self, x: Any, prefix: str, cache: list, index: int) -> Any:
        mx = self.mx
        previous = cache[index]
        offset = 0 if previous is None else previous[0].shape[2]
        b, length, _ = x.shape
        normed = self.norm(x, prefix + ".attention_norm")
        qkv = self.linear(normed, prefix + ".attention.wqkv")
        q = qkv[..., :1024].reshape(b, length, 16, 64)
        k = qkv[..., 1024:1152].reshape(b, length, 2, 64)
        v = qkv[..., 1152:].reshape(b, length, 2, 64)
        q = self.rotary(q, offset).transpose(0, 2, 1, 3)
        k = self.rotary(k, offset).transpose(0, 2, 1, 3)
        v = v.transpose(0, 2, 1, 3)
        if previous is not None:
            k = mx.concatenate((previous[0], k), axis=2)
            v = mx.concatenate((previous[1], v), axis=2)
        cache[index] = (k, v)
        keys = mx.repeat(k, 8, axis=1)
        values = mx.repeat(v, 8, axis=1)
        allowed = mx.arange(k.shape[2])[None, :] <= (
            mx.arange(length)[:, None] + offset
        )
        mask = mx.where(allowed, mx.array(0.0), mx.array(-float("inf"))).astype(q.dtype)
        attention = mx.fast.scaled_dot_product_attention(
            q, keys, values, scale=0.125, mask=mask
        )
        attention = attention.transpose(0, 2, 1, 3).reshape(b, length, 1024)
        h = x + self.linear(attention, prefix + ".attention.wo")
        normed = self.norm(h, prefix + ".ffn_norm")
        a = self.linear(normed, prefix + ".feed_forward.w1")
        gate = a * mx.sigmoid(a)
        ff = gate * self.linear(normed, prefix + ".feed_forward.w3")
        return h + self.linear(ff, prefix + ".feed_forward.w2")

    def slow(self, tokens: Any) -> tuple[Any, Any]:
        mx = self.mx
        if tokens.ndim != 2 or tokens.shape[0] != 9:
            raise ValueError("Fish prompt must contain nine token streams")
        if tokens.shape[1] == 0 or tokens.shape[1] > 8192:
            raise ValueError("Fish prompt length is invalid")
        if self.slow_cache[0] is not None:
            if self.slow_cache[0][0].shape[2] + tokens.shape[1] > 8192:
                raise ValueError("Fish semantic cache is full")
        token = tokens[0]
        x = self.tensors["embeddings.weight"][token]
        code = mx.stack([
            self.tensors["codebook_embeddings.weight"][tokens[i + 1] + i * 1024]
            for i in range(8)
        ], axis=0).sum(axis=0)
        semantic = mx.any(token[:, None] == self.semantic_ids[None, :], axis=-1)
        x = (x + mx.where(semantic[:, None], code, mx.zeros_like(code)))[None, :, :]
        for i in range(24):
            x = self.block(x, f"layers.{i}", self.slow_cache, i)
        hidden = x[:, -1:, :]
        logits = self.linear(self.norm(hidden, "norm"), "output", quantized=False)
        return logits[0, 0], hidden

    def fast(self, x: Any) -> Any:
        if self.fast_cache[0] is not None and self.fast_cache[0][0].shape[2] >= 8:
            raise ValueError("Fish codebook cache is full")
        x = x.reshape(1, 1, 1024)
        for i in range(4):
            x = self.block(x, f"fast_layers.{i}", self.fast_cache, i)
        return self.linear(self.norm(x, "fast_norm"), "fast_output", quantized=False)[0, 0]
