# Fish Speech Variant Comparison

**Compared**: 2026-11-16
**Upstream snapshot**: `0f8a12e8a651062fdee9c33a894bdccd3a8513f1`
**Selected variant**: none
**Local audio evaluation**: not performed

## Published Comparison

| Variant | Published size/resource guidance | English evidence | German evidence | Terms/provenance status |
| --- | --- | --- | --- | --- |
| S2-Pro | 4B parameters; upstream install guide lists an NVIDIA/CPU path and 24 GB GPU guidance. CPU RAM, Apple Silicon compatibility, storage, and target latency are not established. | Upstream reports English benchmark results, including WER 0.99%; these are vendor-reported and not a local comparison. | README claims broad multilingual capability; no German result in the reviewed README establishes suitability for this use. | README says S2-Pro weights use the separate Fish Audio Research License. Exact checkpoint terms and voice provenance remain unreviewed. |
| Drama 3 | 35B total / 3B active parameters; at least 48 GB GPU memory with FP8, NVIDIA only. Upstream excludes CPU, Apple MPS, and AMD ROCm for this model. | Multilingual capabilities and benchmark summaries are vendor-reported; no local English comparison was performed. | Multilingual claims do not establish measured German quality for this use. No local German comparison was performed. | README names the Fish Audio Community License for code/materials and distinguishes S2-Pro weights. Exact Drama 3 checkpoint/codec terms and voice provenance still require review. |

Parameter count is not a substitute for runtime memory, CPU performance, or
storage requirements. Published requirements are not measurements of the target.
The upstream installation guide provides Linux/WSL instructions; it does not
qualify a native macOS deployment. The API server loads a checkpoint at startup
and has no per-request model selector, so different variants require distinct
service configurations if they are ever approved for testing.

## Quality and Size-to-Quality Assessment

- **Local English quality**: not measured.
- **Local German quality**: not measured.
- **Local latency, memory, and storage**: not measured.
- **Paired comparison against macOS `say`**: not performed.
- **Size-to-quality winner**: none. The reviewed public figures do not provide
  a target-machine, paired English/German quality-per-resource comparison.

The S2-Pro English benchmark and broad multilingual claims cannot establish a
size-to-quality ratio for this prototype. Do not rank, select, or enable a
variant from parameter count or vendor benchmark alone.

## Approval Gate

No weights, codecs, reference audio, voices, runtime packages, or Fish service
were downloaded, installed, or enabled by this comparison. Before considering a
test, record the exact checkpoint and codec revisions, review their respective
terms for the intended private use, verify any reference voice consent and
provenance, and separately approve the target runtime plan. Private use does not
remove model-specific terms or voice-rights obligations.

## Sources

- [Pinned Fish Speech README](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/README.md): published variants, model-size claims, benchmark summaries, and license distinction.
- [Pinned installation guide](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/install.md): platform and resource guidance.
- [Pinned inference guide](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/inference.md): one checkpoint per Fish server and no per-request model selection.
- [Prior licensing and language research](research.md#data--constraints): reviewed source license and unavailable checkpoint/voice details.
