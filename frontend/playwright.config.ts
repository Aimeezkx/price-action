import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: 60000, // Increased timeout for document processing
  expect: {
    timeout: 10000, // Increased expect timeout
  },
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['allure-playwright', { outputFolder: 'test-results/allure-results' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
    },
    
    // Mobile devices
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    {
      name: 'Mobile Safari Landscape',
      use: { 
        ...devices['iPhone 12 landscape']
      },
    },
    
    // Tablet devices
    {
      name: 'iPad',
      use: { ...devices['iPad'] },
    },
    {
      name: 'iPad Landscape',
      use: { ...devices['iPad landscape'] },
    },
    
    // Cross-platform compatibility testing
    {
      name: 'cross-platform-chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: '**/cross-platform/**/*.spec.ts'
    },
    {
      name: 'cross-platform-firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: '**/cross-platform/**/*.spec.ts'
    },
    {
      name: 'cross-platform-webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: '**/cross-platform/**/*.spec.ts'
    },
    
    // Edge browser testing (if available)
    {
      name: 'edge',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'msedge',
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: '**/cross-platform/browser-compatibility.spec.ts'
    },
    
    // Responsive design testing across multiple viewports
    {
      name: 'responsive-mobile',
      use: {
        ...devices['iPhone 12'],
        viewport: { width: 390, height: 844 }
      },
      testMatch: '**/cross-platform/responsive-design.spec.ts'
    },
    {
      name: 'responsive-tablet',
      use: {
        ...devices['iPad'],
        viewport: { width: 768, height: 1024 }
      },
      testMatch: '**/cross-platform/responsive-design.spec.ts'
    },
    {
      name: 'responsive-desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
      testMatch: '**/cross-platform/responsive-design.spec.ts'
    },
    
    // Accessibility testing (with specific settings)
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Enable accessibility features
        launchOptions: {
          args: ['--force-prefers-reduced-motion']
        }
      },
      testMatch: '**/accessibility-testing.spec.ts'
    },
    
    // Performance testing
    {
      name: 'performance',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        // Throttle network for performance testing
        launchOptions: {
          args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
        }
      },
      testMatch: '**/complete-user-workflows.spec.ts'
    }
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000, // Increased timeout for server startup
  },
});