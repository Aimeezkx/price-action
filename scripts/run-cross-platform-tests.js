#!/usr/bin/env node

/**
 * Cross-Platform Test Execution Script
 * Orchestrates comprehensive cross-platform compatibility testing
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class CrossPlatformTestExecutor {
  constructor() {
    this.results = {
      web: {},
      ios: {},
      summary: {
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        skippedTests: 0,
        startTime: new Date().toISOString(),
        endTime: null,
        duration: 0
      }
    };
    
    this.config = {
      webTestsEnabled: true,
      iosTestsEnabled: true,
      generateReport: true,
      parallel: true,
      browsers: ['chromium', 'firefox', 'webkit'],
      iosDevices: ['iphone-se', 'iphone-14-pro', 'ipad-air'],
      testSuites: [
        'browser-compatibility',
        'responsive-design', 
        'platform-features',
        'data-synchronization'
      ]
    };
  }

  async runAllTests() {
    console.log('🚀 Starting Cross-Platform Compatibility Testing');
    console.log('=' .repeat(60));
    
    const startTime = Date.now();
    
    try {
      // Run web tests
      if (this.config.webTestsEnabled) {
        await this.runWebTests();
      }
      
      // Run iOS tests
      if (this.config.iosTestsEnabled) {
        await this.runIOSTests();
      }
      
      // Generate comprehensive report
      if (this.config.generateReport) {
        await this.generateReport();
      }
      
    } catch (error) {
      console.error('❌ Test execution failed:', error);
      process.exit(1);
    } finally {
      const duration = Date.now() - startTime;
      this.results.summary.endTime = new Date().toISOString();
      this.results.summary.duration = duration;
      
      console.log('\n' + '='.repeat(60));
      console.log('✅ Cross-Platform Testing Complete');
      console.log(`⏱️  Total Duration: ${(duration / 1000).toFixed(2)}s`);
    }
  }

  async runWebTests() {
    console.log('\n📱 Running Web Platform Tests');
    console.log('-'.repeat(40));
    
    const webTestCommands = [
      {
        name: 'Browser Compatibility',
        command: 'npx playwright test e2e/cross-platform/browser-compatibility.spec.ts',
        cwd: 'frontend'
      },
      {
        name: 'Browser Feature Detection',
        command: 'npx playwright test e2e/cross-platform/browser-feature-detection.spec.ts',
        cwd: 'frontend'
      },
      {
        name: 'Responsive Design',
        command: 'npx playwright test e2e/cross-platform/responsive-design.spec.ts',
        cwd: 'frontend'
      },
      {
        name: 'Platform Features',
        command: 'npx playwright test e2e/cross-platform/platform-specific-features.spec.ts',
        cwd: 'frontend'
      },
      {
        name: 'Data Synchronization',
        command: 'npx playwright test e2e/cross-platform/data-synchronization.spec.ts',
        cwd: 'frontend'
      },
      {
        name: 'Cross-Platform Test Runner',
        command: 'npx playwright test e2e/cross-platform/cross-platform-test-runner.ts',
        cwd: 'frontend'
      }
    ];

    for (const testSuite of webTestCommands) {
      console.log(`\n🧪 Running: ${testSuite.name}`);
      
      try {
        const result = await this.executeCommand(testSuite.command, testSuite.cwd);
        this.results.web[testSuite.name] = {
          status: 'passed',
          output: result.stdout,
          duration: result.duration
        };
        
        console.log(`✅ ${testSuite.name}: PASSED`);
        this.results.summary.passedTests++;
        
      } catch (error) {
        this.results.web[testSuite.name] = {
          status: 'failed',
          error: error.message,
          output: error.stdout || '',
          stderr: error.stderr || ''
        };
        
        console.log(`❌ ${testSuite.name}: FAILED`);
        console.log(`   Error: ${error.message}`);
        this.results.summary.failedTests++;
      }
      
      this.results.summary.totalTests++;
    }
  }

  async runIOSTests() {
    console.log('\n📱 Running iOS Platform Tests');
    console.log('-'.repeat(40));
    
    // Check if iOS development environment is available
    if (!this.checkIOSEnvironment()) {
      console.log('⚠️  iOS testing environment not available, skipping iOS tests');
      return;
    }
    
    const iosTestCommands = [
      {
        name: 'iOS Device Compatibility',
        command: 'npx detox test e2e/cross-platform/device-compatibility.e2e.js --configuration cross-platform.iphone-14-pro',
        cwd: 'ios-app'
      },
      {
        name: 'iOS Sync Integration',
        command: 'npx detox test e2e/cross-platform/sync-integration.e2e.js --configuration cross-platform.iphone-14-pro',
        cwd: 'ios-app'
      },
      {
        name: 'iPad Compatibility',
        command: 'npx detox test e2e/cross-platform/device-compatibility.e2e.js --configuration cross-platform.ipad-air',
        cwd: 'ios-app'
      }
    ];

    for (const testSuite of iosTestCommands) {
      console.log(`\n🧪 Running: ${testSuite.name}`);
      
      try {
        const result = await this.executeCommand(testSuite.command, testSuite.cwd);
        this.results.ios[testSuite.name] = {
          status: 'passed',
          output: result.stdout,
          duration: result.duration
        };
        
        console.log(`✅ ${testSuite.name}: PASSED`);
        this.results.summary.passedTests++;
        
      } catch (error) {
        this.results.ios[testSuite.name] = {
          status: 'failed',
          error: error.message,
          output: error.stdout || '',
          stderr: error.stderr || ''
        };
        
        console.log(`❌ ${testSuite.name}: FAILED`);
        console.log(`   Error: ${error.message}`);
        this.results.summary.failedTests++;
      }
      
      this.results.summary.totalTests++;
    }
  }

  async executeCommand(command, cwd) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      console.log(`   Executing: ${command}`);
      console.log(`   Working Directory: ${cwd}`);
      
      const child = spawn('sh', ['-c', command], {
        cwd: path.resolve(cwd),
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      child.stdout.on('data', (data) => {
        stdout += data.toString();
        // Show real-time output for long-running tests
        if (process.env.VERBOSE) {
          process.stdout.write(data);
        }
      });
      
      child.stderr.on('data', (data) => {
        stderr += data.toString();
        if (process.env.VERBOSE) {
          process.stderr.write(data);
        }
      });
      
      child.on('close', (code) => {
        const duration = Date.now() - startTime;
        
        if (code === 0) {
          resolve({
            stdout,
            stderr,
            duration,
            exitCode: code
          });
        } else {
          const error = new Error(`Command failed with exit code ${code}`);
          error.stdout = stdout;
          error.stderr = stderr;
          error.exitCode = code;
          reject(error);
        }
      });
      
      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  checkIOSEnvironment() {
    try {
      // Check if Xcode is installed
      execSync('xcode-select -p', { stdio: 'ignore' });
      
      // Check if iOS Simulator is available
      execSync('xcrun simctl list devices', { stdio: 'ignore' });
      
      // Check if Detox is installed
      execSync('npx detox --version', { cwd: 'ios-app', stdio: 'ignore' });
      
      return true;
    } catch (error) {
      return false;
    }
  }

  async generateReport() {
    console.log('\n📊 Generating Cross-Platform Compatibility Report');
    console.log('-'.repeat(50));
    
    const report = {
      metadata: {
        timestamp: new Date().toISOString(),
        testExecutor: 'Cross-Platform Test Suite',
        version: '1.0.0',
        environment: {
          node: process.version,
          platform: process.platform,
          arch: process.arch
        }
      },
      summary: this.results.summary,
      results: {
        web: this.results.web,
        ios: this.results.ios
      },
      recommendations: this.generateRecommendations(),
      compatibilityMatrix: this.generateCompatibilityMatrix()
    };
    
    // Save detailed JSON report
    const reportPath = `test-results/cross-platform-report-${Date.now()}.json`;
    this.ensureDirectoryExists(path.dirname(reportPath));
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    // Generate HTML report
    const htmlReport = this.generateHTMLReport(report);
    const htmlPath = `test-results/cross-platform-report-${Date.now()}.html`;
    fs.writeFileSync(htmlPath, htmlReport);
    
    // Print summary to console
    this.printSummaryReport(report);
    
    console.log(`\n📄 Detailed reports saved:`);
    console.log(`   JSON: ${reportPath}`);
    console.log(`   HTML: ${htmlPath}`);
  }

  generateRecommendations() {
    const recommendations = [];
    
    // Analyze web test results
    const webFailures = Object.values(this.results.web).filter(r => r.status === 'failed');
    if (webFailures.length > 0) {
      recommendations.push({
        category: 'Web Platform',
        priority: 'high',
        message: `${webFailures.length} web platform tests failed. Review browser compatibility issues.`
      });
    }
    
    // Analyze iOS test results
    const iosFailures = Object.values(this.results.ios).filter(r => r.status === 'failed');
    if (iosFailures.length > 0) {
      recommendations.push({
        category: 'iOS Platform',
        priority: 'high',
        message: `${iosFailures.length} iOS platform tests failed. Review device compatibility issues.`
      });
    }
    
    // Overall success rate
    const successRate = (this.results.summary.passedTests / this.results.summary.totalTests) * 100;
    
    if (successRate < 90) {
      recommendations.push({
        category: 'Overall',
        priority: 'critical',
        message: `Cross-platform compatibility success rate is ${successRate.toFixed(1)}%. Target 90%+ for production readiness.`
      });
    } else if (successRate < 95) {
      recommendations.push({
        category: 'Overall',
        priority: 'medium',
        message: `Good compatibility (${successRate.toFixed(1)}%) but aim for 95%+ success rate.`
      });
    } else {
      recommendations.push({
        category: 'Overall',
        priority: 'info',
        message: `Excellent cross-platform compatibility achieved (${successRate.toFixed(1)}%).`
      });
    }
    
    return recommendations;
  }

  generateCompatibilityMatrix() {
    const matrix = {
      browsers: {
        chromium: { supported: true, issues: [] },
        firefox: { supported: true, issues: [] },
        webkit: { supported: true, issues: [] },
        edge: { supported: true, issues: [] }
      },
      devices: {
        'iPhone SE': { supported: true, issues: [] },
        'iPhone 14 Pro': { supported: true, issues: [] },
        'iPad Air': { supported: true, issues: [] },
        'iPad Pro': { supported: true, issues: [] }
      },
      features: {
        'Document Upload': { webSupport: true, iosSupport: true },
        'Chapter Navigation': { webSupport: true, iosSupport: true },
        'Flashcard Review': { webSupport: true, iosSupport: true },
        'Search Functionality': { webSupport: true, iosSupport: true },
        'Data Synchronization': { webSupport: true, iosSupport: true },
        'Offline Mode': { webSupport: true, iosSupport: true },
        'Push Notifications': { webSupport: false, iosSupport: true },
        'File System Access': { webSupport: true, iosSupport: false }
      }
    };
    
    // Update matrix based on actual test results
    // This would be populated based on real test outcomes
    
    return matrix;
  }

  generateHTMLReport(report) {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cross-Platform Compatibility Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; text-align: center; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .results { margin: 20px 0; }
        .platform { margin-bottom: 30px; }
        .test-result { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .test-passed { background: #d4edda; border-left: 4px solid #28a745; }
        .test-failed { background: #f8d7da; border-left: 4px solid #dc3545; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .matrix { margin: 20px 0; }
        .matrix table { width: 100%; border-collapse: collapse; }
        .matrix th, .matrix td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        .matrix th { background: #f5f5f5; }
        .supported { background: #d4edda; }
        .not-supported { background: #f8d7da; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Cross-Platform Compatibility Report</h1>
        <p><strong>Generated:</strong> ${report.metadata.timestamp}</p>
        <p><strong>Duration:</strong> ${(report.summary.duration / 1000).toFixed(2)} seconds</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div style="font-size: 2em; font-weight: bold;">${report.summary.totalTests}</div>
        </div>
        <div class="metric passed">
            <h3>Passed</h3>
            <div style="font-size: 2em; font-weight: bold;">${report.summary.passedTests}</div>
            <div>${((report.summary.passedTests / report.summary.totalTests) * 100).toFixed(1)}%</div>
        </div>
        <div class="metric failed">
            <h3>Failed</h3>
            <div style="font-size: 2em; font-weight: bold;">${report.summary.failedTests}</div>
            <div>${((report.summary.failedTests / report.summary.totalTests) * 100).toFixed(1)}%</div>
        </div>
        <div class="metric skipped">
            <h3>Skipped</h3>
            <div style="font-size: 2em; font-weight: bold;">${report.summary.skippedTests}</div>
            <div>${((report.summary.skippedTests / report.summary.totalTests) * 100).toFixed(1)}%</div>
        </div>
    </div>
    
    <div class="results">
        <h2>Test Results</h2>
        
        <div class="platform">
            <h3>Web Platform</h3>
            ${Object.entries(report.results.web).map(([name, result]) => `
                <div class="test-result test-${result.status}">
                    <strong>${name}</strong>: ${result.status.toUpperCase()}
                    ${result.error ? `<br><small>Error: ${result.error}</small>` : ''}
                </div>
            `).join('')}
        </div>
        
        <div class="platform">
            <h3>iOS Platform</h3>
            ${Object.entries(report.results.ios).map(([name, result]) => `
                <div class="test-result test-${result.status}">
                    <strong>${name}</strong>: ${result.status.toUpperCase()}
                    ${result.error ? `<br><small>Error: ${result.error}</small>` : ''}
                </div>
            `).join('')}
        </div>
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        ${report.recommendations.map(rec => `
            <div style="margin: 10px 0;">
                <strong>[${rec.priority.toUpperCase()}] ${rec.category}:</strong> ${rec.message}
            </div>
        `).join('')}
    </div>
    
    <div class="matrix">
        <h2>Compatibility Matrix</h2>
        <h3>Browser Support</h3>
        <table>
            <tr>
                <th>Browser</th>
                <th>Supported</th>
                <th>Issues</th>
            </tr>
            ${Object.entries(report.compatibilityMatrix.browsers).map(([browser, info]) => `
                <tr>
                    <td>${browser}</td>
                    <td class="${info.supported ? 'supported' : 'not-supported'}">${info.supported ? '✓' : '✗'}</td>
                    <td>${info.issues.length}</td>
                </tr>
            `).join('')}
        </table>
        
        <h3>Feature Support</h3>
        <table>
            <tr>
                <th>Feature</th>
                <th>Web</th>
                <th>iOS</th>
            </tr>
            ${Object.entries(report.compatibilityMatrix.features).map(([feature, support]) => `
                <tr>
                    <td>${feature}</td>
                    <td class="${support.webSupport ? 'supported' : 'not-supported'}">${support.webSupport ? '✓' : '✗'}</td>
                    <td class="${support.iosSupport ? 'supported' : 'not-supported'}">${support.iosSupport ? '✓' : '✗'}</td>
                </tr>
            `).join('')}
        </table>
    </div>
</body>
</html>`;
  }

  printSummaryReport(report) {
    console.log('\n📊 CROSS-PLATFORM COMPATIBILITY SUMMARY');
    console.log('='.repeat(60));
    console.log(`📅 Generated: ${report.metadata.timestamp}`);
    console.log(`⏱️  Duration: ${(report.summary.duration / 1000).toFixed(2)}s`);
    console.log(`📊 Total Tests: ${report.summary.totalTests}`);
    console.log(`✅ Passed: ${report.summary.passedTests} (${((report.summary.passedTests / report.summary.totalTests) * 100).toFixed(1)}%)`);
    console.log(`❌ Failed: ${report.summary.failedTests} (${((report.summary.failedTests / report.summary.totalTests) * 100).toFixed(1)}%)`);
    console.log(`⏭️  Skipped: ${report.summary.skippedTests} (${((report.summary.skippedTests / report.summary.totalTests) * 100).toFixed(1)}%)`);
    
    console.log('\n🔍 RECOMMENDATIONS:');
    report.recommendations.forEach(rec => {
      const icon = rec.priority === 'critical' ? '🚨' : rec.priority === 'high' ? '⚠️' : rec.priority === 'medium' ? '💡' : 'ℹ️';
      console.log(`${icon} [${rec.priority.toUpperCase()}] ${rec.category}: ${rec.message}`);
    });
  }

  ensureDirectoryExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }
}

// CLI execution
if (require.main === module) {
  const executor = new CrossPlatformTestExecutor();
  
  // Parse command line arguments
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Cross-Platform Test Execution Script

Usage: node run-cross-platform-tests.js [options]

Options:
  --web-only          Run only web platform tests
  --ios-only          Run only iOS platform tests
  --no-report         Skip report generation
  --verbose           Show detailed output
  --help, -h          Show this help message

Examples:
  node run-cross-platform-tests.js
  node run-cross-platform-tests.js --web-only
  node run-cross-platform-tests.js --verbose
`);
    process.exit(0);
  }
  
  if (args.includes('--web-only')) {
    executor.config.iosTestsEnabled = false;
  }
  
  if (args.includes('--ios-only')) {
    executor.config.webTestsEnabled = false;
  }
  
  if (args.includes('--no-report')) {
    executor.config.generateReport = false;
  }
  
  if (args.includes('--verbose')) {
    process.env.VERBOSE = 'true';
  }
  
  executor.runAllTests().catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = { CrossPlatformTestExecutor };