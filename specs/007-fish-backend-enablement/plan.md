# Implementation Plan: Headroom-First Fish Enablement

**Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)
**Status**: Local resource-policy design ready; private noncommercial artifact terms reviewed; reference, output-sharing, and deployment gates open

## Summary

Implement an opt-in low-priority policy in the existing Python speech backend.
Keep strict selection as the default. Under the new policy, independently
supervise an operator-configured local Fish process, lazy-start only with a
16 GiB peak budget plus 12 GiB free reserve by default, admit one neural request, and
stop the owned process when its budget or host reserve is breached.
The separately authorized private override uses a positive 4 GiB startup
allowance (16 GiB total admission threshold), leaving the 12 GiB reserve,
16 GiB runtime RSS ceiling and monitoring unchanged. Other deployments retain
full-budget cold-start admission unless explicitly configured.
Return native speech in the resolved language when neural resources are absent,
ignoring neural engine/voice preference but preserving the response contract.

Separate model-independent policy implementation from gated runtime installation.
The model and Common Voice archives are installed/downloaded only in private
storage on the authorized host and session; no assets are bundled in Git. The
exact model revision and noncommercial terms are recorded, but the installed
source checkout has unreviewed local modifications, exact references are not
selected, generated-output sharing remains gated, and native qualification is
incomplete. Do not mark the feature complete merely because policy tests pass.

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
| Platform and rights claims | PASS for the reviewed private noncommercial model terms; voice-reference use, output sharing and native qualification remain explicit gates. |

Post-design review retains these boundaries. No exceptions are accepted.

## Phase 0: Runtime and Reference Screening

See [research.md](research.md). Fish Speech v1.5's exact gated model revision,
model-weight terms, local model/decoder hashes, and macOS prototype outputs are
recorded there. The user confirmed noncommercial use. The decoder is a weight
in the same model repository; its license is supported by the model card's
model-weight license statement, not by a separate codec license file. The
installed source checkout contains two local MPS-related modifications, so the
managed worker must not start until those changes are reviewed, tested, and
bound to an exact clean source revision.

The 16 GiB neural-worker budget and 12 GiB reserve remain unchanged; historical
Drama 3 MLX 3-bit estimates do not justify weakening them. Four
language-specific Common Voice Spontaneous Speech 5.0 references replace the
former bilingual/Thorsten candidate. Initial metadata screening found enough
self-declared female and male groups in both languages, but no exact clip has
yet passed audio, transcript, and listener review.

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
- Keep the Fish source checkout clean and pinned. Store the four approved
  references in a separate private data root; run the Fish API with that root as
  its working directory and the clean source checkout on `PYTHONPATH`, so
  Fish's relative `references/<id>` lookup does not contaminate the source tree.
  Bind and revalidate the reference manifest before each worker launch.
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

Bind the exact reviewed source tree and private model/decoder files to the
approval manifest, select and validate four private references, and resolve
whether shared voice-conditioned outputs satisfy the MDC personal-data
restriction. Keep shared output disabled while that interpretation is open.
Then measure native memory, headroom, timing and listening quality on the
isolated prototype. Verify both existing listeners before and after any
approved prototype-only rollout; production remains untouched and native
`say` remains the always-available baseline.
