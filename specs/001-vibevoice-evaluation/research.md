# Research: Private VibeVoice Evaluation

## Candidate models and language support

**Decision:** Track the two candidates as VibeVoice-TTS-1.5B and VibeVoice-Realtime-0.5B. Treat German support as unverified for both and report unsupported or unavailable samples without substituting a voice or model.

**Rationale:** Microsoft's current repository README lists both models. It says the VibeVoice-TTS code was removed after concerns about out-of-scope use, and marks its quick try as disabled. The TTS-1.5B model card describes English and Chinese training and warns that other languages are unsupported. The Realtime-0.5B card describes English as its intended language; its documentation presents German as experimental exploration and cautions that multilingual behavior is not extensively tested. Therefore, German audio cannot be assumed feasible or comparable.

**Alternatives considered:** Treat both variants as ready-to-run and compare all languages. Rejected because official sources report the missing 1.5B implementation and language limitations. Treat experimental German output as supported. Rejected because the published documentation does not qualify it.

## Terms and execution boundary

**Decision:** Do not download models, install packages, or run either model until the exact code, model files, voices, dependencies, and sample-text terms have been reviewed for the intended private research use and the operator has approved any target-machine change. Keep model implementations outside the production backend environment and invoke only an approved local adapter.

**Rationale:** Both Hugging Face model cards identify MIT as the model license and limit intended use to research and development, while also stating responsible-use restrictions and dataset privacy obligations. The 1.5B repository implementation is disabled, so model-file metadata alone does not establish that an implementation or its dependencies may be used. The existing project policy also requires review of exact third-party components and approval before target-machine downloads or installation.

**Alternatives considered:** Add model runtimes to the backend lockfile or let the evaluator download assets automatically. Rejected because permission, implementation availability, dependency terms, and target capacity are not established, and the production service must remain unchanged.

## Baseline and comparison workflow

**Decision:** Use the existing authenticated local `POST /v1/audio/speech` endpoint as the baseline. Pair every eligible baseline and candidate generation with the same five locally supplied, permitted texts per language, and record a blocker if the endpoint or an adapter is unavailable.

**Rationale:** The endpoint is the existing speech contract, so it avoids creating a second baseline implementation with potentially different voice, speed, or audio processing. The backend documentation states that readiness is distinct from liveness and that the service is not automatically registered or started. A missing service must therefore remain an explicit incomplete comparison rather than trigger service changes or a substitute baseline.

**Alternatives considered:** Call macOS `say` directly from the evaluator or modify the backend to add a VibeVoice route. Rejected because direct invocation would duplicate existing synthesis behavior, while a production route would violate the isolated-prototype and unchanged-service boundaries.

## Local review and persistence

**Decision:** Serve a small review page from a loopback-only local server and persist validated run metadata, ratings, observations, and the final decision as a local JSON report. Require the sample manifest and output directory to be supplied by the operator; do not check in sample text, audio, credentials, or evaluation results.

**Rationale:** A local page supports paired listening and ratings without a remote service or new application interface. JSON can preserve individual and incomplete results while allowing explicit averages and decision rationale. Operator-supplied files keep potentially private texts and generated audio out of repository history.

**Alternatives considered:** Upload results to an existing application, use a hosted dashboard, or commit a sample corpus. Rejected because they widen disclosure, deployment, or rights scope without helping the private evaluation.

## Platform and capacity

**Decision:** Record measured capacity and platform details independently for every candidate machine. Treat upstream runtime guidance and reports of Apple Silicon inference as leads for feasibility checks, not as qualification.

**Rationale:** The official Realtime usage guide recommends an NVIDIA container, while also noting that an M4 Pro achieved real-time performance in its tests. Neither claim establishes compatibility, capacity, or acceptable generation time on the actual candidate machines. The evaluator must capture available storage, memory, platform, requirements, and inspection time before an approved run.

**Alternatives considered:** Infer support from model size or upstream benchmark examples. Rejected because measured resource requirements and runtime behavior are machine-specific.

## Sources

- Microsoft VibeVoice repository README: https://github.com/microsoft/VibeVoice/blob/main/README.md
- Microsoft VibeVoice Realtime usage guide: https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-realtime-0.5b.md
- VibeVoice-TTS-1.5B model card: https://huggingface.co/microsoft/VibeVoice-1.5B
- VibeVoice-Realtime-0.5B model card: https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B
- Backend synthesis contract and qualification boundaries: `capabilities/backend-synthesis/backend-synthesis.spec.md`, `backend/README.md`
- Project dependency and third-party review policy: `capabilities/project-licensing/project-licensing.spec.md`, `THIRD_PARTY_NOTICES.md`
