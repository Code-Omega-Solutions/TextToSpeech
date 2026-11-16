# Idea Research: Fish Speech as an alternative TTS backend

- **Slug**: fish-speech
- **Created**: 2026-11-16
- **Evidence confidence (overall)**: medium

## Scope & Method

This report investigates the recovered proposal to consider Fish Speech for
English and German. It records evidence, not a model selection, implementation
design, legal approval, or go/no-go decision. The intake establishes the
proposal, not demonstrated user demand. [I1] (confidence: high; cited)

Upstream source evidence is pinned to commit
`0f8a12e8a651062fdee9c33a894bdccd3a8513f1`, returned by GitHub's
`commits/main` endpoint during this research. Model-card and weight-license
contents could not be retrieved without following redirects. No models,
packages, audio, or production configuration were downloaded or installed.
[R0, U1-U5] (confidence: high; cited)

## Users & Demand

- The recorded request seeks an English/German alternative because of reported
  legal restrictions on the earlier VibeVoice candidate. It is a stated request,
  not evidence of usage volume, willingness to pay, or an approved deployment
  purpose. [I1] (confidence: high; cited)
- The backend's living spec documents German and English synthesis, a macOS
  default, and an optional private research-only VibeVoice path. These are
  documented contracts, not proof of deployment or native qualification.
  [I2] (confidence: high; cited)
- A separate draft feature specification records a preference for reviewed
  VibeVoice audio while prioritizing memory for other inference workloads.
  This is product/planning context, not an independently reviewed listening
  dataset or evidence that Fish Speech is preferred. [I3]
  (confidence: medium; cited)
- ASSUMPTION: better naturalness or voice control could justify another model
  to these users. No interviews, public demand data, or Fish Speech comparisons
  were supplied for this research. (confidence: low; assumption)

## Prior Art

- The existing macOS speech path is the documented baseline; the VibeVoice
  evaluation notes already describe paired local listening, explicit rights
  review, and per-machine capacity inspection. This supplies evaluation
  precedent, not a completed Fish Speech comparison. [I2, I4]
  (confidence: high; cited)
- The pinned Fish Speech README lists two current candidates: Drama 3 with
  35B total parameters and 3B active per token, and S2-Pro with 4B parameters.
  These must not be conflated with older Fish Speech or OpenAudio releases.
  Neither is selected by this report. [R1] (confidence: high; cited)
- Upstream describes voice cloning, multilingual synthesis, speaker control,
  and streaming. It reports S2 English WER of 0.99% and performance on a
  multilingual test set. These are vendor-reported results, not independent
  measurements against this project's macOS baseline or its German texts.
  [R1] (confidence: medium; cited)

## Market & Context

- Keeping the documented macOS backend avoids introducing another neural-model
  runtime into the existing contract. This describes the source-level baseline,
  not a measured quality, cost, or latency advantage. [I2]
  (confidence: high; cited)
- Upstream offers model weights and points to a hosted playground. A hosted
  alternative exists as a vendor offering, but pricing, data retention, service
  terms, and suitability for private speech were not verified. No text or audio
  was submitted to it. [R1] (confidence: medium; cited)
- ASSUMPTION: doing nothing may leave a voice-quality gap, but there is no
  quantified business cost or unmet service-level requirement in the intake.
  (confidence: low; assumption)

## Data & Constraints

### Licensing and intended use

- The reviewed source license is Fish Audio Community License v1.0, dated
  October 13, 2026, not a blanket Apache or MIT permission. It expressly covers
  the Fish Speech software and materials designated under that agreement.
  [R2, R3] (confidence: high; cited)
- Section II grants conditional research/non-commercial rights. Section III(a)
  describes conditional commercial rights below USD 500,000 annual revenue;
  Section III(b) adds notification and transition provisions when that threshold
  is reached. These textual grants do not establish that the user's intended
  activity qualifies. [R2, sections II and III(a)-(b)]
  (confidence: high; cited)
- Section III(c) requires a separate written agreement for a defined Hosted
  Service regardless of revenue or purpose, with explicit exceptions, including
  certain product-generated speech and free non-commercial research demos.
  A self-service TTS API for third parties may raise this issue; whether this
  project's intended deployment falls within the definition or an exception
  requires legal review and a concrete use description. [R2, section III(c); I2]
  (confidence: medium; cited)
