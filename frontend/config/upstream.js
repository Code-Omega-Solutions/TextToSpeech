import {
  closeSync,
  constants as fsConstants,
  fstatSync,
  openSync,
  readSync,
} from "node:fs";

const originPattern = /^https?:\/\/([A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*|[0-9]{1,3}(\.[0-9]{1,3}){3})(:[0-9]{1,5})?$/;
export const MAX_PROXY_BODY_BYTES = 32 * 1024;

export function validateUpstream(value) {
  if (!value) {
    throw new Error("TTS_UPSTREAM_URL is required; configure the authorized speech service origin.");
  }
  if (value !== value.trim() || !originPattern.test(value)) {
    throw new Error("TTS_UPSTREAM_URL must be an HTTP(S) origin with no path, credentials, query, or fragment.");
  }
  return value;
}

export function readProxyCredential(env) {
  const environmentCredential = env.TTS_API_KEY;
  const credentialPath = env.TTS_API_KEY_FILE;
  if (environmentCredential !== undefined && credentialPath !== undefined) {
    throw new Error("Configure only one of TTS_API_KEY and TTS_API_KEY_FILE.");
  }
  if (environmentCredential !== undefined) {
    if (!environmentCredential.trim() || /[\r\n]/.test(environmentCredential)) {
      throw new Error("TTS_API_KEY must contain a single nonempty credential.");
    }
    return environmentCredential;
  }
  if (!credentialPath) {
    throw new Error("TTS_API_KEY or TTS_API_KEY_FILE is required for server-side proxy authorization.");
  }

  let descriptor;
  try {
    descriptor = openSync(
      credentialPath,
      fsConstants.O_RDONLY | (fsConstants.O_NOFOLLOW ?? 0),
    );
    const info = fstatSync(descriptor);
    if (
      !info.isFile()
      || (typeof process.getuid === "function" && info.uid !== process.getuid())
      || (info.mode & 0o077) !== 0
      || info.size > 4096
    ) {
      throw new Error();
    }
    const buffer = Buffer.alloc(4097);
    const length = readSync(descriptor, buffer, 0, buffer.length, 0);
    if (length > 4096) {
      throw new Error();
    }
    const credential = new TextDecoder("utf-8", { fatal: true })
      .decode(buffer.subarray(0, length))
      .replace(/\n$/, "");
    if (!credential.trim() || /[\r\n]/.test(credential)) {
      throw new Error();
    }
    return credential;
  } catch {
    throw new Error("TTS_API_KEY_FILE is unavailable or not protected.");
  } finally {
    if (descriptor !== undefined) closeSync(descriptor);
  }
}

export function apiProxy(upstream, credential) {
  if (!credential || /[\r\n]/.test(credential)) {
    throw new Error("A server-side proxy credential is required.");
  }
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
        headers: {
          Authorization: `Bearer ${credential}`,
          Connection: "",
        },
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyRequest, request) => {
            proxyRequest.setHeader("Authorization", `Bearer ${credential}`);
            if (Buffer.isBuffer(request.proxyBody)) {
              proxyRequest.removeHeader("transfer-encoding");
              proxyRequest.setHeader("Content-Length", String(request.proxyBody.length));
              proxyRequest.end(request.proxyBody);
            }
          });
        },
      },
    ]),
  );
}
