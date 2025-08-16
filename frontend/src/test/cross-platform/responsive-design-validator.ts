/**
 * Responsive design validation across different screen sizes
 */

import { Page } from 'playwright';
import { ResponsiveTestResult, TestContext } from './types';
import { RESPONSIVE_BREAKPOINTS, TEST_TIMEOUTS } from './cross-platform.config';

interface LayoutElement {
  selector: string;
  expectedBehavior: {
    mobile?: string;
    tablet?: string;
    desktop?: string;
  };
  criticalElement: boolean;
}

export class ResponsiveDesignValidator {
  private testResults: ResponsiveTestResult[] = [];

  async runResponsiveTests(page: Page, baseUrl: string = 'http://localhost:3000'): Promise<ResponsiveTestResult[]> {
    console.log('Running responsive design validation tests...');
    this.testResults = [];

    const testCases = this.getResponsiveTestCases();

    for (const [breakpointName, viewport] of Object.entries(RESPONSIVE_BREAKPOINTS)) {
      console.log(`Testing responsive design at ${breakpointName} (${viewport.width}x${viewport.height})`);
      
      // Set viewport size
      await page.setViewportSize(viewport);
      
      const testContext: TestContext = {
        page,
        platform: `Responsive-${breakpointName}`,
        baseUrl
      };

      for (const testCase of testCases) {
        try {
          const result = await testCase.execute(testContext, viewport);
          result.breakpoint = breakpointName;
          this.testResults.push(result);
        } catch (error) {
          this.testResults.push({
            testName: testCase.name,
            breakpoint: breakpointName,
            viewport,
            layoutValid: false,
            elementsVisible: false,
            interactionsWorking: false,
            error: error instanceof Error ? error.message : String(error)
          });
        }
      }
    }

    return this.testResults;
  }

