"""Optional approved-source bridge check; uses synthetic codes and no audio."""

import os
import queue
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


@unittest.skipUnless(
    os.environ.get("TTS_FISH_MLX_SYNTHETIC_BRIDGE_TEST") == "1",
    "requires explicitly selected approved Fish source and checkpoint",
)
class UpstreamBridgeTest(unittest.TestCase):
    def test_upstream_prompt_and_code_transport_without_audio(self):
        source = Path(os.environ["TTS_FISH_SOURCE_ROOT"]).resolve(strict=True)
        checkpoint = Path(os.environ["TTS_FISH_CHECKPOINT_ROOT"]).resolve(strict=True)
        sys.path.insert(0, str(source))
        try:
            import torch
            from fish_speech.models.text2semantic.llama import BaseModelArgs
            from fish_speech.tokenizer import FishTokenizer
            from tools.llama import generate as upstream

            from deployment.fish_mlx.worker import _PrivateGenerationLogger, generation_queue

            class Model:
                tokenizer = FishTokenizer(str(checkpoint / "tokenizer.tiktoken"))
                config = BaseModelArgs.from_pretrained(str(checkpoint))

                def parameters(self):
                    return iter(())

            def synthetic_generate(*, prompt, **_kwargs):
                continuation = torch.zeros((9, 3), dtype=prompt.dtype, device=prompt.device)
                return torch.cat((prompt, continuation), dim=1)

            with patch.object(upstream, "generate", synthetic_generate), patch.object(
                upstream, "logger", _PrivateGenerationLogger(upstream.logger)
            ):
                requests = generation_queue(upstream, Model())
                for prompt in (False, True):
                    request = dict(
                        device="cpu", text="test", max_new_tokens=3, top_p=0.7,
                        repetition_penalty=1.2, temperature=0.7, chunk_length=150,
                    )
                    if prompt:
                        request.update(
                            prompt_text=["test"],
                            prompt_tokens=[torch.zeros((8, 2), dtype=torch.int)],
                        )
                    responses = queue.Queue()
                    requests.put(SimpleNamespace(request=request, response_queue=responses))
                    sample = responses.get(timeout=30)
                    end = responses.get(timeout=30)
                    self.assertEqual((sample.status, sample.response.action), ("success", "sample"))
                    self.assertEqual(tuple(sample.response.codes.shape), (8, 2))
                    self.assertEqual((end.status, end.response.action), ("success", "next"))
                requests.put(None)
        finally:
            sys.path.remove(str(source))


if __name__ == "__main__":
    unittest.main()
