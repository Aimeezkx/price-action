/**
 * Main cross-platform compatibility test runner
 */

import { BrowserCompatibilityTester } from './browser-compatibility-tester';
import { IOSDeviceSimulator } from './ios-device-simulator';
import { DataSyncTester } from './data-sync-tester';
import { ResponsiveDesignValidator } from './responsive-design-validator';
import { PlatformFeatureTester } from './platform-feature-tester';
import { TestResult, SyncTestResult, ResponsiveTestResult } from './types';
import { chromium, firefox, webkit } from 'playwright';

interface CrossPlatformTestResults {
  browserCompatibility: TestResult[];
  iosCompatibility: TestResult[];
  dataSync: SyncTestResult[];
  responsiveDesign: ResponsiveTestResult[];
  platformFeatures: Map<string, any[]>;
  summary: {
    totalTests: number;
    passedTests: number;
    failedTests: number;
    successRate: number;
    duration: number;
  };
}

export class CrossPlatformTestRunner {
  private browserTester: BrowserCompatibilityTester;
  private iosSimulator: IOSDeviceSimulator;
  private syncTester: DataSyncTester;
  private responsiveValidator: ResponsiveDesignValidator;
  private featureTester: PlatformFeatureTester;

  constructor() {
    this.browserTester = new BrowserCompatibilityTester();
    this.iosSimulator = new IOSDeviceSimulator();
    this.syncTester = new DataSyncTester();
    this.responsiveValidator = new ResponsiveDesignValidator();
    this.featureTester = new PlatformFeatureTester();
  }

  async runAllTests(baseUrl: string = 'http://localhost:3000'): Promise<CrossPlatformTestResults> {
    console.log('Starting comprehensive cross-platform compatibility tests...');
    const startTime = Date.now();

    const results: CrossPlatformTestResults = {
      browserCompatibility: [],
      iosCompatibility: [],
      dataSync: [],
      responsiveDesign: [],
      platformFeatures: new Map(),
      summary: {
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        successRate: 0,
        duration: 0
      }
    };

    try {
      // 1. Browser Compatibility Tests
      console.log('\n=== Running Browser Compatibility Tests ===');
      await this.browserTester.initialize();
      results.browserCompatibility = await this.browserTester.runCompatibilityTests(baseUrl);
      await this.browserTester.cleanup();

      // 2. iOS Device Simulation Tests
      console.log('\n=== Running iOS Device Compatibility Tests ===');
      await this.iosSimulator.initialize();
      results.iosCompatibility = await this.iosSimulator.runIOSCompatibilityTests(baseUrl);
      await this.iosSimulator.cleanup();

      // 3. Data Synchronization Tests
      console.log('\n=== Running Data Synchronization Tests ===');
      const browsers = [
        { name: 'Chrome', browser: await chromium.launch() },
        { name: 'Firefox', browser: await firefox.launch() }
      ];
      
      await this.syncTester.initializePlatforms(browsers);
      results.dataSync = await this.syncTester.runSyncTests(baseUrl);
      await this.syncTester.cleanup();
      
      // Cleanup browsers
      for (const { browser } of browsers) {
        await browser.close();
      }

      // 4. Responsive Design Tests
      console.log('\n=== Running Responsive Design Tests ===');
      const testBrowser = await chromium.launch();
      const testPage = await testBrowser.newPage();
      results.responsiveDesign = await this.responsiveValidator.runResponsiveTests(testPage, baseUrl);
      await testBrowser.close();

      // 5. Platform-Specific Feature Tests
      console.log('\n=== Running Platform Feature Tests ===');
      const platforms = ['Chrome', 'Firefox', 'Safari', 'Edge'];
      
      for (const platform of platforms) {
        let browser;
        switch (platform) {
          case 'Chrome':
          case 'Edge':
            browser = await chromium.launch();
            break;
          case 'Firefox':
            browser = await firefox.launch();
            break;
          case 'Safari':
            browser = await webkit.launch();
            break;
          default:
            continue;
        }

        const page = await browser.newPage();
        const featureResults = await this.featureTester.runFeatureTests(page, platform, baseUrl);
        results.platformFeatures.set(platform, featureResults);
        await browser.close();
      }

      // Calculate summary
      results.summary = this.calculateSummary(results);
      results.summary.duration = Date.now() - startTime;

      console.log('\n=== Cross-Platform Tests Completed ===');
      console.log(`Total Duration: ${results.summary.duration}ms`);
      console.log(`Success Rate: ${results.summary.successRate.toFixed(2)}%`);

    } catch (error) {
      console.error('Error during cross-platform testing:', error);
      throw error;
    }

    return results;
  }

