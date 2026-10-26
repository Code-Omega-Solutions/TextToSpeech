import assert from "node:assert/strict";
import { once } from "node:events";
import { createServer as createHttpServer } from "node:http";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { createServer } from "vite";

test("development serving preserves API paths, method restrictions and static 404s", async () => {
  const fixture = createHttpServer(async (request, response) => {
    let body = "";
    for await (const chunk of request) body += chunk;
    response.writeHead(200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ path: request.url, method: request.method, body }));
  });
  fixture.listen(0, "127.0.0.1");
  await once(fixture, "listening");
  const upstream = `http://127.0.0.1:${fixture.address().port}`;
  const previous = process.env.TTS_UPSTREAM_URL;
  process.env.TTS_UPSTREAM_URL = upstream;
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
    for (const path of ["/healthz", "/readyz"]) {
      const response = await fetch(`${url}/api${path}?test=1`);
      assert.equal(response.status, 200);
      assert.equal((await response.json()).path, `${path}?test=1`);
    }
    const body = JSON.stringify({ input: "Development proxy test", response_format: "mp3", speed: 1 });
    const response = await fetch(`${url}/api/v1/audio/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    assert.deepEqual(await response.json(), { path: "/v1/audio/speech", method: "POST", body });
    assert.equal((await fetch(`${url}/api/v1/audio/speech`)).status, 403);
    for (const path of ["/missing", "/missing.js", "/api/unknown", "/api/healthz/extra", "/api/readyzextra"]) {
      assert.equal((await fetch(`${url}${path}`)).status, 404, path);
    }
  } finally {
    if (server) await server.close();
    fixture.closeAllConnections();
    await new Promise((resolve, reject) => fixture.close((error) => error ? reject(error) : resolve()));
    if (previous === undefined) delete process.env.TTS_UPSTREAM_URL;
    else process.env.TTS_UPSTREAM_URL = previous;
  }
});
