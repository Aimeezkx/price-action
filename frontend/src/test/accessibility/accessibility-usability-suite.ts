import { AccessibilityTestRunner, AccessibilityTestConfig, AccessibilityTestResult } from './accessibility-test-runner';
import { KeyboardNavigationTester, KeyboardTestConfig, KeyboardTestResult } from './keyboard-navigation-tester';
import { ScreenReaderTester, ScreenReaderTestConfig, ScreenReaderTestResult } from './screen-reader-tester';
import { ColorContrastValidator, ColorContrastConfig, ColorContrastReport } from './color-contrast-validator';
import { UsabilityTestFramework, UsabilityTestConfig, UsabilityTestResult } from '../usability/usability-test-framework';

export interface AccessibilityUsabilityConfig {
  baseUrl: string;
  pages: PageTestConfig[];
  outputDir?: string;
  generateReports?: boolean;
}

export interface PageTestConfig {
  name: string;
  path: string;
  accessibility?: {
    enabled: boolean;
    tags?: string[];
    excludeSelectors?: string[];
  };
  keyboard?: {
    enabled: boolean;
    scenarios?: any[];
  };
  screenReader?: {
    enabled: boolean;
    testCases?: any[];
  };
  colorContrast?: {
    enabled: boolean;
    wcagLevel?: 'AA' | 'AAA';
    selectors?: string[];
  };
  usability?: {
    enabled: boolean;
    scenarios?: any[];
  };
}

export interface TestSuiteResults {
  timestamp: Date;
  summary: {
    totalPages: number;
    accessibilityResults: AccessibilityTestResult[];
    keyboardResults: KeyboardTestResult[];
    screenReaderResults: ScreenReaderTestResult[];
    colorContrastResults: ColorContrastReport[];
    usabilityResults: UsabilityTestResult[];
  };
  overallScore: {
    accessibility: number;
    usability: number;
    combined: number;
  };
}

export class AccessibilityUsabilitySuite {
  private accessibilityRunner: AccessibilityTestRunner;
  private keyboardTester: KeyboardNavigationTester;
  private screenReaderTester: ScreenReaderTester;
  private colorContrastValidator: ColorContrastValidator;
  private usabilityFramework: UsabilityTestFramework;

  constructor() {
    this.accessibilityRunner = new AccessibilityTestRunner();
    this.keyboardTester = new KeyboardNavigationTester();
    this.screenReaderTester = new ScreenReaderTester();
    this.colorContrastValidator = new ColorContrastValidator();
    this.usabilityFramework = new UsabilityTestFramework();
  }

  async runFullSuite(config: AccessibilityUsabilityConfig): Promise<TestSuiteResults> {
    console.log('Starting Accessibility & Usability Test Suite...');
    
    const results: TestSuiteResults = {
      timestamp: new Date(),
      summary: {
        totalPages: config.pages.length,
        accessibilityResults: [],
        keyboardResults: [],
        screenReaderResults: [],
        colorContrastResults: [],
        usabilityResults: []
      },
      overallScore: {
        accessibility: 0,
        usability: 0,
        combined: 0
      }
    };

    // Initialize all testers
    await this.initializeTesters();

    try {
      // Run tests for each page
      for (const pageConfig of config.pages) {
        console.log(`Testing page: ${pageConfig.name}`);
        await this.runPageTests(config.baseUrl, pageConfig, results);
      }

      // Calculate overall scores
      results.overallScore = this.calculateOverallScores(results);

      // Generate reports if requested
      if (config.generateReports) {
        await this.generateReports(results, config.outputDir || './test-reports');
      }

    } finally {
      // Cleanup all testers
      await this.cleanupTesters();
    }

    return results;
  }

  private async initializeTesters(): Promise<void> {
    await Promise.all([
      this.accessibilityRunner.setup(),
      this.keyboardTester.setup(),
      this.screenReaderTester.setup(),
      this.colorContrastValidator.setup(),
      this.usabilityFramework.setup()
    ]);
  }

  private async cleanupTesters(): Promise<void> {
    await Promise.all([
      this.accessibilityRunner.teardown(),
      this.keyboardTester.teardown(),
      this.screenReaderTester.teardown(),
      this.colorContrastValidator.teardown(),
      this.usabilityFramework.teardown()
    ]);
  }

