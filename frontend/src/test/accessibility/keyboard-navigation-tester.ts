import puppeteer, { Browser, Page, ElementHandle } from 'puppeteer';

export interface KeyboardTestConfig {
  url: string;
  testScenarios: KeyboardTestScenario[];
  viewport?: { width: number; height: number };
}

export interface KeyboardTestScenario {
  name: string;
  description: string;
  startSelector?: string;
  keySequence: KeyboardAction[];
  expectedOutcome: ExpectedOutcome;
}

export interface KeyboardAction {
  type: 'key' | 'tab' | 'shift-tab' | 'enter' | 'space' | 'escape' | 'arrow';
  key?: string;
  direction?: 'up' | 'down' | 'left' | 'right';
  repeat?: number;
}

export interface ExpectedOutcome {
  focusedElement?: string;
  activeElement?: string;
  visibleElements?: string[];
  hiddenElements?: string[];
  customValidation?: (page: Page) => Promise<boolean>;
}

export interface KeyboardTestResult {
  scenario: string;
  passed: boolean;
  error?: string;
  actualFocus?: string;
  expectedFocus?: string;
  timestamp: Date;
  details: string[];
}

export class KeyboardNavigationTester {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async setup(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Enable keyboard navigation
    await this.page.evaluateOnNewDocument(() => {
      // Remove any existing focus rings and add our own for testing
      const style = document.createElement('style');
      style.textContent = `
        *:focus {
          outline: 2px solid #007acc !important;
          outline-offset: 2px !important;
        }
      `;
      document.head.appendChild(style);
    });
  }

  async teardown(): Promise<void> {
    if (this.page) {
      await this.page.close();
    }
    if (this.browser) {
      await this.browser.close();
    }
  }

  async runKeyboardTest(config: KeyboardTestConfig): Promise<KeyboardTestResult[]> {
    if (!this.page) {
      throw new Error('Tester not initialized. Call setup() first.');
    }

    const results: KeyboardTestResult[] = [];

    // Set viewport if specified
    if (config.viewport) {
      await this.page.setViewport(config.viewport);
    }

    // Navigate to the page
    await this.page.goto(config.url, { waitUntil: 'networkidle0' });

    for (const scenario of config.testScenarios) {
      const result = await this.runScenario(scenario);
      results.push(result);
    }

    return results;
  }

  private async runScenario(scenario: KeyboardTestScenario): Promise<KeyboardTestResult> {
    if (!this.page) {
      throw new Error('Page not initialized');
    }

    const details: string[] = [];
    
    try {
      // Start from specified element or document body
      if (scenario.startSelector) {
        await this.page.click(scenario.startSelector);
        details.push(`Started from: ${scenario.startSelector}`);
      } else {
        // Focus on body to start
        await this.page.evaluate(() => document.body.focus());
        details.push('Started from: document.body');
      }

      // Execute key sequence
      for (const action of scenario.keySequence) {
        await this.executeKeyboardAction(action);
        details.push(`Executed: ${this.actionToString(action)}`);
        
        // Small delay to allow for animations/transitions
        await this.page.waitForTimeout(100);
      }

      // Check expected outcome
      const passed = await this.validateOutcome(scenario.expectedOutcome, details);
      
      const actualFocus = await this.getCurrentFocusSelector();
      
      return {
        scenario: scenario.name,
        passed,
        actualFocus,
        expectedFocus: scenario.expectedOutcome.focusedElement,
        timestamp: new Date(),
        details
      };

    } catch (error) {
      return {
        scenario: scenario.name,
        passed: false,
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date(),
        details
      };
    }
  }

  private async executeKeyboardAction(action: KeyboardAction): Promise<void> {
    if (!this.page) return;

    switch (action.type) {
      case 'key':
        if (action.key) {
          for (let i = 0; i < (action.repeat || 1); i++) {
            await this.page.keyboard.press(action.key);
          }
        }
        break;
      
      case 'tab':
        for (let i = 0; i < (action.repeat || 1); i++) {
          await this.page.keyboard.press('Tab');
        }
        break;
      
      case 'shift-tab':
        for (let i = 0; i < (action.repeat || 1); i++) {
          await this.page.keyboard.down('Shift');
          await this.page.keyboard.press('Tab');
          await this.page.keyboard.up('Shift');
        }
        break;
      
      case 'enter':
        await this.page.keyboard.press('Enter');
        break;
      
      case 'space':
        await this.page.keyboard.press('Space');
        break;
      
      case 'escape':
        await this.page.keyboard.press('Escape');
        break;
      
      case 'arrow':
        const arrowKey = `Arrow${action.direction?.charAt(0).toUpperCase()}${action.direction?.slice(1)}`;
        for (let i = 0; i < (action.repeat || 1); i++) {
          await this.page.keyboard.press(arrowKey);
        }
        break;
    }
  }

