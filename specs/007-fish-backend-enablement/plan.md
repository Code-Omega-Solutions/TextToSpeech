# Implementation Plan: Headroom-First Fish Enablement

**Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)
**Status**: Local resource-policy design ready; artifact and deployment gates open

## Summary

Implement an opt-in low-priority policy in the existing Python speech backend.
Keep strict selection as the default. Under the new policy, independently
supervise an operator-configured local Fish process, lazy-start only with a
16 GiB peak budget plus 12 GiB free reserve, admit one neural request, and
stop the owned process when its budget or host reserve is breached.
Return native speech in the resolved language when neural resources are absent,
ignoring neural engine/voice preference but preserving the response contract.

Separate model-independent policy implementation from gated runtime installation.
No inference launcher or model is bundled. Downloads, native qualification and
live service changes remain blocked until exact artifacts and voice references
are reviewed. Do not mark the feature complete merely because policy tests pass.

## Technical Context

**Language/Version**: Existing Python 3.11+ FastAPI/Pydantic backend.
**Dependencies**: Standard-library process/thread primitives and existing Fish
HTTP/MessagePack adapter; no new dependencies.
**Storage**: No model, reference audio, secrets, or host configuration in git.
**Testing**: pytest process/resource fakes, speech dispatch, API and config tests.
**Target Platform**: Apple Silicon macOS with 32 GiB unified memory; mocked
Linux checks establish policy behavior only.
**Performance Goals**: Reserve 12 GiB for higher-priority work, 16 GiB monitored
neural-worker budget, one neural request, 0.25-second monitor interval.
**Constraints**: No guarantees of instantaneous preemption or hard physical
memory isolation; measured counters and sampling have limits. Reserve native
admission by requiring at least two total synthesis permits under this policy.
**Scale/Scope**: One explicitly owned Fish worker process group; native baseline
and unrelated services are never terminated by this supervisor.

## Constitution Check

| Principle | Design result |
| --- | --- |
| Evidence-based specifications | PASS: policy evidence is separate from native/model qualification. |
| Safe bounded behavior | PASS: fail-closed admission, monitored limits, finite cooldown/idle/deadline. |
| Operational boundaries | PASS for local code; deployment is separately gated; terminate only created process group. |
| Observable outcomes | PASS for design: tests require actual fallback metadata and remaining deadline. |
| Platform and rights claims | PASS only with downloads and deployment gated; no artifact approval inferred. |

Post-design review retains these boundaries. No exceptions are accepted.

## Phase 0: Runtime and Reference Screening

See [research.md](research.md). Fish Speech v1.5.0's tagged README claims German,
English, cross-language reference voices, and macOS support. Its exact weight
metadata remains inaccessible; it is a smaller-family screening lead, not a
measured sub-16-GiB candidate. Do not assert it meets latency or memory limits.

Drama 3 MLX 3-bit's reported 22.5-24 GB peak is outside the initial worker
budget. The operator permits considering the weaker 8 GiB reserve only if no
suitable smaller Fish candidate is found. Do not lower limits automatically.
Thorsten original neutral WAV/transcript references remain the first German
candidate; no Piper or Coqui weights are interchangeable with Fish.

## Phase 1: Design

- Add a managed process wrapper around the existing Fish HTTP adapter. The
  reviewed local launcher is configured as a JSON argv list, with an absolute
  executable and no shell interpolation or secrets in arguments. This is a
  runtime integration boundary, not a provided or approved launcher.
- Extract existing available/resident-memory probes into a shared helper;
  keep legacy imports compatible. Do not reuse the old worker's practice of
  adding its resident memory back into available memory: the reserve must remain
  available while Fish is loaded.
- Start the worker with low CPU priority and a new process session. Remove
  unrelated backend/operator credentials and enforce offline model access in
  the child environment. Reject an already listening external endpoint rather
  than adopting or stopping it.
- Keep independent request and process-state locks. A second neural request
  falls back immediately rather than occupying the remaining native permit.
- Sample memory while loading, active, and idle. On probe failure, reserve breach,
  worker RSS breach, timeout, cancellation, idle expiry, or shutdown, stop only
  the owned process group and reap it. Close admission if termination cannot be
  verified; never proceed as if memory was released.
- Use a 30-second restart cooldown after failed/aborted attempts and a 30-second
  idle timeout. Discovery never starts or downloads a model.
- Preserve the overall request deadline. Give Fish at most its configured
  request timeout and reserve up to 10 seconds (half the total for short limits)
  for native fallback. Native fallback uses its locale default, not the requested
  neural voice. Cancellation and output-size errors do not become success.
- Opt-in fallback also covers legacy neural selections; without the flag,
  existing legacy/unavailable 503 behavior remains unchanged.
- Readiness continues to require the native baseline only. A shutdown hook stops
  the owned worker in a threadpool.

Contracts and entities are in [contracts/resource-policy.md](contracts/resource-policy.md)
and [data-model.md](data-model.md); [quickstart.md](quickstart.md) separates local
validation from gated native evaluation.

## Project Structure

```text
backend/app/config.py
backend/app/fish_speech.py
backend/app/fish_process.py
backend/app/memory.py
backend/app/vibevoice.py
backend/app/services.py
backend/app/routers.py
backend/app/main.py
backend/tests/test_fish_process.py
backend/tests/test_engines.py
backend/tests/test_config.py
backend/tests/test_api.py
backend/README.md
capabilities/backend-synthesis/
living-specs.yml
specs/007-fish-backend-enablement/
```

## Deployment Stop Gates

Resolve exact pinned checkpoint/codec/runtime permissions and compatible
authenticated launcher, approve reference assets, then measure native memory,
headroom, timing and listening quality. Verify both existing listeners before
and after an approved prototype-only rollout. Until then the code remains
undeployed, no model is installed, and native `say` is the available baseline.
