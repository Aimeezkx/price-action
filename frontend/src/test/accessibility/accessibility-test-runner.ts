import { AxePuppeteer } from '@axe-core/puppeteer';
import puppeteer, { Browser, Page } from 'puppeteer';
import { AxeResults, Result } from 'axe-core';

export interface AccessibilityTestConfig {
  url: string;
  viewport?: { width: number; height: number };
  waitForSelector?: string;
  excludeSelectors?: string[];
  includeSelectors?: string[];
  tags?: string[];
}

export interface AccessibilityTestResult {
  url: string;
  violations: Result[];
  passes: Result[];
  incomplete: Result[];
  inapplicable: Result[];
  timestamp: Date;
  summary: {
    violationCount: number;
    passCount: number;
    incompleteCount: number;
    criticalViolations: number;
    seriousViolations: number;
    moderateViolations: number;
    minorViolations: number;
  };
}

export class AccessibilityTestRunner {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async setup(): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
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

  async runAccessibilityTest(config: AccessibilityTestConfig): Promise<AccessibilityTestResult> {
    if (!this.page) {
      throw new Error('Test runner not initialized. Call setup() first.');
    }

    // Set viewport if specified
    if (config.viewport) {
      await this.page.setViewport(config.viewport);
    }

    // Navigate to the page
    await this.page.goto(config.url, { waitUntil: 'networkidle0' });

    // Wait for specific selector if provided
    if (config.waitForSelector) {
      await this.page.waitForSelector(config.waitForSelector, { timeout: 10000 });
    }

    // Initialize axe-core
    const axe = new AxePuppeteer(this.page);

    // Configure axe options
    if (config.includeSelectors) {
      axe.include(config.includeSelectors);
    }
    if (config.excludeSelectors) {
      axe.exclude(config.excludeSelectors);
    }
    if (config.tags) {
      axe.withTags(config.tags);
    }

    // Run accessibility analysis
    const results: AxeResults = await axe.analyze();

    // Process results
    const summary = this.generateSummary(results);

    return {
      url: config.url,
      violations: results.violations,
      passes: results.passes,
      incomplete: results.incomplete,
      inapplicable: results.inapplicable,
      timestamp: new Date(),
      summary
    };
  }

  async runMultipleTests(configs: AccessibilityTestConfig[]): Promise<AccessibilityTestResult[]> {
    const results: AccessibilityTestResult[] = [];

    for (const config of configs) {
      try {
        const result = await this.runAccessibilityTest(config);
        results.push(result);
      } catch (error) {
        console.error(`Failed to run accessibility test for ${config.url}:`, error);
        // Continue with other tests
      }
    }

    return results;
  }

  private generateSummary(results: AxeResults) {
    const violationsBySeverity = results.violations.reduce((acc, violation) => {
      acc[violation.impact || 'unknown'] = (acc[violation.impact || 'unknown'] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      violationCount: results.violations.length,
      passCount: results.passes.length,
      incompleteCount: results.incomplete.length,
      criticalViolations: violationsBySeverity.critical || 0,
      seriousViolations: violationsBySeverity.serious || 0,
      moderateViolations: violationsBySeverity.moderate || 0,
      minorViolations: violationsBySeverity.minor || 0
    };
  }

  generateReport(results: AccessibilityTestResult[]): string {
    let report = '# Accessibility Test Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;

    // Overall summary
    const totalViolations = results.reduce((sum, result) => sum + result.summary.violationCount, 0);
    const totalPasses = results.reduce((sum, result) => sum + result.summary.passCount, 0);
    const criticalIssues = results.reduce((sum, result) => sum + result.summary.criticalViolations, 0);

    report += '## Overall Summary\n\n';
    report += `- **Total Pages Tested**: ${results.length}\n`;
    report += `- **Total Violations**: ${totalViolations}\n`;
    report += `- **Total Passes**: ${totalPasses}\n`;
    report += `- **Critical Issues**: ${criticalIssues}\n\n`;

    // Detailed results for each page
    for (const result of results) {
      report += `## ${result.url}\n\n`;
      report += `**Tested**: ${result.timestamp.toISOString()}\n\n`;
      
      if (result.violations.length > 0) {
        report += '### Violations\n\n';
        for (const violation of result.violations) {
          report += `#### ${violation.id} (${violation.impact})\n\n`;
          report += `**Description**: ${violation.description}\n\n`;
          report += `**Help**: ${violation.help}\n\n`;
          report += `**Help URL**: ${violation.helpUrl}\n\n`;
          
          if (violation.nodes.length > 0) {
            report += '**Affected Elements**:\n';
            for (const node of violation.nodes) {
              report += `- \`${node.target.join(', ')}\`\n`;
              if (node.failureSummary) {
                report += `  - ${node.failureSummary}\n`;
              }
            }
            report += '\n';
          }
        }
      } else {
        report += '### ✅ No violations found\n\n';
      }

      report += `**Summary**: ${result.summary.violationCount} violations, ${result.summary.passCount} passes\n\n`;
      report += '---\n\n';
    }

    return report;
  }
}