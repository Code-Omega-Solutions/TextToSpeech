# Engine Catalog and Speech UI Contract

## API

### `GET /v1/audio/engines`

This authenticated, read-only route returns the configured engine catalog. It
reports only public engine identifiers, availability, supported languages, and
public voice identifiers. It does not expose credentials, filesystem paths, or
private host details.

Successful response: JSON with this shape:

```json
{
  "engines": [
    {
      "id": "macos-say",
      "available": true,
      "languages": ["English", "German"],
      "voices": []
    }
  ]
}
```

`engines` contains configured engines. Each `id` is the identifier accepted by
the existing speech selection field. `available` is a boolean. `languages`
contains the supported languages, and `voices` contains public voice identifier
strings supported by that engine. The example's empty `voices` array denotes
that no voice identifiers are advertised in the example; it does not prescribe
an engine's catalog contents.

The route uses the service's existing authentication boundary. Discovery does
not change the response or error contract of the speech route.

### Existing speech route: `POST /v1/audio/speech`

Keep the existing authenticated request and response contract unchanged,
including its request fields, validation, limits, MP3/WAV output, request ID,
backend/fallback response metadata, and safe error behavior. The existing
`model` field remains the per-request engine selector; `voice` remains the voice
selector. An omitted `model` continues to use the configured default. An
unavailable selected engine, including legacy `vibevoice`, returns the existing
safe unavailable response and is not silently replaced unless explicit
fallback policy applies.

## Vanilla-JavaScript UI and Proxy

- On load, the speech interface fetches `GET /v1/audio/engines` through the
  existing same-origin Vite API proxy.
- The proxy allowlists the catalog GET route and applies the existing protected
  server-side authentication behavior. Browser JavaScript does not receive or
  store the upstream credential.
- The interface populates the engine selector with advertised entries and
  filters language and voice choices to the selected language and engine.
  Unavailable engines and unadvertised choices are not selectable.
- If discovery fails or advertises no usable engine, the interface shows a
  safe status and prevents submission of an unavailable choice.
- On submission, the interface sends the selected engine and voice through the
  existing `model` and `voice` fields to `POST /v1/audio/speech`. Existing
  language, format, speed, playback, and download behavior remains in place.
