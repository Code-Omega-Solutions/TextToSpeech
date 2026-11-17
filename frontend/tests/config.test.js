import assert from "node:assert/strict";
import { chmod, mkdtemp, rm, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:http";
import { once } from "node:events";
import { test } from "node:test";
import {
  apiProxy,
  loadApprovedTargets,
  loadConfiguredUpstream,
  readProxyCredential,
  saveConfiguredUpstream,
  validateUpstream,
} from "../config/upstream.js";
import { createApiHandler } from "../runtime/api-handler.js";

test("requires an explicitly configured HTTP(S) origin", () => {
  for (const value of [undefined, ""]) {
    assert.throws(() => validateUpstream(value), /is required/);
  }
  for (const value of [
    "ftp://service",
    "http://service/",
    "http://user:secret@service",
    "http://service/path",
    "http://service?key=value",
    "http://service#fragment",
    "http://service\n",
    "not a URL",
    "http://service:123456",
  ]) {
    assert.throws(() => validateUpstream(value), /must be an HTTP/);
  }
  for (const value of [
    "http://localhost:8000",
    "https://speech.example",
    "http://192.0.2.1:8000",
  ]) {
    assert.equal(validateUpstream(value), value);
  }
});

test("proxies only the three recovered API endpoints, preserving query strings", () => {
  const proxy = apiProxy("http://localhost:8000", "synthetic-proxy-secret");
  const entries = Object.entries(proxy);
  assert.equal(entries.length, 3);
  for (const [path, timeout] of [
    ["/healthz", 10_000],
    ["/readyz", 15_000],
    ["/v1/audio/speech", 75_000],
  ]) {
    const [pattern, options] = entries.find(([pattern]) =>
      new RegExp(pattern).test(`/api${path}`),
    );
    assert.equal(options.target, "http://localhost:8000");
    assert.equal(options.proxyTimeout, timeout);
    assert.equal(
      options.headers.Authorization,
      "Bearer synthetic-proxy-secret",
    );
    assert.deepEqual(options.headers.Connection, "");
    assert.equal(options.rewrite(`/api${path}?test=1`), `${path}?test=1`);
    assert.match(`/api${path}?test=1`, new RegExp(pattern));
    assert.doesNotMatch(`/api${path}/extra`, new RegExp(pattern));
    assert.doesNotMatch(`/api${path}extra`, new RegExp(pattern));
  }
});

test("proxy credentials stay server-side and require one protected source", async () => {
  const path = new URL("./proxy-secret.fixture", import.meta.url);
  const secret = "synthetic-file-secret";
  try {
    await writeFile(path, `${secret}\n`, { mode: 0o600 });
    await chmod(path, 0o600);
    if (process.platform === "win32") {
      assert.throws(
        () => readProxyCredential({ TTS_API_KEY_FILE: path.pathname }),
        /unavailable or not protected/,
        "do not trust POSIX mode bits when Windows ACLs are not verified",
      );
    } else {
      assert.equal(
        readProxyCredential({ TTS_API_KEY_FILE: path.pathname }),
        secret,
      );
    }
    assert.equal(
      readProxyCredential({ TTS_API_KEY: "synthetic-env-secret" }),
      "synthetic-env-secret",
    );
    assert.throws(() => readProxyCredential({}), /TTS_API_KEY/);
    assert.throws(
      () =>
        readProxyCredential({
          TTS_API_KEY: secret,
          TTS_API_KEY_FILE: path.pathname,
        }),
      /only one/,
    );
    if (process.platform !== "win32") {
      await chmod(path, 0o644);
      assert.throws(
        () => readProxyCredential({ TTS_API_KEY_FILE: path.pathname }),
        /protected/,
      );
    }
  } finally {
    await unlink(path).catch(() => {});
  }
});

test("endpoint configuration persists atomically and rejects unsafe origins", async () => {
  const directory = await mkdtemp(join(tmpdir(), "speech-endpoint-"));
  const env = {
    TTS_UPSTREAM_URL: "http://localhost:8000",
    TTS_ENDPOINT_CONFIG_FILE: join(directory, "endpoint.json"),
  };
  try {
    assert.equal(loadConfiguredUpstream(env), env.TTS_UPSTREAM_URL);
    assert.equal(
      saveConfiguredUpstream("https://speech.example", env),
      "https://speech.example",
    );
    assert.equal(loadConfiguredUpstream(env), "https://speech.example");
    assert.throws(
      () => saveConfiguredUpstream("http://user:secret@service", env),
      /must be an HTTP/,
    );
    assert.equal(loadConfiguredUpstream(env), "https://speech.example");
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("browser targets expose opaque approved choices without origins", () => {
  const env = {
    TTS_UPSTREAM_URL: "http://localhost:8000",
    TTS_PROTOTYPE_UPSTREAM_URL: "http://localhost:8001",
    TTS_ALLOWED_UPSTREAMS: "http://localhost:8000,http://localhost:8001",
  };
  assert.deepEqual(Object.keys(loadApprovedTargets(env)), ["production", "prototype"]);
  assert.deepEqual(loadApprovedTargets(env).prototype, {
    label: "Prototype",
    origin: "http://localhost:8001",
  });
  assert.throws(() => loadApprovedTargets({
    ...env,
    TTS_PROTOTYPE_UPSTREAM_URL: "http://attacker.example",
  }), /operator-approved/);
});

test("corrupt and unwritable configuration storage fails without replacing the saved value", async () => {
  const directory = await mkdtemp(join(tmpdir(), "speech-endpoint-failure-"));
  const path = join(directory, "endpoint.json");
  const env = { TTS_UPSTREAM_URL: "http://localhost:8000", TTS_ENDPOINT_CONFIG_FILE: path };
  try {
    await writeFile(path, "{not-json");
    assert.throws(() => loadConfiguredUpstream(env), /corrupt or unreadable/);
    await writeFile(path, JSON.stringify({ origin: "http://localhost:8000" }));
    const blockingDirectory = join(directory, "blocked");
    await writeFile(blockingDirectory, "not-a-directory");
    const blockedEnv = { ...env, TTS_ENDPOINT_CONFIG_FILE: join(blockingDirectory, "endpoint.json") };
    assert.throws(() => saveConfiguredUpstream("http://localhost:8001", blockedEnv), /could not be saved/);
    assert.equal(loadConfiguredUpstream(env), "http://localhost:8000");
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("configuration API enforces operator authorization and destination policy", async () => {
  const directory = await mkdtemp(join(tmpdir(), "speech-api-"));
  const env = {
    TTS_UPSTREAM_URL: "http://localhost:8000",
    TTS_ALLOWED_UPSTREAMS: "http://localhost:8000,http://localhost:8001",
    TTS_API_KEY: "synthetic-backend-token",
    TTS_ENDPOINT_CONFIG_FILE: join(directory, "endpoint.json"),
  };
  const server = createServer((request, response) => createApiHandler(env)(request, response));
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const url = `http://127.0.0.1:${server.address().port}/api/configuration`;
  try {
    assert.equal((await fetch(url)).status, 401);
    assert.equal(
      (await fetch(url, { headers: { Authorization: "Bearer wrong-token" } })).status,
      401,
    );
    const headers = {
      Authorization: "Bearer synthetic-backend-token",
      "Content-Type": "application/json",
    };
    assert.equal((await fetch(url, { headers })).status, 200);
    const denied = await fetch(url, {
      method: "PUT",
      headers,
      body: JSON.stringify({ origin: "http://attacker.example" }),
    });
    assert.equal(denied.status, 403);
    const saved = await fetch(url, {
      method: "PUT",
      headers,
      body: JSON.stringify({ origin: "http://localhost:8001" }),
    });
    assert.deepEqual(await saved.json(), { saved: true });
    assert.deepEqual(await (await fetch(url, { headers })).json(), { configured: true });
    server.close();
    const restarted = createServer((request, response) =>
      createApiHandler(env)(request, response),
    );
    restarted.listen(0, "127.0.0.1");
    await once(restarted, "listening");
    assert.deepEqual(
      await (await fetch(`http://127.0.0.1:${restarted.address().port}/api/configuration`, { headers })).json(),
      { configured: true },
    );
    restarted.close();
  } finally {
    server.close();
    await rm(directory, { recursive: true, force: true });
  }
});

test("persisted configuration routes unselected clients while opaque selections stay isolated", async () => {
  const directory = await mkdtemp(join(tmpdir(), "speech-routing-"));
  const calls = [];
  const upstreams = [];
  const makeUpstream = (name) => {
    const upstream = createServer((request, response) => {
      calls.push(name);
      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ engine: name }));
    });
    upstream.listen(0, "127.0.0.1");
    upstreams.push(upstream);
    return upstream;
  };
  const production = makeUpstream("production");
  const prototype = makeUpstream("prototype");
  await Promise.all(upstreams.map((server) => once(server, "listening")));
  const productionOrigin = `http://127.0.0.1:${production.address().port}`;
  const prototypeOrigin = `http://127.0.0.1:${prototype.address().port}`;
  const env = {
    TTS_UPSTREAM_URL: productionOrigin,
    TTS_ALLOWED_UPSTREAMS: `${productionOrigin},${prototypeOrigin}`,
    TTS_TARGETS_JSON: JSON.stringify({
      production: { label: "Production", origin: productionOrigin },
      prototype: { label: "Prototype", origin: prototypeOrigin },
    }),
    TTS_API_KEY: "synthetic-backend-token",
    TTS_ENDPOINT_CONFIG_FILE: join(directory, "endpoint.json"),
  };
  const startApi = async () => {
    const api = createApiHandler(env);
    const server = createServer((request, response) => api(request, response));
    server.listen(0, "127.0.0.1");
    await once(server, "listening");
    return server;
  };
  const request = (server, path, options = {}) =>
    fetch(`http://127.0.0.1:${server.address().port}${path}`, options);
  const authHeaders = {
    Authorization: "Bearer synthetic-backend-token",
    "Content-Type": "application/json",
  };
  let server;
  try {
    server = await startApi();
    assert.deepEqual(await (await request(server, "/api/healthz")).json(), { engine: "production" });
    const selection = await request(server, "/api/target", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: "prototype" }),
    });
    assert.equal(selection.status, 204);
    const sessionCookie = selection.headers.get("set-cookie").split(";", 1)[0];
    const selected = await request(server, "/api/healthz", { headers: { Cookie: sessionCookie } });
    assert.deepEqual(await selected.json(), { engine: "prototype" });
    assert.equal((await request(server, "/api/configuration", {
      method: "PUT",
      headers: authHeaders,
      body: JSON.stringify({ origin: prototypeOrigin }),
    })).status, 200);
    assert.equal(loadConfiguredUpstream(env), prototypeOrigin);
    assert.deepEqual(await (await request(server, "/api/healthz")).json(), { engine: "prototype" });
    assert.deepEqual(await (await request(server, "/api/healthz", {
      headers: { Cookie: "tts_target=unknown-session" },
    })).json(), { engine: "prototype" });
    assert.equal((await request(server, "/api/configuration", {
      method: "PUT",
      headers: { Authorization: "Bearer wrong-token", "Content-Type": "application/json" },
      body: JSON.stringify({ origin: productionOrigin }),
    })).status, 401);
    assert.equal((await request(server, "/api/configuration", {
      method: "PUT",
      headers: authHeaders,
      body: JSON.stringify({ origin: "http://attacker.example" }),
    })).status, 403);
    server.close();
    server = await startApi();
    assert.deepEqual(await (await request(server, "/api/healthz")).json(), { engine: "prototype" });
    assert.deepEqual(calls, ["production", "prototype", "prototype", "prototype", "prototype"]);
  } finally {
    server?.close();
    await Promise.all(upstreams.map((upstream) => new Promise((resolve) => upstream.close(resolve))));
    await rm(directory, { recursive: true, force: true });
  }
});
