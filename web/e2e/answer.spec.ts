import { readFileSync } from "node:fs";
import { join } from "node:path";

import { expect, test } from "@playwright/test";

const fixture = (f: string) => readFileSync(join(__dirname, "fixtures", f), "utf8");
const ask = (q: string) => `/answer?q=${encodeURIComponent(q)}`;
const LOOKUP = "What did Apple report as its research and development expense for fiscal 2023?";

test("a PASS answer: dev banner, claim, XBRL badge, citations, latency and cost labelled dev", async ({ page }) => {
  await page.goto(ask(LOOKUP));
  await expect(page.getByTestId("dev-banner")).toContainText("Development answer: generated on claude_cli");
  await expect(page.getByTestId("verdict")).toHaveText("PASS");
  await expect(page.getByTestId("confidence")).toHaveText("Confidence: High");
  await expect(page.getByTestId("claim")).toContainText("$29,915 million for fiscal 2023");
  await expect(page.getByTestId("xbrl-badge")).toHaveText("✓ matches SEC XBRL");
  await expect(page.getByTestId("citations")).toContainText("Apple Inc. (AAPL) 10-K FY2023");
  await expect(page.getByTestId("latency-cost")).toContainText("Development backend");
  await expect(page.getByTestId("latency-cost")).toContainText("cost n/a (dev backend)");
});

test("hovering a citation marker previews the excerpt; clicking opens the source panel", async ({ page }) => {
  await page.goto(ask(LOOKUP));
  await page.getByTestId("citation-marker").first().hover();
  await expect(page.getByTestId("citation-preview")).toContainText("AAPL 10-K FY2023");
  await page.getByTestId("citation-marker").first().click();
  const panel = page.getByTestId("source-panel");
  await expect(panel).toContainText("Apple Inc. (AAPL)");
  await expect(panel).toContainText("not computed");
  await expect(panel.getByRole("link", { name: "View the filing on sec.gov" })).toHaveAttribute(
    "href",
    /sec\.gov\/Archives/,
  );
});

test("a chunk the index does not have shows the 404 state in the source panel", async ({ page }) => {
  await page.route("**/web-api/chunks/**", (route) =>
    route.fulfill({ status: 404, contentType: "application/json", body: fixture("chunk_404.json") }),
  );
  await page.goto(ask(LOOKUP));
  await page.getByTestId("citation-marker").first().click();
  await expect(page.getByTestId("source-error")).toHaveText("This chunk was not found in the index.");
});

test("an unsupported question renders the designed abstention state", async ({ page }) => {
  await page.goto(ask("Should I buy NVIDIA stock right now?"));
  await expect(page.getByTestId("dev-banner")).toBeVisible();
  const panel = page.getByTestId("abstention");
  await expect(panel).toContainText("No answer: the filings do not support one");
  await expect(panel).toContainText("outside what the indexed SEC filings can answer");
  await expect(page.getByTestId("claim")).toHaveCount(0);
});

test("a verdict waiting on the NLI threshold says so and shows the band as pending", async ({ page }) => {
  await page.goto(
    ask("How did Bank of America net interest income for the first two quarters of fiscal 2026 compare with the first two quarters of fiscal 2024?"),
  );
  await expect(page.getByTestId("verdict")).toHaveText("Verification pending");
  await expect(page.getByTestId("confidence")).toHaveText("Confidence: Pending");
  await expect(page.getByTestId("pending-note")).toBeVisible();
  await expect(page.getByTestId("claim")).toHaveCount(3);
  await expect(page.getByTestId("xbrl-badge")).toHaveCount(2);
  // Markers are numbered in reading order: the first claim's first citation is [1].
  await expect(page.getByTestId("claim").first().getByTestId("citation-marker").first()).toHaveText("[1]");
});

test("a question over the length limit shows the 422 message", async ({ page }) => {
  await page.goto(ask("revenue ".repeat(600)));
  await expect(page.getByTestId("error")).toContainText("The question is too long for the retriever.");
});
