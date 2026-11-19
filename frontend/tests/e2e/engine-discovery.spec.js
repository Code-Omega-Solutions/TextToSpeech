import { expect, test } from "@playwright/test";

const catalogPath = "/api/v1/audio/engines";
const speechPath = "/api/v1/audio/speech";
const audio = Buffer.from(
  "UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQIAAAAAAA==",
  "base64",
);

const catalog = {
  engines: [
    {
      id: "macos-say",
      available: true,
      languages: ["de-DE", "en-US", "en-GB"],
      voices: {
        "de-DE": ["de-macos"],
        "en-US": ["en-us-macos"],
        "en-GB": ["en-gb-macos"],
      },
    },
    {
      id: "fish-speech",
      available: true,
      languages: ["de-DE", "en-US"],
      voices: {
        "de-DE": ["de-female", "de-male"],
        "en-US": ["en-female", "en-male"],
      },
    },
    {
      id: "unavailable-engine",
      available: false,
      languages: ["de-DE"],
      voices: { "de-DE": ["hidden-voice"] },
    },
  ],
};

async function open(page, catalogResponse = { json: catalog }) {
  await page.route("**/api/healthz", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.route(`**${catalogPath}`, (route) =>
    route.fulfill(typeof catalogResponse === "function" ? catalogResponse() : catalogResponse),
  );
  await page.addInitScript(() => {
    HTMLMediaElement.prototype.play = async function () {};
  });
  await page.goto("/");
  await expect(page.locator("#service-status")).toHaveText(
    " SERVICE CONNECTED",
  );
}

test("populates only available engines and filters choices by language", async ({
  page,
}) => {
  await open(page);
  const engine = page.getByRole("combobox", { name: "SPEECH ENGINE" });
  const voice = page.getByRole("combobox", { name: "VOICE" });

  expect(
    await engine
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
  ).toEqual(["macos-say", "fish-speech"]);
  await expect(engine).toHaveValue("macos-say");
  expect(
    await voice
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
  ).toEqual([""]);

  await page.locator("#language").selectOption("en-GB");
  expect(
    await engine
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
  ).toEqual(["macos-say"]);
  expect(
    await voice
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
  ).toEqual(["", "en-gb-macos"]);

  await page.locator("#language").selectOption("de-DE");
  expect(
    await engine
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
  ).toEqual(["macos-say", "fish-speech"]);
  await engine.selectOption("fish-speech");
  expect(
    await voice
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.value)),
  ).toEqual(["", "de-female", "de-male"]);
  expect(
    await voice
      .locator("option")
      .evaluateAll((options) => options.map((option) => option.textContent)),
  ).toEqual(["Engine default", "Female (German)", "Male (German)"]);
  await expect(page.locator("#discovery-status")).toHaveText(
    "Speech options are ready.",
  );
});

test("selects the advertised Fish runtime on the approved service", async ({ page }) => {
  let runtime = "pytorch";
  await page.route("**/api/targets", (route) =>
    route.fulfill({
      json: {
        targets: [{ id: "pytorch-service", label: "PyTorch" }, { id: "mlx-service", label: "MLX" }],
        selected: "pytorch-service",
      },
    }),
  );
  await page.route("**/api/target", (route) => {
    expect(route.request().postDataJSON()).toEqual({ id: "mlx-service" });
    runtime = "mlx4";
    return route.fulfill({ json: { selected: "mlx-service" } });
  });
  await page.route(`**${speechPath}`, (route) => {
    expect(route.request().postDataJSON()).toEqual({
      input: "Guten Morgen",
      response_format: "mp3",
      speed: 1,
      model: "fish-speech",
      fish_runtime: "mlx4",
    });
    return route.fulfill({
      contentType: "audio/wav",
      headers: {
        "X-Speech-Backend": "macos-say",
        "X-Speech-Fallback": "true",
        "X-Speech-Fallback-Reason": "fish_busy",
      },
      body: audio,
    });
  });
  await open(page, () => ({
    json: {
      engines: catalog.engines.map((engine) =>
        engine.id === "fish-speech" ? { ...engine, fish_runtime: runtime } : engine),
    },
  }));
  const engine = page.locator("#engine");
  await expect(engine.locator("option", { hasText: "Fish Speech (PyTorch)" })).toHaveCount(1);
  await expect(engine.locator("option", { hasText: "Fish Speech (MLX)" })).toHaveCount(0);
  await page.getByRole("button", { name: "Configuration" }).click();
  await page.locator("#target").selectOption("mlx-service");
  await page.getByRole("button", { name: "Speech", exact: true }).click();
  await expect(engine).toHaveValue("macos-say");
  await expect(engine.locator("option", { hasText: "Fish Speech (MLX)" })).toHaveCount(1);
  await engine.selectOption({ label: "Fish Speech (MLX)" });
  await page.getByRole("textbox", { name: "YOUR TEXT" }).fill("Guten Morgen");
  await page.getByRole("button", { name: "Generate speech" }).click();
  await expect(page.locator("#speech-engine-disclosure")).toHaveText(
    "Actual engine: macos-say. Fallback used (fish_busy).",
  );
});

