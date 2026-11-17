import { createReadStream } from "node:fs";
import { existsSync, readFileSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { validateUpstream } from "../config/upstream.js";
import { createApiHandler } from "./api-handler.js";

const root = process.env.STATIC_ROOT || "/usr/share/nginx/html/";
const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
};
const env = process.env;
validateUpstream(env.TTS_UPSTREAM_URL);
const api = createApiHandler(env);
createServer(async (request, response) => {
  response.setHeader("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("Referrer-Policy", "no-referrer");
  response.setHeader("X-Frame-Options", "DENY");
  if (await api(request, response)) return;
  if (request.method !== "GET" && request.method !== "HEAD") {
    return response.writeHead(405, { Allow: "GET, HEAD" }).end();
  }
  const pathname = normalize(new URL(request.url, "http://localhost").pathname);
  const file = pathname === "/" ? join(root, "index.html") : join(root, pathname);
  if (!file.startsWith(root) || !existsSync(file) || !statSync(file).isFile()) return response.writeHead(404).end();
  const extension = file.slice(file.lastIndexOf("."));
  response.writeHead(200, {
    "Content-Type": contentTypes[extension] || "application/octet-stream",
  });
  if (request.method === "HEAD") return response.end();
  createReadStream(file).pipe(response);
}).listen(Number(env.PORT || 8080), "0.0.0.0");