  async runBrowserCompatibilityOnly(baseUrl: string = 'http://localhost:3000'): Promise<TestResult[]> {
    console.log('Running browser compatibility tests only...');
    
    await this.browserTester.initialize();
    const results = await this.browserTester.runCompatibilityTests(baseUrl);
    await this.browserTester.cleanup();
    
    return results;
  }

  async runIOSCompatibilityOnly(baseUrl: string = 'http://localhost:3000'): Promise<TestResult[]> {
    console.log('Running iOS compatibility tests only...');
    
    await this.iosSimulator.initialize();
    const results = await this.iosSimulator.runIOSCompatibilityTests(baseUrl);
    await this.iosSimulator.cleanup();
    
    return results;
  }

  async runDataSyncOnly(baseUrl: string = 'http://localhost:3000'): Promise<SyncTestResult[]> {
    console.log('Running data synchronization tests only...');
    
    const browsers = [
      { name: 'Chrome', browser: await chromium.launch() },
      { name: 'Firefox', browser: await firefox.launch() }
    ];
    
    await this.syncTester.initializePlatforms(browsers);
    const results = await this.syncTester.runSyncTests(baseUrl);
    await this.syncTester.cleanup();
    
    // Cleanup browsers
    for (const { browser } of browsers) {
      await browser.close();
    }
    
    return results;
  }

  async runResponsiveDesignOnly(baseUrl: string = 'http://localhost:3000'): Promise<ResponsiveTestResult[]> {
    console.log('Running responsive design tests only...');
    
    const browser = await chromium.launch();
    const page = await browser.newPage();
    const results = await this.responsiveValidator.runResponsiveTests(page, baseUrl);
    await browser.close();
    
    return results;
  }

  private calculateSummary(results: CrossPlatformTestResults) {
    let totalTests = 0;
    let passedTests = 0;

    // Browser compatibility results
    totalTests += results.browserCompatibility.length;
    passedTests += results.browserCompatibility.filter(r => r.status === 'passed').length;

    // iOS compatibility results
    totalTests += results.iosCompatibility.length;
    passedTests += results.iosCompatibility.filter(r => r.status === 'passed').length;

    // Data sync results
    totalTests += results.dataSync.length;
    passedTests += results.dataSync.filter(r => r.dataConsistency).length;

    // Responsive design results
    totalTests += results.responsiveDesign.length;
    passedTests += results.responsiveDesign.filter(r => 
      r.layoutValid && r.elementsVisible && r.interactionsWorking
    ).length;

    // Platform feature results
    for (const [, featureResults] of results.platformFeatures) {
      totalTests += featureResults.length;
      passedTests += featureResults.filter((r: any) => r.status === 'passed').length;
    }

    const failedTests = totalTests - passedTests;
    const successRate = totalTests > 0 ? (passedTests / totalTests) * 100 : 0;

    return {
      totalTests,
      passedTests,
      failedTests,
      successRate,
      duration: 0 // Will be set by caller
    };
  }

