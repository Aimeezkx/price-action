#!/usr/bin/env node

/**
 * Cross-platform compatibility test execution script
 */

import { CrossPlatformTestRunner } from './cross-platform-test-runner';
import * as fs from 'fs';
import * as path from 'path';

interface TestOptions {
  baseUrl?: string;
  outputDir?: string;
  testSuite?: 'all' | 'browser' | 'ios' | 'sync' | 'responsive' | 'features';
  generateReport?: boolean;
  verbose?: boolean;
}

class CrossPlatformTestExecutor {
  private runner: CrossPlatformTestRunner;
  private options: TestOptions;

  constructor(options: TestOptions = {}) {
    this.runner = new CrossPlatformTestRunner();
    this.options = {
      baseUrl: 'http://localhost:3000',
      outputDir: './test-results/cross-platform',
      testSuite: 'all',
      generateReport: true,
      verbose: false,
      ...options
    };
  }

  async execute(): Promise<void> {
    console.log('Cross-Platform Compatibility Test Suite');
    console.log('=====================================');
    console.log(`Base URL: ${this.options.baseUrl}`);
    console.log(`Test Suite: ${this.options.testSuite}`);
    console.log(`Output Directory: ${this.options.outputDir}\n`);

    // Ensure output directory exists
    this.ensureOutputDirectory();

    try {
      switch (this.options.testSuite) {
        case 'browser':
          await this.runBrowserTests();
          break;
        case 'ios':
          await this.runIOSTests();
          break;
        case 'sync':
          await this.runSyncTests();
          break;
        case 'responsive':
          await this.runResponsiveTests();
          break;
        case 'features':
          await this.runFeatureTests();
          break;
        case 'all':
        default:
          await this.runAllTests();
          break;
      }
    } catch (error) {
      console.error('Test execution failed:', error);
      process.exit(1);
    }
  }

  private async runAllTests(): Promise<void> {
    console.log('Running comprehensive cross-platform tests...\n');
    
    const results = await this.runner.runAllTests(this.options.baseUrl!);
    
    if (this.options.generateReport) {
      const report = this.runner.generateComprehensiveReport(results);
      await this.saveReport('comprehensive-report.txt', report);
      await this.saveResults('comprehensive-results.json', results);
    }

    this.printSummary(results.summary);
    
    // Exit with error code if tests failed
    if (results.summary.successRate < 100) {
      process.exit(1);
    }
  }

  private async runBrowserTests(): Promise<void> {
    console.log('Running browser compatibility tests...\n');
    
    const results = await this.runner.runBrowserCompatibilityOnly(this.options.baseUrl!);
    
    if (this.options.generateReport) {
      const report = this.generateBrowserReport(results);
      await this.saveReport('browser-compatibility-report.txt', report);
      await this.saveResults('browser-compatibility-results.json', results);
    }

    const passedTests = results.filter(r => r.status === 'passed').length;
    const successRate = (passedTests / results.length) * 100;
    
    console.log(`\nBrowser Compatibility Tests Completed:`);
    console.log(`Total: ${results.length}, Passed: ${passedTests}, Success Rate: ${successRate.toFixed(2)}%`);
    
    if (successRate < 100) {
      process.exit(1);
    }
  }

  private async runIOSTests(): Promise<void> {
    console.log('Running iOS compatibility tests...\n');
    
    const results = await this.runner.runIOSCompatibilityOnly(this.options.baseUrl!);
    
    if (this.options.generateReport) {
      const report = this.generateIOSReport(results);
      await this.saveReport('ios-compatibility-report.txt', report);
      await this.saveResults('ios-compatibility-results.json', results);
    }

    const passedTests = results.filter(r => r.status === 'passed').length;
    const successRate = (passedTests / results.length) * 100;
    
    console.log(`\niOS Compatibility Tests Completed:`);
    console.log(`Total: ${results.length}, Passed: ${passedTests}, Success Rate: ${successRate.toFixed(2)}%`);
    
    if (successRate < 100) {
      process.exit(1);
    }
  }

  private async runSyncTests(): Promise<void> {
    console.log('Running data synchronization tests...\n');
    
    const results = await this.runner.runDataSyncOnly(this.options.baseUrl!);
    
    if (this.options.generateReport) {
      const report = this.generateSyncReport(results);
      await this.saveReport('data-sync-report.txt', report);
      await this.saveResults('data-sync-results.json', results);
    }

    const passedTests = results.filter(r => r.dataConsistency).length;
    const successRate = (passedTests / results.length) * 100;
    
    console.log(`\nData Synchronization Tests Completed:`);
    console.log(`Total: ${results.length}, Passed: ${passedTests}, Success Rate: ${successRate.toFixed(2)}%`);
    
    if (successRate < 100) {
      process.exit(1);
    }
  }