test("discovery failure displays a safe status and prevents submission", async ({
  page,
}) => {
  await open(page, {
    status: 503,
    json: { detail: "private upstream failure" },
  });
  await expect(page.locator("#discovery-status")).toHaveText(
    "Speech options are unavailable. Check the service connection and try again.",
  );
  await expect(
    page.getByRole("button", { name: "Generate speech" }),
  ).toBeDisabled();
  await expect(page.locator("#discovery-status")).not.toContainText(
    "private upstream failure",
  );
});

test("discovery authorization failure is distinct from an unavailable service", async ({
  page,
}) => {
  await open(page, { status: 401, json: { detail: "private auth failure" } });
  await expect(page.locator("#discovery-status")).toHaveText(
    "Discovery authorization failed.",
  );
});

test("discovery connectivity failure is distinct from an HTTP failure", async ({
  page,
}) => {
  await page.route(`**${catalogPath}`, (route) => route.abort("failed"));
  await page.route("**/api/healthz", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.goto("/");
  await expect(page.locator("#discovery-status")).toHaveText(
    "Could not reach the speech service. Check the service connection and try again.",
  );
});

test("configuration does not collect backend credentials in the browser", async ({
  page,
}) => {
  await open(page);
  await page.getByRole("button", { name: "Configuration" }).click();
  await expect(page.locator("#operator-token")).toHaveCount(0);
  await expect(page.locator("#configuration-status")).toContainText(
    "Browser users do not enter or receive backend credentials.",
  );
});

test("an empty available catalog explains why submission is disabled", async ({
  page,
}) => {
  await open(page, { json: { engines: [] } });
  await expect(page.locator("#discovery-status")).toHaveText(
    "No speech engines are currently available.",
  );
  await expect(
    page.getByRole("button", { name: "Generate speech" }),
  ).toBeDisabled();
});

test("invalid catalog shape is distinct from an empty catalog", async ({ page }) => {
  await open(page, { json: { engines: "not-an-array" } });
  await expect(page.locator("#discovery-status")).toHaveText(
    "The speech service returned an invalid catalog.",
  );
});

test("legacy discovery omits selectors and submits backend defaults", async ({ page }) => {
  let speechPayload;
  await page.route(`**${catalogPath}`, (route) => route.fulfill({ status: 404 }));
  await page.route(`**${speechPath}`, async (route) => {
    speechPayload = route.request().postDataJSON();
    await route.fulfill({ contentType: "audio/wav", body: audio });
  });
  await page.route("**/api/healthz", (route) => route.fulfill({ json: { status: "ok" } }));
  await page.addInitScript(() => { HTMLMediaElement.prototype.play = async function () {}; });
  await page.goto("/");
  await expect(page.locator("#discovery-status")).toContainText("does not support discovery");
  await expect(page.locator("#engine")).toBeHidden();
  await page.getByRole("textbox", { name: "YOUR TEXT" }).fill("legacy");
  await page.getByRole("button", { name: "Generate speech" }).click();
  await expect.poll(() => speechPayload).toEqual({ input: "legacy", response_format: "mp3", speed: 1 });
});

test("submits selected engine and voice and preserves audio playback and download", async ({
  page,
}) => {
  await page.route(`**${speechPath}`, (route) =>
    route.fulfill({
      contentType: "audio/wav",
      body: audio,
    }),
  );
  await open(page);
  await page.locator("#language").selectOption("de-DE");
  await page
    .getByRole("combobox", { name: "SPEECH ENGINE" })
    .selectOption("fish-speech");
  await page.getByRole("combobox", { name: "VOICE" }).selectOption("de-male");
  await page.locator("#format").selectOption("wav");
  await page.locator("#speed").fill("1.3");
  await page.getByRole("textbox", { name: "YOUR TEXT" }).fill("Guten Morgen");

  const pendingRequest = page.waitForRequest(`**${speechPath}`);
  await page.getByRole("button", { name: "Generate speech" }).click();
  const request = await pendingRequest;

  expect(request.method()).toBe("POST");
  expect(request.postDataJSON()).toEqual({
    input: "Guten Morgen",
    response_format: "wav",
    speed: 1.3,
    language: "de-DE",
    model: "fish-speech",
    voice: "de-male",
  });
  await expect(
    page.getByRole("heading", { name: "Ready to listen." }),
  ).toBeVisible();
  await expect(page.locator("#audio-player")).toHaveAttribute("src", /^blob:/);
  await expect(page.locator("#download")).toHaveAttribute(
    "download",
    "speech.wav",
  );
  await expect(page.locator("#download")).toHaveAttribute("href", /^blob:/);
  await expect(page.locator("#generation-disclosure")).toHaveText(
    "This audio was generated by AI. Review applicable terms before sharing.",
  );
});
