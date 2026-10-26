import { createHash } from "node:crypto";
import { expect, test } from "@playwright/test";

test("matches the original running frontend pixel-for-pixel", async ({ page, context }, testInfo) => {
  test.skip(!process.env.ORIGINAL_FRONTEND_URL, "Set ORIGINAL_FRONTEND_URL for optional recovery fidelity verification.");
  await context.route("**/api/healthz", (route) => route.fulfill({ json: { status: "ok" } }));
  const original = await context.newPage();
  await original.goto(process.env.ORIGINAL_FRONTEND_URL);
  await page.goto("/");
  for (const target of [original, page]) {
    await expect(target.locator("#service-status")).toHaveAttribute("data-state", "online");
    await target.evaluate(() => document.fonts.ready);
  }
  const expected = await original.screenshot({ fullPage: true, animations: "disabled" });
  const actual = await page.screenshot({ fullPage: true, animations: "disabled" });
  if (!actual.equals(expected)) {
    await testInfo.attach("original", { body: expected, contentType: "image/png" });
    await testInfo.attach("restored", { body: actual, contentType: "image/png" });
  }
  const hash = (buffer) => createHash("sha256").update(buffer).digest("hex");
  expect(hash(actual)).toBe(hash(expected));
  await original.close();
});
