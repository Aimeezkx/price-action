import { AccessibilityTestRunner } from '../accessibility-test-runner';
import { KeyboardNavigationTester } from '../keyboard-navigation-tester';
import { ScreenReaderTester } from '../screen-reader-tester';
import { ColorContrastValidator } from '../color-contrast-validator';

describe('Accessibility Tests', () => {
  const baseUrl = process.env.TEST_BASE_URL || 'http://localhost:3000';
  
  let accessibilityRunner: AccessibilityTestRunner;
  let keyboardTester: KeyboardNavigationTester;
  let screenReaderTester: ScreenReaderTester;
  let colorContrastValidator: ColorContrastValidator;

  beforeAll(async () => {
    accessibilityRunner = new AccessibilityTestRunner();
    keyboardTester = new KeyboardNavigationTester();
    screenReaderTester = new ScreenReaderTester();
    colorContrastValidator = new ColorContrastValidator();

    await Promise.all([
      accessibilityRunner.setup(),
      keyboardTester.setup(),
      screenReaderTester.setup(),
      colorContrastValidator.setup()
    ]);
  });

  afterAll(async () => {
    await Promise.all([
      accessibilityRunner.teardown(),
      keyboardTester.teardown(),
      screenReaderTester.teardown(),
      colorContrastValidator.teardown()
    ]);
  });

  describe('Automated Accessibility Testing', () => {
    test('Home page should have no critical accessibility violations', async () => {
      const result = await accessibilityRunner.runAccessibilityTest({
        url: `${baseUrl}/`,
        tags: ['wcag2a', 'wcag2aa']
      });

      expect(result.summary.criticalViolations).toBe(0);
      expect(result.summary.seriousViolations).toBeLessThanOrEqual(2);
      
      // Log violations for debugging
      if (result.violations.length > 0) {
        console.log('Accessibility violations found:', result.violations.map(v => ({
          id: v.id,
          impact: v.impact,
          description: v.description
        })));
      }
    });

    test('Documents page should be accessible', async () => {
      const result = await accessibilityRunner.runAccessibilityTest({
        url: `${baseUrl}/documents`,
        tags: ['wcag2a', 'wcag2aa'],
        excludeSelectors: ['.loading-spinner']
      });

      expect(result.summary.criticalViolations).toBe(0);
      expect(result.summary.seriousViolations).toBeLessThanOrEqual(1);
    });

    test('Study page should be accessible', async () => {
      const result = await accessibilityRunner.runAccessibilityTest({
        url: `${baseUrl}/study`,
        tags: ['wcag2a', 'wcag2aa']
      });

      expect(result.summary.criticalViolations).toBe(0);
      expect(result.summary.seriousViolations).toBeLessThanOrEqual(1);
    });
  });

  describe('Keyboard Navigation Testing', () => {
    test('Home page should support keyboard navigation', async () => {
      const results = await keyboardTester.runKeyboardTest({
        url: `${baseUrl}/`,
        testScenarios: [
          {
            name: 'Tab Navigation',
            description: 'Navigate through focusable elements',
            keySequence: [
              { type: 'tab', repeat: 5 }
            ],
            expectedOutcome: {
              customValidation: async (page) => {
                const activeElement = await page.evaluate(() => {
                  const focused = document.activeElement;
                  return focused && focused !== document.body;
                });
                return activeElement;
              }
            }
          }
        ]
      });

      const passedTests = results.filter(r => r.passed);
      expect(passedTests.length).toBeGreaterThan(0);
      
      // At least 80% of keyboard tests should pass
      const passRate = passedTests.length / results.length;
      expect(passRate).toBeGreaterThanOrEqual(0.8);
    });

    test('Documents page should support keyboard navigation', async () => {
      const results = await keyboardTester.runKeyboardTest({
        url: `${baseUrl}/documents`,
        testScenarios: [
          {
            name: 'Upload Button Navigation',
            description: 'Navigate to upload button',
            keySequence: [
              { type: 'tab', repeat: 3 },
              { type: 'enter' }
            ],
            expectedOutcome: {
              visibleElements: ['[data-testid="upload-modal"]']
            }
          }
        ]
      });

      const passedTests = results.filter(r => r.passed);
      expect(passedTests.length).toBeGreaterThan(0);
    });
  });

  describe('Screen Reader Compatibility', () => {
    test('Home page should have proper ARIA labels', async () => {
      const results = await screenReaderTester.runScreenReaderTest({
        url: `${baseUrl}/`,
        testCases: [
          {
            name: 'Main Navigation',
            description: 'Check navigation ARIA labels',
            selector: 'nav',
            expectedAttributes: {
              role: 'navigation'
            }
          },
          {
            name: 'Main Content',
            description: 'Check main content area',
            selector: 'main',
            expectedAttributes: {
              role: 'main'
            }
          }
        ]
      });

      const passedTests = results.filter(r => r.passed);
      expect(passedTests.length).toBeGreaterThan(0);
      
      // All critical screen reader tests should pass
      const criticalFailures = results.filter(r => !r.passed && r.errors.some(e => e.includes('Missing')));
      expect(criticalFailures.length).toBe(0);
    });

    test('Interactive elements should have accessible names', async () => {
      const results = await screenReaderTester.runScreenReaderTest({
        url: `${baseUrl}/documents`,
        testCases: [
          {
            name: 'Upload Button',
            description: 'Check upload button accessibility',
            selector: '[data-testid="upload-button"]',
            expectedAttributes: {
              ariaLabel: 'Upload new document'
            },
            shouldBeFocusable: true
          }
        ]
      });

      const passedTests = results.filter(r => r.passed);
      expect(passedTests.length).toBeGreaterThan(0);
    });
  });

  describe('Color Contrast Validation', () => {
    test('Home page should meet WCAG AA color contrast requirements', async () => {
      const report = await colorContrastValidator.validateColorContrast({
        url: `${baseUrl}/`,
        wcagLevel: 'AA',
        selectors: ['h1', 'h2', 'p', 'a', 'button']
      });

      // At least 90% of tested elements should pass
      const passRate = report.summary.passRate;
      expect(passRate).toBeGreaterThanOrEqual(90);
      
      // No critical contrast failures
      const criticalFailures = report.results.filter(r => 
        !r.passed && r.contrastRatio < 3.0
      );
      expect(criticalFailures.length).toBe(0);
    });

    test('Documents page should have good color contrast', async () => {
      const report = await colorContrastValidator.validateColorContrast({
        url: `${baseUrl}/documents`,
        wcagLevel: 'AA',
        selectors: [
          '[data-testid="upload-button"]',
          '[data-testid="document-title"]'
        ]
      });

      expect(report.summary.passRate).toBeGreaterThanOrEqual(85);
    });
  });

  describe('Integration Tests', () => {
    test('All pages should meet minimum accessibility standards', async () => {
      const pages = ['/', '/documents', '/study', '/search'];
      const results = [];

      for (const page of pages) {
        const result = await accessibilityRunner.runAccessibilityTest({
          url: `${baseUrl}${page}`,
          tags: ['wcag2a']
        });
        results.push(result);
      }

      // No page should have critical violations
      for (const result of results) {
        expect(result.summary.criticalViolations).toBe(0);
      }

      // Average violations per page should be low
      const totalViolations = results.reduce((sum, r) => sum + r.summary.violationCount, 0);
      const averageViolations = totalViolations / results.length;
      expect(averageViolations).toBeLessThanOrEqual(5);
    });

    test('Keyboard navigation should work across all pages', async () => {
      const pages = ['/', '/documents', '/study'];
      const allResults = [];

      for (const page of pages) {
        const results = await keyboardTester.runKeyboardTest({
          url: `${baseUrl}${page}`,
          testScenarios: [
            {
              name: 'Basic Tab Navigation',
              description: 'Navigate with Tab key',
              keySequence: [{ type: 'tab', repeat: 3 }],
              expectedOutcome: {
                customValidation: async (page) => {
                  const focused = await page.evaluate(() => document.activeElement !== document.body);
                  return focused;
                }
              }
            }
          ]
        });
        allResults.push(...results);
      }

      const passedTests = allResults.filter(r => r.passed);
      const passRate = passedTests.length / allResults.length;
      expect(passRate).toBeGreaterThanOrEqual(0.75);
    });
  });
});