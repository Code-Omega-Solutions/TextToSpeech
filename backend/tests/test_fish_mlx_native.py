"""Synthetic numerical checks; these never load a model or generate speech."""

import unittest

try:
    import mlx.core as mx
except ModuleNotFoundError:
    mx = None


@unittest.skipIf(mx is None, "MLX is available only in the candidate environment")
class NativeMLXTest(unittest.TestCase):
    def test_sampling_and_eight_codebook_generation(self):
        import torch

        from deployment.fish_mlx.generation import generate, sample

        self.assertEqual(
            sample(mx, mx.array([2.0, 1.9]), [0], 0.7, 0.01, 2.0 - 1e-5), 1
        )

        class Tokenizer:
            semantic_begin_id = 0

            def get_token_id(self, _token):
                return 3

        class Model:
            tokenizer = Tokenizer()
            tensors = {"fast_embeddings.weight": mx.zeros((1024, 1024), dtype=mx.float16)}

            def __init__(self):
                self.mx = mx
                self.slow_lengths = []
                self.fast_calls = 0

            def reset(self):
                self.slow_lengths = []

            def slow(self, tokens):
                self.slow_lengths.append(tokens.shape[1])
                return mx.array([10.0, -10.0, -10.0, -10.0]), mx.zeros((1, 1, 1024))

            def fast(self, _hidden):
                self.fast_calls += 1
                return mx.concatenate((mx.array([-10.0, 10.0]), mx.full((1022,), -10.0)))

        model = Model()
        prompt = torch.zeros((9, 3), dtype=torch.int32)
        output = generate(
            model=model, prompt=prompt, max_new_tokens=2,
            temperature=0.7, top_p=0.01, repetition_penalty=1.2,
        )
        self.assertEqual(tuple(output.shape), (9, 5))
        self.assertEqual(model.slow_lengths, [3, 1])
        self.assertEqual(model.fast_calls, 16)
        self.assertTrue(torch.equal(output[2:, 3:], torch.ones((7, 2), dtype=torch.int32)))

    def test_packed_transformer_block_matches_dequantized_torch(self):
        import numpy as np
        import torch
        import torch.nn.functional as F

        from deployment.fish_mlx.model import DualAR

        rng = np.random.default_rng(42)
        shapes = {
            "attention.wqkv": (1280, 1024),
            "attention.wo": (1024, 1024),
            "feed_forward.w1": (4096, 1024),
            "feed_forward.w3": (4096, 1024),
            "feed_forward.w2": (1024, 4096),
        }
        tensors = {}
        reference = {}
        for name, shape in shapes.items():
            array = mx.array((rng.standard_normal(shape) * 0.01).astype(np.float16))
            packed, scales, biases = mx.quantize(array, group_size=64, bits=4, mode="affine")
            reconstructed = mx.dequantize(
                packed, scales, biases, group_size=64, bits=4, mode="affine"
            )
            mx.eval(packed, scales, biases, reconstructed)
            tensors[f"block.{name}.weight"] = packed
            tensors[f"block.{name}.scales"] = scales
            tensors[f"block.{name}.biases"] = biases
            reference[name] = torch.from_numpy(np.array(reconstructed))
        for name in ("attention_norm", "ffn_norm"):
            tensors[f"block.{name}.weight"] = mx.ones((1024,), dtype=mx.float16)

        def norm(x):
            f = x.float()
            return (f * torch.rsqrt((f * f).mean(dim=-1, keepdim=True) + 1e-6)).half()

        def rotary(x):
            length = x.shape[1]
            f = 1.0 / (1000000.0 ** (torch.arange(0, 64, 2).float() / 64))
            angle = torch.outer(torch.arange(length).float(), f)
            cos = angle.cos().bfloat16().half().float()[None, :, None, :]
            sin = angle.sin().bfloat16().half().float()[None, :, None, :]
            pairs = x.float().reshape(*x.shape[:-1], 32, 2)
            return torch.stack(
                (pairs[..., 0] * cos - pairs[..., 1] * sin,
                 pairs[..., 1] * cos + pairs[..., 0] * sin), dim=-1
            ).reshape(x.shape).half()

        def torch_block(x):
            length = x.shape[1]
            qkv = F.linear(norm(x), reference["attention.wqkv"])
            q = rotary(qkv[..., :1024].reshape(1, length, 16, 64)).transpose(1, 2)
            k = rotary(qkv[..., 1024:1152].reshape(1, length, 2, 64)).transpose(1, 2)
            v = qkv[..., 1152:].reshape(1, length, 2, 64).transpose(1, 2)
            y = F.scaled_dot_product_attention(
                q, k.repeat_interleave(8, dim=1), v.repeat_interleave(8, dim=1),
                is_causal=True
            ).transpose(1, 2).reshape(1, length, 1024)
            h = x + F.linear(y, reference["attention.wo"])
            n = norm(h)
            return h + F.linear(
                F.silu(F.linear(n, reference["feed_forward.w1"]))
                * F.linear(n, reference["feed_forward.w3"]),
                reference["feed_forward.w2"],
            )

        model = DualAR.__new__(DualAR)
        model.mx = mx
        model.tensors = tensors
        data = (rng.standard_normal((1, 4, 1024)) * 0.1).astype(np.float16)
        cache = [None]
        first = model.block(mx.array(data[:, :3]), "block", cache, 0)
        last = model.block(mx.array(data[:, 3:]), "block", cache, 0)
        mx.eval(first, last)
        expected = torch_block(torch.from_numpy(data)).numpy()
        np.testing.assert_allclose(np.array(first), expected[:, :3], atol=0.005, rtol=0.02)
        np.testing.assert_allclose(np.array(last), expected[:, 3:], atol=0.005, rtol=0.02)
        self.assertEqual(cache[0][0].shape, (1, 2, 4, 64))


if __name__ == "__main__":
    unittest.main()
