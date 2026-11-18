"""Compatibility checks for the approved Fish Speech 1.5 semantic model."""

from collections.abc import Mapping, Sequence


APPROVED_CONFIG = {
    "attention_qkv_bias": False,
    "codebook_size": 1024,
    "dim": 1024,
    "dropout": 0.0,
    "fast_attention_qkv_bias": False,
    "fast_dim": 1024,
    "fast_head_dim": 64,
    "fast_intermediate_size": 4096,
    "fast_n_head": 16,
    "fast_n_local_heads": 2,
    "head_dim": 64,
    "initializer_range": 0.02,
    "intermediate_size": 4096,
    "is_reward_model": False,
    "max_seq_len": 8192,
    "model_type": "dual_ar",
    "n_fast_layer": 4,
    "n_head": 16,
    "n_layer": 24,
    "n_local_heads": 2,
    "norm_eps": 1e-6,
    "num_codebooks": 8,
    "rope_base": 1000000.0,
    "tie_word_embeddings": False,
    "use_gradient_checkpointing": True,
    "vocab_size": 102048,
}

_OPTIONAL_DEFAULTS = {
    "share_codebook_embeddings": True,
    "scale_codebook_embeddings": False,
}


def validate_config(config: Mapping[str, object]) -> None:
    allowed = APPROVED_CONFIG | _OPTIONAL_DEFAULTS
    if set(config) - set(allowed) or set(APPROVED_CONFIG) - set(config):
        raise ValueError("Incompatible Fish 1.5 configuration fields")
    for key, expected in allowed.items():
        actual = config.get(key, expected)
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"Incompatible Fish 1.5 configuration: {key}")


def expected_tensor_shapes() -> dict[str, tuple[int, ...]]:
    shapes = {
        "embeddings.weight": (102048, 1024),
        "codebook_embeddings.weight": (8192, 1024),
        "norm.weight": (1024,),
        "output.weight": (102048, 1024),
        "fast_embeddings.weight": (1024, 1024),
        "fast_norm.weight": (1024,),
        "fast_output.weight": (1024, 1024),
    }
    block = {
        "attention.wqkv.weight": (1280, 1024),
        "attention.wo.weight": (1024, 1024),
        "feed_forward.w1.weight": (4096, 1024),
        "feed_forward.w3.weight": (4096, 1024),
        "feed_forward.w2.weight": (1024, 4096),
        "ffn_norm.weight": (1024,),
        "attention_norm.weight": (1024,),
    }
    for prefix, count in (("layers", 24), ("fast_layers", 4)):
        for index in range(count):
            shapes.update(
                (f"{prefix}.{index}.{name}", shape) for name, shape in block.items()
            )
    return shapes


def validate_tensor_shapes(shapes: Mapping[str, Sequence[int]]) -> None:
    expected = expected_tensor_shapes()
    if set(shapes) != set(expected):
        raise ValueError("Incompatible Fish 1.5 tensor inventory")
    if any(tuple(shapes[name]) != shape for name, shape in expected.items()):
        raise ValueError("Incompatible Fish 1.5 tensor shape")
