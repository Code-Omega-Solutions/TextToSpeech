# Research: Language detection fallback

## Decision

Return en-US for unsupported automatic classifications, while leaving
unexpected detector errors visible and the short-input default configurable.

## Rationale

The existing classifier can return languages outside the supported voice set.
An explicit fallback fulfills the requested behavior without weakening input
validation or concealing runtime failures.

## Alternatives

Rejecting unsupported classifications retains the reported failure. Restricting
classification to two languages changes the classifier's choice and could
select German where an inconclusive classification should use en-US.
