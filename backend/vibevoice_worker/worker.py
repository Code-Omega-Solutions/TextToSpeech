from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any, BinaryIO

_SOURCE_REVISION = "0063f5b175d07c0a7d0aab2c5806bee9aa15f2a1"
_TOKENIZER_REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"
_MAX_PROTOCOL_LINE_BYTES = 64 * 1024
_MAX_AUDIO_BYTES = int(os.environ.get("TTS_MAX_OUTPUT_BYTES", "26214400"))
_VOICE_FILES = {
    "en-Carter_man": "en-carter_man",
    "de-Spk1_woman": "de-spk1_woman",
    "de-Spk0_man": "de-spk0_man",
}


class WorkerError(RuntimeError):
    pass


def serve(engine: Any, stdin: BinaryIO | None = None, stdout: BinaryIO | None = None) -> None:
    source = stdin or sys.stdin.buffer
    destination = stdout or sys.stdout.buffer
    while True:
        line = source.readline(_MAX_PROTOCOL_LINE_BYTES + 1)
        if not line:
            return
        request_id = _request_id_from_line(line)
        try:
            if len(line) > _MAX_PROTOCOL_LINE_BYTES or not line.endswith(b"\n"):
                raise WorkerError("invalid_request")
            request = json.loads(line)
            _validate_request(request)
            engine.synthesize(request)
            response = {"request_id": request["request_id"], "status": "ok"}
        except WorkerError as exc:
            response = {
                "request_id": request_id,
                "status": "error",
                "reason": str(exc),
            }
        except Exception:
            response = {
                "request_id": request_id,
                "status": "error",
                "reason": "generation_failed",
            }
        encoded = (json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8")
        destination.write(encoded)
        destination.flush()


def _request_id_from_line(line: bytes) -> str:
    try:
        value = json.loads(line).get("request_id")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return "invalid"
    return value if isinstance(value, str) and len(value) <= 128 else "invalid"


def _validate_request(request: Any) -> None:
    if not isinstance(request, dict) or set(request) != {
        "request_id",
        "text",
        "locale",
        "voice",
        "output_path",
    }:
        raise WorkerError("invalid_request")
    if not isinstance(request["request_id"], str) or not re.fullmatch(
        r"[a-f0-9]{32}", request["request_id"]
    ):
        raise WorkerError("invalid_request")
    text = request["text"]
    if not isinstance(text, str) or not text:
        raise WorkerError("invalid_request")
    try:
        if len(text.encode("utf-16-le")) // 2 > 5000:
            raise WorkerError("invalid_request")
    except UnicodeEncodeError:
        raise WorkerError("invalid_request") from None
    locale = request["locale"]
    voice = request["voice"]
    if locale not in {"de-DE", "en-US", "en-GB"} or voice not in _VOICE_FILES:
        raise WorkerError("invalid_request")
    if locale.startswith("de-") != voice.startswith("de-"):
        raise WorkerError("invalid_request")
    output_path = Path(request["output_path"])
    if (
        not output_path.is_absolute()
        or output_path.name != "speech.wav"
        or not output_path.parent.name.startswith("vibevoice-request-")
    ):
        raise WorkerError("invalid_request")


class VibeVoiceEngine:
    def __init__(self, source_path: Path, model_path: Path):
        import torch
        from transformers.cache_utils import DynamicCache
        from transformers.modeling_outputs import BaseModelOutputWithPast

        if not torch.backends.mps.is_available():
            raise WorkerError("device_unavailable")
        self.torch = torch
        self._safe_globals = [BaseModelOutputWithPast, DynamicCache]
        self.device = "mps"
        self.processor, self.model, self.voice_directory = _load_model(
            torch, source_path, model_path, self.device
        )
        self._voice_prompts: dict[str, dict[str, Any]] = {}

    def synthesize(self, request: dict[str, Any]) -> None:
        torch = self.torch
        voice_name = request["voice"]
        prompt = self._voice_prompts.get(voice_name)
        if prompt is None:
            voice_path = self.voice_directory / f"{_VOICE_FILES[voice_name]}.pt"
            if not voice_path.is_file() or voice_path.is_symlink():
                raise WorkerError("voice_unavailable")
            with torch.serialization.safe_globals(self._safe_globals):
                prompt = torch.load(
                    voice_path,
                    map_location=self.device,
                    weights_only=True,
                )
            if not isinstance(prompt, dict):
                raise WorkerError("voice_unavailable")
            self._voice_prompts[voice_name] = prompt

        inputs = self.processor.process_input_with_cached_prompt(
            text=request["text"],
            cached_prompt=prompt,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )
        for key, value in inputs.items():
            if torch.is_tensor(value):
                inputs[key] = value.to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=None,
            cfg_scale=1.5,
            tokenizer=self.processor.tokenizer,
            generation_config={"do_sample": False},
            verbose=False,
            show_progress_bar=False,
            all_prefilled_outputs=copy.deepcopy(prompt),
        )
        if not outputs.speech_outputs or outputs.speech_outputs[0] is None:
            raise WorkerError("generation_failed")

        output_path = Path(request["output_path"])
        self.processor.save_audio(outputs.speech_outputs[0], output_path=str(output_path))
        if output_path.is_symlink() or output_path.stat().st_size > _MAX_AUDIO_BYTES:
            output_path.unlink(missing_ok=True)
            raise WorkerError("audio_too_large")
        try:
            with wave.open(str(output_path), "rb") as wav_file:
                if wav_file.getnchannels() < 1 or wav_file.getframerate() < 1:
                    raise WorkerError("generation_failed")
                wav_file.readframes(wav_file.getnframes())
        except (OSError, EOFError, wave.Error):
            output_path.unlink(missing_ok=True)
            raise WorkerError("generation_failed") from None


