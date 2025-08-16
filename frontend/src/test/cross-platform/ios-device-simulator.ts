/**
 * iOS device simulation and testing framework
 */

import { webkit, Browser, BrowserContext, Page } from 'playwright';
import { DeviceConfig, TestResult, TestContext } from './types';
import { DEVICE_CONFIGS, TEST_TIMEOUTS } from './cross-platform.config';

export class IOSDeviceSimulator {
  private browser: Browser | null = null;
  private contexts: Map<string, BrowserContext> = new Map();
  private testResults: TestResult[] = [];

  async initialize(): Promise<void> {
    console.log('Initializing iOS device simulator...');
    
    // Use WebKit for iOS simulation
    this.browser = await webkit.launch({ 
      headless: true,
      args: ['--enable-experimental-web-platform-features']
    });
  }

  async simulateDevice(deviceConfig: DeviceConfig): Promise<BrowserContext> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const context = await this.browser.newContext({
      viewport: deviceConfig.viewport,
      deviceScaleFactor: deviceConfig.pixelRatio,
      isMobile: deviceConfig.type === 'mobile',
      hasTouch: deviceConfig.touchEnabled,
      userAgent: this.getIOSUserAgent(deviceConfig)
    });

    this.contexts.set(deviceConfig.name, context);
    return context;
  }

  private getIOSUserAgent(device: DeviceConfig): string {
    const baseUA = 'Mozilla/5.0';
    
    if (device.type === 'mobile') {
      return `${baseUA} (iPhone; CPU iPhone OS ${device.osVersion.replace('.', '_')} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1`;
    } else if (device.type === 'tablet') {
      return `${baseUA} (iPad; CPU OS ${device.osVersion.replace('.', '_')} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1`;
    } else {
      return `${baseUA} (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15`;
    }
  }

  async runIOSCompatibilityTests(baseUrl: string = 'http://localhost:3000'): Promise<TestResult[]> {
    console.log('Running iOS compatibility tests...');
    this.testResults = [];

    const iosDevices = DEVICE_CONFIGS.filter(device => device.os === 'iOS');

    for (const deviceConfig of iosDevices) {
      console.log(`Testing on ${deviceConfig.name}...`);
      
      const context = await this.simulateDevice(deviceConfig);
      const page = await context.newPage();

      const testContext: TestContext = {
        browser: this.browser!,
        page,
        device: deviceConfig,
        platform: `iOS-${deviceConfig.name}`,
        baseUrl
      };

      const testCases = this.getIOSTestCases();

      for (const testCase of testCases) {
        try {
          const result = await this.executeTestCase(testCase, testContext);
          this.testResults.push(result);
        } catch (error) {
          this.testResults.push({
            testName: testCase.name,
            platform: testContext.platform,
            device: deviceConfig.name,
            status: 'failed',
            duration: 0,
            error: error instanceof Error ? error.message : String(error)
          });
        }
      }

      await context.close();
    }

    return this.testResults;
  }

  private async executeTestCase(testCase: any, context: TestContext): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const result = await testCase.execute(context);
      result.duration = Date.now() - startTime;
      return result;
    } catch (error) {
      return {
        testName: testCase.name,
        platform: context.platform,
        device: context.device?.name,
        status: 'failed',
        duration: Date.now() - startTime,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  private getIOSTestCases() {
    return [
      {
        name: 'Touch Interactions Test',
        description: 'Test touch-based interactions on iOS',
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform, device } = context;
          
          await page.goto(context.baseUrl);
          
          // Test tap interactions
          const navigationButton = page.locator('[data-testid="main-navigation"] button').first();
          await navigationButton.waitFor({ timeout: TEST_TIMEOUTS.elementWait });
          
          // Simulate touch tap
          await navigationButton.tap();
          await page.waitForTimeout(500);
          
          // Test swipe gestures if on mobile
          if (device?.type === 'mobile') {
            // Test horizontal swipe (if applicable)
            const swipeableElement = page.locator('[data-testid="swipeable-content"]').first();
            if (await swipeableElement.isVisible()) {
              const box = await swipeableElement.boundingBox();
              if (box) {
                await page.touchscreen.tap(box.x + box.width * 0.8, box.y + box.height / 2);
                await page.mouse.move(box.x + box.width * 0.2, box.y + box.height / 2);
              }
            }
          }
          
          return {
            testName: 'Touch Interactions Test',
            platform,
            device: device?.name,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'Viewport Adaptation Test',
        description: 'Test viewport adaptation on different iOS devices',
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform, device } = context;
          
          await page.goto(context.baseUrl);
          
          // Check if content adapts to viewport
          const mainContent = page.locator('[data-testid="main-content"]');
          await mainContent.waitFor({ timeout: TEST_TIMEOUTS.elementWait });
          
          const contentBox = await mainContent.boundingBox();
          const viewport = page.viewportSize();
          
          if (!contentBox || !viewport) {
            throw new Error('Could not get content or viewport dimensions');
          }
          
          // Check if content fits within viewport
          if (contentBox.width > viewport.width) {
            throw new Error('Content overflows viewport width');
          }
          
          // Test orientation change simulation (for mobile devices)
          if (device?.type === 'mobile') {
            await page.setViewportSize({ 
              width: device.viewport.height, 
              height: device.viewport.width 
            });
            
            await page.waitForTimeout(1000); // Wait for reflow
            
            const newContentBox = await mainContent.boundingBox();
            const newViewport = page.viewportSize();
            
            if (!newContentBox || !newViewport) {
              throw new Error('Could not get dimensions after orientation change');
            }
            
            if (newContentBox.width > newViewport.width) {
              throw new Error('Content overflows viewport after orientation change');
            }
          }
          
          return {
            testName: 'Viewport Adaptation Test',
            platform,
            device: device?.name,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'iOS Safari Features Test',
        description: 'Test iOS Safari specific features and limitations',
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform, device } = context;
          
          await page.goto(context.baseUrl);
          
          // Test iOS Safari specific features
          const features = await page.evaluate(() => {
            const results: Record<string, boolean> = {};
            
            // Test Web App Manifest support
            results.webAppManifest = 'serviceWorker' in navigator;
            
            // Test iOS specific viewport meta tag handling
            const viewportMeta = document.querySelector('meta[name="viewport"]');
            results.viewportMeta = !!viewportMeta;
            
            // Test touch events
            results.touchEvents = 'ontouchstart' in window;
            
            // Test device orientation
            results.deviceOrientation = 'orientation' in window;
            
            // Test iOS specific CSS features
            results.webkitOverflowScrolling = CSS.supports('-webkit-overflow-scrolling', 'touch');
            
            return results;
          });
          
          // Check for iOS-specific issues
          const issues = [];
          
          if (!features.touchEvents && device?.touchEnabled) {
            issues.push('Touch events not supported');
          }
          
          if (!features.viewportMeta) {
            issues.push('Viewport meta tag missing');
          }
          
          if (issues.length > 0) {
            console.warn(`iOS compatibility issues: ${issues.join(', ')}`);
          }
          
          return {
            testName: 'iOS Safari Features Test',
            platform,
            device: device?.name,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'File Upload Test (iOS)',
        description: 'Test file upload functionality on iOS devices',
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform, device } = context;
          
          await page.goto(`${context.baseUrl}/documents`);
          
          // Test file input accessibility on iOS
          const fileInput = page.locator('input[type="file"]');
          
          if (await fileInput.count() > 0) {
            const isVisible = await fileInput.first().isVisible();
            
            // On iOS, file inputs might be hidden and triggered by buttons
            if (!isVisible) {
              const uploadButton = page.locator('[data-testid="upload-button"]');
              await uploadButton.waitFor({ timeout: TEST_TIMEOUTS.elementWait });
              
              const buttonVisible = await uploadButton.isVisible();
              if (!buttonVisible) {
                throw new Error('Upload interface not accessible on iOS');
              }
            }
          }
          
          // Test drag and drop (not supported on iOS)
          if (device?.touchEnabled) {
            const dropZone = page.locator('[data-testid="drop-zone"]');
            if (await dropZone.count() > 0) {
              // Should show alternative upload method on touch devices
              const alternativeUpload = page.locator('[data-testid="touch-upload"]');
              const hasAlternative = await alternativeUpload.count() > 0;
              
              if (!hasAlternative) {
                console.warn('No touch-friendly upload alternative provided');
              }
            }
          }
          
          return {
            testName: 'File Upload Test (iOS)',
            platform,
            device: device?.name,
            status: 'passed',
            duration: 0
          };
        }
      },
      {
        name: 'Performance on iOS Test',
        description: 'Test performance characteristics on iOS devices',
        execute: async (context: TestContext): Promise<TestResult> => {
          const { page, platform, device } = context;
          
          const startTime = Date.now();
          await page.goto(context.baseUrl, { waitUntil: 'networkidle' });
          const loadTime = Date.now() - startTime;
          
          // Test scroll performance
          const scrollStartTime = Date.now();
          await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight / 2);
          });
          await page.waitForTimeout(100);
          const scrollTime = Date.now() - scrollStartTime;
          
          // Test interaction responsiveness
          const interactionStartTime = Date.now();
          const button = page.locator('button').first();
          if (await button.count() > 0) {
            await button.tap();
            await page.waitForTimeout(100);
          }
          const interactionTime = Date.now() - interactionStartTime;
          
          // Performance thresholds for iOS devices
          const maxLoadTime = device?.type === 'mobile' ? 5000 : 3000;
          const maxInteractionTime = 300;
          
          if (loadTime > maxLoadTime) {
            throw new Error(`Load time ${loadTime}ms exceeds threshold ${maxLoadTime}ms`);
          }
          
          if (interactionTime > maxInteractionTime) {
            throw new Error(`Interaction time ${interactionTime}ms exceeds threshold ${maxInteractionTime}ms`);
          }
          
          return {
            testName: 'Performance on iOS Test',
            platform,
            device: device?.name,
            status: 'passed',
            duration: 0,
            metrics: {
              loadTime,
              renderTime: scrollTime,
              interactionTime
            }
          };
        }
      }
    ];
  }

  async cleanup(): Promise<void> {
    console.log('Cleaning up iOS device simulator...');
    
    // Close all contexts
    for (const [deviceName, context] of this.contexts) {
      try {
        await context.close();
        console.log(`Closed context for ${deviceName}`);
      } catch (error) {
        console.error(`Error closing context for ${deviceName}:`, error);
      }
    }
    this.contexts.clear();
    
    // Close browser
    if (this.browser) {
      try {
        await this.browser.close();
        console.log('Closed iOS simulator browser');
      } catch (error) {
        console.error('Error closing iOS simulator browser:', error);
      }
      this.browser = null;
    }
  }

  getResults(): TestResult[] {
    return this.testResults;
  }

  generateReport(): string {
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => r.status === 'passed').length;
    const failedTests = this.testResults.filter(r => r.status === 'failed').length;
    
    let report = `\n=== iOS Device Compatibility Test Report ===\n`;
    report += `Total Tests: ${totalTests}\n`;
    report += `Passed: ${passedTests}\n`;
    report += `Failed: ${failedTests}\n`;
    report += `Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;
    
    // Group results by device
    const resultsByDevice = this.testResults.reduce((acc, result) => {
      const device = result.device || result.platform;
      if (!acc[device]) acc[device] = [];
      acc[device].push(result);
      return acc;
    }, {} as Record<string, TestResult[]>);
    
    for (const [device, results] of Object.entries(resultsByDevice)) {
      const devicePassed = results.filter(r => r.status === 'passed').length;
      const deviceTotal = results.length;
      
      report += `${device}: ${devicePassed}/${deviceTotal} tests passed\n`;
      
      // Show performance metrics if available
      const performanceResults = results.filter(r => r.metrics);
      if (performanceResults.length > 0) {
        report += `  Performance metrics:\n`;
        performanceResults.forEach(result => {
          if (result.metrics) {
            report += `    Load time: ${result.metrics.loadTime}ms\n`;
            if (result.metrics.interactionTime) {
              report += `    Interaction time: ${result.metrics.interactionTime}ms\n`;
            }
          }
        });
      }
      
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