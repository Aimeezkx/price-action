import { jest } from '@jest/globals';

// Extend Jest timeout for accessibility tests
jest.setTimeout(60000);

// Global test configuration
const testConfig = {
  baseUrl: process.env.TEST_BASE_URL || 'http://localhost:3000',
  headless: process.env.TEST_HEADLESS !== 'false',
  slowMo: process.env.TEST_SLOW_MO ? parseInt(process.env.TEST_SLOW_MO) : 0,
  devtools: process.env.TEST_DEVTOOLS === 'true'
};

// Make config available globally
(global as any).testConfig = testConfig;

// Console logging configuration
const originalConsoleLog = console.log;
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

// Suppress noisy logs in test environment unless verbose
if (!process.env.VERBOSE_TESTS) {
  console.log = (...args: any[]) => {
    // Only log test-related messages
    const message = args.join(' ');
    if (message.includes('Test') || message.includes('Accessibility') || message.includes('Usability')) {
      originalConsoleLog(...args);
    }
  };
  
  console.warn = (...args: any[]) => {
    // Always show warnings
    originalConsoleWarn(...args);
  };
  
  console.error = (...args: any[]) => {
    // Always show errors
    originalConsoleError(...args);
  };
}

// Global error handler for unhandled promises
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Cleanup function for after tests
afterAll(async () => {
  // Restore console methods
  console.log = originalConsoleLog;
  console.warn = originalConsoleWarn;
  console.error = originalConsoleError;
});

// Custom matchers for accessibility testing
expect.extend({
  toHaveNoAccessibilityViolations(received: any) {
    const violations = received.violations || [];
    const criticalViolations = violations.filter((v: any) => v.impact === 'critical');
    
    if (criticalViolations.length === 0) {
      return {
        message: () => `Expected accessibility violations but found none`,
        pass: true
      };
    } else {
      return {
        message: () => `Expected no critical accessibility violations but found ${criticalViolations.length}:\n${
          criticalViolations.map((v: any) => `- ${v.id}: ${v.description}`).join('\n')
        }`,
        pass: false
      };
    }
  },
  
  toHaveGoodColorContrast(received: any, threshold = 4.5) {
    const contrastRatio = received.contrastRatio || 0;
    
    if (contrastRatio >= threshold) {
      return {
        message: () => `Expected poor color contrast but got ${contrastRatio}:1`,
        pass: true
      };
    } else {
      return {
        message: () => `Expected color contrast ratio of at least ${threshold}:1 but got ${contrastRatio}:1`,
        pass: false
      };
    }
  },
  
  toBeKeyboardAccessible(received: any) {
    const passed = received.passed || false;
    const errors = received.errors || [];
    
    if (passed) {
      return {
        message: () => `Expected keyboard accessibility issues but found none`,
        pass: true
      };
    } else {
      return {
        message: () => `Expected keyboard accessibility but found issues:\n${
          errors.join('\n')
        }`,
        pass: false
      };
    }
  },
  
  toHaveGoodUsabilityScore(received: any, threshold = 80) {
    const score = received.userExperienceScore || 0;
    
    if (score >= threshold) {
      return {
        message: () => `Expected poor usability score but got ${score}/100`,
        pass: true
      };
    } else {
      return {
        message: () => `Expected usability score of at least ${threshold}/100 but got ${score}/100`,
        pass: false
      };
    }
  }
});

// Type declarations for custom matchers
declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveNoAccessibilityViolations(): R;
      toHaveGoodColorContrast(threshold?: number): R;
      toBeKeyboardAccessible(): R;
      toHaveGoodUsabilityScore(threshold?: number): R;
    }
  }
}