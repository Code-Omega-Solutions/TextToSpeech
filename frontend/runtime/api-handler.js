import { loadConfiguredUpstream, readProxyCredential, saveConfiguredUpstream, validateUpstream } from "../config/upstream.js";

const maxBody = 32 * 1024;
const routes = new Map([
  ["/api/healthz", [10_000, "GET"]],
  ["/api/readyz", [15_000, "GET"]],
  ["/api/v1/audio/engines", [15_000, "GET"]],
  ["/api/v1/audio/speech", [75_000, "POST"]],
]);
const json = (res, status, value) => {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(value));
};
const auth = (req, env) => {
  // Configuration is privileged, but intentionally uses the same protected
  // bearer credential as the upstream backend. This avoids a second operator
  // secret while preserving an explicit authorization check.
  const expected = env.TTS_API_KEY;
  return Boolean(expected && req.headers.authorization?.replace(/^Bearer\s+/i, "") === expected);
};
const body = async (req) => {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > maxBody) throw Object.assign(new Error("Request body exceeds the 32 KiB limit."), { status: 413 });
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
};
function allowed(origin, env) {
  return (env.TTS_ALLOWED_UPSTREAMS || env.TTS_UPSTREAM_URL).split(",").map((v) => v.trim()).filter(Boolean).map(validateUpstream).includes(origin);
}
export function createApiHandler(env = process.env) {
  return async (req, res) => {
    const url = new URL(req.url, "http://localhost");
    if (url.pathname === "/api/configuration") {
      if (!auth(req, env)) { json(res, 401, { detail: "Operator authorization is required." }); return true; }
      if (req.method === "GET") {
        try { json(res, 200, { origin: loadConfiguredUpstream(env) }); } catch (error) { json(res, 503, { detail: error.message }); }
        return true;
      }
      if (req.method !== "PUT") { json(res, 403, { detail: "Configuration requires GET or PUT." }); return true; }
      try {
        const origin = validateUpstream(JSON.parse((await body(req)).toString("utf8")).origin);
        if (!allowed(origin, env)) { json(res, 403, { detail: "That destination is not operator-approved." }); return true; }
        json(res, 200, { origin: saveConfiguredUpstream(origin, env) });
      } catch (error) { json(res, error.status || 400, { detail: error.message }); }
      return true;
    }
    if (!routes.has(url.pathname)) {
      if (url.pathname.startsWith("/api/")) { json(res, 404, { detail: "Unknown API endpoint." }); return true; }
      return false;
    }
    const [timeout, method] = routes.get(url.pathname);
    if (req.method !== method) { json(res, 403, { detail: `${method} required.` }); return true; }
    let payload;
    try { payload = method === "POST" ? await body(req) : undefined; } catch (error) { json(res, error.status || 400, { detail: error.message }); return true; }
    try {
      const target = new URL(loadConfiguredUpstream(env) + url.pathname.replace(/^\/api/, "") + url.search);
      const headers = { Authorization: `Bearer ${readProxyCredential(env)}` };
      if (payload) headers["Content-Length"] = String(payload.length);
      const upstream = await fetch(target, { method, headers, body: payload, signal: AbortSignal.timeout(timeout), redirect: "manual" });
      res.writeHead(upstream.status, Object.fromEntries(upstream.headers));
      res.end(Buffer.from(await upstream.arrayBuffer()));
    } catch { json(res, 502, { detail: "The configured speech service could not be reached." }); }
    return true;
  };
}
