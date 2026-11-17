import { loadApprovedTargets, loadConfiguredUpstream, readProxyCredential, saveConfiguredUpstream, validateUpstream } from "../config/upstream.js";
import { randomBytes } from "node:crypto";

const maxBody = 32 * 1024;
const routes = new Map([
  ["/api/targets", [5_000, "GET"]],
  ["/api/target", [5_000, "POST"]],
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
const cookieValue = (req) => (req.headers.cookie || "").match(/(?:^|;\s*)tts_target=([^;]+)/)?.[1];
export function createApiHandler(env = process.env) {
  const sessions = new Map();
  const targetFor = (req) => {
    const targets = loadApprovedTargets(env);
    const session = cookieValue(req);
    const selectedId = sessions.get(session);
    if (selectedId && targets[selectedId]) {
      return { targets, target: targets[selectedId] };
    }

    // Unselected clients follow the protected persisted configuration. The
    // configured origin must still correspond to an operator-approved target;
    // explicit opaque session choices never mutate this fallback.
    const configured = loadConfiguredUpstream(env);
    const target = Object.values(targets).find(({ origin }) => origin === configured);
    if (!target) throw new Error("The configured speech service is not an approved target.");
    return { targets, target };
  };
  return async (req, res) => {
    const url = new URL(req.url, "http://localhost");
    if (url.pathname === "/api/targets") {
      if (req.method !== "GET") { json(res, 403, { detail: "Target discovery requires GET." }); return true; }
      try {
        const { targets, target } = targetFor(req);
        json(res, 200, { targets: Object.entries(targets).map(([id, value]) => ({ id, label: value.label })), selected: Object.entries(targets).find(([, value]) => value === target)?.[0] });
      } catch (error) { json(res, 503, { detail: error.message }); }
      return true;
    }
    if (url.pathname === "/api/target") {
      if (req.method !== "POST") { json(res, 403, { detail: "Target selection requires POST." }); return true; }
      try {
        const payload = JSON.parse((await body(req)).toString("utf8"));
        const targets = loadApprovedTargets(env);
        if (!payload || typeof payload.id !== "string" || !targets[payload.id]) { json(res, 403, { detail: "That target is not operator-approved." }); return true; }
        const session = cookieValue(req) || randomSessionId();
        if (sessions.size >= 1024 && !sessions.has(session)) sessions.delete(sessions.keys().next().value);
        sessions.set(session, payload.id);
        res.writeHead(204, { "Set-Cookie": `tts_target=${session}; HttpOnly; SameSite=Lax; Path=/` });
        res.end();
      } catch (error) { json(res, error.status || 400, { detail: error.message }); }
      return true;
    }
    if (url.pathname === "/api/configuration") {
      if (!auth(req, env)) { json(res, 401, { detail: "Operator authorization is required." }); return true; }
      if (req.method === "GET") {
        try { loadConfiguredUpstream(env); json(res, 200, { configured: true }); } catch (error) { json(res, 503, { detail: error.message }); }
        return true;
      }
      if (req.method !== "PUT") { json(res, 403, { detail: "Configuration requires GET or PUT." }); return true; }
      try {
        const origin = validateUpstream(JSON.parse((await body(req)).toString("utf8")).origin);
        const approved = (env.TTS_ALLOWED_UPSTREAMS || env.TTS_UPSTREAM_URL).split(",").map((value) => value.trim()).filter(Boolean).map(validateUpstream);
        if (!approved.includes(origin)) { json(res, 403, { detail: "That destination is not operator-approved." }); return true; }
        saveConfiguredUpstream(origin, env);
        json(res, 200, { saved: true });
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
      const { target: selected } = targetFor(req);
      const target = new URL(selected.origin + url.pathname.replace(/^\/api/, "") + url.search);
      const headers = { Authorization: `Bearer ${readProxyCredential(env)}` };
      if (payload) headers["Content-Length"] = String(payload.length);
      const upstream = await fetch(target, { method, headers, body: payload, signal: AbortSignal.timeout(timeout), redirect: "manual" });
      res.writeHead(upstream.status, Object.fromEntries(upstream.headers));
      res.end(Buffer.from(await upstream.arrayBuffer()));
    } catch { json(res, 502, { detail: "The configured speech service could not be reached." }); }
    return true;
  };
}

function randomSessionId() {
  return randomBytes(18).toString("base64url");
}
