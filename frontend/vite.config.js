import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import {
  apiProxy,
  MAX_PROXY_BODY_BYTES,
  readProxyCredential,
  loadConfiguredUpstream,
  saveConfiguredUpstream,
  validateUpstream,
} from "./config/upstream.js";

const root = fileURLToPath(new URL(".", import.meta.url));

const headers = {
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};

function restrictApi(server, env) {
  server.middlewares.use((request, response, next) => {
    const path = (request.url || "/").split("?")[0];
    const reject = (status, detail) => {
      response.writeHead(status, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ detail }));
    };
    if (path === "/api/configuration") {
      if (request.method === "GET") {
        try {
          response.writeHead(200, { "Content-Type": "application/json" });
          response.end(JSON.stringify({ origin: loadConfiguredUpstream(env) }));
        } catch (error) {
          reject(503, error.message);
        }
        return;
      }
      if (request.method !== "PUT") {
        response.writeHead(403).end("Configuration requires GET or PUT.");
        return;
      }
      const chunks = [];
      let size = 0;
      request.on("data", (chunk) => {
        size += chunk.length;
        if (size <= 4096) chunks.push(chunk);
      });
      request.on("end", () => {
        if (size > 4096) {
          reject(413, "Configuration request is too large.");
          return;
        }
        try {
          const payload = JSON.parse(Buffer.concat(chunks).toString("utf8"));
          const origin = saveConfiguredUpstream(payload.origin, env);
          response.writeHead(200, { "Content-Type": "application/json" });
          response.end(JSON.stringify({ origin }));
        } catch (error) {
          reject(400, error.message);
        }
      });
      return;
    }
    if (path === "/api/v1/audio/speech" && request.method !== "POST") {
      response.writeHead(403).end("Speech generation requires POST.");
    } else if (path === "/api/v1/audio/engines" && request.method !== "GET") {
      response.writeHead(403).end("Engine discovery requires GET.");
    } else if (
      ["/api/healthz", "/api/readyz"].includes(path) &&
      request.method !== "GET"
    ) {
      response.writeHead(403).end("Health routes require GET.");
    } else if (
      path.startsWith("/api/") &&
      ![
        "/api/configuration",
        "/api/healthz",
        "/api/readyz",
        "/api/v1/audio/engines",
        "/api/v1/audio/speech",
      ].includes(path)
    ) {
      response.writeHead(404).end("Unknown API endpoint.");
    } else if (path === "/api/v1/audio/speech") {
      const contentLength = request.headers["content-length"];
      if (contentLength !== undefined) {
        const declaredLength = Number(contentLength);
        if (!Number.isSafeInteger(declaredLength) || declaredLength < 0) {
          reject(400, "Invalid request.");
          request.resume();
          return;
        }
        if (declaredLength > MAX_PROXY_BODY_BYTES) {
          reject(413, "Request body exceeds the 32 KiB limit.");
          request.resume();
          return;
        }
      }

      const chunks = [];
      let bodySize = 0;
      let rejected = false;
      request.on("data", (chunk) => {
        bodySize += chunk.length;
        if (bodySize > MAX_PROXY_BODY_BYTES) {
          rejected = true;
          chunks.length = 0;
          if (!response.headersSent) {
            reject(413, "Request body exceeds the 32 KiB limit.");
          }
          return;
        }
        if (!rejected) chunks.push(chunk);
      });
      request.on("end", () => {
        if (rejected) return;
        request.proxyBody = Buffer.concat(chunks, bodySize);
        next();
      });
      request.on("error", () => {
        if (!response.headersSent) reject(400, "Invalid request.");
      });
    } else {
      next();
    }
  });
}

export default defineConfig(({ command, mode, isPreview }) => {
  const env = loadEnv(mode, root, "TTS_");
  const proxy =
    command === "serve" || isPreview
      ? apiProxy(
          validateUpstream(env.TTS_UPSTREAM_URL),
          readProxyCredential(env),
          env,
        )
      : undefined;

  return {
    root,
    appType: "mpa",
    build: { cssMinify: false },
    plugins: [
      {
        name: "speech-api-boundary",
        configureServer: (server) => restrictApi(server, env),
        configurePreviewServer: (server) => restrictApi(server, env),
      },
    ],
    server: { host: "127.0.0.1", port: 5173, strictPort: true, proxy },
    preview: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy,
      headers,
    },
  };
});
