import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { chmod, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { once } from "node:events";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { test } from "node:test";
import { chromium, expect } from "@playwright/test";

const root = fileURLToPath(new URL("../..", import.meta.url));
const image = "private-speech-studio-frontend:local";
const port = 8082;
const name = `speech-production-${process.pid}`;
const volume = `speech-production-volume-${process.pid}`;
const dockerAvailable = spawnSync("docker", ["--version"]).status === 0;
const audio = Buffer.from("RIFF-production-audio");

function docker(...args) {
  return execFileSync("docker", args, {
    cwd: root,
    encoding: "utf8",
    timeout: 180_000,
    maxBuffer: 10 * 1024 * 1024,
  }).trim();
}

async function waitFor(url) {
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (response.ok) return;
    } catch {}
    await delay(200);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function service(name, options = {}) {
  const requests = [];
  const server = createServer(async (request, response) => {
    requests.push(request.url);
    if (request.url === "/healthz" && options.delayHealth) await delay(options.delayHealth);
    if (request.url === "/v1/audio/speech" && options.delaySpeech) await delay(options.delaySpeech);
    if (request.url === "/v1/audio/engines") {
      response.writeHead(200, { "Content-Type": "application/json" });
      response.end(JSON.stringify({
        engines: [{ id: `engine-${name}`, available: true, languages: ["en-US"], voices: { "en-US": [`voice-${name}`] } }],
      }));
      return;
    }
    if (request.url === "/v1/audio/speech") {
      for await (const _chunk of request) {}
      response.writeHead(200, { "Content-Type": "audio/wav" });
      response.end(Buffer.concat([audio, Buffer.from(name)]));
      return;
    }
    response.writeHead(options.healthStatus || 200, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ status: options.healthStatus === 200 ? "ok" : "failed", service: name }));
  });
  return { server, requests };
}

