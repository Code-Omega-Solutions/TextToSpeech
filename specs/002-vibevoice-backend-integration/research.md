# Research: VibeVoice Backend Integration

## Decision: Limit current use to private R&D

**Decision**: The operator authorizes English and German preset testing only
for private research and development on the named private system. Require the
explicit `TTS_VIBEVOICE_RESEARCH_ONLY` setting. Do not treat this as production
support, legal clearance, Microsoft permission for unsupported German output,
or permission to publish or redistribute model assets, prompts, or audio.

**Rationale**: The reviewed model card limits direct intended use to research
and says English is supported while German is unsupported. The German tests
are exploratory measurements, not a claim that the model supports German
reliably. Preserve the reported fallback behavior and keep user data and audio
outside the repository.

## Decision: Keep the model in one persistent child process

**Decision**: The API process owns one lazy, persistent VibeVoice worker. The
worker serializes inference requests and retains the shared model while the
resource policy allows it. Worker termination is the memory-release mechanism.

**Rationale**: The evaluation showed materially lower latency after the model
was warm and used one model instance for English and German. The optional
PyTorch/Transformers runtime should not be imported into the API process, and
ending the child process releases its model and accelerator allocations more
reliably than attempting to free selected tensors in place.

**Alternatives considered**: Reloading a one-shot worker for each request
releases memory promptly but repeats cold-start cost. Loading the model in the
API process complicates dependency isolation and does not provide a reliable
way to yield all runtime allocations.

## Decision: Require explicit memory budgets and fail closed to macOS speech

**Decision**: Use the existing macOS `vm_stat`-based available-memory approach
to gate worker admission and monitor a configured minimum reserve. Require
operators to configure both the worker's measured peak-memory budget and the
reserve for higher-priority workloads. Admit loading only when available
memory covers both. Evict the worker when the reserve is crossed. If the probe,
configuration, or worker is unavailable, use macOS `say`.

**Rationale**: `memory_pressure -Q` is available on the target host, but reports
a free-memory percentage rather than a workload-priority request. A configured
reserve gives image generation and other inference a concrete amount of memory
that TTS must leave available. The measured 7.28 GiB process peak included the
unused encoder, so the optimized worker must be profiled before setting its
budget. This is a capacity-based signal, not process-aware coordination. If
target-host qualification cannot establish that the gate protects higher-
priority workloads, keep VibeVoice disabled. Do not guess a universal threshold.

**Alternatives considered**: A fixed threshold is unsafe across hosts and
workloads. Treating the `memory_pressure -Q` percentage as a direct request to
yield would not express how much memory higher-priority work needs. Keeping the
worker resident without eviction conflicts with the low-priority requirement.

## Decision: Construct the acoustic decoder without the unused encoder

**Decision**: The worker will use the supported VibeVoice decoder implementation
without constructing the acoustic encoder, and will load and validate the
decoder checkpoint weights before serving.

**Rationale**: Inspection of the cached upstream source showed that the
acoustic-tokenizer constructor creates both components, while the Realtime
generation path calls `acoustic_tokenizer.decode`. The evaluation checkpoint
also reported 276 newly initialized encoder tensors. A decoder-only loader
avoids allocating those unused parameters, but must be checked against normal
generation output and the selected voice presets.

**Alternatives considered**: Loading the full tokenizer and deleting its
encoder afterward still incurs construction and peak-memory costs. Changing
the upstream package in place would make upgrades harder to audit.

## Decision: Preserve the existing audio conversion path

**Decision**: Have the worker produce a bounded WAV artifact. Validate it in the
backend, pass WAV through unchanged when requested, and use the existing
`ffmpeg` conversion path for MP3.

**Rationale**: The backend already owns output-format conversion and request
limits. Keeping conversion in the parent preserves the API's MP3/WAV behavior
and avoids adding codec responsibilities or dependencies to the model worker.

**Alternatives considered**: Adding MP3 encoding to the worker duplicates the
existing conversion path and expands the worker's optional dependency surface.

## Decision: Use a framed, private worker protocol

**Decision**: Exchange one JSON request and one JSON response per line over the
worker's private standard streams. The request names a unique WAV path inside a
per-request temporary directory; the worker writes the artifact there. Keep
protocol output on stdout, diagnostics on stderr, bound line and artifact
sizes, and enforce a backend timeout.

**Rationale**: The evaluator's current subprocess adapter uses safe
argument-based process creation, bounded output, and a timeout, but its
one-request lifetime cannot retain a warm model. JSON lines allow multiple
requests without making stdout carry unframed audio bytes. A private temporary
directory keeps partial output out of API responses.

**Alternatives considered**: Restarting the process per request defeats warm
reuse. Returning raw audio bytes on a long-lived stdout stream requires
additional framing and complicates distinguishing protocol responses from
audio.

## Decision: Keep optional runtime dependencies and model assets separate

**Decision**: Pin the optional model runtime in a worker-specific environment.
Do not add PyTorch, Transformers, or VibeVoice imports to the API dependency
set. Require model provenance, license, and deployment checks before enabling
the worker on a release host.

**Rationale**: This preserves the lightweight backend path and lets operators
choose whether to install the model runtime. The evaluation prototype remains a
reference until the integrated worker passes the same host checks.

**Alternatives considered**: Adding the full stack to the backend environment
forces its installation and footprint on deployments that use only `say`.

## Decision: Delay prototype cleanup until integration is verified

**Decision**: Keep prototype source and evidence available during implementation.
After backend tests and target-host smoke, latency, memory, and fallback checks
pass, remove prototype-only server copies, virtual environments, and generated
sample artifacts. Preserve aggregate ratings in the completed evaluation spec,
and retain model weights/cache if the integrated worker still uses them.

**Rationale**: The stopped prototype is useful for source and configuration
reference. Deleting it earlier risks losing reproducible comparison evidence or
the only local model assets needed to qualify the integrated worker.

**Alternatives considered**: Immediate deletion reduces disk use but removes
useful references before the replacement is proven. Retaining every generated
artifact indefinitely is unnecessary once the aggregate evidence and required
model assets are preserved.
