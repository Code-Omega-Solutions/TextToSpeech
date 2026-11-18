# Headroom-First Speech Contract

The existing speech request schema is unchanged. With
`TTS_FISH_OPPORTUNISTIC=true`, optional engine preference is best effort.
Native fallback preserves the resolved locale, requested output format, bounded
speed, authentication, cancellation and output limits; it ignores the optional
voice preference. Explicit native requests never start Fish.

Successful fallback returns `X-Speech-Backend: macos-say` and
`X-Speech-Fallback: true`. Invalid input remains 422, invalid credentials remain
401, cancellation produces no replacement audio, and native failure remains an
explicit error. Strict mode remains the default and preserves legacy 503s.

The managed Fish launcher must implement the existing adapter's authenticated
loopback `GET /v1/health` and MessagePack `POST /v1/tts` WAV contract. Configuring
an MLX OpenAI-compatible server alone does not establish that compatibility.
It must use local, pre-reviewed artifacts without runtime network downloads and
run all model-bearing subprocesses in the owned process group. Daemonizing or
launching an external supervisor is not supported.

The application owns the command it starts, not arbitrary pre-existing listeners.
It must not adopt an externally managed Fish process. An existing listener or
an uncertain TCP connection probe denies launch without waiting for HTTP health. No secret may be
placed in argv; use a reviewed protected launcher and server-side credential
configuration. Command configuration is private operator data, not API input.

Cold start defaults to available memory >= reserve + full worker budget.
An explicit `TTS_FISH_STARTUP_MEMORY_BYTES` sets a smaller positive startup
allowance no greater than that budget. It does not change loading/active/idle
reserve checks, the RSS ceiling, cooldown or native fallback. The authorized
private trial uses 4 GiB startup + 12 GiB reserve, retaining the 16 GiB runtime
ceiling. Sampled monitoring is not hard physical/Metal isolation and can yield
only after pressure is observed.

The Fish catalog may expose only the four approved local Common Voice profiles
(`de-male`, `de-female`, `en-male`, `en-female`) after exact private reference
and artifact approvals. It must not expose contributor IDs or dataset paths.
Any downstream generated-audio sharing must identify the output as
machine-generated and remain disabled unless the output complies with all
applicable terms, including the MDC personal-data restriction. A user's
permission attestation does not override that restriction.
