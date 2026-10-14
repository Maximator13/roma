import { defineConfig, devices } from '@playwright/test'

const port = 4173
const liveUrl = process.env.LIVE_URL

export default defineConfig({
  testDir: 'tests',
  outputDir: 'test-results',
  timeout: 60_000,
  reporter: [['list']],
  use: {
    baseURL: liveUrl ?? `http://localhost:${port}/roma/`,
    trace: 'retain-on-failure',
  },
  webServer: liveUrl
    ? undefined
    : {
        command: `npx vite preview --port ${port} --strictPort`,
        url: `http://localhost:${port}/roma/`,
        reuseExistingServer: !process.env.CI,
      },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
})
