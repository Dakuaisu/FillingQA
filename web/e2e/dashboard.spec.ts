import { expect, test } from "@playwright/test";

test("the dashboard shows the gate failing, with a reason on every row", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByTestId("gate-status")).toContainText("The CI eval gate fails.");
  await expect(page.getByTestId("gate-status")).toContainText("No gated run exists (F-59). Development runs cannot pass the gate and are not results.");
  const rows = page.getByTestId("gate-row");
  await expect(rows).toHaveCount(21);
  await expect(page.getByTestId("gate-table")).not.toContainText("PASS");
  await expect(page.getByTestId("gate-table")).toContainText("pending: judge answer correctness (F-105)");
  const later = page.getByTestId("pending-with-run");
  await expect(later).toContainText("Even once a gated run exists, these stay pending:");
  await expect(later).toContainText("cost per query (needs a priced run, F-134)");
  await expect(later.locator("li")).toHaveCount(4);
});

test("model-free retrieval is labelled Config 3 on unreviewed candidates, as the README says", async ({ page }) => {
  await page.goto("/dashboard");
  const cur = page.getByTestId("retrieval-current");
  await expect(cur).toContainText("Retrieval run 5b3c3ac13e5e, Config 3 (PRD 11.6)");
  await expect(cur).toContainText("unreviewed candidates");
  await expect(page.getByTestId("retrieval-aggregate")).toContainText("0.537");
  await expect(page.getByTestId("retrieval-aggregate")).toContainText("0.82");
  await expect(page.getByTestId("retrieval-xbrl_auto")).toContainText("0.375");
  await expect(page.getByTestId("retrieval-xbrl_auto")).toContainText("misses");
  await expect(page.getByTestId("retrieval-llm_seeded")).toContainText("F-110");
});

test("development runs appear as ids with the banner and no value", async ({ page }) => {
  await page.goto("/dashboard");
  const dev = page.getByTestId("development-runs");
  await expect(dev).toContainText("a4e39a65c2c8");
  await expect(dev).toContainText("not a result");
  expect(await dev.innerText()).not.toMatch(/\b\d\.\d{2,}/);
  await expect(page.getByTestId("owner-blocked").locator("tr")).toHaveCount(8);
});
