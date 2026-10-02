import { defineConfig, devices } from "@playwright/test";

// e2e against a mocked API serving captured development responses (e2e/fixtures).
// Ports: the mock API on 8765 and the suite's own Next dev server on 3100, building
// into .next-e2e, so it never shares a port or a .next with `make web-dev` (:3000).
const MOCK = 8765;
const WEB = 3100;

export default defineConfig({
  testDir: "e2e",
  fullyParallel: false,
  retries: 0,
  use: { baseURL: `http://localhost:${WEB}`, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    { command: `MOCK_PORT=${MOCK} node e2e/mock-api.mjs`, port: MOCK, reuseExistingServer: false },
    {
      command: `NEXT_DIST_DIR=.next-e2e API_BASE=http://127.0.0.1:${MOCK} npx next dev -p ${WEB}`,
      port: WEB,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