  private async runResponsiveTests(): Promise<void> {
    console.log('Running responsive design tests...\n');
    
    const results = await this.runner.runResponsiveDesignOnly(this.options.baseUrl!);
    
    if (this.options.generateReport) {
      const report = this.generateResponsiveReport(results);
      await this.saveReport('responsive-design-report.txt', report);
      await this.saveResults('responsive-design-results.json', results);
    }

    const passedTests = results.filter(r => 
      r.layoutValid && r.elementsVisible && r.interactionsWorking
    ).length;
    const successRate = (passedTests / results.length) * 100;
    
    console.log(`\nResponsive Design Tests Completed:`);
    console.log(`Total: ${results.length}, Passed: ${passedTests}, Success Rate: ${successRate.toFixed(2)}%`);
    
    if (successRate < 100) {
      process.exit(1);
    }
  }

  private async runFeatureTests(): Promise<void> {
    console.log('Running platform feature tests...\n');
    
    // This would need to be implemented in the runner
    console.log('Feature-only tests not yet implemented. Use "all" to run feature tests.');
  }

  private ensureOutputDirectory(): void {
    if (!fs.existsSync(this.options.outputDir!)) {
      fs.mkdirSync(this.options.outputDir!, { recursive: true });
    }
  }

  private async saveReport(filename: string, content: string): Promise<void> {
    const filePath = path.join(this.options.outputDir!, filename);
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Report saved to: ${filePath}`);
  }

  private async saveResults(filename: string, results: any): Promise<void> {
    const filePath = path.join(this.options.outputDir!, filename);
    fs.writeFileSync(filePath, JSON.stringify(results, null, 2), 'utf8');
    console.log(`Results saved to: ${filePath}`);
  }

  private generateBrowserReport(results: any[]): string {
    // Use the browser tester's report generation
    const tester = new (require('./browser-compatibility-tester').BrowserCompatibilityTester)();
    (tester as any).testResults = results;
    return tester.generateReport();
  }

  private generateIOSReport(results: any[]): string {
    // Use the iOS simulator's report generation
    const simulator = new (require('./ios-device-simulator').IOSDeviceSimulator)();
    (simulator as any).testResults = results;
    return simulator.generateReport();
  }

  private generateSyncReport(results: any[]): string {
    // Use the sync tester's report generation
    const tester = new (require('./data-sync-tester').DataSyncTester)();
    (tester as any).testResults = results;
    return tester.generateReport();
  }

  private generateResponsiveReport(results: any[]): string {
    // Use the responsive validator's report generation
    const validator = new (require('./responsive-design-validator').ResponsiveDesignValidator)();
    (validator as any).testResults = results;
    return validator.generateReport();
  }

  private printSummary(summary: any): void {
    console.log('\n' + '='.repeat(50));
    console.log('TEST EXECUTION SUMMARY');
    console.log('='.repeat(50));
    console.log(`Total Tests: ${summary.totalTests}`);
    console.log(`Passed: ${summary.passedTests}`);
    console.log(`Failed: ${summary.failedTests}`);
    console.log(`Success Rate: ${summary.successRate.toFixed(2)}%`);
    console.log(`Duration: ${(summary.duration / 1000).toFixed(2)}s`);
    console.log('='.repeat(50));
  }
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const options: TestOptions = {};

  // Parse command line arguments
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--base-url':
        options.baseUrl = args[++i];
        break;
      case '--output-dir':
        options.outputDir = args[++i];
        break;
      case '--test-suite':
        options.testSuite = args[++i] as any;
        break;
      case '--no-report':
        options.generateReport = false;
        break;
      case '--verbose':
        options.verbose = true;
        break;
      case '--help':
        console.log(`
Cross-Platform Compatibility Test Runner

Usage: node run-cross-platform-tests.js [options]

Options:
  --base-url <url>        Base URL for testing (default: http://localhost:3000)
  --output-dir <dir>      Output directory for reports (default: ./test-results/cross-platform)
  --test-suite <suite>    Test suite to run: all|browser|ios|sync|responsive|features (default: all)
  --no-report            Skip report generation
  --verbose              Enable verbose output
  --help                 Show this help message

Examples:
  node run-cross-platform-tests.js
  node run-cross-platform-tests.js --test-suite browser
  node run-cross-platform-tests.js --base-url http://localhost:8080 --output-dir ./reports
        `);
        process.exit(0);
    }
  }

  const executor = new CrossPlatformTestExecutor(options);
  executor.execute().catch(error => {
    console.error('Execution failed:', error);
    process.exit(1);
  });
}

export { CrossPlatformTestExecutor };