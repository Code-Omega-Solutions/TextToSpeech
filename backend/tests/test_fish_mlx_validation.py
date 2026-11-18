import pytest

from deployment.fish_mlx.validation import (
    APPROVED_CONFIG,
    expected_tensor_shapes,
    validate_config,
    validate_tensor_shapes,
)


def test_approved_config_and_tensor_inventory():
    validate_config(dict(APPROVED_CONFIG))
    shapes = expected_tensor_shapes()
    assert len(shapes) == 203
    validate_tensor_shapes(shapes)


@pytest.mark.parametrize(
    "changes",
    [
        {"model_type": "naive"},
        {"n_fast_layer": 5},
        {"num_codebooks": 4},
        {"rope_base": 10000.0},
        {"tie_word_embeddings": True},
        {"share_codebook_embeddings": False},
        {"unexpected": 1},
    ],
)
def test_incompatible_config_is_rejected(changes):
    with pytest.raises(ValueError):
        validate_config(dict(APPROVED_CONFIG, **changes))


def test_missing_or_mismatched_tensors_are_rejected():
    shapes = expected_tensor_shapes()
    shapes.pop("output.weight")
    with pytest.raises(ValueError):
        validate_tensor_shapes(shapes)
    shapes["output.weight"] = (1, 1024)
    with pytest.raises(ValueError):
        validate_tensor_shapes(shapes)
