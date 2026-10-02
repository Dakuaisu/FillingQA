import { expect, test } from "@playwright/test";

test("Ask shows three examples, one labelled as unanswerable, and submits to Answer", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Ask the filings" })).toBeVisible();
  const examples = page.getByTestId("example");
  await expect(examples).toHaveCount(3);
  await expect(examples.nth(2)).toContainText("See how it handles a question it can't answer.");
  await page.getByLabel("Question", { exact: true }).fill("What did Apple report as its research and development expense for fiscal 2023?");
  await page.getByRole("button", { name: "Ask" }).click();
  await expect(page).toHaveURL(/\/answer\?q=What\+did\+Apple/);
  await expect(page.getByTestId("answer")).toBeVisible();
});

test("the unanswerable example lands on the abstention state", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("example").nth(2).click();
  await expect(page.getByTestId("abstention")).toBeVisible();
});
