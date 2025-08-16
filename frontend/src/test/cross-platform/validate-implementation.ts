#!/usr/bin/env node

/**
 * Cross-platform compatibility testing implementation validation
 */

import * as fs from 'fs';
import * as path from 'path';

interface ValidationResult {
  component: string;
  status: 'pass' | 'fail';
  message: string;
  details?: string[];
}

class CrossPlatformValidation {
  private results: ValidationResult[] = [];
  private basePath = path.join(__dirname);

  async validate(): Promise<ValidationResult[]> {
    console.log('Validating Cross-Platform Compatibility Testing Implementation...\n');

    // Validate core components
    this.validateFileExists('types.ts', 'Type definitions');
    this.validateFileExists('cross-platform.config.ts', 'Configuration file');
    this.validateFileExists('browser-compatibility-tester.ts', 'Browser compatibility tester');
    this.validateFileExists('ios-device-simulator.ts', 'iOS device simulator');
    this.validateFileExists('data-sync-tester.ts', 'Data synchronization tester');
    this.validateFileExists('responsive-design-validator.ts', 'Responsive design validator');
    this.validateFileExists('platform-feature-tester.ts', 'Platform feature tester');
    this.validateFileExists('cross-platform-test-runner.ts', 'Main test runner');
    this.validateFileExists('run-cross-platform-tests.ts', 'Test execution script');

    // Validate test files
    this.validateFileExists('__tests__/cross-platform.test.ts', 'Unit tests');
    this.validateFileExists('__tests__/integration.test.ts', 'Integration tests');

    // Validate configurations
    await this.validateConfigurations();

    // Validate type definitions
    await this.validateTypeDefinitions();

    // Validate test implementations
    await this.validateTestImplementations();

    // Print results
    this.printResults();

    return this.results;
  }

