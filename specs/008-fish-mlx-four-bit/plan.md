# Implementation Plan: Fish Speech MLX 4-bit candidate

**Branch**: `pgfeller-mlx-fish-4bit` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## Summary

Implement an isolated, opt-in Fish 1.5 DualAR MLX semantic runtime using packed affine 4-bit weights derived from the existing checkpoint. Retain the approved Firefly codec, tokenizer and reference machinery, and use the existing managed lifecycle and HTTP contract. Exact numerical compatibility and performance remain unverified until real native tests.

## Technical Context

**Language/Version**: Python 3.11+; target existing isolated macOS Python runtime.

**Primary Dependencies**: MLX, PyTorch and Fish 1.5 source; candidate dependencies isolated and pinned, macOS ARM only.

**Storage**: Separate private derived artifact tree; approved trees remain read-only.

**Testing**: pytest for contract and rejection tests; native MLX numerical and synthesis qualification on Apple Silicon only within approved boundaries.

**Target Platform**: Apple Silicon macOS; native-only operation remains supported without MLX.

**Project Type**: Optional managed worker for existing Python backend.

**Performance Goals**: Measure synchronized inference and compare against baseline; no unverified threshold or improvement is assumed.

**Constraints**: Offline, approved-only, unchanged HTTP/voice contracts, managed ownership, memory controls, native fallback, no deployment.

**Scale/Scope**: One serialized worker; exact Fish 1.5 DualAR and original codec.

## Constitution Check

PASS: Preserve approval, privacy, cleanup and native fallback; distinguish mocked tests and measurements from qualification. No production modification or download is authorized. Review model/source/runtime/reference terms independently.

## Project Structure

```text
backend/app/                  Existing service and managed worker lifecycle
backend/deployment/           Approved launcher and candidate startup
backend/tests/                Focused regression and conversion tests
capabilities/backend-synthesis/  Living behavior and coverage
specs/008-fish-mlx-four-bit/  Feature artifacts
```

**Structure Decision**: Keep candidate-specific conversion and runtime code isolated under backend; preserve the existing public service and source checkout.

## Design and post-design gates

Validate exact configuration and all checkpoint keys and shapes before conversion. Quantize attention and feed-forward linear matrices in groups of 64 using 4-bit affine MLX operations; retain embeddings, output heads, normalization and codec in higher precision initially. Use separate hash-bound metadata for conversion parameters, exact runtime and original source/codec/reference approvals. Reuse Fish prompt encoding and codec only through reviewed fixed interfaces, and bridge the existing managed MessagePack/WAV transport. Fail closed on incompatible artifacts and incomplete approvals.

Numerical parity, lazy execution synchronization, English/German quality, measured memory and actual inference remain qualification gates, not assumptions. A real conversion and synthesis path is required; mocked-only code or a stub is not completion.