  private async validateOutcome(expected: ExpectedOutcome, details: string[]): Promise<boolean> {
    if (!this.page) return false;

    let passed = true;

    // Check focused element
    if (expected.focusedElement) {
      const actualFocus = await this.getCurrentFocusSelector();
      if (actualFocus !== expected.focusedElement) {
        details.push(`Focus mismatch: expected ${expected.focusedElement}, got ${actualFocus}`);
        passed = false;
      } else {
        details.push(`✓ Focus correct: ${actualFocus}`);
      }
    }

    // Check visible elements
    if (expected.visibleElements) {
      for (const selector of expected.visibleElements) {
        const isVisible = await this.page.evaluate((sel) => {
          const element = document.querySelector(sel);
          if (!element) return false;
          const style = window.getComputedStyle(element);
          return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        }, selector);
        
        if (!isVisible) {
          details.push(`Element not visible: ${selector}`);
          passed = false;
        } else {
          details.push(`✓ Element visible: ${selector}`);
        }
      }
    }

    // Check hidden elements
    if (expected.hiddenElements) {
      for (const selector of expected.hiddenElements) {
        const isHidden = await this.page.evaluate((sel) => {
          const element = document.querySelector(sel);
          if (!element) return true;
          const style = window.getComputedStyle(element);
          return style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0';
        }, selector);
        
        if (!isHidden) {
          details.push(`Element should be hidden: ${selector}`);
          passed = false;
        } else {
          details.push(`✓ Element hidden: ${selector}`);
        }
      }
    }

    // Run custom validation
    if (expected.customValidation) {
      try {
        const customResult = await expected.customValidation(this.page);
        if (!customResult) {
          details.push('Custom validation failed');
          passed = false;
        } else {
          details.push('✓ Custom validation passed');
        }
      } catch (error) {
        details.push(`Custom validation error: ${error}`);
        passed = false;
      }
    }

    return passed;
  }

  private async getCurrentFocusSelector(): Promise<string> {
    if (!this.page) return '';

    return await this.page.evaluate(() => {
      const focused = document.activeElement;
      if (!focused || focused === document.body) return 'body';
      
      // Try to generate a unique selector
      if (focused.id) return `#${focused.id}`;
      
      const tagName = focused.tagName.toLowerCase();
      const className = focused.className ? `.${focused.className.split(' ').join('.')}` : '';
      
      // Get position among siblings
      const siblings = Array.from(focused.parentElement?.children || []);
      const index = siblings.indexOf(focused);
      
      return `${tagName}${className}:nth-child(${index + 1})`;
    });
  }

  private actionToString(action: KeyboardAction): string {
    switch (action.type) {
      case 'key':
        return `Key: ${action.key}${action.repeat ? ` (${action.repeat}x)` : ''}`;
      case 'tab':
        return `Tab${action.repeat ? ` (${action.repeat}x)` : ''}`;
      case 'shift-tab':
        return `Shift+Tab${action.repeat ? ` (${action.repeat}x)` : ''}`;
      case 'arrow':
        return `Arrow ${action.direction}${action.repeat ? ` (${action.repeat}x)` : ''}`;
      default:
        return action.type;
    }
  }

  generateReport(results: KeyboardTestResult[]): string {
    let report = '# Keyboard Navigation Test Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;

    const passed = results.filter(r => r.passed).length;
    const failed = results.length - passed;

    report += '## Summary\n\n';
    report += `- **Total Tests**: ${results.length}\n`;
    report += `- **Passed**: ${passed}\n`;
    report += `- **Failed**: ${failed}\n`;
    report += `- **Success Rate**: ${((passed / results.length) * 100).toFixed(1)}%\n\n`;

    report += '## Test Results\n\n';

    for (const result of results) {
      const status = result.passed ? '✅' : '❌';
      report += `### ${status} ${result.scenario}\n\n`;
      
      if (result.error) {
        report += `**Error**: ${result.error}\n\n`;
      }
      
      if (result.expectedFocus && result.actualFocus) {
        report += `**Expected Focus**: ${result.expectedFocus}\n`;
        report += `**Actual Focus**: ${result.actualFocus}\n\n`;
      }
      
      if (result.details.length > 0) {
        report += '**Details**:\n';
        for (const detail of result.details) {
          report += `- ${detail}\n`;
        }
        report += '\n';
      }
      
      report += '---\n\n';
    }

    return report;
  }
}