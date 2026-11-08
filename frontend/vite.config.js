import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import {
  apiProxy,
  MAX_PROXY_BODY_BYTES,
  readProxyCredential,
  validateUpstream,
} from "./config/upstream.js";

const root = fileURLToPath(new URL(".", import.meta.url));

const headers = {
  "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};

function restrictApi(server) {
  server.middlewares.use((request, response, next) => {
    const path = (request.url || "/").split("?")[0];
    const reject = (status, detail) => {
      response.writeHead(status, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ detail }));
    };
    if (path === "/api/v1/audio/speech" && request.method !== "POST") {
      response.writeHead(403).end("Speech generation requires POST.");
    } else if (
      ["/api/healthz", "/api/readyz"].includes(path)
      && request.method !== "GET"
    ) {
      response.writeHead(403).end("Health routes require GET.");
    } else if (path.startsWith("/api/") && ![
      "/api/healthz", "/api/readyz", "/api/v1/audio/speech",
    ].includes(path)) {
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
  const proxy = command === "serve" || isPreview
    ? apiProxy(
      validateUpstream(env.TTS_UPSTREAM_URL),
      readProxyCredential(env),
    )
    : undefined;

  return {
    root,
    appType: "mpa",
    build: { cssMinify: false },
    plugins: [{
      name: "speech-api-boundary",
      configureServer: restrictApi,
      configurePreviewServer: restrictApi,
    }],
    server: { host: "127.0.0.1", port: 5173, strictPort: true, proxy },
    preview: { host: "127.0.0.1", port: 5173, strictPort: true, proxy, headers },
  };
});