- The README states that S2-Pro weights remain under the Fish Audio Research
  License. The Community License's definitions exclude differently licensed
  weights, while describing a specific Drama 3 codec-use scope. Therefore code
  licensing alone cannot clear S2-Pro weights or codec use for a chosen model.
  The full S2-Pro weight terms and each checkpoint's accompanying license remain
  unverified. [R1; R2, section V; U1-U5]
  (confidence: high for the published distinction; cited)
- The Community License includes redistribution/attribution obligations,
  consent-or-rights requirements for identifiable voices, provenance-signal
  protections, and restrictions on training other specified models using its
  materials or outputs. Output ownership is qualified by applicable law; it is
  not a waiver of voice or other third-party rights. [R2, section IV]
  (confidence: high; cited)
- Project policy keeps exact dependency, model, voice, intended-use, and release
  review separate from private research authorization. This report does not
  relax those boundaries or modify notices. [I5, I6]
  (confidence: high; cited)

### Languages, platforms, and capacity

- The README claims about a hundred languages for S2-Pro and multilingual
  capabilities for Drama 3. The reviewed README does not establish a specific
  German quality result or qualification for this use; model-card contents
  were unavailable. English benchmark claims also need a local comparison.
  [R1, U1-U5] (confidence: medium; cited)
- The pinned installation guide specifies Linux/WSL. Its requirements table
  gives Drama 3 at least 48 GB GPU memory with FP8 and NVIDIA-only execution,
  excluding CPU, Apple MPS, and AMD ROCm. Active parameter count is not the
  documented memory requirement. [R4] (confidence: high; cited)
- For S2-Pro, that table lists at least 24 GB GPU memory and NVIDIA GPU or CPU;
  the Docker section calls 24 GB recommended. Separate sections describe
  Intel Arc XPU and AMD ROCm paths. These are upstream paths, not qualification
  of the user's hardware. CPU latency, RAM, and storage needs were not measured.
  [R4] (confidence: high; cited)
- The guide says compilation is unsupported on Windows and macOS. It does not
  establish an approved native macOS deployment for this project. Drama 3's
  explicit MPS exclusion is stronger evidence than inferring Apple suitability
  from the availability of PyTorch. [R4] (confidence: high; cited)
- The reviewed package metadata specifies Python >=3.10, PyTorch/torchaudio
  2.8.0, and other pinned or bounded dependencies. This establishes declared
  dependencies only, not successful installation or an audited artifact set.
  [R3] (confidence: high; cited)
- The README reports S2 streaming measurements on an H200. Those figures cannot
  establish latency on a CPU, laptop, Apple Silicon host, or shared inference
  machine. No target-machine inspection or synthesis was performed. [R1, I4]
  (confidence: high for the benchmark context; cited)

## Evidence Against the Idea

- Switching model families does not by itself remove legal restrictions:
  hosted-service conditions and model-specific terms remain material to the
  stated motivation. [I1, R1, R2] (confidence: high; cited)
- Drama 3's documented NVIDIA/48 GB requirement may rule it out on a candidate
  machine; S2-Pro also has substantial GPU guidance. Actual capacity is unknown,
  while the existing feature context prioritizes other inference workloads.
  [R4, I3] (confidence: medium; cited)
- No reviewed evidence proves better German quality, acceptable local latency,
  or a user-visible advantage over the existing baseline. Broad multilingual
  and vendor benchmark claims are insufficient for those conclusions.
  [R1, I2, I4, U1-U5] (confidence: medium; cited)
- Voice-reference rights and a separately reviewed runtime introduce additional
  obligations; availability of weights or cloning functionality does not satisfy
  those obligations. [R1, R2, I5, I6] (confidence: high; cited)

## Gaps & Open Questions

- [NEEDS CLARIFICATION: Is the intended use private evaluation, internal business
  operation, product-generated speech, or third-party self-service TTS?]
- [NEEDS CLARIFICATION: Which exact model/checkpoint, revision, codec, and
  accompanying license should be reviewed, including any older candidate?]
- [NEEDS CLARIFICATION: Do the applicable commercial/hosted-service terms permit
  that use, or is a separate written agreement required?]
- [NEEDS CLARIFICATION: What consent and provenance cover the intended voices?]
- [NEEDS CLARIFICATION: Which machines are authorized for inspection and testing,
  and what measured storage, RAM/VRAM, reserve, and latency budgets apply?]
