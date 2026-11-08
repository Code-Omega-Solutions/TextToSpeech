import assert from "node:assert/strict";
import { chmod, unlink, writeFile } from "node:fs/promises";
import { test } from "node:test";
import { apiProxy, readProxyCredential, validateUpstream } from "../config/upstream.js";

test("requires an explicitly configured HTTP(S) origin", () => {
  for (const value of [undefined, ""]) {
    assert.throws(() => validateUpstream(value), /is required/);
  }
  for (const value of [
    "ftp://service", "http://service/", "http://user:secret@service",
    "http://service/path", "http://service?key=value", "http://service#fragment",
    "http://service\n", "not a URL", "http://service:123456",
  ]) {
    assert.throws(() => validateUpstream(value), /must be an HTTP/);
  }
  for (const value of ["http://localhost:8000", "https://speech.example", "http://192.0.2.1:8000"]) {
    assert.equal(validateUpstream(value), value);
  }
});

test("proxies only the three recovered API endpoints, preserving query strings", () => {
  const proxy = apiProxy("http://localhost:8000", "synthetic-proxy-secret");
  const entries = Object.entries(proxy);
  assert.equal(entries.length, 3);
  for (const [path, timeout] of [
    ["/healthz", 10_000], ["/readyz", 15_000], ["/v1/audio/speech", 75_000],
  ]) {
    const [pattern, options] = entries.find(([pattern]) => new RegExp(pattern).test(`/api${path}`));
    assert.equal(options.target, "http://localhost:8000");
    assert.equal(options.proxyTimeout, timeout);
    assert.equal(options.headers.Authorization, "Bearer synthetic-proxy-secret");
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
    assert.equal(readProxyCredential({ TTS_API_KEY_FILE: path.pathname }), secret);
    assert.equal(readProxyCredential({ TTS_API_KEY: "synthetic-env-secret" }), "synthetic-env-secret");
    assert.throws(() => readProxyCredential({}), /TTS_API_KEY/);
    assert.throws(
      () => readProxyCredential({ TTS_API_KEY: secret, TTS_API_KEY_FILE: path.pathname }),
      /only one/,
    );
    await chmod(path, 0o644);
    assert.throws(() => readProxyCredential({ TTS_API_KEY_FILE: path.pathname }), /protected/);
  } finally {
    await unlink(path).catch(() => {});
  }
});
