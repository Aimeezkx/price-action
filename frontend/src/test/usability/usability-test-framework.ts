import puppeteer, { Browser, Page } from 'puppeteer';

export interface UsabilityTestConfig {
  url: string;
  scenarios: UsabilityScenario[];
  viewport?: { width: number; height: number };
  recordVideo?: boolean;
  recordScreenshots?: boolean;
}

export interface UsabilityScenario {
  name: string;
  description: string;
  userGoal: string;
  steps: UsabilityStep[];
  successCriteria: SuccessCriteria;
  timeLimit?: number; // in seconds
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface UsabilityStep {
  action: 'navigate' | 'click' | 'type' | 'wait' | 'scroll' | 'hover' | 'verify';
  target?: string;
  value?: string;
  timeout?: number;
  description: string;
  optional?: boolean;
}

export interface SuccessCriteria {
  requiredElements?: string[];
  forbiddenElements?: string[];
  expectedUrl?: string;
  expectedText?: string[];
  customValidation?: (page: Page) => Promise<boolean>;
  performanceThresholds?: {
    maxLoadTime?: number;
    maxInteractionTime?: number;
  };
}

export interface UsabilityTestResult {
  scenario: string;
  completed: boolean;
  success: boolean;
  timeToComplete: number;
  errors: UsabilityError[];
  warnings: string[];
  stepResults: StepResult[];
  performanceMetrics: PerformanceMetrics;
  userExperienceScore: number;
  timestamp: Date;
}

export interface UsabilityError {
  step: number;
  type: 'navigation' | 'interaction' | 'validation' | 'performance' | 'accessibility';
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  suggestion?: string;
}

export interface StepResult {
  stepIndex: number;
  description: string;
  success: boolean;
  timeToComplete: number;
  error?: string;
  screenshot?: string;
}

export interface PerformanceMetrics {
  pageLoadTime: number;
  timeToInteractive: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  totalInteractionTime: number;
}

export class UsabilityTestFramework {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private screenshotCounter = 0;

