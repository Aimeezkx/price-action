import puppeteer, { Browser, Page } from 'puppeteer';

export interface ScreenReaderTestConfig {
  url: string;
  testCases: ScreenReaderTestCase[];
  viewport?: { width: number; height: number };
}

export interface ScreenReaderTestCase {
  name: string;
  description: string;
  selector: string;
  expectedAttributes: {
    role?: string;
    ariaLabel?: string;
    ariaLabelledBy?: string;
    ariaDescribedBy?: string;
    ariaExpanded?: string;
    ariaHidden?: string;
    ariaLive?: string;
    ariaAtomic?: string;
    tabIndex?: string;
    alt?: string;
    title?: string;
  };
  expectedText?: string;
  shouldBeFocusable?: boolean;
  customValidation?: (element: any) => boolean;
}

export interface ScreenReaderTestResult {
  testCase: string;
  passed: boolean;
  errors: string[];
  warnings: string[];
  actualAttributes: Record<string, string>;
  expectedAttributes: Record<string, string>;
  timestamp: Date;
}

export interface AccessibilityTreeNode {
  role: string;
  name: string;
  description?: string;
  children: AccessibilityTreeNode[];
  properties: Record<string, any>;
}

export class ScreenReaderTester {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async setup(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--enable-accessibility-object-model'
      ]
    });
    this.page = await this.browser.newPage();
  }

  async teardown(): Promise<void> {
    if (this.page) {
      await this.page.close();
    }
    if (this.browser) {
      await this.browser.close();
    }
  }

  async runScreenReaderTest(config: ScreenReaderTestConfig): Promise<ScreenReaderTestResult[]> {
    if (!this.page) {
      throw new Error('Tester not initialized. Call setup() first.');
    }

    const results: ScreenReaderTestResult[] = [];

    // Set viewport if specified
    if (config.viewport) {
      await this.page.setViewport(config.viewport);
    }

    // Navigate to the page
    await this.page.goto(config.url, { waitUntil: 'networkidle0' });

    for (const testCase of config.testCases) {
      const result = await this.runTestCase(testCase);
      results.push(result);
    }

    return results;
  }

  private async runTestCase(testCase: ScreenReaderTestCase): Promise<ScreenReaderTestResult> {
    if (!this.page) {
      throw new Error('Page not initialized');
    }

    const errors: string[] = [];
    const warnings: string[] = [];
    let actualAttributes: Record<string, string> = {};

    try {
      // Check if element exists
      const element = await this.page.$(testCase.selector);
      if (!element) {
        errors.push(`Element not found: ${testCase.selector}`);
        return {
          testCase: testCase.name,
          passed: false,
          errors,
          warnings,
          actualAttributes: {},
          expectedAttributes: testCase.expectedAttributes,
          timestamp: new Date()
        };
      }

      // Get actual attributes
      actualAttributes = await this.page.evaluate((selector) => {
        const el = document.querySelector(selector);
        if (!el) return {};

        const attrs: Record<string, string> = {};
        
        // Standard attributes
        if (el.getAttribute('role')) attrs.role = el.getAttribute('role')!;
        if (el.getAttribute('aria-label')) attrs.ariaLabel = el.getAttribute('aria-label')!;
        if (el.getAttribute('aria-labelledby')) attrs.ariaLabelledBy = el.getAttribute('aria-labelledby')!;
        if (el.getAttribute('aria-describedby')) attrs.ariaDescribedBy = el.getAttribute('aria-describedby')!;
        if (el.getAttribute('aria-expanded')) attrs.ariaExpanded = el.getAttribute('aria-expanded')!;
        if (el.getAttribute('aria-hidden')) attrs.ariaHidden = el.getAttribute('aria-hidden')!;
        if (el.getAttribute('aria-live')) attrs.ariaLive = el.getAttribute('aria-live')!;
        if (el.getAttribute('aria-atomic')) attrs.ariaAtomic = el.getAttribute('aria-atomic')!;
        if (el.getAttribute('tabindex')) attrs.tabIndex = el.getAttribute('tabindex')!;
        if (el.getAttribute('alt')) attrs.alt = el.getAttribute('alt')!;
        if (el.getAttribute('title')) attrs.title = el.getAttribute('title')!;

        return attrs;
      }, testCase.selector);

      // Validate expected attributes
      for (const [key, expectedValue] of Object.entries(testCase.expectedAttributes)) {
        const actualValue = actualAttributes[key];
        
        if (expectedValue && !actualValue) {
          errors.push(`Missing ${key}: expected "${expectedValue}"`);
        } else if (expectedValue && actualValue !== expectedValue) {
          errors.push(`Incorrect ${key}: expected "${expectedValue}", got "${actualValue}"`);
        } else if (expectedValue && actualValue === expectedValue) {
          // Attribute matches - this is good
        }
      }

      // Check if element should be focusable
      if (testCase.shouldBeFocusable !== undefined) {
        const isFocusable = await this.page.evaluate((selector) => {
          const el = document.querySelector(selector) as HTMLElement;
          if (!el) return false;
          
          // Try to focus the element
          el.focus();
          return document.activeElement === el;
        }, testCase.selector);

        if (testCase.shouldBeFocusable && !isFocusable) {
          errors.push('Element should be focusable but is not');
        } else if (!testCase.shouldBeFocusable && isFocusable) {
          warnings.push('Element is focusable but may not need to be');
        }
      }

      // Check expected text content
      if (testCase.expectedText) {
        const actualText = await this.page.evaluate((selector) => {
          const el = document.querySelector(selector);
          return el?.textContent?.trim() || '';
        }, testCase.selector);

        if (actualText !== testCase.expectedText) {
          errors.push(`Text mismatch: expected "${testCase.expectedText}", got "${actualText}"`);
        }
      }

      // Run custom validation
      if (testCase.customValidation) {
        const elementHandle = await this.page.$(testCase.selector);
        if (elementHandle) {
          const elementData = await this.page.evaluate((el) => {
            return {
              tagName: el.tagName,
              attributes: Array.from(el.attributes).reduce((acc, attr) => {
                acc[attr.name] = attr.value;
                return acc;
              }, {} as Record<string, string>),
              textContent: el.textContent,
              innerHTML: el.innerHTML
            };
          }, elementHandle);

          try {
            const customResult = testCase.customValidation(elementData);
            if (!customResult) {
              errors.push('Custom validation failed');
            }
          } catch (error) {
            errors.push(`Custom validation error: ${error}`);
          }
        }
      }

      // Additional accessibility checks
      await this.performAdditionalChecks(testCase.selector, errors, warnings);

    } catch (error) {
      errors.push(`Test execution error: ${error}`);
    }

    return {
      testCase: testCase.name,
      passed: errors.length === 0,
      errors,
      warnings,
      actualAttributes,
      expectedAttributes: testCase.expectedAttributes,
      timestamp: new Date()
    };
  }

  private async performAdditionalChecks(selector: string, errors: string[], warnings: string[]): Promise<void> {
    if (!this.page) return;

    // Check for common accessibility issues
    const issues = await this.page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el) return [];

      const issues: string[] = [];

      // Check for images without alt text
      if (el.tagName === 'IMG' && !el.getAttribute('alt')) {
        issues.push('Image missing alt attribute');
      }

      // Check for buttons without accessible names
      if (el.tagName === 'BUTTON' && !el.textContent?.trim() && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby')) {
        issues.push('Button missing accessible name');
      }

      // Check for links without accessible names
      if (el.tagName === 'A' && !el.textContent?.trim() && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby')) {
        issues.push('Link missing accessible name');
      }

      // Check for form inputs without labels
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)) {
        const hasLabel = el.getAttribute('aria-label') || 
                         el.getAttribute('aria-labelledby') || 
                         document.querySelector(`label[for="${el.id}"]`);
        if (!hasLabel) {
          issues.push('Form input missing label');
        }
      }

      // Check for interactive elements with tabindex=-1
      if (['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName) && el.getAttribute('tabindex') === '-1') {
        issues.push('Interactive element has tabindex="-1"');
      }

      return issues;
    }, selector);

    errors.push(...issues);
  }

  async getAccessibilityTree(): Promise<AccessibilityTreeNode | null> {
    if (!this.page) return null;

    try {
      // Get the accessibility tree using Chrome DevTools Protocol
      const client = await this.page.target().createCDPSession();
      await client.send('Accessibility.enable');
      
      const { nodes } = await client.send('Accessibility.getFullAXTree');
      
      // Convert to our format
      const rootNode = nodes.find(node => node.role?.value === 'RootWebArea');
      if (!rootNode) return null;

      return this.convertToAccessibilityTreeNode(rootNode, nodes);
    } catch (error) {
      console.warn('Could not get accessibility tree:', error);
      return null;
    }
  }

  private convertToAccessibilityTreeNode(node: any, allNodes: any[]): AccessibilityTreeNode {
    const children = (node.childIds || [])
      .map((childId: string) => allNodes.find(n => n.nodeId === childId))
      .filter(Boolean)
      .map((childNode: any) => this.convertToAccessibilityTreeNode(childNode, allNodes));

    return {
      role: node.role?.value || 'unknown',
      name: node.name?.value || '',
      description: node.description?.value,
      children,
      properties: node.properties || {}
    };
  }

  generateReport(results: ScreenReaderTestResult[]): string {
    let report = '# Screen Reader Compatibility Test Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;

    const passed = results.filter(r => r.passed).length;
    const failed = results.length - passed;
    const totalWarnings = results.reduce((sum, r) => sum + r.warnings.length, 0);

    report += '## Summary\n\n';
    report += `- **Total Tests**: ${results.length}\n`;
    report += `- **Passed**: ${passed}\n`;
    report += `- **Failed**: ${failed}\n`;
    report += `- **Warnings**: ${totalWarnings}\n`;
    report += `- **Success Rate**: ${((passed / results.length) * 100).toFixed(1)}%\n\n`;

    report += '## Test Results\n\n';

    for (const result of results) {
      const status = result.passed ? '✅' : '❌';
      report += `### ${status} ${result.testCase}\n\n`;
      
      if (result.errors.length > 0) {
        report += '**Errors**:\n';
        for (const error of result.errors) {
          report += `- ❌ ${error}\n`;
        }
        report += '\n';
      }
      
      if (result.warnings.length > 0) {
        report += '**Warnings**:\n';
        for (const warning of result.warnings) {
          report += `- ⚠️ ${warning}\n`;
        }
        report += '\n';
      }
      
      // Show attribute comparison
      const expectedKeys = Object.keys(result.expectedAttributes);
      const actualKeys = Object.keys(result.actualAttributes);
      
      if (expectedKeys.length > 0 || actualKeys.length > 0) {
        report += '**Attributes**:\n\n';
        report += '| Attribute | Expected | Actual | Status |\n';
        report += '|-----------|----------|--------|--------|\n';
        
        const allKeys = new Set([...expectedKeys, ...actualKeys]);
        for (const key of allKeys) {
          const expected = result.expectedAttributes[key] || '-';
          const actual = result.actualAttributes[key] || '-';
          const status = expected === actual ? '✅' : '❌';
          report += `| ${key} | ${expected} | ${actual} | ${status} |\n`;
        }
        report += '\n';
      }
      
      report += '---\n\n';
    }

    return report;
  }
}