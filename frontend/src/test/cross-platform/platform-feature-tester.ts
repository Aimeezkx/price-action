/**
 * Platform-specific feature testing
 */

import { Page } from 'playwright';
import { TestResult, TestContext, PlatformFeature } from './types';
import { PLATFORM_FEATURES, TEST_TIMEOUTS } from './cross-platform.config';

interface FeatureTestResult extends TestResult {
  featureName: string;
  supported: boolean;
  fallbackAvailable: boolean;
  performanceImpact?: number;
}

export class PlatformFeatureTester {
  private testResults: FeatureTestResult[] = [];

  async runFeatureTests(page: Page, platform: string, baseUrl: string = 'http://localhost:3000'): Promise<FeatureTestResult[]> {
    console.log(`Running platform-specific feature tests for ${platform}...`);
    this.testResults = [];

    const testContext: TestContext = {
      page,
      platform,
      baseUrl
    };

    const platformFeatures = this.getPlatformFeatures();

    for (const feature of platformFeatures) {
      if (feature.platforms.includes(platform) || feature.platforms.includes('all')) {
        try {
          const result = await this.testFeature(feature, testContext);
          this.testResults.push(result);
        } catch (error) {
          this.testResults.push({
            testName: `${feature.name} Test`,
            featureName: feature.name,
            platform,
            status: 'failed',
            duration: 0,
            supported: false,
            fallbackAvailable: false,
            error: error instanceof Error ? error.message : String(error)
          });
        }
      }
    }

    return this.testResults;
  }