  async setup(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
      ]
    });
    this.page = await this.browser.newPage();
    
    // Enable performance monitoring
    await this.page.setCacheEnabled(false);
  }

  async teardown(): Promise<void> {
    if (this.page) {
      await this.page.close();
    }
    if (this.browser) {
      await this.browser.close();
    }
  }

  async runUsabilityTest(config: UsabilityTestConfig): Promise<UsabilityTestResult[]> {
    if (!this.page) {
      throw new Error('Framework not initialized. Call setup() first.');
    }

    const results: UsabilityTestResult[] = [];

    // Set viewport if specified
    if (config.viewport) {
      await this.page.setViewport(config.viewport);
    }

    for (const scenario of config.scenarios) {
      const result = await this.runScenario(scenario, config);
      results.push(result);
    }

    return results;
  }

  private async runScenario(scenario: UsabilityScenario, config: UsabilityTestConfig): Promise<UsabilityTestResult> {
    if (!this.page) {
      throw new Error('Page not initialized');
    }

    const startTime = Date.now();
    const errors: UsabilityError[] = [];
    const warnings: string[] = [];
    const stepResults: StepResult[] = [];
    let completed = false;
    let success = false;

    try {
      // Navigate to the starting URL
      await this.page.goto(config.url, { waitUntil: 'networkidle0' });
      
      // Capture initial performance metrics
      const initialMetrics = await this.capturePerformanceMetrics();

      // Execute each step
      for (let i = 0; i < scenario.steps.length; i++) {
        const step = scenario.steps[i];
        const stepStartTime = Date.now();
        
        try {
          await this.executeStep(step, i);
          
          const stepResult: StepResult = {
            stepIndex: i,
            description: step.description,
            success: true,
            timeToComplete: Date.now() - stepStartTime
          };

          // Capture screenshot if enabled
          if (config.recordScreenshots) {
            stepResult.screenshot = await this.captureScreenshot(`step-${i}`);
          }

          stepResults.push(stepResult);

        } catch (error) {
          const stepResult: StepResult = {
            stepIndex: i,
            description: step.description,
            success: false,
            timeToComplete: Date.now() - stepStartTime,
            error: error instanceof Error ? error.message : String(error)
          };

          stepResults.push(stepResult);

          if (!step.optional) {
            errors.push({
              step: i,
              type: 'interaction',
              message: `Step failed: ${step.description}`,
              severity: 'high',
              suggestion: `Check if the target element "${step.target}" exists and is interactable`
            });
            break; // Stop execution on critical step failure
          } else {
            warnings.push(`Optional step ${i} failed: ${step.description}`);
          }
        }
      }

      completed = stepResults.every(r => r.success || scenario.steps[r.stepIndex].optional);

      // Validate success criteria
      if (completed) {
        success = await this.validateSuccessCriteria(scenario.successCriteria, errors);
      }

      // Capture final performance metrics
      const finalMetrics = await this.capturePerformanceMetrics();
      const performanceMetrics = this.calculatePerformanceMetrics(initialMetrics, finalMetrics);

      // Check performance thresholds
      if (scenario.successCriteria.performanceThresholds) {
        this.validatePerformanceThresholds(
          performanceMetrics,
          scenario.successCriteria.performanceThresholds,
          errors
        );
      }

      // Calculate user experience score
      const userExperienceScore = this.calculateUserExperienceScore(
        success,
        performanceMetrics,
        errors,
        warnings
      );

      return {
        scenario: scenario.name,
        completed,
        success,
        timeToComplete: Date.now() - startTime,
        errors,
        warnings,
        stepResults,
        performanceMetrics,
        userExperienceScore,
        timestamp: new Date()
      };

    } catch (error) {
      errors.push({
        step: -1,
        type: 'navigation',
        message: `Scenario execution failed: ${error}`,
        severity: 'critical'
      });

      return {
        scenario: scenario.name,
        completed: false,
        success: false,
        timeToComplete: Date.now() - startTime,
        errors,
        warnings,
        stepResults,
        performanceMetrics: {
          pageLoadTime: 0,
          timeToInteractive: 0,
          firstContentfulPaint: 0,
          largestContentfulPaint: 0,
          cumulativeLayoutShift: 0,
          totalInteractionTime: 0
        },
        userExperienceScore: 0,
        timestamp: new Date()
      };
    }
  }

  private async executeStep(step: UsabilityStep, stepIndex: number): Promise<void> {
    if (!this.page) return;

    const timeout = step.timeout || 5000;

    switch (step.action) {
      case 'navigate':
        if (step.value) {
          await this.page.goto(step.value, { waitUntil: 'networkidle0', timeout });
        }
        break;

      case 'click':
        if (step.target) {
          await this.page.waitForSelector(step.target, { timeout });
          await this.page.click(step.target);
        }
        break;

      case 'type':
        if (step.target && step.value) {
          await this.page.waitForSelector(step.target, { timeout });
          await this.page.type(step.target, step.value);
        }
        break;

      case 'wait':
        if (step.target) {
          await this.page.waitForSelector(step.target, { timeout });
        } else if (step.value) {
          await this.page.waitForTimeout(parseInt(step.value));
        }
        break;

      case 'scroll':
        if (step.target) {
          await this.page.evaluate((selector) => {
            const element = document.querySelector(selector);
            if (element) {
              element.scrollIntoView({ behavior: 'smooth' });
            }
          }, step.target);
        } else if (step.value) {
          const scrollAmount = parseInt(step.value);
          await this.page.evaluate((amount) => {
            window.scrollBy(0, amount);
          }, scrollAmount);
        }
        break;

      case 'hover':
        if (step.target) {
          await this.page.waitForSelector(step.target, { timeout });
          await this.page.hover(step.target);
        }
        break;

      case 'verify':
        if (step.target) {
          await this.page.waitForSelector(step.target, { timeout });
        }
        if (step.value) {
          const text = await this.page.evaluate(() => document.body.textContent);
          if (!text?.includes(step.value)) {
            throw new Error(`Expected text "${step.value}" not found`);
          }
        }
        break;
    }

    // Small delay between steps for more realistic interaction
    await this.page.waitForTimeout(200);
  }

  private async validateSuccessCriteria(criteria: SuccessCriteria, errors: UsabilityError[]): Promise<boolean> {
    if (!this.page) return false;

    let success = true;

    // Check required elements
    if (criteria.requiredElements) {
      for (const selector of criteria.requiredElements) {
        const element = await this.page.$(selector);
        if (!element) {
          errors.push({
            step: -1,
            type: 'validation',
            message: `Required element not found: ${selector}`,
            severity: 'high'
          });
          success = false;
        }
      }
    }

    // Check forbidden elements
    if (criteria.forbiddenElements) {
      for (const selector of criteria.forbiddenElements) {
        const element = await this.page.$(selector);
        if (element) {
          errors.push({
            step: -1,
            type: 'validation',
            message: `Forbidden element found: ${selector}`,
            severity: 'medium'
          });
          success = false;
        }
      }
    }

    // Check expected URL
    if (criteria.expectedUrl) {
      const currentUrl = this.page.url();
      if (!currentUrl.includes(criteria.expectedUrl)) {
        errors.push({
          step: -1,
          type: 'navigation',
          message: `Expected URL "${criteria.expectedUrl}" not reached. Current: ${currentUrl}`,
          severity: 'high'
        });
        success = false;
      }
    }

    // Check expected text
    if (criteria.expectedText) {
      const pageText = await this.page.evaluate(() => document.body.textContent);
      for (const expectedText of criteria.expectedText) {
        if (!pageText?.includes(expectedText)) {
          errors.push({
            step: -1,
            type: 'validation',
            message: `Expected text not found: "${expectedText}"`,
            severity: 'medium'
          });
          success = false;
        }
      }
    }

    // Run custom validation
    if (criteria.customValidation) {
      try {
        const customResult = await criteria.customValidation(this.page);
        if (!customResult) {
          errors.push({
            step: -1,
            type: 'validation',
            message: 'Custom validation failed',
            severity: 'high'
          });
          success = false;
        }
      } catch (error) {
        errors.push({
          step: -1,
          type: 'validation',
          message: `Custom validation error: ${error}`,
          severity: 'high'
        });
        success = false;
      }
    }

    return success;
  }

  private async capturePerformanceMetrics(): Promise<any> {
    if (!this.page) return {};

    try {
      const metrics = await this.page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        const paint = performance.getEntriesByType('paint');
        
        return {
          loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
          domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
          firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
          firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
          timestamp: Date.now()
        };
      });

      return metrics;
    } catch (error) {
      console.warn('Could not capture performance metrics:', error);
      return {};
    }
  }

  private calculatePerformanceMetrics(initial: any, final: any): PerformanceMetrics {
    return {
      pageLoadTime: final.loadTime || 0,
      timeToInteractive: final.domContentLoaded || 0,
      firstContentfulPaint: final.firstContentfulPaint || 0,
      largestContentfulPaint: 0, // Would need additional measurement
      cumulativeLayoutShift: 0, // Would need additional measurement
      totalInteractionTime: final.timestamp - initial.timestamp
    };
  }

  private validatePerformanceThresholds(
    metrics: PerformanceMetrics,
    thresholds: { maxLoadTime?: number; maxInteractionTime?: number },
    errors: UsabilityError[]
  ): void {
    if (thresholds.maxLoadTime && metrics.pageLoadTime > thresholds.maxLoadTime) {
      errors.push({
        step: -1,
        type: 'performance',
        message: `Page load time exceeded threshold: ${metrics.pageLoadTime}ms > ${thresholds.maxLoadTime}ms`,
        severity: 'medium',
        suggestion: 'Optimize page loading performance'
      });
    }

    if (thresholds.maxInteractionTime && metrics.totalInteractionTime > thresholds.maxInteractionTime) {
      errors.push({
        step: -1,
        type: 'performance',
        message: `Total interaction time exceeded threshold: ${metrics.totalInteractionTime}ms > ${thresholds.maxInteractionTime}ms`,
        severity: 'medium',
        suggestion: 'Optimize user interaction responsiveness'
      });
    }
  }

  private calculateUserExperienceScore(
    success: boolean,
    metrics: PerformanceMetrics,
    errors: UsabilityError[],
    warnings: string[]
  ): number {
    let score = 100;

    // Deduct points for failure
    if (!success) {
      score -= 50;
    }

    // Deduct points for errors
    for (const error of errors) {
      switch (error.severity) {
        case 'critical':
          score -= 20;
          break;
        case 'high':
          score -= 10;
          break;
        case 'medium':
          score -= 5;
          break;
        case 'low':
          score -= 2;
          break;
      }
    }

    // Deduct points for warnings
    score -= warnings.length * 1;

    // Deduct points for poor performance
    if (metrics.pageLoadTime > 3000) score -= 10;
    if (metrics.timeToInteractive > 5000) score -= 10;
    if (metrics.firstContentfulPaint > 2000) score -= 5;

    return Math.max(0, Math.min(100, score));
  }

  private async captureScreenshot(name: string): Promise<string> {
    if (!this.page) return '';

    try {
      const filename = `screenshot-${name}-${this.screenshotCounter++}.png`;
      await this.page.screenshot({ path: filename, fullPage: true });
      return filename;
    } catch (error) {
      console.warn('Could not capture screenshot:', error);
      return '';
    }
  }

  generateReport(results: UsabilityTestResult[]): string {
    let report = '# Usability Test Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;

    // Overall summary
    const totalScenarios = results.length;
    const completedScenarios = results.filter(r => r.completed).length;
    const successfulScenarios = results.filter(r => r.success).length;
    const averageScore = results.reduce((sum, r) => sum + r.userExperienceScore, 0) / totalScenarios;
    const averageTime = results.reduce((sum, r) => sum + r.timeToComplete, 0) / totalScenarios;

    report += '## Overall Summary\n\n';
    report += `- **Total Scenarios**: ${totalScenarios}\n`;
    report += `- **Completed**: ${completedScenarios} (${((completedScenarios / totalScenarios) * 100).toFixed(1)}%)\n`;
    report += `- **Successful**: ${successfulScenarios} (${((successfulScenarios / totalScenarios) * 100).toFixed(1)}%)\n`;
    report += `- **Average UX Score**: ${averageScore.toFixed(1)}/100\n`;
    report += `- **Average Completion Time**: ${(averageTime / 1000).toFixed(1)}s\n\n`;

    // Detailed results
    report += '## Scenario Results\n\n';

    for (const result of results) {
      const status = result.success ? '✅' : result.completed ? '⚠️' : '❌';
      report += `### ${status} ${result.scenario}\n\n`;
      
      report += `**Status**: ${result.success ? 'Success' : result.completed ? 'Completed with issues' : 'Failed'}\n`;
      report += `**Time to Complete**: ${(result.timeToComplete / 1000).toFixed(1)}s\n`;
      report += `**UX Score**: ${result.userExperienceScore}/100\n\n`;

      // Performance metrics
      report += '**Performance**:\n';
      report += `- Page Load Time: ${result.performanceMetrics.pageLoadTime}ms\n`;
      report += `- Time to Interactive: ${result.performanceMetrics.timeToInteractive}ms\n`;
      report += `- First Contentful Paint: ${result.performanceMetrics.firstContentfulPaint}ms\n\n`;

      // Errors
      if (result.errors.length > 0) {
        report += '**Errors**:\n';
        for (const error of result.errors) {
          const icon = error.severity === 'critical' ? '🔴' : error.severity === 'high' ? '🟠' : error.severity === 'medium' ? '🟡' : '🔵';
          report += `- ${icon} ${error.message}\n`;
          if (error.suggestion) {
            report += `  - *Suggestion: ${error.suggestion}*\n`;
          }
        }
        report += '\n';
      }

      // Warnings
      if (result.warnings.length > 0) {
        report += '**Warnings**:\n';
        for (const warning of result.warnings) {
          report += `- ⚠️ ${warning}\n`;
        }
        report += '\n';
      }

      // Step details
      if (result.stepResults.length > 0) {
        report += '**Step Results**:\n';
        for (const step of result.stepResults) {
          const stepStatus = step.success ? '✅' : '❌';
          report += `${step.stepIndex + 1}. ${stepStatus} ${step.description} (${step.timeToComplete}ms)\n`;
          if (step.error) {
            report += `   - Error: ${step.error}\n`;
          }
        }
        report += '\n';
      }

      report += '---\n\n';
    }

    return report;
  }
}