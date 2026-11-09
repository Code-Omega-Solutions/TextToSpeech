# Speech contract: Automatic language fallback

For `POST /v1/audio/speech`, a valid request with no language and an automatic
classification outside German and English proceeds using en-US. Explicit
supported languages continue to bypass detection. Unsupported explicit language
values remain invalid. Other request limits, authentication, response formats,
and error handling remain unchanged.
