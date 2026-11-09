# Implementation Plan: Language detection fallback

## Summary

Use en-US when the language detector returns an unsupported result and the
request contains no explicit language. Preserve configured short-input behavior,
explicit locale validation, and error propagation.

## Technical Context

- Python backend, FastAPI request handling, and the existing langid classifier.
- Backend unit and API tests use mocked synthesis; native macOS qualification is separate.
- The existing speech contract changes only for unsupported automatic detections.

## Constitution Check

Update the backend living requirement and coverage map together with code and
tests. Use synthetic input, avoid exposing speech text or credentials, preserve
existing safeguards, and do not deploy. Native qualification remains a release gate.

## Design

Normalize supported detector results and return en-US for other results. Do not
catch unexpected classifier exceptions. Retain the early return for an explicit
language and the configured short-input default. Verify both classifier injection
and the real classifier entry point, plus the speech endpoint with mocked audio.

See [research](research.md), [data model](data-model.md),
[contract](contracts/speech.md), and [quickstart](quickstart.md).