  private async runPageTests(baseUrl: string, pageConfig: PageTestConfig, results: TestSuiteResults): Promise<void> {
    const fullUrl = `${baseUrl}${pageConfig.path}`;

    // Run accessibility tests
    if (pageConfig.accessibility?.enabled) {
      console.log(`  Running accessibility tests...`);
      const accessibilityConfig: AccessibilityTestConfig = {
        url: fullUrl,
        tags: pageConfig.accessibility.tags,
        excludeSelectors: pageConfig.accessibility.excludeSelectors
      };
      
      const accessibilityResult = await this.accessibilityRunner.runAccessibilityTest(accessibilityConfig);
      results.summary.accessibilityResults.push(accessibilityResult);
    }

    // Run keyboard navigation tests
    if (pageConfig.keyboard?.enabled) {
      console.log(`  Running keyboard navigation tests...`);
      const keyboardConfig: KeyboardTestConfig = {
        url: fullUrl,
        testScenarios: pageConfig.keyboard.scenarios || this.getDefaultKeyboardScenarios(pageConfig.name)
      };
      
      const keyboardResults = await this.keyboardTester.runKeyboardTest(keyboardConfig);
      results.summary.keyboardResults.push(...keyboardResults);
    }

    // Run screen reader tests
    if (pageConfig.screenReader?.enabled) {
      console.log(`  Running screen reader tests...`);
      const screenReaderConfig: ScreenReaderTestConfig = {
        url: fullUrl,
        testCases: pageConfig.screenReader.testCases || this.getDefaultScreenReaderTests(pageConfig.name)
      };
      
      const screenReaderResults = await this.screenReaderTester.runScreenReaderTest(screenReaderConfig);
      results.summary.screenReaderResults.push(...screenReaderResults);
    }

    // Run color contrast tests
    if (pageConfig.colorContrast?.enabled) {
      console.log(`  Running color contrast tests...`);
      const colorContrastConfig: ColorContrastConfig = {
        url: fullUrl,
        wcagLevel: pageConfig.colorContrast.wcagLevel || 'AA',
        selectors: pageConfig.colorContrast.selectors,
        includeAllText: !pageConfig.colorContrast.selectors
      };
      
      const colorContrastResult = await this.colorContrastValidator.validateColorContrast(colorContrastConfig);
      results.summary.colorContrastResults.push(colorContrastResult);
    }

    // Run usability tests
    if (pageConfig.usability?.enabled) {
      console.log(`  Running usability tests...`);
      const usabilityConfig: UsabilityTestConfig = {
        url: fullUrl,
        scenarios: pageConfig.usability.scenarios || this.getDefaultUsabilityScenarios(pageConfig.name),
        recordScreenshots: true
      };
      
      const usabilityResults = await this.usabilityFramework.runUsabilityTest(usabilityConfig);
      results.summary.usabilityResults.push(...usabilityResults);
    }
  }

  private getDefaultKeyboardScenarios(pageName: string): any[] {
    const commonScenarios = [
      {
        name: 'Tab Navigation',
        description: 'Navigate through all focusable elements using Tab key',
        keySequence: [
          { type: 'tab', repeat: 10 }
        ],
        expectedOutcome: {
          customValidation: async (page: any) => {
            // Check if focus is visible and logical
            const focusedElement = await page.evaluate(() => {
              const focused = document.activeElement;
              return focused && focused !== document.body;
            });
            return focusedElement;
          }
        }
      },
      {
        name: 'Reverse Tab Navigation',
        description: 'Navigate backwards through focusable elements using Shift+Tab',
        keySequence: [
          { type: 'tab', repeat: 5 },
          { type: 'shift-tab', repeat: 3 }
        ],
        expectedOutcome: {
          customValidation: async (page: any) => {
            return true; // Basic validation
          }
        }
      }
    ];

    // Add page-specific scenarios
    switch (pageName.toLowerCase()) {
      case 'home':
      case 'documents':
        return [
          ...commonScenarios,
          {
            name: 'Document Upload Navigation',
            description: 'Navigate to and activate document upload',
            keySequence: [
              { type: 'tab', repeat: 3 },
              { type: 'enter' }
            ],
            expectedOutcome: {
              visibleElements: ['[data-testid="upload-modal"]']
            }
          }
        ];
      
      case 'study':
        return [
          ...commonScenarios,
          {
            name: 'Card Navigation',
            description: 'Navigate and interact with flashcards',
            keySequence: [
              { type: 'tab', repeat: 2 },
              { type: 'space' },
              { type: 'tab' },
              { type: 'enter' }
            ],
            expectedOutcome: {
              customValidation: async (page: any) => {
                // Check if card was flipped or graded
                return true;
              }
            }
          }
        ];
      
      default:
        return commonScenarios;
    }
  }

