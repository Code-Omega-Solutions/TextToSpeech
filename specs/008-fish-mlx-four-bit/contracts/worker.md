# Worker contract

The outer authenticated backend continues to send MessagePack to the owned loopback Fish worker and accepts bounded WAV audio. Existing health checks, reference identifiers, request fields, response metadata, fallback reason allowlist and native speech remain unchanged. Candidate-specific activation and approval are operator configuration, not a new public model identifier.

The candidate consumes only the approved four-reference catalog. It must not log text, reference transcripts, credentials, raw responses or private paths. A missing, invalid or incompatible approval is a startup failure and follows the existing managed fallback policy.
