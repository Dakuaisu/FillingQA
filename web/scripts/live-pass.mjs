// Manual live pass: drives the real frontend against the real API (development
// backend). Screenshots and a text summary go to ../build/web-live/ (git-ignored);
// nothing here is committed output or README material (F-59).
// Usage: make serve; make web-dev; node scripts/live-pass.mjs [http://localhost:3000] [--browse-only]
// --browse-only: Ask, Corpus and Dashboard only (no generation calls).
import { mkdirSync, writeFileSync } from "node:fs";

import { chromium } from "@playwright/test";

const BASE = process.argv.slice(2).find((a) => a.startsWith("http")) ?? "http://localhost:3000";
const OUT = new URL("../../build/web-live/", import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const QUESTIONS = [
  ["lookup", "What did Apple report as its research and development expense for fiscal 2023?"],
  [
    "comparison",
    "How did Bank of America net interest income for the first two quarters of fiscal 2026 compare with the first two quarters of fiscal 2024?",
  ],
  ["unsupported", "Should I buy NVIDIA stock right now?"],
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
const summary = { base: BASE, at: new Date().toISOString(), screens: [] };
const text = async (id) => ((await page.getByTestId(id).count()) ? (await page.getByTestId(id).allInnerTexts()) : []);

await page.goto(BASE);
await page.screenshot({ path: `${OUT}ask.png`, fullPage: true });
summary.screens.push({ screen: "ask", examples: await text("example") });

await page.goto(`${BASE}/corpus`);
await page.getByTestId("quarantined").waitFor({ timeout: 30_000 });
await page.screenshot({ path: `${OUT}corpus.png`, fullPage: true });
summary.screens.push({ screen: "corpus", totals: await text("corpus-totals"), freeze: await text("freeze"),
  companies: await page.getByTestId("companies").locator("tbody tr").allInnerTexts(),
  quarantined: await page.getByTestId("quarantined").locator("li").allInnerTexts() });

await page.goto(`${BASE}/dashboard`);
await page.getByTestId("gate-status").waitFor({ timeout: 30_000 });
await page.screenshot({ path: `${OUT}dashboard.png`, fullPage: true });
summary.screens.push({ screen: "dashboard", gate: await text("gate-status"),
  gate_rows: await page.getByTestId("gate-row").count(),
  retrieval: await text("retrieval-current"), development: await text("development-runs"),
  owner_blocked: await page.getByTestId("owner-blocked").locator("tr").allInnerTexts() });
if (process.argv.includes("--browse-only")) {
  summary.page_errors = errors;
  writeFileSync(`${OUT}summary.json`, JSON.stringify(summary, null, 1));
  await browser.close();
  console.log(JSON.stringify(summary, null, 1));
  process.exit(0);
}

for (const [name, q] of QUESTIONS) {
  const t0 = Date.now();
  await page.goto(`${BASE}/answer?q=${encodeURIComponent(q)}`, { timeout: 180_000 });
  await page.locator('[data-testid="answer"], [data-testid="abstention"], [data-testid="error"]').first().waitFor({ timeout: 180_000 });
  const s = { screen: `answer:${name}`, question: q, seconds: (Date.now() - t0) / 1000 };
  for (const id of ["dev-banner", "verdict", "confidence", "pending-note", "claim", "xbrl-badge", "citations", "abstention", "error", "latency-cost"]) {
    s[id] = await text(id);
  }
  await page.screenshot({ path: `${OUT}answer-${name}.png`, fullPage: true });
  const markers = page.getByTestId("citation-marker");
  if (await markers.count()) {
    await markers.first().hover();
    await page.getByTestId("citation-preview").waitFor({ timeout: 5000 }).catch(() => {});
    s["citation-preview"] = await text("citation-preview");
    await page.screenshot({ path: `${OUT}answer-${name}-hover.png` });
    await markers.first().click();
    await page.getByTestId("source-panel").getByRole("link").waitFor({ timeout: 15_000 }).catch(() => {});
    s["source-panel"] = (await text("source-panel")).map((x) => x.slice(0, 600));
    await page.screenshot({ path: `${OUT}answer-${name}-source.png` });
    await page.keyboard.press("Escape");
  }
  summary.screens.push(s);
}

await page.goto(`${BASE}/answer?q=${encodeURIComponent("revenue ".repeat(600))}`, { timeout: 120_000 });
await page.getByTestId("error").waitFor({ timeout: 120_000 });
summary.screens.push({ screen: "answer:too-long", error: await text("error") });
await page.screenshot({ path: `${OUT}answer-too-long.png`, fullPage: true });

summary.page_errors = errors;
writeFileSync(`${OUT}summary.json`, JSON.stringify(summary, null, 1));
await browser.close();
console.log(JSON.stringify(summary, null, 1));
