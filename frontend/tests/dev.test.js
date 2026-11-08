import assert from "node:assert/strict";
import { once } from "node:events";
import { createServer as createHttpServer } from "node:http";
import { request as httpRequest } from "node:http";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { createServer } from "vite";

function postChunked(url, path, body, headers = {}) {
  const target = new URL(path, url);
  return new Promise((resolve, reject) => {
    const request = httpRequest(
      target,
      { method: "POST", headers: { "Content-Type": "application/json", ...headers } },
      (response) => {
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () => resolve({
          status: response.statusCode,
          body: Buffer.concat(chunks),
        }));
      },
    );
    request.on("error", reject);
    for (let offset = 0; offset < body.length; offset += 4096) {
      request.write(body.subarray(offset, offset + 4096));
    }
    request.end();
  });
}

test("development serving preserves API paths, method restrictions and static 404s", async () => {
  const requests = [];
  const fixture = createHttpServer(async (request, response) => {
    let body = "";
    for await (const chunk of request) body += chunk;
    requests.push({
      path: request.url,
      method: request.method,
      authorization: request.headers.authorization,
      body,
    });
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({
      path: request.url,
      method: request.method,
      body,
      authorization: request.headers.authorization,
    }));
  });
  fixture.listen(0, "127.0.0.1");
  await once(fixture, "listening");
  const upstream = `http://127.0.0.1:${fixture.address().port}`;
  const previous = {
    TTS_UPSTREAM_URL: process.env.TTS_UPSTREAM_URL,
    TTS_API_KEY: process.env.TTS_API_KEY,
    TTS_API_KEY_FILE: process.env.TTS_API_KEY_FILE,
  };
  const secret = "synthetic-development-secret";
  process.env.TTS_UPSTREAM_URL = upstream;
  process.env.TTS_API_KEY = secret;
  delete process.env.TTS_API_KEY_FILE;
  let server;
  try {
    server = await createServer({
      configFile: fileURLToPath(new URL("../vite.config.js", import.meta.url)),
      mode: "test",
      server: { port: 0 },
    });
    await server.listen();
    const url = `http://127.0.0.1:${server.httpServer.address().port}`;
    const html = await (await fetch(url)).text();
    assert.match(html, /Private Speech Studio/);
    assert.ok(!html.includes(upstream), "Upstream origin must not be injected into the HTML");
    assert.ok(!html.includes(secret), "Backend credentials must not be injected into HTML");
    for (const path of ["/healthz", "/readyz"]) {
      const response = await fetch(`${url}/api${path}?test=1`);
      assert.equal(response.status, 200);
      assert.equal((await response.json()).path, `${path}?test=1`);
      assert.equal(requests.at(-1).authorization, `Bearer ${secret}`);
    }
    const body = JSON.stringify({ input: "Development proxy test", response_format: "mp3", speed: 1 });
    const response = await fetch(`${url}/api/v1/audio/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer attacker-value" },
      body,
    });
    assert.deepEqual(await response.json(), {
      path: "/v1/audio/speech",
      method: "POST",
      body,
      authorization: `Bearer ${secret}`,
    });
    assert.equal((await fetch(`${url}/api/v1/audio/speech`)).status, 403);
    assert.equal((await fetch(`${url}/api/healthz`, { method: "POST" })).status, 403);
    for (const path of ["/missing", "/missing.js", "/api/unknown", "/api/healthz/extra", "/api/readyzextra"]) {
      assert.equal((await fetch(`${url}${path}`)).status, 404, path);
    }

    const payload = Buffer.from('{"input":"ok"}');
    const exact = Buffer.concat([
      Buffer.alloc(32 * 1024 - payload.length, 0x20),
      payload,
    ]);
    assert.equal(exact.length, 32 * 1024);
    const exactResult = await postChunked(url, "/api/v1/audio/speech", exact, {
      Authorization: "Bearer untrusted-client-value",
    });
    assert.equal(exactResult.status, 200);
    assert.equal(requests.at(-1).authorization, `Bearer ${secret}`);
    const forwardedCount = requests.length;
    const oversized = Buffer.concat([exact, Buffer.from(" ")]);
    const oversizedResult = await postChunked(url, "/api/v1/audio/speech", oversized);
    assert.equal(oversizedResult.status, 413);
    assert.equal(requests.length, forwardedCount, "oversized bodies must not reach upstream");
  } finally {
    if (server) await server.close();
    fixture.closeAllConnections();
    await new Promise((resolve, reject) => fixture.close((error) => error ? reject(error) : resolve()));
    for (const [name, value] of Object.entries(previous)) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
});
