import { expect, test } from "@playwright/test";

const speechPath = "/api/v1/audio/speech";
const audio = Buffer.from(
  "UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQIAAAAAAA==",
  "base64",
);

test.beforeEach(async ({ page }) => {
  await page.route("**/api/healthz", (route) => route.fulfill({ json: { status: "ok" } }));
  await page.addInitScript(() => {
    HTMLMediaElement.prototype.play = async function () {};
    const create = URL.createObjectURL.bind(URL);
    const revoke = URL.revokeObjectURL.bind(URL);
    globalThis.audioUrls = { created: [], revoked: [] };
    URL.createObjectURL = (blob) => {
      const url = create(blob);
      globalThis.audioUrls.created.push(url);
      return url;
    };
    URL.revokeObjectURL = (url) => {
      globalThis.audioUrls.revoked.push(url);
      revoke(url);
    };
  });
});

async function open(page) {
  await page.goto("/");
  await expect(page.locator("#service-status")).toHaveText(" SERVICE CONNECTED");
}

async function generate(page, input = "Hello world") {
  await page.getByRole("textbox", { name: "YOUR TEXT" }).fill(input);
  await page.getByRole("button", { name: "Generate speech" }).click();
}

async function mockAudio(page) {
  await page.route(`**${speechPath}`, (route) => route.fulfill({
    contentType: "audio/wav",
    body: audio,
  }));
}

async function clipboard(page, text, reject = false) {
  await page.evaluate(({ text, reject }) => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { readText: async () => {
        if (reject) throw new DOMException("Permission denied", "NotAllowedError");
        return text;
      } },
    });
  }, { text, reject });
}

