# Speech generation - Requirement-to-test map

These links identify existing tests, not a fresh execution result or proof that
every sentence of a requirement has an assertion. Review both when behavior changes.

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Text entry is bounded and editable | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Input limit, counter, clear/focus and clipboard success/failure cases |
| Generation preserves the speech request contract | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Defaults, exact requests, locale omission/inclusion, formats, speeds and loading |
| Audio is available without persistent frontend storage | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Audio visibility, filename, blocked autoplay and object-URL revocation; persistent-storage absence also needs code review |
| Service and generation errors are visible | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Health failures, JSON/plain/network/empty-audio errors and successful retry |
| The restored interface remains usable on desktop and mobile | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js), [frontend/tests/e2e/fidelity.spec.js](../../frontend/tests/e2e/fidelity.spec.js) | Labeled controls, keyboard entry, overflow and optional original-page pixel comparison; not a complete accessibility audit |