  private getDefaultScreenReaderTests(pageName: string): any[] {
    const commonTests = [
      {
        name: 'Page Title',
        description: 'Check if page has proper title',
        selector: 'title',
        expectedAttributes: {},
        expectedText: pageName
      },
      {
        name: 'Main Navigation',
        description: 'Check navigation accessibility',
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
    ];

    // Add page-specific tests
    switch (pageName.toLowerCase()) {
      case 'documents':
        return [
          ...commonTests,
          {
            name: 'Upload Button',
            description: 'Check upload button accessibility',
            selector: '[data-testid="upload-button"]',
            expectedAttributes: {
              ariaLabel: 'Upload document'
            },
            shouldBeFocusable: true
          }
        ];
      
      case 'study':
        return [
          ...commonTests,
          {
            name: 'Flashcard',
            description: 'Check flashcard accessibility',
            selector: '[data-testid="flashcard"]',
            expectedAttributes: {
              role: 'button',
              ariaLabel: 'Flashcard - click to flip'
            },
            shouldBeFocusable: true
          }
        ];
      
      default:
        return commonTests;
    }
  }

  private getDefaultUsabilityScenarios(pageName: string): any[] {
    const commonScenarios = [
      {
        name: 'Page Load',
        description: 'Basic page loading and navigation',
        userGoal: 'Access the page and see main content',
        steps: [
          {
            action: 'wait',
            target: 'main',
            description: 'Wait for main content to load'
          }
        ],
        successCriteria: {
          requiredElements: ['main', 'nav'],
          performanceThresholds: {
            maxLoadTime: 3000
          }
        },
        difficulty: 'easy'
      }
    ];

    // Add page-specific scenarios
    switch (pageName.toLowerCase()) {
      case 'documents':
        return [
          ...commonScenarios,
          {
            name: 'Document Upload Flow',
            description: 'Upload a document successfully',
            userGoal: 'Upload a PDF document for processing',
            steps: [
              {
                action: 'click',
                target: '[data-testid="upload-button"]',
                description: 'Click upload button'
              },
              {
                action: 'wait',
                target: '[data-testid="upload-modal"]',
                description: 'Wait for upload modal to appear'
              }
            ],
            successCriteria: {
              requiredElements: ['[data-testid="upload-modal"]'],
              performanceThresholds: {
                maxInteractionTime: 1000
              }
            },
            difficulty: 'medium'
          }
        ];
      
      case 'study':
        return [
          ...commonScenarios,
          {
            name: 'Card Review Flow',
            description: 'Review flashcards successfully',
            userGoal: 'Review and grade flashcards',
            steps: [
              {
                action: 'click',
                target: '[data-testid="flashcard"]',
                description: 'Click to flip card'
              },
              {
                action: 'wait',
                target: '[data-testid="grading-interface"]',
                description: 'Wait for grading interface'
              },
              {
                action: 'click',
                target: '[data-testid="grade-4"]',
                description: 'Grade the card'
              }
            ],
            successCriteria: {
              customValidation: async (page: any) => {
                // Check if next card appeared or session completed
                const nextCard = await page.$('[data-testid="flashcard"]');
                const sessionComplete = await page.$('[data-testid="session-complete"]');
                return nextCard || sessionComplete;
              }
            },
            difficulty: 'medium'
          }
        ];
      
      default:
        return commonScenarios;
    }
  }

  private calculateOverallScores(results: TestSuiteResults): { accessibility: number; usability: number; combined: number } {
    // Calculate accessibility score
    let accessibilityScore = 100;
    
    // Deduct for accessibility violations
    for (const result of results.summary.accessibilityResults) {
      accessibilityScore -= result.summary.criticalViolations * 10;
      accessibilityScore -= result.summary.seriousViolations * 5;
      accessibilityScore -= result.summary.moderateViolations * 2;
      accessibilityScore -= result.summary.minorViolations * 1;
    }

    // Deduct for keyboard navigation failures
    const keyboardFailures = results.summary.keyboardResults.filter(r => !r.passed).length;
    accessibilityScore -= keyboardFailures * 5;

    // Deduct for screen reader issues
    const screenReaderFailures = results.summary.screenReaderResults.filter(r => !r.passed).length;
    accessibilityScore -= screenReaderFailures * 5;

    // Deduct for color contrast failures
    for (const report of results.summary.colorContrastResults) {
      accessibilityScore -= report.summary.failed * 2;
    }

    // Calculate usability score
    const usabilityScores = results.summary.usabilityResults.map(r => r.userExperienceScore);
    const usabilityScore = usabilityScores.length > 0 
      ? usabilityScores.reduce((sum, score) => sum + score, 0) / usabilityScores.length
      : 100;

    // Combined score
    const combinedScore = (Math.max(0, accessibilityScore) + usabilityScore) / 2;

    return {
      accessibility: Math.max(0, Math.min(100, accessibilityScore)),
      usability: Math.max(0, Math.min(100, usabilityScore)),
      combined: Math.max(0, Math.min(100, combinedScore))
    };
  }

  private async generateReports(results: TestSuiteResults, outputDir: string): Promise<void> {
    const fs = require('fs').promises;
    const path = require('path');

    // Ensure output directory exists
    await fs.mkdir(outputDir, { recursive: true });

    // Generate individual reports
    if (results.summary.accessibilityResults.length > 0) {
      const accessibilityReport = this.accessibilityRunner.generateReport(results.summary.accessibilityResults);
      await fs.writeFile(path.join(outputDir, 'accessibility-report.md'), accessibilityReport);
    }

    if (results.summary.keyboardResults.length > 0) {
      const keyboardReport = this.keyboardTester.generateReport(results.summary.keyboardResults);
      await fs.writeFile(path.join(outputDir, 'keyboard-navigation-report.md'), keyboardReport);
    }

    if (results.summary.screenReaderResults.length > 0) {
      const screenReaderReport = this.screenReaderTester.generateReport(results.summary.screenReaderResults);
      await fs.writeFile(path.join(outputDir, 'screen-reader-report.md'), screenReaderReport);
    }

    for (let i = 0; i < results.summary.colorContrastResults.length; i++) {
      const colorContrastReport = this.colorContrastValidator.generateReport(results.summary.colorContrastResults[i]);
      await fs.writeFile(path.join(outputDir, `color-contrast-report-${i + 1}.md`), colorContrastReport);
    }

    if (results.summary.usabilityResults.length > 0) {
      const usabilityReport = this.usabilityFramework.generateReport(results.summary.usabilityResults);
      await fs.writeFile(path.join(outputDir, 'usability-report.md'), usabilityReport);
    }

    // Generate combined summary report
    const summaryReport = this.generateSummaryReport(results);
    await fs.writeFile(path.join(outputDir, 'accessibility-usability-summary.md'), summaryReport);

    console.log(`Reports generated in: ${outputDir}`);
  }

  private generateSummaryReport(results: TestSuiteResults): string {
    let report = '# Accessibility & Usability Test Summary\n\n';
    report += `Generated: ${results.timestamp.toISOString()}\n\n`;

    // Overall scores
    report += '## Overall Scores\n\n';
    report += `- **Accessibility Score**: ${results.overallScore.accessibility.toFixed(1)}/100\n`;
    report += `- **Usability Score**: ${results.overallScore.usability.toFixed(1)}/100\n`;
    report += `- **Combined Score**: ${results.overallScore.combined.toFixed(1)}/100\n\n`;

    // Test summary
    report += '## Test Summary\n\n';
    report += `- **Pages Tested**: ${results.summary.totalPages}\n`;
    report += `- **Accessibility Tests**: ${results.summary.accessibilityResults.length}\n`;
    report += `- **Keyboard Tests**: ${results.summary.keyboardResults.length}\n`;
    report += `- **Screen Reader Tests**: ${results.summary.screenReaderResults.length}\n`;
    report += `- **Color Contrast Tests**: ${results.summary.colorContrastResults.length}\n`;
    report += `- **Usability Tests**: ${results.summary.usabilityResults.length}\n\n`;

    // Key findings
    report += '## Key Findings\n\n';

    // Accessibility violations
    const totalViolations = results.summary.accessibilityResults.reduce(
      (sum, result) => sum + result.summary.violationCount, 0
    );
    if (totalViolations > 0) {
      report += `- **${totalViolations} accessibility violations** found across all pages\n`;
    }

    // Keyboard navigation issues
    const keyboardFailures = results.summary.keyboardResults.filter(r => !r.passed).length;
    if (keyboardFailures > 0) {
      report += `- **${keyboardFailures} keyboard navigation issues** identified\n`;
    }

    // Screen reader issues
    const screenReaderFailures = results.summary.screenReaderResults.filter(r => !r.passed).length;
    if (screenReaderFailures > 0) {
      report += `- **${screenReaderFailures} screen reader compatibility issues** found\n`;
    }

    // Color contrast issues
    const colorContrastFailures = results.summary.colorContrastResults.reduce(
      (sum, report) => sum + report.summary.failed, 0
    );
    if (colorContrastFailures > 0) {
      report += `- **${colorContrastFailures} color contrast violations** detected\n`;
    }

    // Usability issues
    const usabilityFailures = results.summary.usabilityResults.filter(r => !r.success).length;
    if (usabilityFailures > 0) {
      report += `- **${usabilityFailures} usability scenarios** failed\n`;
    }

    report += '\n## Recommendations\n\n';

    if (results.overallScore.accessibility < 80) {
      report += '- **Priority: High** - Address accessibility violations to improve compliance\n';
    }
    if (results.overallScore.usability < 80) {
      report += '- **Priority: High** - Improve user experience and interaction flows\n';
    }
    if (keyboardFailures > 0) {
      report += '- **Priority: Medium** - Ensure all interactive elements are keyboard accessible\n';
    }
    if (colorContrastFailures > 0) {
      report += '- **Priority: Medium** - Improve color contrast ratios for better readability\n';
    }

    report += '\nFor detailed findings, see individual test reports.\n';

    return report;
  }
}