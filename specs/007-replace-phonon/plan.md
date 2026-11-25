# Plan: Replace Fish Speech with Ollama Phonon

## Summary

Replace Fish Speech with an explicitly selected Ollama Phonon engine for English and German while preserving native macOS speech and the authenticated speech API. Keep Phonon disabled until the exact model and voice assets have approved provenance and the configured unauthenticated service endpoint is verified as trusted. Split inputs to Phonon's documented per-request limit, then use the existing bounded audio conversion path to preserve WAV/MP3, speed, timeout, cancellation, and output-size behavior.

## Project Structure

```text
backend/app/
  config.py                         # Phonon endpoint, model, voice, and approval settings
  engines.py                        # Shared engine registry contract
  models.py                         # Speech request identifiers and text validation
  phonon.py                         # New bounded Ollama speech adapter
  routers.py                        # Authentication, legacy Fish response, health/catalog
  services.py                       # Engine registration, PCM/WAV conversion, dispatch
backend/tests/
  test_phonon.py                    # New adapter, response, and segmentation tests
  phonon_test_support.py            # Fake transport and approved-profile test fixtures
  test_phonon_api.py                # Public API contract tests with a fake endpoint
  test_phonon_request_contract.py   # Request limits and existing controls
  test_phonon_segmentation.py       # Public long-input segmentation behavior
  test_phonon_streaming.py          # Complete-response compatibility
  test_phonon_response_metadata.py  # Actual-engine response metadata
  test_phonon_security.py           # Authentication and trusted endpoint boundary
  test_phonon_privacy.py            # Error and log redaction behavior
  test_phonon_approval.py           # Unapproved asset and endpoint behavior
  test_phonon_availability.py       # Safe unavailable response, no fallback
  test_config.py                    # Phonon settings and endpoint validation
  test_models.py                    # Long text and retired-engine request validation
  test_phonon_live.py               # Opt-in, approval-gated model qualification
  test_native_speech_preservation.py # Public native-speech regression
  test_fish_retirement.py           # Public retired-engine and readiness behavior
  test_services.py                  # Engine routing and response behavior
  test_api.py                        # Public API, auth, safe errors, and readiness
  test_engine_catalog.py            # Public engine catalog
  test_speech_contract.py           # Cross-engine binary response contract
  test_fish_speech.py               # Remove Fish adapter coverage
  test_fish_process.py              # Remove Fish process coverage
  test_fish_worker_launcher.py      # Remove Fish launcher coverage
  test_fish_deployment_template.py  # Retain generic deployment safeguards; assert retired config is absent
backend/app/
  fish_speech.py                    # Remove Fish adapter
  fish_process.py                   # Remove managed Fish process
backend/deployment/
  fish_worker_launcher.py           # Remove Fish-only launcher
  com.example.private-speech-studio-backend.plist # Keep Phonon disabled in the retained template
capabilities/backend-synthesis/
  backend-synthesis.spec.md         # Update requirements and scenarios after implementation
  backend-synthesis.coverage.md     # Update requirement-to-test evidence
living-specs.yml                    # Register new Phonon implementation and tests
```

**Structure Decision**: Keep the Phonon HTTP adapter separate from `SpeechService`, reuse the registry and bounded conversion path, and remove Fish-only runtime/deployment code instead of maintaining two parallel integrations.

## Calls

```calls bounded speech request
  RequestBoundaryMiddleware.__call__ @ backend/app/main.py:23
+   create_speech @ backend/app/routers.py:94
+     SpeechService.synthesize_reserved @ backend/app/services.py:282
+       SpeechService._synthesize_phonon @ backend/app/services.py:246
+         PhononSpeechEngine.synthesize_pcm **new** @ backend/app/phonon.py
+         SpeechService._transcode_wav @ backend/app/services.py:469
```

## States

