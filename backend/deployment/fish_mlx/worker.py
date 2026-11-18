"""Bridge the original Fish API and Firefly codec to MLX semantic generation."""

from __future__ import annotations

import importlib.metadata
import logging
import os
import queue
import sys
import threading
from pathlib import Path
from typing import Any


def validate_reference_request(request: Any) -> None:
    if request.references or request.reference_id not in {
        "de-female", "de-male", "en-female", "en-male"
    }:
        raise ValueError("Fish MLX requires a qualified reference")


class _PrivateGenerationLogger:
    def __init__(self, original: Any):
        self.original = original

    def info(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def __getattr__(self, name: str) -> Any:
        return getattr(self.original, name)


def generation_queue(upstream: Any, model: Any) -> queue.Queue:
    requests: queue.Queue = queue.Queue()

    def run() -> None:
        while True:
            item = requests.get()
            if item is None:
                return
            try:
                for response in upstream.generate_long(
                    model=model, decode_one_token=None, **item.request
                ):
                    item.response_queue.put(
                        upstream.WrappedGenerateResponse(status="success", response=response)
                    )
            except Exception as exc:
                logging.getLogger(__name__).error(
                    "Fish MLX generation failed: %s", type(exc).__name__
                )
                item.response_queue.put(
                    upstream.WrappedGenerateResponse(
                        status="error", response=RuntimeError("Fish MLX generation failed")
                    )
                )

    threading.Thread(target=run, name="fish-mlx-generation", daemon=True).start()
    return requests


def serve(host: str, port: int) -> None:
    import mlx.core as mx
    import uvicorn
    from fish_speech.models.text2semantic.llama import BaseModelArgs
    from fish_speech.tokenizer import FishTokenizer
    from tools import inference_engine
    from tools.llama import generate as upstream
    from tools.server import model_manager
    from tools import api_server

    from deployment.fish_mlx.conversion import inspect_mlx_tensors
    from deployment.fish_mlx.generation import generate
    from deployment.fish_mlx.model import DualAR

    if mx.__version__ != "0.32.4" or importlib.metadata.version("mlx-metal") != "0.32.4":
        raise RuntimeError("Fish MLX runtime version does not match approval")
    checkpoint = Path(os.environ["TTS_FISH_CHECKPOINT_ROOT"]).resolve()
    candidate = Path(os.environ["TTS_FISH_MLX_CANDIDATE_ROOT"]).resolve()
    original_seed = inference_engine.set_seed
    original_inference = inference_engine.TTSInferenceEngine.inference

    def qualified_inference(self: Any, request: Any):
        validate_reference_request(request)
        yield from original_inference(self, request)

    inference_engine.TTSInferenceEngine.inference = qualified_inference

    def set_seed(seed: int) -> None:
        original_seed(seed)
        mx.random.seed(seed)

    inference_engine.set_seed = set_seed
    upstream.generate = generate
    upstream.logger = _PrivateGenerationLogger(upstream.logger)

    def launch_queue(**_kwargs: Any) -> queue.Queue:
        weights = mx.load(str(candidate / "semantic.safetensors"))
        inspect_mlx_tensors(weights)
        mx.eval(*weights.values())
        tokenizer = FishTokenizer(str(checkpoint / "tokenizer.tiktoken"))
        model = DualAR(mx, weights, tokenizer)
        model.config = BaseModelArgs.from_pretrained(str(checkpoint))
        return generation_queue(upstream, model)

    model_manager.launch_thread_safe_queue = launch_queue
    model_manager.ModelManager.warm_up = lambda self, engine: None
    decoder = checkpoint / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    os.chdir(Path(os.environ["TTS_FISH_REFERENCE_ROOT"]).resolve())
    sys.argv = [
        "fish-mlx-worker", "--mode", "tts", "--listen", f"{host}:{port}", "--workers", "1",
        "--device", "mps", "--half", "--max-text-length", "5000",
        "--llama-checkpoint-path", str(checkpoint),
        "--decoder-checkpoint-path", str(decoder),
        "--decoder-config-name", "firefly_gan_vq",
    ]
    api = api_server.API()
    uvicorn.run(api.app, host=host, port=port, workers=1, log_level="info")