  private getResponsiveTestCases() {
    return [
      {
        name: 'Navigation Responsiveness Test',
        description: 'Test navigation adaptation across screen sizes',
        execute: async (context: TestContext, viewport: { width: number; height: number }): Promise<ResponsiveTestResult> => {
          const { page } = context;
          
          await page.goto(context.baseUrl);
          await page.waitForLoadState('networkidle');

          // Check navigation elements
          const navigation = page.locator('[data-testid="main-navigation"]');
          await navigation.waitFor({ timeout: TEST_TIMEOUTS.elementWait });

          const navVisible = await navigation.isVisible();
          
          // Check for mobile menu on smaller screens
          let mobileMenuWorking = true;
          if (viewport.width < 768) {
            const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
            const hasMobileMenu = await mobileMenuButton.count() > 0;
            
            if (hasMobileMenu) {
              await mobileMenuButton.click();
              await page.waitForTimeout(500); // Wait for animation
              
              const mobileMenu = page.locator('[data-testid="mobile-menu"]');
              mobileMenuWorking = await mobileMenu.isVisible();
            }
          }

          // Check if navigation items are accessible
          const navItems = page.locator('[data-testid="nav-item"]');
          const navItemCount = await navItems.count();
          let navItemsVisible = 0;

          for (let i = 0; i < navItemCount; i++) {
            const item = navItems.nth(i);
            if (await item.isVisible()) {
              navItemsVisible++;
            }
          }

          const elementsVisible = navVisible && (navItemsVisible > 0 || viewport.width < 768);
          const interactionsWorking = mobileMenuWorking;

          return {
            testName: 'Navigation Responsiveness Test',
            breakpoint: '',
            viewport,
            layoutValid: true,
            elementsVisible,
            interactionsWorking
          };
        }
      },
      {
        name: 'Content Layout Test',
        description: 'Test main content layout adaptation',
        execute: async (context: TestContext, viewport: { width: number; height: number }): Promise<ResponsiveTestResult> => {
          const { page } = context;
          
          await page.goto(context.baseUrl);
          
          // Check main content container
          const mainContent = page.locator('[data-testid="main-content"]');
          await mainContent.waitFor({ timeout: TEST_TIMEOUTS.elementWait });

          const contentBox = await mainContent.boundingBox();
          if (!contentBox) {
            throw new Error('Could not get main content dimensions');
          }

          // Check if content fits within viewport
          const layoutValid = contentBox.width <= viewport.width;
          
          // Check if content is visible and not cut off
          const elementsVisible = contentBox.height > 0 && contentBox.width > 0;

          // Test scrolling if content is taller than viewport
          let interactionsWorking = true;
          if (contentBox.height > viewport.height) {
            await page.evaluate(() => window.scrollTo(0, 100));
            await page.waitForTimeout(200);
            
            const scrollY = await page.evaluate(() => window.scrollY);
            interactionsWorking = scrollY > 0;
          }

          return {
            testName: 'Content Layout Test',
            breakpoint: '',
            viewport,
            layoutValid,
            elementsVisible,
            interactionsWorking
          };
        }
      },
      {
        name: 'Form Elements Responsiveness Test',
        description: 'Test form elements adaptation on different screen sizes',
        execute: async (context: TestContext, viewport: { width: number; height: number }): Promise<ResponsiveTestResult> => {
          const { page } = context;
          
          // Test on search page which has form elements
          await page.goto(`${context.baseUrl}/search`);
          
          // Check search input
          const searchInput = page.locator('[data-testid="search-input"]');
          await searchInput.waitFor({ timeout: TEST_TIMEOUTS.elementWait });

          const inputBox = await searchInput.boundingBox();
          if (!inputBox) {
            throw new Error('Could not get search input dimensions');
          }

          // Check if input adapts to screen size
          const expectedMinWidth = Math.min(200, viewport.width * 0.8);
          const layoutValid = inputBox.width >= expectedMinWidth && inputBox.width <= viewport.width;

          // Check if input is visible and accessible
          const elementsVisible = await searchInput.isVisible() && await searchInput.isEnabled();

          // Test input interaction
          let interactionsWorking = false;
          try {
            await searchInput.fill('test query');
            const inputValue = await searchInput.inputValue();
            interactionsWorking = inputValue === 'test query';
          } catch (error) {
            console.warn('Input interaction test failed:', error);
          }

          return {
            testName: 'Form Elements Responsiveness Test',
            breakpoint: '',
            viewport,
            layoutValid,
            elementsVisible,
            interactionsWorking
          };
        }
      },
      {
        name: 'Card Layout Responsiveness Test',
        description: 'Test flashcard layout on different screen sizes',
        execute: async (context: TestContext, viewport: { width: number; height: number }): Promise<ResponsiveTestResult> => {
          const { page } = context;
          
          await page.goto(`${context.baseUrl}/study`);
          
          // Check if flashcard or no-cards message is present
          const flashcard = page.locator('[data-testid="flashcard"]');
          const noCardsMessage = page.locator('[data-testid="no-cards-message"]');
          
          await page.waitForSelector('[data-testid="flashcard"], [data-testid="no-cards-message"]', 
            { timeout: TEST_TIMEOUTS.elementWait });

          let layoutValid = true;
          let elementsVisible = true;
          let interactionsWorking = true;

          if (await flashcard.isVisible()) {
            const cardBox = await flashcard.boundingBox();
            if (cardBox) {
              // Check if card fits within viewport with some margin
              const margin = 40; // 20px margin on each side
              layoutValid = cardBox.width <= (viewport.width - margin);
              
              // Check if card is not too small on larger screens
              if (viewport.width > 768) {
                const minCardWidth = Math.min(400, viewport.width * 0.6);
                layoutValid = layoutValid && cardBox.width >= minCardWidth;
              }
            }

            // Test card interactions
            const flipButton = page.locator('[data-testid="flip-button"]');
            if (await flipButton.isVisible()) {
              try {
                await flipButton.click();
                await page.waitForTimeout(300); // Wait for flip animation
                
                // Check if grading buttons appear
                const gradeButtons = page.locator('[data-testid^="grade-"]');
                const gradeButtonCount = await gradeButtons.count();
                interactionsWorking = gradeButtonCount > 0;
              } catch (error) {
                interactionsWorking = false;
              }
            }
          } else if (await noCardsMessage.isVisible()) {
            // No cards to test, but message should be visible
            elementsVisible = true;
            interactionsWorking = true;
          } else {
            elementsVisible = false;
          }

          return {
            testName: 'Card Layout Responsiveness Test',
            breakpoint: '',
            viewport,
            layoutValid,
            elementsVisible,
            interactionsWorking
          };
        }
      },
      {
        name: 'Document List Responsiveness Test',
        description: 'Test document list layout adaptation',
        execute: async (context: TestContext, viewport: { width: number; height: number }): Promise<ResponsiveTestResult> => {
          const { page } = context;
          
          await page.goto(`${context.baseUrl}/documents`);
          
          // Check document list or empty state
          const documentList = page.locator('[data-testid="document-list"]');
          const emptyState = page.locator('[data-testid="empty-documents"]');
          
          await page.waitForSelector('[data-testid="document-list"], [data-testid="empty-documents"]', 
            { timeout: TEST_TIMEOUTS.elementWait });

          let layoutValid = true;
          let elementsVisible = true;
          let interactionsWorking = true;

          if (await documentList.isVisible()) {
            const listBox = await documentList.boundingBox();
            if (listBox) {
              layoutValid = listBox.width <= viewport.width;
            }

            // Check document items
            const documentItems = page.locator('[data-testid="document-item"]');
            const itemCount = await documentItems.count();

            if (itemCount > 0) {
              // Check first item layout
              const firstItem = documentItems.first();
              const itemBox = await firstItem.boundingBox();
              
              if (itemBox) {
                // Items should stack vertically on mobile, be in grid on desktop
                if (viewport.width < 768) {
                  // Mobile: items should be full width (minus margins)
                  layoutValid = itemBox.width >= (viewport.width * 0.8);
                } else {
                  // Desktop: items can be in grid, but not too narrow
                  layoutValid = itemBox.width >= 200;
                }
              }

              // Test item interaction
              try {
                await firstItem.click();
                await page.waitForTimeout(500);
                interactionsWorking = true;
              } catch (error) {
                interactionsWorking = false;
              }
            }
          } else if (await emptyState.isVisible()) {
            // Empty state should be visible and centered
            const emptyBox = await emptyState.boundingBox();
            if (emptyBox) {
              layoutValid = emptyBox.width <= viewport.width;
            }
          } else {
            elementsVisible = false;
          }

          return {
            testName: 'Document List Responsiveness Test',
            breakpoint: '',
            viewport,
            layoutValid,
            elementsVisible,
            interactionsWorking
          };
        }
      },
      {
        name: 'Touch Target Size Test',
        description: 'Test touch target sizes on mobile devices',
        execute: async (context: TestContext, viewport: { width: number; height: number }): Promise<ResponsiveTestResult> => {
          const { page } = context;
          
          await page.goto(context.baseUrl);

          let layoutValid = true;
          let elementsVisible = true;
          let interactionsWorking = true;

          // Only test touch targets on mobile/tablet sizes
          if (viewport.width <= 1024) {
            const touchTargets = [
              '[data-testid="upload-button"]',
              '[data-testid="nav-item"]',
              'button',
              'a[href]',
              '[data-testid="flip-button"]',
              '[data-testid^="grade-"]'
            ];

            const minTouchSize = 44; // 44px minimum touch target size (iOS HIG)

            for (const selector of touchTargets) {
              const elements = page.locator(selector);
              const count = await elements.count();

              for (let i = 0; i < Math.min(count, 5); i++) { // Test first 5 elements
                const element = elements.nth(i);
                
                if (await element.isVisible()) {
                  const box = await element.boundingBox();
                  
                  if (box) {
                    const meetsMinSize = box.width >= minTouchSize && box.height >= minTouchSize;
                    if (!meetsMinSize) {
                      console.warn(`Touch target too small: ${selector} (${box.width}x${box.height})`);
                      layoutValid = false;
                    }
                  }
                }
              }
            }
          }

          return {
            testName: 'Touch Target Size Test',
            breakpoint: '',
            viewport,
            layoutValid,
            elementsVisible,
            interactionsWorking
          };
        }
      }
    ];
  }

