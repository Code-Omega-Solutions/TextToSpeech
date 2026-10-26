import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { once } from "node:events";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { setTimeout } from "node:timers/promises";
import { test } from "node:test";

const root = fileURLToPath(new URL("..", import.meta.url));
const image = "private-speech-studio-frontend:local";
const port = 8081;
const audio = Buffer.from([82, 73, 70, 70, 0, 1, 255, 128]);

function docker(...args) {
  return execFileSync("docker", args, {
    cwd: root,
    encoding: "utf8",
    timeout: 180_000,
    maxBuffer: 10 * 1024 * 1024,
  }).trim();
}

async function waitForFrontend(url) {
  let lastError;
  for (let attempt = 0; attempt < 50; attempt++) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (response.ok) return;
      lastError = new Error(`Frontend returned HTTP ${response.status}`);
    } catch (error) {
      if (!(error instanceof TypeError) && error.name !== "TimeoutError") throw error;
      lastError = error;
    }
    await setTimeout(200);
  }
  throw new Error("Isolated frontend did not become responsive.", { cause: lastError });
}

test("restored Docker image preserves the static and API contract", { timeout: 240_000 }, async (t) => {
  docker("build", "-t", image, ".");
  const requests = [];
  const fixture = createServer(async (request, response) => {
    let body = "";
    for await (const chunk of request) body += chunk;
    requests.push({ method: request.method, url: request.url, body });
    const speech = request.url === "/v1/audio/speech";
    response.writeHead(200, {
      "Content-Type": speech ? "audio/wav" : "application/json",
      "X-Test-Upstream": "fixture",
    });
    response.end(speech ? audio : JSON.stringify({ path: request.url, method: request.method, body }));
  });
  fixture.listen(0, "0.0.0.0");
  await once(fixture, "listening");
  const upstreamPort = fixture.address().port;
  let container;
  try {
    container = docker(
      "create",
      "--name", `speech-frontend-verification-${process.pid}`,
      "--add-host", "host.docker.internal:host-gateway",
      "--publish", `127.0.0.1:${port}:8080`,
      "--env", `TTS_UPSTREAM_URL=http://host.docker.internal:${upstreamPort}`,
      image,
    );
    docker("start", container);
    const url = `http://127.0.0.1:${port}`;
    await waitForFrontend(url);
    console.log(`Verified isolated frontend responsive at ${url}`);

    await t.test("Nginx configuration and hardened static serving", async () => {
      docker("exec", container, "nginx", "-t");
      const response = await fetch(url);
      const html = await response.text();
      assert.match(html, /Private Speech Studio/);
      assert.equal(response.headers.get("x-content-type-options"), "nosniff");
      assert.equal(response.headers.get("x-frame-options"), "DENY");
      assert.equal(response.headers.get("referrer-policy"), "no-referrer");
      assert.match(response.headers.get("content-security-policy"), /media-src 'self' blob:/);
      const assets = [...html.matchAll(/(?:src|href)="([^"]+\.(?:js|css|svg))"/g)].map((match) => match[1]);
      assert.equal(assets.length, 3);
      for (const asset of assets) {
        assert.equal((await fetch(`${url}${asset}`)).status, 200, asset);
      }
      for (const path of ["/missing", "/missing.js", "/api/not-allowed", "/.env", "/app.js"]) {
        const missing = await fetch(`${url}${path}`);
        assert.equal(missing.status, 404, path);
        assert.equal(missing.headers.get("x-frame-options"), "DENY");
      }
    });

    await t.test("health, readiness and speech use exact upstream paths", async () => {
      for (const path of ["/healthz", "/readyz"]) {
        const response = await fetch(`${url}/api${path}`);
        assert.equal(response.status, 200);
        assert.equal(response.headers.get("x-test-upstream"), "fixture");
        assert.equal((await response.json()).path, path);
      }
      const payload = { input: "Frontend proxy test", response_format: "wav", speed: 1.3, language: "de-DE" };
      const response = await fetch(`${url}/api/v1/audio/speech`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      assert.equal(response.status, 200);
      assert.equal(response.headers.get("content-type"), "audio/wav");
      assert.deepEqual(Buffer.from(await response.arrayBuffer()), audio);
      const forwarded = requests.at(-1);
      assert.equal(forwarded.method, "POST");
      assert.deepEqual(JSON.parse(forwarded.body), payload);
      assert.deepEqual(requests.map((request) => request.url), ["/healthz", "/readyz", "/v1/audio/speech"]);
    });

    await t.test("method restriction and original 16k body limit", async () => {
      const count = requests.length;
      assert.equal((await fetch(`${url}/api/v1/audio/speech`)).status, 403);
      assert.equal((await fetch(`${url}/api/v1/audio/speech`, {
        method: "POST",
        body: "x".repeat(16 * 1024 + 1),
      })).status, 413);
      assert.equal(requests.length, count);
    });

    await t.test("startup rejects missing or invalid upstream configuration", () => {
      for (const upstream of [
        undefined, "ftp://service", "http://user:secret@service",
        "http://service/path", "http://service/", "http://service?key=value", "http://service#fragment",
      ]) {
        const args = ["run", "--rm", ...(upstream ? ["--env", `TTS_UPSTREAM_URL=${upstream}`] : []), image];
        const result = spawnSync("docker", args, { encoding: "utf8", timeout: 30_000 });
        assert.ifError(result.error);
        assert.equal(result.status, 1);
        assert.match(result.stderr, /TTS_UPSTREAM_URL (is required|must be an HTTP)/);
      }
    });
  } finally {
    if (container) docker("rm", "--force", container);
    fixture.closeAllConnections();
    await new Promise((resolve, reject) => fixture.close((error) => error ? reject(error) : resolve()));
  }
});
