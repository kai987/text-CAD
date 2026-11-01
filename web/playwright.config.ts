import { defineConfig } from '@playwright/test';

// Browser plugin not available. This independent browser is the committed CI
// regression runner; interactive acceptance uses the in-app browser separately.
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1,
  forbidOnly: !!process.env.CI, retries: process.env.CI ? 1 : 0,
  timeout: 120_000, expect: { timeout: 45_000, toHaveScreenshot: { maxDiffPixelRatio: .015, threshold: .2, animations: 'disabled' } },
  snapshotPathTemplate: '{testDir}/snapshots/{projectName}/{arg}{ext}',
  reporter: [['list'], ['html', { open: 'never' }], ['json', { outputFile: 'test-results/results.json' }]],
  use: { baseURL: 'http://127.0.0.1:4213/text-CAD/', locale: 'en-US', colorScheme: 'light',
    deviceScaleFactor: 1, trace: 'retain-on-failure', screenshot: 'only-on-failure',
    launchOptions: { args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1280, height: 900 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: { command: 'npm run preview -- --port 4213 --strictPort', url: 'http://127.0.0.1:4213/text-CAD/', reuseExistingServer: false, timeout: 30_000 },
});