  getResults(): ResponsiveTestResult[] {
    return this.testResults;
  }

  generateReport(): string {
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(r => 
      r.layoutValid && r.elementsVisible && r.interactionsWorking
    ).length;
    const failedTests = totalTests - passedTests;
    
    let report = `\n=== Responsive Design Validation Report ===\n`;
    report += `Total Tests: ${totalTests}\n`;
    report += `Passed: ${passedTests}\n`;
    report += `Failed: ${failedTests}\n`;
    report += `Success Rate: ${((passedTests / totalTests) * 100).toFixed(2)}%\n\n`;
    
    // Group results by breakpoint
    const resultsByBreakpoint = this.testResults.reduce((acc, result) => {
      if (!acc[result.breakpoint]) acc[result.breakpoint] = [];
      acc[result.breakpoint].push(result);
      return acc;
    }, {} as Record<string, ResponsiveTestResult[]>);
    
    for (const [breakpoint, results] of Object.entries(resultsByBreakpoint)) {
      const breakpointPassed = results.filter(r => 
        r.layoutValid && r.elementsVisible && r.interactionsWorking
      ).length;
      const breakpointTotal = results.length;
      
      report += `${breakpoint}: ${breakpointPassed}/${breakpointTotal} tests passed\n`;
      
      const failedResults = results.filter(r => 
        !r.layoutValid || !r.elementsVisible || !r.interactionsWorking
      );
      
      if (failedResults.length > 0) {
        report += `  Issues:\n`;
        failedResults.forEach(result => {
          const issues = [];
          if (!result.layoutValid) issues.push('Layout invalid');
          if (!result.elementsVisible) issues.push('Elements not visible');
          if (!result.interactionsWorking) issues.push('Interactions not working');
          
          report += `    - ${result.testName}: ${issues.join(', ')}\n`;
          if (result.error) {
            report += `      Error: ${result.error}\n`;
          }
        });
      }
      report += '\n';
    }
    
    return report;
  }
}