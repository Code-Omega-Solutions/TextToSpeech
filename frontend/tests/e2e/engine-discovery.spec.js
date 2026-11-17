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
      voices: { "de-DE": ["de-fish"], "en-US": ["en-us-fish"] },
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
    route.fulfill(catalogResponse),
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
  ).toEqual(["", "de-fish"]);
  await expect(page.locator("#discovery-status")).toHaveText(
    "Speech options are ready.",
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
  await page.getByRole("combobox", { name: "VOICE" }).selectOption("de-fish");
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
    voice: "de-fish",
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
});
