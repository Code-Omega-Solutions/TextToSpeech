import pytest
from types import SimpleNamespace

from deployment.fish_mlx.conversion import (
    convert_tensors,
    expected_derived_tensors,
    validate_derived_tensors,
)
from deployment.fish_mlx.prepare import isolated_destination, prepare
from deployment.fish_mlx.validation import expected_tensor_shapes


def test_derived_inventory_requires_packed_attention_and_feed_forward():
    inventory = expected_derived_tensors()
    assert inventory["layers.0.attention.wqkv.weight"] == ((1280, 128), "uint32")
    assert inventory["layers.0.attention.wqkv.scales"] == ((1280, 16), "float16")
    assert inventory["layers.0.attention.wqkv.biases"] == ((1280, 16), "float16")
    assert inventory["embeddings.weight"] == ((102048, 1024), "float16")
    assert inventory["output.weight"] == ((102048, 1024), "float16")
    assert len(inventory) == 483
    validate_derived_tensors(inventory)


@pytest.mark.parametrize("kind", ["missing", "extra", "dtype", "shape"])
def test_derived_inventory_rejects_tampering(kind):
    inventory = expected_derived_tensors()
    key = "fast_layers.3.feed_forward.w2.weight"
    if kind == "missing":
        del inventory[key]
    elif kind == "extra":
        inventory["extra"] = ((1,), "float16")
    elif kind == "dtype":
        inventory[key] = (inventory[key][0], "float16")
    else:
        inventory[key] = ((1, 1), "uint32")
    with pytest.raises(ValueError):
        validate_derived_tensors(inventory)


def test_destination_must_be_new_and_outside_protected_tree(tmp_path):
    protected = tmp_path / "approved"
    protected.mkdir()
    with pytest.raises(ValueError, match="overlaps"):
        isolated_destination(protected / "candidate", (protected,))
    with pytest.raises(ValueError, match="already exists"):
        isolated_destination(protected, (protected,))
    candidate = tmp_path / "candidate"
    assert isolated_destination(candidate, (protected,)) == candidate.resolve()
    assert not candidate.exists()


def test_prepare_refuses_before_creating_directory_without_approval(monkeypatch, tmp_path):
    monkeypatch.setattr("deployment.fish_mlx.prepare.platform.system", lambda: "Darwin")
    monkeypatch.setattr("deployment.fish_mlx.prepare.platform.machine", lambda: "arm64")
    monkeypatch.setattr(
        "deployment.fish_mlx.prepare.sys.flags", SimpleNamespace(isolated=1, no_site=1)
    )
    monkeypatch.setattr("deployment.fish_mlx.prepare.sys.dont_write_bytecode", True)
    monkeypatch.delenv("TTS_FISH_SOURCE_ROOT", raising=False)
    candidate = tmp_path / "candidate"
    with pytest.raises(SystemExit, match="TTS_FISH_SOURCE_ROOT"):
        prepare(candidate)
    assert not candidate.exists()


def test_conversion_quantizes_only_supported_transformer_matrices():
    class Array:
        def __init__(self, shape, dtype):
            self.shape, self.dtype = shape, dtype

        def detach(self):
            return self

        def to(self, *, dtype, device):
            assert device == "cpu"
            return Array(self.shape, dtype)

        def numpy(self):
            return self

    class Torch:
        bfloat16 = "bfloat16"
        float16 = "float16"

    class MLX:
        calls = 0

        @staticmethod
        def array(value):
            return value

        @classmethod
        def quantize(cls, value, *, group_size, bits, mode):
            assert (group_size, bits, mode) == (64, 4, "affine")
            cls.calls += 1
            rows, columns = value.shape
            return (
                Array((rows, columns // 8), "uint32"),
                Array((rows, columns // 64), "float16"),
                Array((rows, columns // 64), "float16"),
            )

        @staticmethod
        def eval(*values):
            assert values

    weights = {name: Array(shape, "bfloat16") for name, shape in expected_tensor_shapes().items()}
    checks = []
    converted = convert_tensors(weights, MLX, Torch, lambda: checks.append(True))
    assert MLX.calls == 140
    assert len(converted) == 483
    assert len(checks) == 406
    weights["output.weight"].dtype = "float32"
    with pytest.raises(ValueError, match="dtype"):
        convert_tensors(weights, MLX, Torch, lambda: None)