test("preserves defaults, accessible controls, required input and responsive layout", async ({ page }) => {
  await open(page);
  await expect(page).toHaveTitle("Private Speech Studio");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Give your words a voice.");
  await expect(page.getByRole("textbox", { name: "YOUR TEXT" })).toHaveAttribute("maxlength", "5000");
  await expect(page.getByRole("textbox", { name: "YOUR TEXT" })).toHaveAttribute("required", "");
  await expect(page.getByRole("combobox", { name: "LANGUAGE" })).toHaveValue("");
  await expect(page.getByRole("combobox", { name: "AUDIO FORMAT" })).toHaveValue("mp3");
  await expect(page.getByRole("slider", { name: "SPEAKING SPEED" })).toHaveValue("1");
  await expect(page.locator("#speed-value")).toHaveText("1.0×");
  await expect(page.getByRole("button", { name: "Clear", exact: true })).toBeDisabled();
  await expect(page.locator("#result")).toBeHidden();
  let submitted = false;
  page.on("request", (request) => { if (request.url().endsWith(speechPath)) submitted = true; });
  await page.getByRole("button", { name: "Generate speech" }).click();
  expect(submitted).toBe(false);
  expect(await page.locator("#speech-text").evaluate((element) => element.validity.valueMissing)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("textbox", { name: "YOUR TEXT" }).focus();
  await page.keyboard.type("Keyboard input");
  await expect(page.locator("#character-count")).toHaveText("14 / 5,000");
});

test("enforces the exact text limit and clear restores focus and counter", async ({ page }) => {
  await open(page);
  await page.locator("#speech-text").fill("x".repeat(5001));
  await expect(page.locator("#speech-text")).toHaveValue("x".repeat(5000));
  await expect(page.locator("#character-count")).toHaveText("5,000 / 5,000");
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await expect(page.locator("#speech-text")).toHaveValue("");
  await expect(page.locator("#speech-text")).toBeFocused();
  await expect(page.locator("#character-count")).toHaveText("0 / 5,000");
  await expect(page.getByRole("button", { name: "Clear", exact: true })).toBeDisabled();
});

for (const [name, text, message] of [
  ["normal", "Pasted words", ""],
  ["empty", "", "The clipboard does not contain any text."],
  ["over limit", "x".repeat(5001), "Clipboard text was truncated to the 5,000-character limit."],
  ["UTF-16 limit", "\u{1f600}".repeat(2501), "Clipboard text was truncated to the 5,000-character limit."],
]) {
  test(`clipboard: ${name}`, async ({ page }) => {
    await open(page);
    await clipboard(page, text);
    await page.getByRole("button", { name: "Paste from clipboard" }).click();
    await expect(page.locator("#speech-text")).toHaveValue(text.slice(0, 5000));
    await expect(page.locator("#speech-text")).toBeFocused();
    await expect(page.locator("#status")).toHaveText(message);
    await expect(page.locator("#character-count")).toHaveText(`${Math.min(text.length, 5000).toLocaleString("en-US")} / 5,000`);
  });
}

test("clipboard permission errors are visible and do not lose existing input", async ({ page }) => {
  await open(page);
  await page.locator("#speech-text").fill("Keep this");
  await clipboard(page, "", true);
  await page.getByRole("button", { name: "Paste from clipboard" }).click();
  await expect(page.locator("#status")).toHaveText("Clipboard access is unavailable. Allow clipboard permission and try again.");
  await expect(page.locator("#speech-text")).toHaveValue("Keep this");
});

for (const [language, format, speed] of [
  ["", "mp3", "1"],
  ["de-DE", "wav", "0.5"],
  ["en-US", "mp3", "2"],
  ["en-GB", "wav", "1.3"],
]) {
  test(`generates exact ${language || "auto"} ${format} request at speed ${speed}`, async ({ page }) => {
    await mockAudio(page);
    await open(page);
    await page.locator("#language").selectOption(language);
    await page.locator("#format").selectOption(format);
    await page.locator("#speed").fill(speed);
    await expect(page.locator("#speed-value")).toHaveText(`${Number(speed).toFixed(1)}×`);
    const pendingRequest = page.waitForRequest(`**${speechPath}`);
    await generate(page, "Sample speech");
    const request = await pendingRequest;
    expect(request.method()).toBe("POST");
    expect(request.headers()["content-type"]).toBe("application/json");
    expect(request.postDataJSON()).toEqual({
      input: "Sample speech",
      response_format: format,
      speed: Number(speed),
      ...(language ? { language } : {}),
    });
    await expect(page.getByRole("heading", { name: "Ready to listen." })).toBeVisible();
    await expect(page.locator("#audio-player")).toHaveAttribute("src", /^blob:/);
    await expect(page.locator("#download")).toHaveAttribute("download", `speech.${format}`);
    await expect(page.locator("#download")).toHaveAttribute("href", /^blob:/);
    await expect(page.locator("#status")).toBeEmpty();
    await expect(page.getByRole("button", { name: "Generate speech" })).toBeEnabled();
  });
}

test("shows loading and prevents duplicate submission until completion", async ({ page }) => {
  let release;
  const pending = new Promise((resolve) => { release = resolve; });
  let requests = 0;
  await page.route(`**${speechPath}`, async (route) => {
    requests++;
    await pending;
    await route.fulfill({ contentType: "audio/wav", body: audio });
  });
  await open(page);
  await generate(page);
  await expect(page.getByRole("button", { name: "Generating" })).toBeDisabled();
  expect(requests).toBe(1);
  release();
  await expect(page.getByRole("button", { name: "Generate speech" })).toBeEnabled();
  await expect(page.locator("#result")).toBeVisible();
});

test("revokes old audio when regenerating, clearing and pasting", async ({ page }) => {
  await mockAudio(page);
  await open(page);
  for (const action of ["regenerate", "clear", "paste"]) {
    await generate(page);
    await expect(page.locator("#result")).toBeVisible();
    const url = await page.locator("#download").getAttribute("href");
    if (action === "regenerate") {
      await generate(page, "New speech");
      await expect(page.locator("#download")).not.toHaveAttribute("href", url);
    } else if (action === "clear") {
      await page.getByRole("button", { name: "Clear", exact: true }).click();
      await expect(page.locator("#result")).toBeHidden();
      await expect(page.locator("#audio-player")).not.toHaveAttribute("src");
      await expect(page.locator("#download")).not.toHaveAttribute("href");
    } else {
      await clipboard(page, "Replacement");
      await page.getByRole("button", { name: "Paste from clipboard" }).click();
      await expect(page.locator("#result")).toBeHidden();
    }
    expect(await page.evaluate((url) => globalThis.audioUrls.revoked.includes(url), url)).toBe(true);
  }
});

test("reports blocked autoplay while keeping audio downloadable", async ({ page }) => {
  await mockAudio(page);
  await open(page);
  await page.evaluate(() => {
    HTMLMediaElement.prototype.play = async function () { throw new DOMException("Blocked", "NotAllowedError"); };
  });
  await generate(page);
  await expect(page.locator("#status")).toHaveText("Audio is ready, but your browser blocked automatic playback. Select play to listen.");
  await expect(page.locator("#result")).toBeVisible();
  await expect(page.locator("#service-status")).toHaveAttribute("data-state", "online");
});

for (const scenario of [
  { name: "structured error", status: 422, json: { detail: "Unsupported voice" }, message: "Unsupported voice" },
  { name: "non-string detail", status: 422, json: { detail: [{ message: "invalid" }] }, message: "Speech generation failed (HTTP 422)." },
  { name: "non-JSON error", status: 502, body: "Bad gateway", message: "Speech generation failed (HTTP 502)." },
  { name: "empty audio", status: 200, body: "", message: "The service returned an empty audio file." },
  { name: "network failure", abort: true, message: "Could not reach the speech service. Check the service connection and try again." },
]) {
  test(`handles ${scenario.name} and allows a successful retry`, async ({ page }) => {
    let fail = true;
    await page.route(`**${speechPath}`, async (route) => {
      if (!fail) return route.fulfill({ contentType: "audio/wav", body: audio });
      if (scenario.abort) return route.abort("failed");
      return route.fulfill({
        status: scenario.status,
        ...(scenario.json ? { json: scenario.json } : { body: scenario.body }),
      });
    });
    await open(page);
    await generate(page);
    await expect(page.locator("#status")).toHaveText(scenario.message);
    await expect(page.locator("#service-status")).toHaveAttribute("data-state", "offline");
    await expect(page.locator("#result")).toBeHidden();
    await expect(page.getByRole("button", { name: "Generate speech" })).toBeEnabled();
    fail = false;
    await generate(page);
    await expect(page.locator("#result")).toBeVisible();
    await expect(page.locator("#status")).toBeEmpty();
    await expect(page.locator("#service-status")).toHaveAttribute("data-state", "online");
  });
}

for (const network of [false, true]) {
  test(`reports ${network ? "network" : "HTTP"} health failures`, async ({ page }) => {
    await page.route("**/api/healthz", (route) => network
      ? route.abort("failed")
      : route.fulfill({ status: 503 }));
    await page.goto("/");
    await expect(page.locator("#service-status")).toHaveText(" SERVICE UNAVAILABLE");
    await expect(page.locator("#service-status")).toHaveAttribute("data-state", "offline");
  });
}