test("production container switches real services, isolates late work, and retains volume settings", {
  timeout: 300_000,
  skip: !dockerAvailable && "Docker is unavailable",
}, async (t) => {
  docker("build", "-f", "frontend/Dockerfile", "-t", image, ".");
  const a = service("a", { delayHealth: 1800, delaySpeech: 2200, healthStatus: 503 });
  const b = service("b");
  a.server.listen(0, "0.0.0.0");
  b.server.listen(0, "0.0.0.0");
  await Promise.all([once(a.server, "listening"), once(b.server, "listening")]);
  const aOrigin = `http://host.docker.internal:${a.server.address().port}`;
  const bOrigin = `http://host.docker.internal:${b.server.address().port}`;
  let container;
  let browser;
  t.after(async () => { await browser?.close(); });
  const secretDir = await mkdtemp(join(tmpdir(), "speech-production-"));
  const secretPath = join(secretDir, "proxy-secret");
  try {
    await writeFile(secretPath, "synthetic-production-secret\n", { mode: 0o400 });
    await chmod(secretPath, 0o400);
    docker("volume", "create", volume);
    const create = () => docker(
      "create", "--name", name, "--add-host", "host.docker.internal:host-gateway",
      "--publish", `127.0.0.1:${port}:8080`,
      "--env", `TTS_UPSTREAM_URL=${aOrigin}`,
      "--env", `TTS_ALLOWED_UPSTREAMS=${aOrigin},${bOrigin}`,
      "--env", "TTS_OPERATOR_TOKEN=synthetic-operator-token",
      "--env", "TTS_API_KEY_FILE=/run/secrets/tts_api_key",
      "--mount", `type=bind,src=${secretPath},dst=/run/secrets/tts_api_key,readonly`,
      "--mount", `type=volume,src=${volume},dst=/var/lib/private-speech-studio`,
      image,
    );
    container = create();
    docker("start", container);
    const url = `http://127.0.0.1:${port}`;
    await waitFor(url);
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(url);
    await page.getByRole("button", { name: "Configuration" }).click();
    await page.locator("#operator-token").fill("synthetic-operator-token");
    const configurationResponse = page.waitForResponse((response) =>
      response.url() === `${url}/api/configuration` &&
      response.request().method() === "GET" &&
      response.status() === 200
    );
    await page.locator("#operator-token").press("Tab");
    await configurationResponse;
    await expect(page.locator("#endpoint-input")).toHaveValue(aOrigin);
    await page.locator("#endpoint-input").focus();
    await page.keyboard.press("Control+A");
    await page.keyboard.type(aOrigin);
    await page.locator("#endpoint-input").press("Tab");
    await expect(page.locator("#endpoint-input")).toHaveValue(aOrigin);
    await page.getByRole("button", { name: "Speech" }).click();
    await expectText(page, "#discovery-status", "Speech options are ready.");

    await page.locator("#speech-text").fill("old speech");
    await page.getByRole("button", { name: "Generate speech" }).click();
    await page.getByRole("button", { name: "Configuration" }).click();
    await page.locator("#endpoint-input").focus();
    await page.keyboard.press("Control+A");
    await page.keyboard.type(bOrigin);
    await expect(page.locator("#unsaved-endpoint")).toBeVisible();
    await expect(page.getByRole("button", { name: "Save endpoint" })).toBeEnabled();
    await page.getByRole("button", { name: "Save endpoint" }).focus();
    await page.keyboard.press("Enter");
    await expectText(page, "#configuration-status", "Endpoint saved.");
    await expect(page.locator("#unsaved-endpoint")).toBeHidden();
    await expect(page.getByRole("button", { name: "Save endpoint" })).toBeDisabled();
    await page.getByRole("button", { name: "Speech" }).click();
    await expectText(page, "#discovery-status", "Speech options are ready.");
    await delay(2600);
    await expect(page.locator("#service-status")).toHaveText(" SERVICE CONNECTED");
    await expect(page.locator("#result")).toBeHidden();
    await waitForEnabled(page.locator("#generate"));
    await page.locator("#speech-text").fill("new speech");
    await page.getByRole("button", { name: "Generate speech" }).click();
    await expect.poll(() => b.requests.filter((request) => request === "/v1/audio/speech").length).toBeGreaterThan(0);
    await expect(page.locator("#result")).toBeVisible();
    await expect(page.locator("#result")).toContainText("Ready to listen.");
    assert.ok(a.requests.includes("/v1/audio/speech"));
    assert.ok(b.requests.includes("/v1/audio/speech"));
    await browser.close();
    browser = undefined;

    docker("rm", "-f", container);
    container = create();
    docker("start", container);
    await waitFor(url);
    browser = await chromium.launch({ headless: true });
    const freshContext = await browser.newContext();
    const freshPage = await freshContext.newPage();
    await freshPage.goto(url);
    await freshPage.getByRole("button", { name: "Configuration" }).click();
    await freshPage.locator("#operator-token").fill("synthetic-operator-token");
    await freshPage.locator("#operator-token").press("Tab");
    await expect(freshPage.locator("#active-endpoint")).toHaveText(`Active endpoint: ${bOrigin}`);
    await freshPage.getByRole("button", { name: "Speech" }).click();
    await expectText(freshPage, "#discovery-status", "Speech options are ready.");
    await freshPage.locator("#speech-text").fill("persisted routing");
    await freshPage.getByRole("button", { name: "Generate speech" }).click();
    await expect.poll(() => b.requests.filter((request) => request === "/v1/audio/speech").length).toBeGreaterThan(1);
    await expect(freshPage.locator("#result")).toBeVisible();
    await freshContext.close();
    const persisted = await fetch(`${url}/api/configuration`, {
      headers: { Authorization: "Bearer synthetic-operator-token" },
    });
    assert.deepEqual(await persisted.json(), { origin: bOrigin });
    assert.equal(
      docker("run", "--rm", "--volumes-from", container, "--entrypoint", "stat", image, "-c", "%a", "/var/lib/private-speech-studio/endpoint.json"),
      "600",
    );
  } finally {
    if (container) docker("rm", "-f", container);
    docker("volume", "rm", "-f", volume);
    a.server.close();
    b.server.close();
    a.server.closeAllConnections?.();
    b.server.closeAllConnections?.();
    await rm(secretDir, { recursive: true, force: true });
  }
});

async function expectText(page, selector, text) {
  for (let attempt = 0; attempt < 60; attempt++) {
    if ((await page.locator(selector).textContent()).includes(text)) return;
    await delay(100);
  }

  assert.fail(`Timed out waiting for ${selector} to contain ${text}`);
}

async function waitForEnabled(locator) {
  for (let attempt = 0; attempt < 60; attempt++) {
    if (await locator.isEnabled()) return;
    await delay(100);
  }
  assert.fail("Timed out waiting for the speech button to be enabled");
}
