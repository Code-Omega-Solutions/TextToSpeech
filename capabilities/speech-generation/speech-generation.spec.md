# Speech generation - Living Spec

> [DRAFT] Adopted from implemented frontend behavior and existing tests.
> This is a current-behavior baseline, not the proposed backend design.

## Purpose

Let a user turn text into playable, downloadable speech through their configured
service without adding browser-side text persistence.

## Requirements

### Text entry is bounded and editable
<!-- touches: frontend/app.js, frontend/index.html, frontend/tests/e2e/** -->
<!-- adopted: frontend/app.js, frontend/index.html, frontend/tests/e2e/speech.spec.js -->

The form SHALL require text, limit entry to 5,000 UTF-16 code units, show its
current length, and provide clear and clipboard-paste controls.

#### Scenario: clipboard text exceeds the limit
- **WHEN** a permitted paste returns more than 5,000 units
- **THEN** the input contains the first 5,000 units and a truncation message appears.

#### Scenario: clearing the form
- **WHEN** the user clears nonempty input
- **THEN** input, count, status and previous audio reset, and focus returns to the input.

#### Scenario: clipboard access fails
- **WHEN** the browser denies or cannot provide clipboard access
- **THEN** existing input remains and a visible permission message appears.

### Generation preserves the speech request contract
<!-- touches: frontend/app.js, frontend/index.html, frontend/tests/e2e/** -->
<!-- adopted: frontend/app.js, frontend/index.html, frontend/tests/e2e/speech.spec.js -->

The form SHALL offer automatic detection or German/US-English/UK-English,
MP3 or WAV, and speed 0.5-2.0 in increments of 0.1. Defaults are automatic
detection, MP3 and speed 1.0. Generation sends JSON to `/api/v1/audio/speech`
with `input`, `response_format`, numeric `speed`, and `language` only when selected.

#### Scenario: automatic language detection
- **WHEN** the user generates speech with the default language choice
- **THEN** the request omits `language` rather than sending an empty value.

#### Scenario: a request is pending
- **WHEN** generation begins
- **THEN** previous audio is cleared and the submit control stays disabled until completion.

### Audio is available without persistent frontend storage
<!-- touches: frontend/app.js, frontend/index.html, frontend/tests/e2e/** -->
<!-- adopted: frontend/app.js, frontend/tests/e2e/speech.spec.js -->

Successful nonempty audio SHALL be presented through a browser object URL for
playback and download. Replacing, clearing or pasting text revokes previous audio
as implemented; text and audio are not written to browser persistent storage.

#### Scenario: autoplay is blocked
- **WHEN** generation succeeds but automatic playback is denied
- **THEN** audio and its download remain available, with an instruction to select play.

#### Scenario: audio is replaced
- **WHEN** regeneration, clear, or successful paste removes previous audio
- **THEN** its object URL is revoked.

### Service and generation errors are visible
<!-- touches: frontend/app.js, frontend/index.html, frontend/tests/e2e/** -->
<!-- adopted: frontend/app.js, frontend/tests/e2e/speech.spec.js -->

The page SHALL check service health on load. HTTP generation failures use a
string JSON `detail` when available, otherwise the HTTP status; network failures
and empty audio have explicit messages. Generation failure marks the service
unavailable; successful generation marks it connected.

#### Scenario: the service recovers
- **WHEN** a request succeeds after a failed request
- **THEN** previous error text clears, audio becomes available and the service is connected.

### The restored interface remains usable on desktop and mobile
<!-- touches: frontend/index.html, frontend/styles.css, frontend/public/**, frontend/playwright.config.js, frontend/tests/e2e/** -->
<!-- adopted: frontend/index.html, frontend/styles.css, frontend/tests/e2e/fidelity.spec.js -->

The interface SHALL retain labeled controls, keyboard-operable text entry,
live status feedback, responsive layout, and the recovered visual identity.

#### Scenario: a narrow screen
- **WHEN** the page is displayed at a supported mobile test viewport
- **THEN** the interface has no horizontal overflow and generation controls remain usable.

## Uncovered

- Backend synthesis behavior is not implemented in this repository.
- The browser does not supply backend credentials. Authentication improvements
  remain proposed in [the backend feature](../../specs/001-macos-backend/spec.md).
- Plain input editing does not currently invalidate existing audio. Changing
  settings during an in-flight request is not specified as snapshot-isolated.
- A text limit does not guarantee the encoded request fits the current proxy limit.
