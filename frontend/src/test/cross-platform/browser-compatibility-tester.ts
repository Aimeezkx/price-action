/**
 * Browser compatibility testing framework
 */

import { chromium, firefox, webkit, Browser, Page } from 'playwright';
import { BrowserConfig, TestResult, TestContext, TestCase } from './types';
import { BROWSER_CONFIGS, TEST_TIMEOUTS } from './cross-platform.config';

export class BrowserCompatibilityTester {
  private browsers: Map<string, Browser> = new Map();
  private testResults: TestResult[] = [];

  async initialize(): Promise<void> {
    console.log('Initializing browser compatibility tester...');
    
    // Launch browsers
    const chromiumBrowser = await chromium.launch({ headless: true });
    const firefoxBrowser = await firefox.launch({ headless: true });
    const webkitBrowser = await webkit.launch({ headless: true });

    this.browsers.set('Chrome', chromiumBrowser);
    this.browsers.set('Edge', chromiumBrowser); // Edge uses Chromium
    this.browsers.set('Firefox', firefoxBrowser);
    this.browsers.set('Safari', webkitBrowser);
  }

  async runCompatibilityTests(baseUrl: string = 'http://localhost:3000'): Promise<TestResult[]> {
    console.log('Running browser compatibility tests...');
    this.testResults = [];

    const testCases = this.getCompatibilityTestCases();

    for (const browserConfig of BROWSER_CONFIGS) {
      console.log(`Testing on ${browserConfig.name}...`);
      
      const browser = this.browsers.get(browserConfig.name);
      if (!browser) {
        console.warn(`Browser ${browserConfig.name} not available`);
        continue;
      }

      const context = await browser.newContext({
        viewport: browserConfig.viewport,
        userAgent: browserConfig.userAgent
      });

      const page = await context.newPage();

      const testContext: TestContext = {
        browser,
        page,
        platform: browserConfig.name,
        baseUrl
      };

      for (const testCase of testCases) {
        if (testCase.platforms.includes(browserConfig.name) || testCase.platforms.includes('all')) {
          try {
            const result = await this.executeTestCase(testCase, testContext);
            this.testResults.push(result);
          } catch (error) {
            this.testResults.push({
              testName: testCase.name,
              platform: browserConfig.name,
              browser: browserConfig.name,
              status: 'failed',
              duration: 0,
              error: error instanceof Error ? error.message : String(error)
            });
          }
        }
      }

      await context.close();
    }

    return this.testResults;
  }

