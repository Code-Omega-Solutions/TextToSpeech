# Research: Replace Fish Speech with Ollama Phonon

Research performed 2026-11-24. This records public source claims for planning; it is not legal approval, model qualification, or permission to download or use assets.

## Decision: Use Ollama's speech endpoint

**Decision**: The adapter will call Ollama's OpenAI-compatible `POST /v1/audio/speech` endpoint. Request raw `pcm`, the configured model tag, and an approved voice. Bound the PCM response, wrap it in a correctly sized WAV container, then use the existing FFmpeg path for speed adjustment and requested WAV or MP3 output.

**Rationale**: Ollama documents streamed WAV and PCM output at 24 kHz mono, and notes that its WAV stream uses maximum placeholder size fields. PCM avoids relying on those incomplete WAV lengths; the application can create a valid WAV after collecting the bounded result. The current service returns a complete `SynthesisResult.audio` byte string and a Starlette `Response`, so retaining the complete-response contract is the smallest way to preserve current size, timeout, cancellation, and conversion behavior.

**Alternatives considered**: Calling `/api/chat` is not the documented speech interface. Passing Ollama's WAV directly would require handling its maximum-size header. Client-facing streaming MP3 is deferred because the current service buffers a whole result and Ollama does not provide MP3 or speed control through the speech endpoint. Revisit streaming only if a bounded streaming encoder can preserve every existing guarantee.

## Decision: Keep candidate model tags explicit and disabled until approved

**Decision**: Plan against `phonon:31m-en` for English and `phonon:40m-de` for German as separate-language candidates. Do not set these as implicit runtime defaults. Keep Phonon unavailable until an explicit approval record pins the installed model identity, source, terms, and approved voice IDs.

**Rationale**: Ollama's library describes these tags as English and German checkpoints. It lists Apache 2.0 for the 31M English checkpoint and CC BY-NC 4.0 for the 40M German checkpoint. The latter's noncommercial restriction is consistent with the requester's stated private, noncommercial intent, but that statement does not replace review of the exact source, terms, voice assets, and target use. The Hugging Face model page also requires acceptance of its conditions before accessing model files.

**Alternatives considered**: A multilingual checkpoint could cover both languages, but the reviewed page lists it under CC BY-NC 4.0 and it is not needed to meet the two-language requirement. Keeping both candidate tags out of runtime defaults prevents an unreviewed download or accidental use.

## Decision: Do not hard-code unreviewed voice IDs

**Decision**: Expose only voice IDs in the approved configuration for each configured model. Missing approval or an empty approved catalog makes Phonon unavailable. A missing request voice may use a configured approved default; an unknown or language-incompatible voice fails safely.

**Rationale**: Ollama documents `default` as the checkpoint voice and supports named voices for Phonon. Gradium's public voice catalog lists additional German and English voices, but voice data has its own source and terms. The configured allowlist keeps discovery limited to reviewed choices and avoids placeholder IDs.

**Alternatives considered**: Advertising every voice returned by a local runtime would make the service's public catalog depend on mutable host state and could expose voices whose terms were not reviewed. Invented sample IDs are not valid configuration.

## Decision: Use bounded client-side segmentation

**Decision**: Split request text into ordered segments that do not exceed Ollama's documented 4,096-character input limit. Preserve every source character across segment boundaries, including separators. Enforce the existing request-body, timeout, segment-count, temporary-storage, and output-size limits across the complete operation.

**Rationale**: Ollama documents the 4,096-character limit and says its CLI splits longer text. The application calls the API directly, so it must split the request itself. Applying limits to the complete synthesis prevents segmentation from bypassing existing safeguards.

**Alternatives considered**: Rejecting every over-capacity request would fail FR-005. Sending the whole request and relying on truncation or undocumented server behavior risks omitted speech.

## Decision: Restrict the service endpoint to an explicitly trusted local origin

**Decision**: Leave the Phonon endpoint unset by default. Initially accept only an HTTP(S) loopback origin, reject redirects, bypass ambient proxies, and send no backend credential to Ollama. Do not enable a non-loopback endpoint until its network boundary is separately reviewed and approved.

**Rationale**: The Ollama service is unauthenticated and the repository's existing Fish integration already validates loopback origins, disables proxies, and blocks redirects. The feature description's same-machine assumption is unverified, so an arbitrary host or container-network route cannot be treated as trusted.

**Alternatives considered**: Accepting any operator-supplied URL could send private speech text to an unverified endpoint. Reusing the backend bearer credential is not useful because Ollama does not authenticate local speech requests.

## Evidence

- Ollama Speech documentation: https://docs.ollama.com/capabilities/speech
  - Local Ollama 0.40.9 or later; streamed WAV/PCM output; 24 kHz mono; 4,096-character request limit; no speed or MP3 support; `default` and named voice support.
- Ollama English model: https://ollama.com/library/phonon:31m-en
  - English checkpoint, Apache 2.0 license, and source link to `gradium/phonon-31m-en`.
- Ollama German model: https://ollama.com/library/phonon:40m-de
  - German checkpoint, CC BY-NC 4.0 terms and source links to Gradium model and voice repositories.
- Gradium German model card: https://huggingface.co/gradium/phonon-40m-de
  - German language, 24 kHz mono output, CC BY-NC 4.0, runtime usage and voice example. Access requires acceptance of the model conditions.
- Gradium voice catalog: https://huggingface.co/gradium/phonon-voices
  - Public inventory of language-specific voices and IDs; exact IDs and terms still require review before use.
- Existing backend patterns: `backend/app/fish_speech.py`, `backend/app/services.py`, `backend/app/config.py`, and `backend/app/main.py`.
  - Standard-library HTTP transport, no redirects/proxies, engine registry, bounded conversion, auth, and a 32 KiB request-body boundary.
