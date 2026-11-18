from types import SimpleNamespace
import queue

import pytest

from deployment.fish_mlx.worker import generation_queue, validate_reference_request


@pytest.mark.parametrize("reference", ["de-female", "de-male", "en-female", "en-male"])
def test_candidate_accepts_only_existing_qualified_references(reference):
    validate_reference_request(SimpleNamespace(reference_id=reference, references=[]))


@pytest.mark.parametrize("reference", [None, "unknown", "../de-female"])
def test_candidate_rejects_unqualified_reference(reference):
    with pytest.raises(ValueError, match="qualified"):
        validate_reference_request(SimpleNamespace(reference_id=reference, references=[]))


def test_candidate_rejects_inline_reference_even_with_qualified_id():
    with pytest.raises(ValueError, match="qualified"):
        validate_reference_request(SimpleNamespace(reference_id="de-female", references=[object()]))


def test_generation_queue_forwards_contract_and_sanitizes_errors(caplog):
    seen = []

    def generate_long(**kwargs):
        seen.append(kwargs)
        if kwargs["text"] == "error":
            raise RuntimeError("sensitive content")
        yield "sample"
        yield "next"

    upstream = SimpleNamespace(
        generate_long=generate_long,
        WrappedGenerateResponse=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    model = object()
    requests = generation_queue(upstream, model)
    responses = queue.Queue()
    requests.put(SimpleNamespace(request={"text": "test"}, response_queue=responses))
    assert responses.get(timeout=2).response == "sample"
    assert responses.get(timeout=2).response == "next"
    assert seen[0] == {"model": model, "decode_one_token": None, "text": "test"}
    requests.put(SimpleNamespace(request={"text": "error"}, response_queue=responses))
    failure = responses.get(timeout=2)
    assert failure.status == "error"
    assert str(failure.response) == "Fish MLX generation failed"
    assert "sensitive content" not in caplog.text
    requests.put(None)
