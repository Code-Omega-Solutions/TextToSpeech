"""Fish 1.5 semantic weight conversion primitives.

These primitives do not authorize a checkpoint or a destination. Callers must
validate the existing artifact approvals before conversion.
"""

from collections.abc import Callable, Mapping
import re
from typing import Any

from .validation import expected_tensor_shapes, validate_tensor_shapes

GROUP_SIZE = 64
BITS = 4
FP16_SLOW_LAYERS = 8
_LINEAR = re.compile(
    r"^(?:fast_)?layers\.\d+\."
    r"(?:attention\.(?:wqkv|wo)|feed_forward\.(?:w1|w2|w3))\.weight$"
)


def is_quantized_weight(name: str) -> bool:
    if not _LINEAR.fullmatch(name):
        return False
    return not any(name.startswith(f"layers.{index}.") for index in range(FP16_SLOW_LAYERS))


def expected_derived_tensors() -> dict[str, tuple[tuple[int, ...], str]]:
    result: dict[str, tuple[tuple[int, ...], str]] = {}
    for name, shape in expected_tensor_shapes().items():
        if not is_quantized_weight(name):
            result[name] = (shape, "float16")
            continue
        rows, columns = shape
        prefix = name.removesuffix(".weight")
        result[name] = ((rows, columns // 8), "uint32")
        result[prefix + ".scales"] = ((rows, columns // GROUP_SIZE), "float16")
        result[prefix + ".biases"] = ((rows, columns // GROUP_SIZE), "float16")
    return result


def validate_derived_tensors(
    inventory: Mapping[str, tuple[tuple[int, ...], str]],
) -> None:
    if dict(inventory) != expected_derived_tensors():
        raise ValueError("Incompatible Fish MLX tensor inventory")


def inspect_mlx_tensors(tensors: Mapping[str, Any]) -> None:
    validate_derived_tensors(
        {
            name: (tuple(value.shape), str(value.dtype).rsplit(".", 1)[-1])
            for name, value in tensors.items()
        }
    )


def convert_tensors(
    weights: Mapping[str, Any],
    mx: Any,
    torch: Any,
    check_resources: Callable[[], None],
) -> dict[str, Any]:
    validate_tensor_shapes({name: tuple(value.shape) for name, value in weights.items()})
    if any(value.dtype != torch.bfloat16 for value in weights.values()):
        raise ValueError("Incompatible Fish checkpoint tensor dtype")
    converted = {}
    for name, value in weights.items():
        check_resources()
        tensor = mx.array(value.detach().to(dtype=torch.float16, device="cpu").numpy())
        if is_quantized_weight(name):
            packed, scales, biases = mx.quantize(
                tensor, group_size=GROUP_SIZE, bits=BITS, mode="affine"
            )
            mx.eval(packed, scales, biases)
            prefix = name.removesuffix(".weight")
            converted[name] = packed
            converted[prefix + ".scales"] = scales
            converted[prefix + ".biases"] = biases
        else:
            mx.eval(tensor)
            converted[name] = tensor
        check_resources()
    inspect_mlx_tensors(converted)
    return converted
