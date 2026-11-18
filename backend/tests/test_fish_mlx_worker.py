import queue
import sys
from types import ModuleType, SimpleNamespace

import pytest

from deployment.fish_mlx import worker
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


def test_serve_wires_original_api_queue_and_qualified_references(monkeypatch, tmp_path):
    def module(name, **attributes):
        result = ModuleType(name)
        result.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, result)
        return result

    seeded = []
    mx = module(
        "mlx.core", __version__="0.32.4", random=SimpleNamespace(seed=seeded.append),
        load=lambda _path: {"synthetic": object()}, eval=lambda *_args: None,
    )
    module("mlx", core=mx)
    runs = []
    module("uvicorn", run=lambda *args, **kwargs: runs.append((args, kwargs)))

    class Engine:
        def inference(self, request):
            yield request.reference_id

    inference = module(
        "tools.inference_engine", TTSInferenceEngine=Engine,
        set_seed=lambda seed: seeded.append(("original", seed)),
    )
    upstream = module(
        "tools.llama.generate", logger=SimpleNamespace(info=lambda *_args: None),
        generate_long=lambda **_kwargs: iter(["synthetic-codes"]),
        WrappedGenerateResponse=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    manager = module("tools.server.model_manager", ModelManager=type("Manager", (), {}))
    api = module("tools.api_server", API=lambda: SimpleNamespace(app="synthetic-app"))
    module("tools.llama", generate=upstream)
    module("tools.server", model_manager=manager)
    module("tools", inference_engine=inference, api_server=api)
    module(
        "fish_speech.models.text2semantic.llama",
        BaseModelArgs=SimpleNamespace(from_pretrained=lambda _path: "config"),
    )
    module("fish_speech.tokenizer", FishTokenizer=lambda _path: "tokenizer")

    class Model:
        def __init__(self, _mx, weights, tokenizer):
            assert weights.keys() == {"synthetic"}
            assert tokenizer == "tokenizer"

    monkeypatch.setattr("deployment.fish_mlx.conversion.inspect_mlx_tensors", lambda _weights: None)
    monkeypatch.setattr("deployment.fish_mlx.model.DualAR", Model)
    monkeypatch.setattr(worker.importlib.metadata, "version", lambda _package: "0.32.4")
    monkeypatch.setenv("TTS_FISH_CHECKPOINT_ROOT", str(tmp_path))
    monkeypatch.setenv("TTS_FISH_MLX_CANDIDATE_ROOT", str(tmp_path))
    monkeypatch.setenv("TTS_FISH_REFERENCE_ROOT", str(tmp_path))
    monkeypatch.setattr(worker.os, "chdir", lambda _path: None)
    monkeypatch.setattr(sys, "argv", [])
    worker.serve("127.0.0.1", 8002)

    assert runs == [(("synthetic-app",), {
        "host": "127.0.0.1", "port": 8002, "workers": 1, "log_level": "info"
    })]
    assert "--half" in sys.argv and "--decoder-config-name" in sys.argv
    inference.set_seed(42)
    assert seeded == [("original", 42), 42]
    assert list(Engine().inference(SimpleNamespace(references=[], reference_id="en-female"))) == [
        "en-female"
    ]
    with pytest.raises(ValueError, match="qualified"):
        list(Engine().inference(SimpleNamespace(references=[], reference_id="unknown")))
    responses = queue.Queue()
    requests = manager.launch_thread_safe_queue()
    requests.put(SimpleNamespace(request={}, response_queue=responses))
    assert responses.get(timeout=2).response == "synthetic-codes"
    requests.put(None)
    assert manager.ModelManager().warm_up(None) is None