  private async testFeature(feature: PlatformFeature, context: TestContext): Promise<FeatureTestResult> {
    const startTime = Date.now();
    
    try {
      const supported = await feature.testFunction(context);
      const duration = Date.now() - startTime;
      
      // Test fallback if feature is not supported
      let fallbackAvailable = false;
      if (!supported && feature.fallbackBehavior) {
        fallbackAvailable = await this.testFallback(feature, context);
      }

      return {
        testName: `${feature.name} Test`,
        featureName: feature.name,
        platform: context.platform,
        status: supported || fallbackAvailable ? 'passed' : 'failed',
        duration,
        supported,
        fallbackAvailable
      };
    } catch (error) {
      return {
        testName: `${feature.name} Test`,
        featureName: feature.name,
        platform: context.platform,
        status: 'failed',
        duration: Date.now() - startTime,
        supported: false,
        fallbackAvailable: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  private async testFallback(feature: PlatformFeature, context: TestContext): Promise<boolean> {
    // Test if fallback behavior is available
    try {
      const { page } = context;
      
      // Check if fallback UI elements are present
      const fallbackElements = await page.locator(`[data-testid="${feature.name}-fallback"]`).count();
      return fallbackElements > 0;
    } catch (error) {
      return false;
    }
  }

  private getPlatformFeatures(): PlatformFeature[] {
    return [
      {
        name: 'file-upload',
        platforms: ['all'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(`${context.baseUrl}/documents`);
          
          // Test file input support
          const fileInput = page.locator('input[type="file"]');
          const hasFileInput = await fileInput.count() > 0;
          
          if (hasFileInput) {
            const isEnabled = await fileInput.first().isEnabled();
            return isEnabled;
          }
          
          return false;
        },
        fallbackBehavior: 'manual-upload-form'
      },
      {
        name: 'drag-and-drop',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(`${context.baseUrl}/documents`);
          
          // Test drag and drop support
          const dragSupported = await page.evaluate(() => {
            const div = document.createElement('div');
            return 'draggable' in div && 'ondrop' in div && 'ondragstart' in div;
          });
          
          // Check if drop zone is present
          const dropZone = page.locator('[data-testid="drop-zone"]');
          const hasDropZone = await dropZone.count() > 0;
          
          return dragSupported && hasDropZone;
        },
        fallbackBehavior: 'click-to-upload'
      },
      {
        name: 'offline-storage',
        platforms: ['all'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          // Test IndexedDB support
          const indexedDBSupported = await page.evaluate(() => {
            return typeof indexedDB !== 'undefined';
          });
          
          // Test localStorage support
          const localStorageSupported = await page.evaluate(() => {
            try {
              localStorage.setItem('test', 'test');
              localStorage.removeItem('test');
              return true;
            } catch (e) {
              return false;
            }
          });
          
          return indexedDBSupported && localStorageSupported;
        },
        fallbackBehavior: 'server-only-storage'
      },
      {
        name: 'service-worker',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const serviceWorkerSupported = await page.evaluate(() => {
            return 'serviceWorker' in navigator;
          });
          
          return serviceWorkerSupported;
        },
        fallbackBehavior: 'no-offline-caching'
      },
      {
        name: 'push-notifications',
        platforms: ['Chrome', 'Firefox', 'Edge'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const pushSupported = await page.evaluate(() => {
            return 'PushManager' in window && 'Notification' in window;
          });
          
          return pushSupported;
        },
        fallbackBehavior: 'email-notifications'
      },
      {
        name: 'web-share-api',
        platforms: ['Chrome', 'Safari', 'Edge'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const webShareSupported = await page.evaluate(() => {
            return 'share' in navigator;
          });
          
          return webShareSupported;
        },
        fallbackBehavior: 'copy-to-clipboard'
      },
      {
        name: 'clipboard-api',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const clipboardSupported = await page.evaluate(() => {
            return 'clipboard' in navigator && 'writeText' in navigator.clipboard;
          });
          
          return clipboardSupported;
        },
        fallbackBehavior: 'manual-copy-instruction'
      },
      {
        name: 'fullscreen-api',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const fullscreenSupported = await page.evaluate(() => {
            return 'requestFullscreen' in document.documentElement ||
                   'webkitRequestFullscreen' in document.documentElement ||
                   'mozRequestFullScreen' in document.documentElement ||
                   'msRequestFullscreen' in document.documentElement;
          });
          
          return fullscreenSupported;
        },
        fallbackBehavior: 'maximize-window'
      },
      {
        name: 'geolocation',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const geolocationSupported = await page.evaluate(() => {
            return 'geolocation' in navigator;
          });
          
          return geolocationSupported;
        },
        fallbackBehavior: 'manual-location-input'
      },
      {
        name: 'camera-access',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const cameraSupported = await page.evaluate(() => {
            return 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices;
          });
          
          return cameraSupported;
        },
        fallbackBehavior: 'file-upload-only'
      },
      {
        name: 'webgl',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const webglSupported = await page.evaluate(() => {
            try {
              const canvas = document.createElement('canvas');
              const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
              return !!gl;
            } catch (e) {
              return false;
            }
          });
          
          return webglSupported;
        },
        fallbackBehavior: 'canvas-2d-rendering'
      },
      {
        name: 'web-workers',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const webWorkersSupported = await page.evaluate(() => {
            return typeof Worker !== 'undefined';
          });
          
          return webWorkersSupported;
        },
        fallbackBehavior: 'main-thread-processing'
      },
      {
        name: 'websockets',
        platforms: ['Chrome', 'Firefox', 'Edge', 'Safari'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const websocketsSupported = await page.evaluate(() => {
            return typeof WebSocket !== 'undefined';
          });
          
          return websocketsSupported;
        },
        fallbackBehavior: 'polling-updates'
      },
      {
        name: 'css-grid',
        platforms: ['all'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const cssGridSupported = await page.evaluate(() => {
            return CSS.supports('display', 'grid');
          });
          
          return cssGridSupported;
        },
        fallbackBehavior: 'flexbox-layout'
      },
      {
        name: 'css-custom-properties',
        platforms: ['all'],
        testFunction: async (context: TestContext): Promise<boolean> => {
          const { page } = context;
          await page.goto(context.baseUrl);
          
          const customPropsSupported = await page.evaluate(() => {
            return CSS.supports('color', 'var(--test)');
          });
          
          return customPropsSupported;
        },
        fallbackBehavior: 'static-css-values'
      }
    ];
  }

  getResults(): FeatureTestResult[] {
    return this.testResults;
  }

  generateReport(): string {
    const totalFeatures = this.testResults.length;
    const supportedFeatures = this.testResults.filter(r => r.supported).length;
    const featuresWithFallback = this.testResults.filter(r => !r.supported && r.fallbackAvailable).length;
    const unsupportedFeatures = this.testResults.filter(r => !r.supported && !r.fallbackAvailable).length;
    
    let report = `\n=== Platform Feature Compatibility Report ===\n`;
    report += `Platform: ${this.testResults[0]?.platform || 'Unknown'}\n`;
    report += `Total Features Tested: ${totalFeatures}\n`;
    report += `Natively Supported: ${supportedFeatures}\n`;
    report += `Supported with Fallback: ${featuresWithFallback}\n`;
    report += `Unsupported: ${unsupportedFeatures}\n`;
    report += `Overall Compatibility: ${(((supportedFeatures + featuresWithFallback) / totalFeatures) * 100).toFixed(2)}%\n\n`;
    
    // Group by support status
    const nativelySupported = this.testResults.filter(r => r.supported);
    const withFallback = this.testResults.filter(r => !r.supported && r.fallbackAvailable);
    const unsupported = this.testResults.filter(r => !r.supported && !r.fallbackAvailable);
    
    if (nativelySupported.length > 0) {
      report += `Natively Supported Features:\n`;
      nativelySupported.forEach(result => {
        report += `  ✓ ${result.featureName}\n`;
      });
      report += '\n';
    }
    
    if (withFallback.length > 0) {
      report += `Features with Fallback Support:\n`;
      withFallback.forEach(result => {
        report += `  ⚠ ${result.featureName} (fallback available)\n`;
      });
      report += '\n';
    }
    
    if (unsupported.length > 0) {
      report += `Unsupported Features:\n`;
      unsupported.forEach(result => {
        report += `  ✗ ${result.featureName}`;
        if (result.error) {
          report += ` - ${result.error}`;
        }
        report += '\n';
      });
      report += '\n';
    }
    
    // Performance impact summary
    const featuresWithPerformanceData = this.testResults.filter(r => r.performanceImpact);
    if (featuresWithPerformanceData.length > 0) {
      report += `Performance Impact:\n`;
      featuresWithPerformanceData.forEach(result => {
        report += `  ${result.featureName}: ${result.performanceImpact}ms\n`;
      });
      report += '\n';
    }
    
    return report;
  }
}