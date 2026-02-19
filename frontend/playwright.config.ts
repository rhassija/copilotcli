import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests.
 * 
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Test match patterns
  testMatch: '**/*.e2e.{test,spec}.{js,ts}',
  
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL for navigating
    baseURL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    
    // Collect trace on first retry
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Timeout for each action (e.g., click)
    actionTimeout: 10000,
    
    // Navigation timeout
    navigationTimeout: 30000,
  },
  
  // Test timeout (30 seconds)
  timeout: 30000,
  
  // Expect timeout (5 seconds)
  expect: {
    timeout: 5000,
  },
  
  // Configure projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    
    // Uncomment to test in Firefox
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    
    // Uncomment to test in WebKit (Safari)
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
    
    // Uncomment for mobile testing
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],
  
  // Run your local dev server before starting tests
  webServer: [
    {
      command: 'cd ../backend && source ../copilotcompanion/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8000',
      port: 8000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI,
      env: {
        GITHUB_TOKEN: process.env.GITHUB_TOKEN || 'test_token',
      },
    },
    {
      command: 'npm run dev',
      port: 3000,
      timeout: 120000,
      reuseExistingServer: !process.env.CI,
    },
  ],
  
  // Output directory for test artifacts
  outputDir: 'test-results/',
});
