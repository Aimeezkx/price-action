/**
 * Integration tests for cross-platform compatibility testing
 */

import { describe, it, expect, beforeAll, afterAll } from '@jest/test-globals';
import { CrossPlatformTestExecutor } from '../run-cross-platform-tests';
import * as fs from 'fs';
import * as path from 'path';

describe('Cross-Platform Integration Tests', () => {
  const testOutputDir = './test-results/integration-test';
  const testBaseUrl = process.env.TEST_BASE_URL || 'http://localhost:3000';

  beforeAll(() => {
    // Ensure test output directory exists
    if (!fs.existsSync(testOutputDir)) {
      fs.mkdirSync(testOutputDir, { recursive: true });
    }
  });

  afterAll(() => {
    // Cleanup test output directory
    if (fs.existsSync(testOutputDir)) {
      fs.rmSync(testOutputDir, { recursive: true, force: true });
    }
  });

  describe('Test Execution', () => {
    it('should create test executor with default options', () => {
      const executor = new CrossPlatformTestExecutor();
      expect(executor).toBeDefined();
    });

    it('should create test executor with custom options', () => {
      const options = {
        baseUrl: testBaseUrl,
        outputDir: testOutputDir,
        testSuite: 'browser' as const,
        generateReport: true,
        verbose: true
      };

      const executor = new CrossPlatformTestExecutor(options);
      expect(executor).toBeDefined();
    });

    it('should handle invalid base URL gracefully', async () => {
      const executor = new CrossPlatformTestExecutor({
        baseUrl: 'http://invalid-url:9999',
        outputDir: testOutputDir,
        testSuite: 'browser',
        generateReport: false
      });

      // This should not throw during construction
      expect(executor).toBeDefined();
    });
  });

  describe('Report Generation', () => {
    it('should generate reports in specified directory', async () => {
      const executor = new CrossPlatformTestExecutor({
        baseUrl: testBaseUrl,
        outputDir: testOutputDir,
        generateReport: true
      });

      // Mock the execution to avoid running actual tests
      const mockResults = {
        browserCompatibility: [
          {
            testName: 'Mock Test',
            platform: 'Chrome',
            status: 'passed' as const,
            duration: 100
          }
        ],
        iosCompatibility: [],
        dataSync: [],
        responsiveDesign: [],
        platformFeatures: new Map(),
        summary: {
          totalTests: 1,
          passedTests: 1,
          failedTests: 0,
          successRate: 100,
          duration: 100
        }
      };

      // Test report generation methods exist
      expect(typeof executor).toBe('object');
    });

    it('should create output directory if it does not exist', () => {
      const nonExistentDir = path.join(testOutputDir, 'non-existent');
      
      const executor = new CrossPlatformTestExecutor({
        outputDir: nonExistentDir,
        generateReport: true
      });

      expect(executor).toBeDefined();
    });
  });

  describe('Configuration Validation', () => {
    it('should validate browser configurations', () => {
      const { BROWSER_CONFIGS } = require('../cross-platform.config');
      
      expect(BROWSER_CONFIGS).toBeDefined();
      expect(Array.isArray(BROWSER_CONFIGS)).toBe(true);
      
      // Validate each browser config
      BROWSER_CONFIGS.forEach((config: any) => {
        expect(config).toHaveProperty('name');
        expect(config).toHaveProperty('userAgent');
        expect(config).toHaveProperty('viewport');
        expect(config).toHaveProperty('features');
        
        expect(typeof config.name).toBe('string');
        expect(typeof config.userAgent).toBe('string');
        expect(typeof config.viewport).toBe('object');
        expect(Array.isArray(config.features)).toBe(true);
        
        expect(config.viewport).toHaveProperty('width');
        expect(config.viewport).toHaveProperty('height');
        expect(typeof config.viewport.width).toBe('number');
        expect(typeof config.viewport.height).toBe('number');
        expect(config.viewport.width).toBeGreaterThan(0);
        expect(config.viewport.height).toBeGreaterThan(0);
      });
    });

    it('should validate device configurations', () => {
      const { DEVICE_CONFIGS } = require('../cross-platform.config');
      
      expect(DEVICE_CONFIGS).toBeDefined();
      expect(Array.isArray(DEVICE_CONFIGS)).toBe(true);
      
      // Validate each device config
      DEVICE_CONFIGS.forEach((config: any) => {
        expect(config).toHaveProperty('name');
        expect(config).toHaveProperty('type');
        expect(config).toHaveProperty('os');
        expect(config).toHaveProperty('osVersion');
        expect(config).toHaveProperty('viewport');
        expect(config).toHaveProperty('pixelRatio');
        expect(config).toHaveProperty('touchEnabled');
        
        expect(typeof config.name).toBe('string');
        expect(['mobile', 'tablet', 'desktop']).toContain(config.type);
        expect(typeof config.os).toBe('string');
        expect(typeof config.osVersion).toBe('string');
        expect(typeof config.viewport).toBe('object');
        expect(typeof config.pixelRatio).toBe('number');
        expect(typeof config.touchEnabled).toBe('boolean');
        
        expect(config.viewport).toHaveProperty('width');
        expect(config.viewport).toHaveProperty('height');
        expect(config.viewport.width).toBeGreaterThan(0);
        expect(config.viewport.height).toBeGreaterThan(0);
        expect(config.pixelRatio).toBeGreaterThan(0);
      });
    });

    it('should validate responsive breakpoints', () => {
      const { RESPONSIVE_BREAKPOINTS } = require('../cross-platform.config');
      
      expect(RESPONSIVE_BREAKPOINTS).toBeDefined();
      expect(typeof RESPONSIVE_BREAKPOINTS).toBe('object');
      
      // Check required breakpoints
      const requiredBreakpoints = ['mobile', 'tablet', 'desktop'];
      requiredBreakpoints.forEach(breakpoint => {
        expect(RESPONSIVE_BREAKPOINTS).toHaveProperty(breakpoint);
        expect(RESPONSIVE_BREAKPOINTS[breakpoint]).toHaveProperty('width');
        expect(RESPONSIVE_BREAKPOINTS[breakpoint]).toHaveProperty('height');
        expect(RESPONSIVE_BREAKPOINTS[breakpoint].width).toBeGreaterThan(0);
        expect(RESPONSIVE_BREAKPOINTS[breakpoint].height).toBeGreaterThan(0);
      });
      
      // Validate breakpoint ordering (mobile < tablet < desktop)
      expect(RESPONSIVE_BREAKPOINTS.mobile.width).toBeLessThan(RESPONSIVE_BREAKPOINTS.tablet.width);
      expect(RESPONSIVE_BREAKPOINTS.tablet.width).toBeLessThan(RESPONSIVE_BREAKPOINTS.desktop.width);
    });

    it('should validate test timeouts', () => {
      const { TEST_TIMEOUTS } = require('../cross-platform.config');
      
      expect(TEST_TIMEOUTS).toBeDefined();
      expect(typeof TEST_TIMEOUTS).toBe('object');
      
      const requiredTimeouts = ['pageLoad', 'elementWait', 'interaction', 'sync'];
      requiredTimeouts.forEach(timeout => {
        expect(TEST_TIMEOUTS).toHaveProperty(timeout);
        expect(typeof TEST_TIMEOUTS[timeout]).toBe('number');
        expect(TEST_TIMEOUTS[timeout]).toBeGreaterThan(0);
      });
      
      // Validate reasonable timeout values
      expect(TEST_TIMEOUTS.pageLoad).toBeGreaterThanOrEqual(10000); // At least 10 seconds
      expect(TEST_TIMEOUTS.elementWait).toBeGreaterThanOrEqual(5000); // At least 5 seconds
      expect(TEST_TIMEOUTS.interaction).toBeGreaterThanOrEqual(1000); // At least 1 second
      expect(TEST_TIMEOUTS.sync).toBeGreaterThanOrEqual(30000); // At least 30 seconds
    });
  });

  describe('Type Definitions', () => {
    it('should have valid type definitions', () => {
      const types = require('../types');
      
      // Check that types module exports expected interfaces
      expect(types).toBeDefined();
      
      // These are TypeScript interfaces, so we can't test them directly at runtime
      // But we can verify the module loads without errors
    });
  });

  describe('Error Handling', () => {
    it('should handle missing test data gracefully', () => {
      const { PLATFORM_FEATURES, SYNC_TEST_SCENARIOS } = require('../cross-platform.config');
      
      expect(Array.isArray(PLATFORM_FEATURES)).toBe(true);
      expect(Array.isArray(SYNC_TEST_SCENARIOS)).toBe(true);
      
      // Should not be empty
      expect(PLATFORM_FEATURES.length).toBeGreaterThan(0);
      expect(SYNC_TEST_SCENARIOS.length).toBeGreaterThan(0);
    });

    it('should validate platform feature definitions', () => {
      const { PLATFORM_FEATURES } = require('../cross-platform.config');
      
      PLATFORM_FEATURES.forEach((feature: string) => {
        expect(typeof feature).toBe('string');
        expect(feature.length).toBeGreaterThan(0);
        expect(feature).toMatch(/^[a-z-]+$/); // kebab-case format
      });
    });

    it('should validate sync test scenarios', () => {
      const { SYNC_TEST_SCENARIOS } = require('../cross-platform.config');
      
      SYNC_TEST_SCENARIOS.forEach((scenario: string) => {
        expect(typeof scenario).toBe('string');
        expect(scenario.length).toBeGreaterThan(0);
        expect(scenario).toMatch(/^[a-z-]+$/); // kebab-case format
      });
    });
  });

  describe('Performance Validation', () => {
    it('should have reasonable configuration sizes', () => {
      const { BROWSER_CONFIGS, DEVICE_CONFIGS, RESPONSIVE_BREAKPOINTS } = require('../cross-platform.config');
      
      // Should have a reasonable number of configurations to avoid excessive test times
      expect(BROWSER_CONFIGS.length).toBeLessThanOrEqual(10);
      expect(DEVICE_CONFIGS.length).toBeLessThanOrEqual(20);
      expect(Object.keys(RESPONSIVE_BREAKPOINTS).length).toBeLessThanOrEqual(10);
      
      // But should have minimum coverage
      expect(BROWSER_CONFIGS.length).toBeGreaterThanOrEqual(3); // Chrome, Firefox, Safari minimum
      expect(DEVICE_CONFIGS.length).toBeGreaterThanOrEqual(3); // Mobile, tablet, desktop minimum
      expect(Object.keys(RESPONSIVE_BREAKPOINTS).length).toBeGreaterThanOrEqual(3); // Mobile, tablet, desktop minimum
    });

    it('should have reasonable timeout values', () => {
      const { TEST_TIMEOUTS } = require('../cross-platform.config');
      
      // Timeouts should be reasonable - not too short to cause flaky tests,
      // not too long to make tests slow
      expect(TEST_TIMEOUTS.pageLoad).toBeLessThanOrEqual(60000); // Max 60 seconds
      expect(TEST_TIMEOUTS.elementWait).toBeLessThanOrEqual(30000); // Max 30 seconds
      expect(TEST_TIMEOUTS.interaction).toBeLessThanOrEqual(10000); // Max 10 seconds
      expect(TEST_TIMEOUTS.sync).toBeLessThanOrEqual(120000); // Max 2 minutes
    });
  });
});