import {
  closeSync,
  chmodSync,
  existsSync,
  constants as fsConstants,
  fstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  readSync,
  renameSync,
  writeFileSync,
} from "node:fs";
import { randomBytes } from "node:crypto";
import { dirname } from "node:path";

const originPattern =
  /^https?:\/\/([A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*|[0-9]{1,3}(\.[0-9]{1,3}){3})(:[0-9]{1,5})?$/;
export const MAX_PROXY_BODY_BYTES = 32 * 1024;
export const DEFAULT_ENDPOINT_CONFIG_FILE =
  "/var/lib/private-speech-studio/endpoint.json";
export const DEFAULT_TARGET_IDS = ["production", "prototype"];

export function validateUpstream(value) {
  if (!value) {
    throw new Error(
      "TTS_UPSTREAM_URL is required; configure the authorized speech service origin.",
    );
  }
  if (value !== value.trim() || !originPattern.test(value)) {
    throw new Error(
      "TTS_UPSTREAM_URL must be an HTTP(S) origin with no path, credentials, query, or fragment.",
    );
  }
  return value;
}

function approvedOrigins(env = process.env) {
  return (env.TTS_ALLOWED_UPSTREAMS || env.TTS_UPSTREAM_URL)
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .map(validateUpstream);
}

export function loadApprovedTargets(env = process.env) {
  const production = env.TTS_TARGET_PRODUCTION_URL || env.TTS_UPSTREAM_URL;
  const configured = env.TTS_TARGETS_JSON;
  let targets = { production: { label: "Production", origin: production } };
  if (env.TTS_PROTOTYPE_UPSTREAM_URL) {
    targets.prototype = { label: "Prototype", origin: env.TTS_PROTOTYPE_UPSTREAM_URL };
  }
  if (configured !== undefined) {
    let parsed;
    try { parsed = JSON.parse(configured); } catch { throw new Error("TTS_TARGETS_JSON must be valid JSON."); }
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("TTS_TARGETS_JSON must be an object.");
    }
    targets = parsed;
  }
  const allowed = new Set(approvedOrigins(env));
  return Object.fromEntries(Object.entries(targets).map(([id, value]) => {
    if (!/^[a-z0-9][a-z0-9_-]{0,31}$/.test(id) || !value || typeof value !== "object") {
      throw new Error("TTS_TARGETS_JSON contains an invalid target.");
    }
    const origin = validateUpstream(value.origin);
    if (!allowed.has(origin)) throw new Error("Every target must be operator-approved.");
    return [id, { label: typeof value.label === "string" && value.label.trim() ? value.label.trim() : id, origin }];
  }));
}

export function endpointConfigPath(env = process.env) {
  return env.TTS_ENDPOINT_CONFIG_FILE || DEFAULT_ENDPOINT_CONFIG_FILE;
}

export function loadConfiguredUpstream(env = process.env) {
  const fallback = validateUpstream(env.TTS_UPSTREAM_URL);
  const path = endpointConfigPath(env);
  if (!existsSync(path)) return fallback;
  let parsed;
  try {
    parsed = JSON.parse(readFileSync(path, "utf8"));
  } catch {
    throw new Error("The endpoint configuration file is corrupt or unreadable.");
  }
  if (!parsed || typeof parsed.origin !== "string") {
    throw new Error("The endpoint configuration file is invalid.");
  }
  return validateUpstream(parsed.origin);
}

export function saveConfiguredUpstream(value, env = process.env) {
  const origin = validateUpstream(value);
  const path = endpointConfigPath(env);
  const directory = dirname(path);
  const temporary = `${path}.${randomBytes(8).toString("hex")}.tmp`;
  try {
    mkdirSync(directory, { recursive: true, mode: 0o700 });
    writeFileSync(temporary, `${JSON.stringify({ origin })}\n`, {
      encoding: "utf8",
      mode: 0o600,
    });
    chmodSync(temporary, 0o600);
    renameSync(temporary, path);
  } catch (error) {
    try {
      if (existsSync(temporary)) renameSync(temporary, `${temporary}.failed`);
    } catch {
      // Preserve the original write failure.
    }
    throw new Error("The endpoint configuration could not be saved.", {
      cause: error,
    });
  }
  return origin;
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
    throw new Error(
      "TTS_API_KEY or TTS_API_KEY_FILE is required for server-side proxy authorization.",
    );
  }

  let descriptor;
  try {
    descriptor = openSync(
      credentialPath,
      fsConstants.O_RDONLY | (fsConstants.O_NOFOLLOW ?? 0),
    );
    const info = fstatSync(descriptor);
    if (
      !info.isFile() ||
      (typeof process.getuid === "function" && info.uid !== process.getuid()) ||
      (info.mode & 0o077) !== 0 ||
      info.size > 4096
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

export function apiProxy(upstream, credential, env = process.env) {
  if (!credential || /[\r\n]/.test(credential)) {
    throw new Error("A server-side proxy credential is required.");
  }
  return Object.fromEntries(
    [
      ["/healthz", 10_000],
      ["/(?:readyz|v1/audio/engines)", 15_000],
      ["/v1/audio/speech", 75_000],
    ].map(([path, timeout]) => [
      `^/api${path}(?:\\?.*)?$`,
      {
        target: upstream,
        router: () => loadConfiguredUpstream(env),
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
              proxyRequest.setHeader(
                "Content-Length",
                String(request.proxyBody.length),
              );
              proxyRequest.end(request.proxyBody);
            }
          });
        },
      },
    ]),
  );
}
