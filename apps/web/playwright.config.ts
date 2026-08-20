import { defineConfig, devices } from "@playwright/test";

const PORT = 3100;
const API_PORT = 8100;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  timeout: 30_000,
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: process.env.PLAYWRIGHT_CHROMIUM_PATH
          ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH }
          : undefined,
      },
    },
  ],
  webServer: [
    {
      command:
        `cd ../api && rm -f e2e_test.db && ` +
        `DATABASE_URL=sqlite+aiosqlite:///./e2e_test.db AUTH_SECRET=e2e-test-secret-not-for-prod ` +
        `uv run alembic upgrade head && ` +
        `DATABASE_URL=sqlite+aiosqlite:///./e2e_test.db AUTH_SECRET=e2e-test-secret-not-for-prod ` +
        `FRONTEND_ORIGIN=http://localhost:${PORT} ` +
        `uv run uvicorn stackup_api.main:app --host 0.0.0.0 --port ${API_PORT}`,
      port: API_PORT,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: `API_BASE_URL=http://localhost:${API_PORT} pnpm dev --port ${PORT}`,
      port: PORT,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
