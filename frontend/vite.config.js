import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import { apiProxy, validateUpstream } from "./config/upstream.js";

const root = fileURLToPath(new URL(".", import.meta.url));

const headers = {
  "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};

function restrictApi(server) {
  server.middlewares.use((request, response, next) => {
    const path = request.url.split("?")[0];
    if (path === "/api/v1/audio/speech" && request.method !== "POST") {
      response.writeHead(403).end("Speech generation requires POST.");
    } else if (path.startsWith("/api/") && ![
      "/api/healthz", "/api/readyz", "/api/v1/audio/speech",
    ].includes(path)) {
      response.writeHead(404).end("Unknown API endpoint.");
    } else {
      next();
    }
  });
}

export default defineConfig(({ command, mode, isPreview }) => {
  const env = loadEnv(mode, root, "TTS_");
  const proxy = command === "serve" || isPreview
    ? apiProxy(validateUpstream(env.TTS_UPSTREAM_URL))
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
