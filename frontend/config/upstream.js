const originPattern = /^https?:\/\/([A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*|[0-9]{1,3}(\.[0-9]{1,3}){3})(:[0-9]{1,5})?$/;

export function validateUpstream(value) {
  if (!value) {
    throw new Error("TTS_UPSTREAM_URL is required; configure the authorized speech service origin.");
  }
  if (value !== value.trim() || !originPattern.test(value)) {
    throw new Error("TTS_UPSTREAM_URL must be an HTTP(S) origin with no path, credentials, query, or fragment.");
  }
  return value;
}

export function apiProxy(upstream) {
  return Object.fromEntries(
    [
      ["/healthz", 10_000],
      ["/readyz", 15_000],
      ["/v1/audio/speech", 75_000],
    ].map(([path, timeout]) => [
      `^/api${path}(?:\\?.*)?$`,
      {
        target: upstream,
        rewrite: (requestPath) => requestPath.slice("/api".length),
        timeout,
        proxyTimeout: timeout,
        headers: { Connection: "" },
      },
    ]),
  );
}