  private async executeTestCase(testCase: TestCase, context: TestContext): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const result = await testCase.execute(context);
      result.duration = Date.now() - startTime;
      return result;
    } catch (error) {
      return {
        testName: testCase.name,
        platform: context.platform,
        browser: context.platform,
        status: 'failed',
        duration: Date.now() - startTime,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  private getCompatibilityTestCases(): TestCase[] {
    return [
      {
        name: 'Page Load Test',
        description: 'Test if the main page loads correctly',
        category: 'functionality',
        platforms: ['all'],
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform } = context;
          const startTime = Date.now();
          
          await page.goto(context.baseUrl, { waitUntil: 'networkidle', timeout: TEST_TIMEOUTS.pageLoad });
          
          // Check if main elements are present
          await page.waitForSelector('[data-testid="main-navigation"]', { timeout: TEST_TIMEOUTS.elementWait });
          await page.waitForSelector('[data-testid="main-content"]', { timeout: TEST_TIMEOUTS.elementWait });
          
          const loadTime = Date.now() - startTime;
          
          return {
            testName: 'Page Load Test',
            platform,
            browser: platform,
            status: 'passed',
            duration: loadTime,
            metrics: { loadTime }
          };
        }
      },
      {
        name: 'Document Upload Test',
        description: 'Test document upload functionality',
        category: 'functionality',
        platforms: ['all'],
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform } = context;
          
          await page.goto(`${context.baseUrl}/documents`);
          
          // Test upload button exists and is clickable
          const uploadButton = page.locator('[data-testid="upload-button"]');
          await uploadButton.waitFor({ timeout: TEST_TIMEOUTS.elementWait });
          
          const isVisible = await uploadButton.isVisible();
          const isEnabled = await uploadButton.isEnabled();
          
          if (!isVisible || !isEnabled) {
            throw new Error('Upload button not accessible');
          }
          
          return {
            testName: 'Document Upload Test',
            platform,
            browser: platform,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'Search Functionality Test',
        description: 'Test search input and results',
        category: 'functionality',
        platforms: ['all'],
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform } = context;
          
          await page.goto(`${context.baseUrl}/search`);
          
          // Test search input
          const searchInput = page.locator('[data-testid="search-input"]');
          await searchInput.waitFor({ timeout: TEST_TIMEOUTS.elementWait });
          
          await searchInput.fill('test query');
          await searchInput.press('Enter');
          
          // Wait for search results or no results message
          try {
            await page.waitForSelector('[data-testid="search-results"], [data-testid="no-results"]', 
              { timeout: TEST_TIMEOUTS.elementWait });
          } catch (error) {
            throw new Error('Search results not displayed');
          }
          
          return {
            testName: 'Search Functionality Test',
            platform,
            browser: platform,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'Card Review Interface Test',
        description: 'Test flashcard review functionality',
        category: 'functionality',
        platforms: ['all'],
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform } = context;
          
          await page.goto(`${context.baseUrl}/study`);
          
          // Check if study interface loads
          try {
            await page.waitForSelector('[data-testid="flashcard"], [data-testid="no-cards-message"]', 
              { timeout: TEST_TIMEOUTS.elementWait });
          } catch (error) {
            throw new Error('Study interface not loaded');
          }
          
          // If flashcard is present, test interactions
          const flashcard = page.locator('[data-testid="flashcard"]');
          if (await flashcard.isVisible()) {
            // Test flip functionality
            const flipButton = page.locator('[data-testid="flip-button"]');
            if (await flipButton.isVisible()) {
              await flipButton.click();
              await page.waitForTimeout(500); // Wait for flip animation
            }
            
            // Test grading buttons
            const gradeButtons = page.locator('[data-testid^="grade-"]');
            const gradeCount = await gradeButtons.count();
            
            if (gradeCount === 0) {
              throw new Error('No grading buttons found');
            }
          }
          
          return {
            testName: 'Card Review Interface Test',
            platform,
            browser: platform,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'CSS Features Test',
        description: 'Test CSS features support',
        category: 'compatibility',
        platforms: ['all'],
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform } = context;
          
          await page.goto(context.baseUrl);
          
          // Test CSS Grid support
          const gridSupport = await page.evaluate(() => {
            return CSS.supports('display', 'grid');
          });
          
          // Test CSS Flexbox support
          const flexSupport = await page.evaluate(() => {
            return CSS.supports('display', 'flex');
          });
          
          // Test CSS Custom Properties support
          const customPropsSupport = await page.evaluate(() => {
            return CSS.supports('color', 'var(--test)');
          });
          
          const unsupportedFeatures = [];
          if (!gridSupport) unsupportedFeatures.push('CSS Grid');
          if (!flexSupport) unsupportedFeatures.push('CSS Flexbox');
          if (!customPropsSupport) unsupportedFeatures.push('CSS Custom Properties');
          
          if (unsupportedFeatures.length > 0) {
            throw new Error(`Unsupported CSS features: ${unsupportedFeatures.join(', ')}`);
          }
          
          return {
            testName: 'CSS Features Test',
            platform,
            browser: platform,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'JavaScript Features Test',
        description: 'Test JavaScript features support',
        category: 'compatibility',
        platforms: ['all'],
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform } = context;
          
          await page.goto(context.baseUrl);
          
          // Test modern JavaScript features
          const features = await page.evaluate(() => {
            const results: Record<string, boolean> = {};
            
            // Test async/await
            results.asyncAwait = typeof (async () => {}) === 'function';
            
            // Test Promises
            results.promises = typeof Promise !== 'undefined';
            
            // Test Fetch API
            results.fetch = typeof fetch !== 'undefined';
            
            // Test localStorage
            results.localStorage = typeof localStorage !== 'undefined';
            
            // Test sessionStorage
            results.sessionStorage = typeof sessionStorage !== 'undefined';
            
            // Test IndexedDB
            results.indexedDB = typeof indexedDB !== 'undefined';
            
            // Test Service Workers
            results.serviceWorker = 'serviceWorker' in navigator;
            
            return results;
          });
          
          const unsupportedFeatures = Object.entries(features)
            .filter(([, supported]) => !supported)
            .map(([feature]) => feature);
          
          if (unsupportedFeatures.length > 0) {
            console.warn(`${platform} missing features: ${unsupportedFeatures.join(', ')}`);
          }
          
          return {
            testName: 'JavaScript Features Test',
            platform,
            browser: platform,
            status: 'passed',
            duration: 0
          };
        }
      }
    ];
  }

  async cleanup(): Promise<void> {
    console.log('Cleaning up browser compatibility tester...');
    
    for (const [name, browser] of this.browsers) {
      try {
        await browser.close();
        console.log(`Closed ${name} browser`);
      } catch (error) {
        console.error(`Error closing ${name} browser:`, error);
      }
    }
    
    this.browsers.clear();
  }

  getResults(): TestResult[] {
    return this.testResults;
  }

  generateReport(): string {
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => r.status === 'passed').length;
    const failedTests = this.testResults.filter(r => r.status === 'failed').length;
    
    let report = `\n=== Browser Compatibility Test Report ===\n`;
    report += `Total Tests: ${totalTests}\n`;
    report += `Passed: ${passedTests}\n`;
    report += `Failed: ${failedTests}\n`;
    report += `Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;
    
    // Group results by browser
    const resultsByBrowser = this.testResults.reduce((acc, result) => {
      const browser = result.browser || result.platform;
      if (!acc[browser]) acc[browser] = [];
      acc[browser].push(result);
      return acc;
    }, {} as Record<string, TestResult[]>);
    
    for (const [browser, results] of Object.entries(resultsByBrowser)) {
      const browserPassed = results.filter(r => r.status === 'passed').length;
      const browserTotal = results.length;
      
      report += `${browser}: ${browserPassed}/${browserTotal} tests passed\n`;
      
      const failedResults = results.filter(r => r.status === 'failed');
      if (failedResults.length > 0) {
        report += `  Failed tests:\n`;
        failedResults.forEach(result => {
          report += `    - ${result.testName}: ${result.error}\n`;
        });
      }
      report += '\n';
    }
    
    return report;
  }
}