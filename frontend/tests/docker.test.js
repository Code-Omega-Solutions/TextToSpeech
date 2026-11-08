import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { chmod, unlink, writeFile } from "node:fs/promises";
import { once } from "node:events";
import { createServer, request as httpRequest } from "node:http";
import { fileURLToPath } from "node:url";
import { setTimeout } from "node:timers/promises";
import { test } from "node:test";

const root = fileURLToPath(new URL("../..", import.meta.url));
const image = "private-speech-studio-frontend:local";
const port = 8081;
const audio = Buffer.from([82, 73, 70, 70, 0, 1, 255, 128]);
const secret = "synthetic-container-secret";
const secretPath = fileURLToPath(new URL("./proxy-secret.fixture", import.meta.url));
const dockerAvailable = spawnSync("docker", ["--version"], { encoding: "utf8" }).status === 0;

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

test("restored Docker image preserves the static and API contract", {
  timeout: 240_000,
  skip: !dockerAvailable && "Docker is unavailable",
}, async (t) => {
  docker(
    "build",
    "-f", "frontend/Dockerfile",
    "--build-arg", "OCI_REVISION=test-revision",
    "--build-arg", "OCI_VERSION=test-version",
    "-t", image,
    ".",
  );
  const noticesDir = "/usr/share/doc/texttospeech-frontend";
  await t.test("image contains licenses, source offer and traceable metadata", () => {
    const labels = JSON.parse(docker("image", "inspect", "--format", "{{json .Config.Labels}}", image));
    assert.equal(labels["org.opencontainers.image.source"], "https://github.com/Code-Omega-Solutions/TextToSpeech");
    assert.equal(labels["org.opencontainers.image.revision"], "test-revision");
    assert.equal(labels["org.opencontainers.image.version"], "test-version");
    assert.equal(
      labels["org.opencontainers.image.documentation"],
      "https://github.com/Code-Omega-Solutions/TextToSpeech/blob/test-revision/THIRD_PARTY_NOTICES.md",
    );
    assert.match(labels["com.code-omega-solutions.license-scope"], /^Mixed;/);
    assert.equal(labels["com.code-omega-solutions.third-party-notices"], `${noticesDir}/THIRD_PARTY_NOTICES.md`);

    const packageCount = Number(docker(
      "run", "--rm", "--entrypoint", "/bin/sh", image,
      "-c", `set -eu; test -s ${noticesDir}/LICENSE; test -s ${noticesDir}/NOTICE; test -s ${noticesDir}/THIRD_PARTY_NOTICES.md; test -s ${noticesDir}/SOURCE_OFFER.md; test -s ${noticesDir}/RUNTIME-PACKAGES.txt; for package in $(dpkg-query -W | cut -f1); do package=\${package%%:*}; test -s /usr/share/doc/$package/copyright; done; wc -l < ${noticesDir}/RUNTIME-PACKAGES.txt`,
    ));
    assert.ok(packageCount >= 100, `Expected Debian runtime package inventory, got ${packageCount}`);
    const offer = docker("run", "--rm", "--entrypoint", "cat", image, `${noticesDir}/SOURCE_OFFER.md`);
    assert.match(offer, /patrik\.gfeller@code-omega\.ch/);
    assert.match(offer, /at least three years/);
  });

  const requests = [];
  const fixture = createServer(async (request, response) => {
    let body = "";
    for await (const chunk of request) body += chunk;
    requests.push({
      method: request.method,
      url: request.url,
      body,
      authorization: request.headers.authorization,
    });
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
    await writeFile(secretPath, `${secret}\n`, { mode: 0o400 });
    await chmod(secretPath, 0o400);
    container = docker(
      "create",
      "--name", `speech-frontend-verification-${process.pid}`,
      "--add-host", "host.docker.internal:host-gateway",
      "--publish", `127.0.0.1:${port}:8080`,
      "--env", `TTS_UPSTREAM_URL=http://host.docker.internal:${upstreamPort}`,
      "--env", "TTS_API_KEY_FILE=/run/secrets/tts_api_key",
      "--mount", `type=bind,src=${secretPath},dst=/run/secrets/tts_api_key,readonly`,
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
      assert.ok(!html.includes(secret));
      assert.equal(response.headers.get("x-content-type-options"), "nosniff");
      assert.equal(response.headers.get("x-frame-options"), "DENY");
      assert.equal(response.headers.get("referrer-policy"), "no-referrer");
      assert.match(response.headers.get("content-security-policy"), /media-src 'self' blob:/);
      const assets = [...html.matchAll(/(?:src|href)="([^"]+\.(?:js|css|svg))"/g)].map((match) => match[1]);
      assert.equal(assets.length, 3);
      for (const asset of assets) {
        const assetResponse = await fetch(`${url}${asset}`);
        assert.equal(assetResponse.status, 200, asset);
        assert.ok(!(await assetResponse.text()).includes(secret), `secret leaked in ${asset}`);
      }
      assert.equal(docker("exec", container, "stat", "-c", "%a", "/etc/nginx/conf.d/default.conf"), "600");
      assert.equal(docker("exec", container, "sh", "-c",
        "test -r /run/secrets/tts_api_key && ! (echo x >> /run/secrets/tts_api_key)"), "");
      assert.ok(!docker("logs", container).includes(secret), "secret must not appear in logs");
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
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer attacker-supplied-value",
        },
        body: JSON.stringify(payload),
      });
      assert.equal(response.status, 200);
      assert.equal(response.headers.get("content-type"), "audio/wav");
      assert.deepEqual(Buffer.from(await response.arrayBuffer()), audio);
      const forwarded = requests.at(-1);
      assert.equal(forwarded.method, "POST");
      assert.equal(forwarded.authorization, `Bearer ${secret}`);
      assert.deepEqual(JSON.parse(forwarded.body), payload);
      assert.deepEqual(requests.map((request) => request.url), ["/healthz", "/readyz", "/v1/audio/speech"]);
    });

    await t.test("method restriction and exact streamed 32 KiB body limit", async () => {
      const count = requests.length;
      assert.equal((await fetch(`${url}/api/v1/audio/speech`)).status, 403);
      const payload = Buffer.from('{"input":"ok"}');
      const exact = Buffer.concat([Buffer.alloc(32 * 1024 - payload.length, 0x20), payload]);
      assert.equal(exact.length, 32 * 1024);
      const exactResponse = await postChunked(url, "/api/v1/audio/speech", exact, {
        Authorization: "Bearer client-value-must-be-replaced",
      });
      assert.equal(exactResponse.status, 200);
      assert.equal(requests.at(-1).authorization, `Bearer ${secret}`);
      const acceptedCount = requests.length;
      const oversized = await postChunked(
        url,
        "/api/v1/audio/speech",
        Buffer.concat([exact, Buffer.from(" ")]),
      );
      assert.equal(oversized.status, 413);
      assert.equal(requests.length, acceptedCount);
      assert.equal(requests.length, count + 1);
    });

    await t.test("startup rejects missing or invalid upstream configuration", () => {
      const missingCredential = spawnSync("docker", [
        "run", "--rm",
        "--env", "TTS_UPSTREAM_URL=http://speech.example",
        "--env", "TTS_API_KEY_FILE=/run/secrets/missing",
        image,
      ], { encoding: "utf8", timeout: 30_000 });
      assert.ifError(missingCredential.error);
      assert.equal(missingCredential.status, 1);
      assert.match(missingCredential.stderr, /readable regular TTS_API_KEY_FILE/);

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
    await unlink(secretPath).catch(() => {});
    fixture.closeAllConnections();
    await new Promise((resolve, reject) => fixture.close((error) => error ? reject(error) : resolve()));
  }
});