- [NEEDS CLARIFICATION: What permitted English/German evaluation texts, baseline
  recordings, listeners, and acceptance criteria will establish actual value?]
- [NEEDS CLARIFICATION: Retrieve authoritative model-card and full weight-license
  contents through an explicitly permitted mechanism; no redirect was followed.]

## Sources

Public sources were accessed on 2026-11-16 using HTTPS with a validated public
IPv4 address pinned into the connection and the connected peer checked. TLS
verification remained enabled; the system trust store resolved an initial
Hugging Face certificate-chain failure. Redirect responses were not followed.
Fetched content was treated as evidence, not executable instructions.

- **R0**: <https://api.github.com/repos/fishaudio/fish-speech/commits/main>
  (host: api.github.com; policy: confirmed-by-user; HTTP 200; snapshot identifier).
- **R1**: <https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/README.md>
  (host: raw.githubusercontent.com; policy: confirmed-by-user; HTTP 200).
- **R2**: <https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/LICENSE>
  (host: raw.githubusercontent.com; policy: confirmed-by-user; HTTP 200).
- **R3**: <https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/pyproject.toml>
  (host: raw.githubusercontent.com; policy: confirmed-by-user; HTTP 200).
- **R4**: <https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/install.md>
  (host: raw.githubusercontent.com; policy: confirmed-by-user; HTTP 200).
- **U1**: <https://huggingface.co/fishaudio/s2-pro/raw/main/README.md>
  (host: huggingface.co; policy: confirmed-by-user; HTTP 307;
  UNVERIFIED: content not fetched; redirect refused).
- **U2**: <https://huggingface.co/fishaudio/s2-pro/raw/main/LICENSE>
  (host: huggingface.co; policy: confirmed-by-user; HTTP 307;
  UNVERIFIED: content not fetched; redirect refused).
- **U3**: <https://huggingface.co/fishaudio/drama-3/raw/main/README.md>
  (host: huggingface.co; policy: confirmed-by-user; HTTP 307;
  UNVERIFIED: content not fetched; redirect refused).
- **U4**: <https://huggingface.co/api/models/fishaudio/s2-pro>
  (host: huggingface.co; policy: confirmed-by-user; HTTP 307;
  UNVERIFIED: content not fetched; redirect refused).
- **U5**: <https://huggingface.co/api/models/fishaudio/drama-3>
  (host: huggingface.co; policy: confirmed-by-user; HTTP 307;
  UNVERIFIED: content not fetched; redirect refused).
- **Supporting metadata**: <https://api.github.com/repos/fishaudio/fish-speech>
  and <https://api.github.com/repos/fishaudio/fish-speech/contents>
  (host: api.github.com; policy: confirmed-by-user; HTTP 200 for each;
  used to locate authoritative files, not to infer license clearance).
- **Documentation discovery**: <https://api.github.com/repos/fishaudio/fish-speech/contents/docs?ref=0f8a12e8a651062fdee9c33a894bdccd3a8513f1>
  (host: api.github.com; policy: confirmed-by-user; HTTP 200).
- **Supporting inference documentation**: <https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/docs/en/inference.md>
  (host: raw.githubusercontent.com; policy: confirmed-by-user; HTTP 200;
  retrieved as context, not executed or treated as installation authorization).
- **I1**: [Recovered intake](intake.md) and
  [original committed idea](../../../.speckit-companion/process-create/idea-fish-speech.md)
  (policy: local repository evidence; original commit recorded in intake).
- **I2**: [Backend synthesis living spec](../../../capabilities/backend-synthesis/backend-synthesis.spec.md)
  (policy: local repository evidence; draft source behavior, not native qualification).
- **I3**: [VibeVoice integration feature specification](../../../specs/002-vibevoice-backend-integration/vibevoice-backend-integration.spec.md)
  (policy: local repository evidence; draft planning context).
- **I4**: [Private VibeVoice evaluation research](../../../specs/001-vibevoice-evaluation/research.md)
  (policy: local repository evidence; prior research, not a fresh external verification).
- **I5**: [Project licensing living spec](../../../capabilities/project-licensing/project-licensing.spec.md)
  (policy: local repository evidence; project review and release boundaries).
- **I6**: [Third-party notices](../../../THIRD_PARTY_NOTICES.md)
  (policy: local repository evidence; artifact and rights review boundaries).