```states Phonon request lifecycle
received: A request enters authenticated request validation. (start)
rejected: Validation, retired Fish selection, or unavailable prerequisites stop the request safely. (final)
ready: The selected Phonon model and approved voice are available through the configured trusted endpoint.
generating: Text is split within the model limit and bounded PCM segments are collected.
complete: The complete requested audio is returned with the actual engine metadata. (final)
failed: Timeout, cancellation, malformed audio, or an output bound stops synthesis without fallback. (final)
received -> rejected: invalid request, retired Fish identifier, or missing Phonon prerequisites
received -> ready: authenticated valid Phonon request with approved assets
ready -> generating: acquire synthesis capacity
generating -> complete: all segments validate and bounded conversion succeeds
generating -> failed: generation or conversion violates an established guarantee
grid:
received | ready | generating
rejected | complete | failed
```

## Constitution Check

| Principle | Assessment |
|---|---|
| Keep specifications evidence-based | PASS. Update the living requirement scenarios and coverage map only alongside tested implementation; neither the plan nor mocked tests claim native qualification. |
| Prefer safe, bounded behavior | PASS. Keep the 32 KiB request-body, synthesis deadline, segment-count, temporary-storage, and output-size limits. Fail safely without truncation or silent fallback. |
| Protect users and operational boundaries | PASS. Keep Phonon off unless configured with reviewed assets and a trusted endpoint. Do not download models, generate speech, inspect a host, or change a running service as part of this repository work. |
| Verify observable outcomes | PASS. Test request, catalog, response, error, and readiness behavior through the API as well as adapter boundaries. |
| Be precise about platform and release claims | PASS. Treat Ollama/Apple Silicon compatibility and each model/voice's terms as release gates until verified for the target. |
| Development workflow | PASS. Keep changes on the existing branch and do not commit or deploy them as part of this plan. |

## Requirements Mapping

- **FR-001 / FR-011**: Remove Fish registration and runtime dependencies; explicitly reject retired `fish-speech` selections with a safe unavailable response. Do not redirect them.
- **FR-002 / FR-010**: Register Phonon only after the configured model and voice are reviewed, installed, and available. Keep model use disabled without the approval record.
- **FR-003**: Preserve the native `macos-say` registration and baseline readiness behavior.
- **FR-004 / FR-008**: Preserve authentication, speed control, voice selection, MP3/WAV, response metadata, and the 32 KiB encoded-request safeguard. Remove only the fixed 5,000-UTF-16-unit limit.
- **FR-005**: Split text at safe boundaries under the selected model's documented per-request capacity and preserve all segments in order.
- **FR-006**: Retain complete-response behavior initially. Add client-facing streaming only if bounded conversion, timeout, cancellation, error, and response guarantees can all be demonstrated.
- **FR-007 / FR-009**: Report the actual producing engine and keep speech text, credentials, endpoint details, and local paths out of errors, logs, and catalog output.
- **FR-012**: Keep post-use expectation follow-up separate from readiness and model qualification.
- **FR-013**: Remove the browser's fixed character limit and paste truncation. Measure the complete UTF-8 encoded JSON request against the existing 32 KiB boundary before sending; retain oversize input and show an actionable error.
- **FR-014 / FR-015**: Preserve response-driven engine disclosure and dynamic language-aware discovery; replace retired-engine browser fixtures with Phonon and verify both languages through the rendered form.

## Browser alignment

Update `frontend/app.js`, `frontend/index.html`, and the focused Playwright tests. Keep native speech as the initial engine and retain existing proxy authentication and request safeguards. Align the speech-generation living requirements and coverage map. Repository implementation does not itself authorize deployment.

## Unresolved Release Gates

The official source pages identify candidate English and German model tags and their published licenses, but do not grant project approval to use them. Exact model digests, voice IDs, source revisions, applicable voice terms, target compatibility, and the service endpoint's trusted network path must be reviewed before enabling Phonon or generating speech. Do not fetch models or voice assets as part of implementation.
