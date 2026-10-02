import { expect, test } from "@playwright/test";

test("Corpus says what is indexed and what is not", async ({ page }) => {
  await page.goto("/corpus");
  await expect(page.getByTestId("corpus-totals")).toContainText(
    "96 filings listed in the frozen corpus: 90 parsed and indexed, 6 quarantined (not indexed). 22,354 chunks.",
  );
  await expect(page.getByTestId("freeze")).toContainText("parser d58d26e08e5a · chunker 964f77f6f9cb");
  await expect(page.getByTestId("companies").locator("tbody tr")).toHaveCount(8);
  const q = page.getByTestId("quarantined").locator("li");
  await expect(q).toHaveCount(6);
  await expect(page.getByTestId("quarantined")).toContainText("JPM 10-K");
  await expect(page.getByTestId("quarantined")).toContainText("F-66");
  await expect(page.getByTestId("quarantined")).toContainText("XOM 10-K");
  await expect(page.getByTestId("quarantined")).toContainText("F-70");
  await expect(page.getByTestId("dev-banner")).toHaveCount(0); // no generated text on this screen
});