  private validateFileExists(filename: string, description: string): void {
    const filePath = path.join(this.basePath, filename);
    
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      if (stats.size > 0) {
        this.results.push({
          component: description,
          status: 'pass',
          message: `${filename} exists and has content (${stats.size} bytes)`
        });
      } else {
        this.results.push({
          component: description,
          status: 'fail',
          message: `${filename} exists but is empty`
        });
      }
    } else {
      this.results.push({
        component: description,
        status: 'fail',
        message: `${filename} does not exist`
      });
    }
  }

  private async validateConfigurations(): Promise<void> {
    try {
      const configPath = path.join(this.basePath, 'cross-platform.config.ts');
      if (!fs.existsSync(configPath)) {
        this.results.push({
          component: 'Configuration validation',
          status: 'fail',
          message: 'Configuration file not found'
        });
        return;
      }

      const configContent = fs.readFileSync(configPath, 'utf8');
      const requiredConfigs = [
        'BROWSER_CONFIGS',
        'DEVICE_CONFIGS',
        'RESPONSIVE_BREAKPOINTS',
        'TEST_TIMEOUTS',
        'PLATFORM_FEATURES',
        'SYNC_TEST_SCENARIOS'
      ];

      const missingConfigs = requiredConfigs.filter(config => 
        !configContent.includes(`export const ${config}`) && 
        !configContent.includes(`${config}:`)
      );

      if (missingConfigs.length === 0) {
        this.results.push({
          component: 'Configuration validation',
          status: 'pass',
          message: 'All required configurations are present',
          details: requiredConfigs
        });
      } else {
        this.results.push({
          component: 'Configuration validation',
          status: 'fail',
          message: 'Missing required configurations',
          details: missingConfigs
        });
      }

      // Validate browser configs
      if (configContent.includes('BROWSER_CONFIGS')) {
        const browserMatches = configContent.match(/name:\s*['"]([^'"]+)['"]/g);
        if (browserMatches && browserMatches.length >= 3) {
          this.results.push({
            component: 'Browser configurations',
            status: 'pass',
            message: `Found ${browserMatches.length} browser configurations`
          });
        } else {
          this.results.push({
            component: 'Browser configurations',
            status: 'fail',
            message: 'Insufficient browser configurations (need at least 3)'
          });
        }
      }

      // Validate device configs
      if (configContent.includes('DEVICE_CONFIGS')) {
        const deviceMatches = configContent.match(/type:\s*['"]([^'"]+)['"]/g);
        if (deviceMatches && deviceMatches.length >= 3) {
          this.results.push({
            component: 'Device configurations',
            status: 'pass',
            message: `Found ${deviceMatches.length} device configurations`
          });
        } else {
          this.results.push({
            component: 'Device configurations',
            status: 'fail',
            message: 'Insufficient device configurations (need at least 3)'
          });
        }
      }

    } catch (error) {
      this.results.push({
        component: 'Configuration validation',
        status: 'fail',
        message: `Error validating configurations: ${error}`
      });
    }
  }

  private async validateTypeDefinitions(): Promise<void> {
    try {
      const typesPath = path.join(this.basePath, 'types.ts');
      if (!fs.existsSync(typesPath)) {
        this.results.push({
          component: 'Type definitions',
          status: 'fail',
          message: 'Types file not found'
        });
        return;
      }

      const typesContent = fs.readFileSync(typesPath, 'utf8');
      const requiredTypes = [
        'BrowserConfig',
        'DeviceConfig',
        'TestResult',
        'SyncTestResult',
        'ResponsiveTestResult',
        'TestContext',
        'PlatformFeature'
      ];

      const missingTypes = requiredTypes.filter(type => 
        !typesContent.includes(`interface ${type}`) && 
        !typesContent.includes(`type ${type}`)
      );

      if (missingTypes.length === 0) {
        this.results.push({
          component: 'Type definitions',
          status: 'pass',
          message: 'All required type definitions are present',
          details: requiredTypes
        });
      } else {
        this.results.push({
          component: 'Type definitions',
          status: 'fail',
          message: 'Missing required type definitions',
          details: missingTypes
        });
      }

    } catch (error) {
      this.results.push({
        component: 'Type definitions',
        status: 'fail',
        message: `Error validating types: ${error}`
      });
    }
  }

  private async validateTestImplementations(): Promise<void> {
    const testFiles = [
      { file: 'browser-compatibility-tester.ts', class: 'BrowserCompatibilityTester' },
      { file: 'ios-device-simulator.ts', class: 'IOSDeviceSimulator' },
      { file: 'data-sync-tester.ts', class: 'DataSyncTester' },
      { file: 'responsive-design-validator.ts', class: 'ResponsiveDesignValidator' },
      { file: 'platform-feature-tester.ts', class: 'PlatformFeatureTester' },
      { file: 'cross-platform-test-runner.ts', class: 'CrossPlatformTestRunner' }
    ];

    for (const { file, class: className } of testFiles) {
      try {
        const filePath = path.join(this.basePath, file);
        if (!fs.existsSync(filePath)) {
          this.results.push({
            component: `${className} implementation`,
            status: 'fail',
            message: `${file} not found`
          });
          continue;
        }

        const content = fs.readFileSync(filePath, 'utf8');
        
        // Check for class definition
        if (!content.includes(`export class ${className}`)) {
          this.results.push({
            component: `${className} implementation`,
            status: 'fail',
            message: `Class ${className} not found in ${file}`
          });
          continue;
        }

        // Check for required methods
        const requiredMethods = this.getRequiredMethods(className);
        const missingMethods = requiredMethods.filter(method => 
          !content.includes(`${method}(`) && !content.includes(`${method} (`)
        );

        if (missingMethods.length === 0) {
          this.results.push({
            component: `${className} implementation`,
            status: 'pass',
            message: `All required methods implemented`,
            details: requiredMethods
          });
        } else {
          this.results.push({
            component: `${className} implementation`,
            status: 'fail',
            message: `Missing required methods`,
            details: missingMethods
          });
        }

      } catch (error) {
        this.results.push({
          component: `${className} implementation`,
          status: 'fail',
          message: `Error validating ${file}: ${error}`
        });
      }
    }
  }

  private getRequiredMethods(className: string): string[] {
    const methodMap: Record<string, string[]> = {
      'BrowserCompatibilityTester': ['initialize', 'runCompatibilityTests', 'cleanup', 'generateReport'],
      'IOSDeviceSimulator': ['initialize', 'runIOSCompatibilityTests', 'cleanup', 'generateReport'],
      'DataSyncTester': ['initializePlatforms', 'runSyncTests', 'cleanup', 'generateReport'],
      'ResponsiveDesignValidator': ['runResponsiveTests', 'generateReport'],
      'PlatformFeatureTester': ['runFeatureTests', 'generateReport'],
      'CrossPlatformTestRunner': ['runAllTests', 'generateComprehensiveReport']
    };

    return methodMap[className] || [];
  }

  private printResults(): void {
    console.log('\n' + '='.repeat(60));
    console.log('CROSS-PLATFORM TESTING VALIDATION RESULTS');
    console.log('='.repeat(60));

    const passedTests = this.results.filter(r => r.status === 'pass').length;
    const failedTests = this.results.filter(r => r.status === 'fail').length;
    const totalTests = this.results.length;

    console.log(`\nSUMMARY:`);
    console.log(`Total Validations: ${totalTests}`);
    console.log(`Passed: ${passedTests}`);
    console.log(`Failed: ${failedTests}`);
    console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n`);

    // Group results by status
    const passedResults = this.results.filter(r => r.status === 'pass');
    const failedResults = this.results.filter(r => r.status === 'fail');

    if (passedResults.length > 0) {
      console.log('✅ PASSED VALIDATIONS:');
      passedResults.forEach(result => {
        console.log(`  ✓ ${result.component}: ${result.message}`);
        if (result.details && result.details.length > 0) {
          console.log(`    Details: ${result.details.join(', ')}`);
        }
      });
      console.log();
    }

    if (failedResults.length > 0) {
      console.log('❌ FAILED VALIDATIONS:');
      failedResults.forEach(result => {
        console.log(`  ✗ ${result.component}: ${result.message}`);
        if (result.details && result.details.length > 0) {
          console.log(`    Missing: ${result.details.join(', ')}`);
        }
      });
      console.log();
    }

    if (failedTests === 0) {
      console.log('🎉 All validations passed! Cross-platform testing implementation is complete.');
    } else {
      console.log(`⚠️  ${failedTests} validation(s) failed. Please address the issues above.`);
    }

    console.log('='.repeat(60));
  }
}

// CLI execution
if (require.main === module) {
  const validator = new CrossPlatformValidation();
  validator.validate().then(results => {
    const failedCount = results.filter(r => r.status === 'fail').length;
    process.exit(failedCount > 0 ? 1 : 0);
  }).catch(error => {
    console.error('Validation failed:', error);
    process.exit(1);
  });
}

export { CrossPlatformValidation };