  generateComprehensiveReport(results: CrossPlatformTestResults): string {
    let report = `\n${'='.repeat(60)}\n`;
    report += `CROSS-PLATFORM COMPATIBILITY TEST REPORT\n`;
    report += `${'='.repeat(60)}\n\n`;

    // Summary
    report += `SUMMARY:\n`;
    report += `Total Tests: ${results.summary.totalTests}\n`;
    report += `Passed: ${results.summary.passedTests}\n`;
    report += `Failed: ${results.summary.failedTests}\n`;
    report += `Success Rate: ${results.summary.successRate.toFixed(2)}%\n`;
    report += `Duration: ${(results.summary.duration / 1000).toFixed(2)}s\n\n`;

    // Browser Compatibility Report
    if (results.browserCompatibility.length > 0) {
      report += this.browserTester.generateReport();
    }

    // iOS Compatibility Report
    if (results.iosCompatibility.length > 0) {
      report += this.iosSimulator.generateReport();
    }

    // Data Sync Report
    if (results.dataSync.length > 0) {
      report += this.syncTester.generateReport();
    }

    // Responsive Design Report
    if (results.responsiveDesign.length > 0) {
      report += this.responsiveValidator.generateReport();
    }

    // Platform Feature Reports
    if (results.platformFeatures.size > 0) {
      report += `\n=== Platform Feature Compatibility Reports ===\n`;
      for (const [platform, featureResults] of results.platformFeatures) {
        // Create a temporary feature tester to generate the report
        const tempTester = new PlatformFeatureTester();
        (tempTester as any).testResults = featureResults;
        report += tempTester.generateReport();
      }
    }

    // Recommendations
    report += this.generateRecommendations(results);

    return report;
  }

  private generateRecommendations(results: CrossPlatformTestResults): string {
    let recommendations = `\n=== RECOMMENDATIONS ===\n`;

    const failedBrowserTests = results.browserCompatibility.filter(r => r.status === 'failed');
    const failedIOSTests = results.iosCompatibility.filter(r => r.status === 'failed');
    const failedSyncTests = results.dataSync.filter(r => !r.dataConsistency);
    const failedResponsiveTests = results.responsiveDesign.filter(r => 
      !r.layoutValid || !r.elementsVisible || !r.interactionsWorking
    );

    if (failedBrowserTests.length > 0) {
      recommendations += `\nBrowser Compatibility Issues:\n`;
      const browserIssues = failedBrowserTests.reduce((acc, test) => {
        const browser = test.browser || test.platform;
        if (!acc[browser]) acc[browser] = [];
        acc[browser].push(test.testName);
        return acc;
      }, {} as Record<string, string[]>);

      for (const [browser, issues] of Object.entries(browserIssues)) {
        recommendations += `- ${browser}: Consider polyfills or alternative implementations for ${issues.join(', ')}\n`;
      }
    }

    if (failedIOSTests.length > 0) {
      recommendations += `\niOS Compatibility Issues:\n`;
      recommendations += `- Consider iOS-specific optimizations and touch-friendly interfaces\n`;
      recommendations += `- Test viewport meta tags and touch event handling\n`;
    }

    if (failedSyncTests.length > 0) {
      recommendations += `\nData Synchronization Issues:\n`;
      recommendations += `- Implement robust conflict resolution mechanisms\n`;
      recommendations += `- Consider offline-first architecture with eventual consistency\n`;
      recommendations += `- Add retry logic for failed sync operations\n`;
    }

    if (failedResponsiveTests.length > 0) {
      recommendations += `\nResponsive Design Issues:\n`;
      recommendations += `- Review CSS media queries and breakpoint definitions\n`;
      recommendations += `- Ensure touch targets meet minimum size requirements (44px)\n`;
      recommendations += `- Test layout on actual devices, not just browser simulation\n`;
    }

    // Feature-specific recommendations
    let unsupportedFeatures: string[] = [];
    for (const [platform, featureResults] of results.platformFeatures) {
      const unsupported = featureResults.filter((r: any) => !r.supported && !r.fallbackAvailable);
      unsupportedFeatures = unsupportedFeatures.concat(
        unsupported.map((r: any) => `${r.featureName} (${platform})`)
      );
    }

    if (unsupportedFeatures.length > 0) {
      recommendations += `\nUnsupported Features:\n`;
      recommendations += `- Consider implementing fallbacks for: ${unsupportedFeatures.join(', ')}\n`;
      recommendations += `- Use progressive enhancement approach\n`;
    }

    if (results.summary.successRate < 90) {
      recommendations += `\nGeneral Recommendations:\n`;
      recommendations += `- Success rate is below 90%. Consider prioritizing cross-platform compatibility\n`;
      recommendations += `- Implement feature detection and graceful degradation\n`;
      recommendations += `- Add more comprehensive error handling\n`;
    }

    return recommendations;
  }
}