def _load_model(torch: Any, source_path: Path, model_path: Path, device: str):
    _verify_source_revision(source_path)
    if not model_path.is_dir():
        raise WorkerError("model_unavailable")
    sys.path.insert(0, str(source_path))
    import transformers
    from vibevoice.modular.configuration_vibevoice import VibeVoiceAcousticTokenizerConfig
    from vibevoice.modular.modular_vibevoice_tokenizer import TokenizerDecoder
    from vibevoice.modular.modeling_vibevoice_streaming_inference import (
        VibeVoiceStreamingForConditionalGenerationInference,
    )
    from vibevoice.processor.vibevoice_streaming_processor import VibeVoiceStreamingProcessor

    original_descriptor = transformers.AutoModel.__dict__["from_config"]
    original_from_config = transformers.AutoModel.from_config

    def decoder_only_factory(model_class: Any, config: Any, **kwargs: Any) -> Any:
        if isinstance(config, VibeVoiceAcousticTokenizerConfig):
            return _create_decoder_only_tokenizer(torch, config, TokenizerDecoder)
        return original_from_config(config, **kwargs)

    transformers.AutoModel.from_config = classmethod(decoder_only_factory)
    try:
        processor = VibeVoiceStreamingProcessor.from_pretrained(
            str(model_path),
            local_files_only=True,
            revision=_TOKENIZER_REVISION,
        )
        model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
            str(model_path),
            local_files_only=True,
            torch_dtype=torch.float32,
            attn_implementation="sdpa",
            device_map=None,
        )
    finally:
        transformers.AutoModel.from_config = original_descriptor
    model.to(device)
    model.eval()
    model.set_ddpm_inference_steps(num_steps=5)
    if hasattr(model.model.acoustic_tokenizer, "encoder"):
        raise WorkerError("decoder_only_load_failed")
    voice_directory = source_path / "demo" / "voices" / "streaming_model"
    return processor, model, voice_directory


def _create_decoder_only_tokenizer(torch: Any, config: Any, tokenizer_decoder: Any) -> Any:
    class DecoderOnlyAcousticTokenizer(torch.nn.Module):
        def __init__(self, tokenizer_config: Any):
            super().__init__()
            decoder_config = copy.deepcopy(tokenizer_config)
            encoder_depths = _depth_values(tokenizer_config.encoder_depths)
            decoder_config.dimension = tokenizer_config.vae_dim
            decoder_config.n_filters = tokenizer_config.decoder_n_filters
            decoder_config.ratios = tokenizer_config.decoder_ratios
            decoder_config.depths = (
                _depth_values(tokenizer_config.decoder_depths)
                if tokenizer_config.decoder_depths is not None
                else list(reversed(encoder_depths))
            )
            decoder_config.norm = tokenizer_config.conv_norm
            decoder_config.pad_mode = tokenizer_config.pad_mode
            decoder_config.bias = tokenizer_config.conv_bias
            decoder_config.layernorm_eps = tokenizer_config.layernorm_eps
            decoder_config.layernorm_elementwise_affine = (
                tokenizer_config.layernorm_elementwise_affine
            )
            decoder_config.mixer_layer = tokenizer_config.mixer_layer
            decoder_config.layer_scale_init_value = tokenizer_config.layer_scale_init_value
            decoder_config.disable_last_norm = tokenizer_config.disable_last_norm
            self.config = tokenizer_config
            self.decoder = tokenizer_decoder(decoder_config)

        @property
        def device(self) -> Any:
            return next(self.parameters()).device

        def decode(self, latents: Any, **kwargs: Any) -> Any:
            if latents.shape[1] != self.config.vae_dim:
                latents = latents.permute(0, 2, 1)
            return self.decoder(latents, **kwargs)

    return DecoderOnlyAcousticTokenizer(config)


def _depth_values(value: Any) -> list[int]:
    if isinstance(value, str):
        return [int(depth) for depth in value.split("-")]
    return list(value)


def _verify_source_revision(source_path: Path) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise WorkerError("source_unavailable") from None
    if result.stdout.strip() != _SOURCE_REVISION:
        raise WorkerError("source_revision_mismatch")


def main() -> int:
    if os.environ.get("TTS_VIBEVOICE_RESEARCH_ONLY") != "true":
        return 2
    source_path = Path(os.environ.get("TTS_VIBEVOICE_SOURCE_PATH", ""))
    model_path = Path(os.environ.get("TTS_VIBEVOICE_MODEL_PATH", ""))
    if not source_path.is_dir() or not model_path.is_dir():
        return 2
    try:
        engine = VibeVoiceEngine(source_path, model_path)
    except Exception:
        return 2
    serve(engine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
