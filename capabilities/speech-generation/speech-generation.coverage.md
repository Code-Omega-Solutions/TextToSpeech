# Speech generation - Requirement-to-test map

These links identify existing tests, not a fresh execution result or proof that
every sentence of a requirement has an assertion. Review both when behavior changes.

| Requirement | Existing test reference | Evidence scope |
| --- | --- | --- |
| Text entry is bounded and editable | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Long typed and pasted text, encoded request boundary, counter, clear/focus and clipboard cases |
| Generation preserves the speech request contract | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js), [frontend/tests/e2e/engine-discovery.spec.js](../../frontend/tests/e2e/engine-discovery.spec.js), [frontend/tests/config.test.js](../../frontend/tests/config.test.js) | Defaults, Phonon selection and disclosure in both supported locales, voices, formats, speeds, loading, discovery failure and catalog filtering; endpoint policy/persistence is covered separately |
| Audio is available without persistent frontend storage | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Audio visibility, engine and fallback disclosure, legacy headers, filename, blocked autoplay and object-URL revocation; persistent-storage absence also needs code review |
| Service and generation errors are visible | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js) | Health failures, JSON/plain/network/empty-audio errors and successful retry |
| The restored interface remains usable on desktop and mobile | [frontend/tests/e2e/speech.spec.js](../../frontend/tests/e2e/speech.spec.js), [frontend/tests/e2e/fidelity.spec.js](../../frontend/tests/e2e/fidelity.spec.js) | Labeled controls, keyboard entry, overflow and optional original-page pixel comparison; not a complete accessibility audit |
