/**
 * Icon Visual Regression Tests
 *
 * This test suite captures and compares screenshots of icon implementations
 * to detect visual regressions when icon sizes are changed.
 */

import { test, expect, Page } from '@playwright/test';

// Test data for different icon contexts
const iconTestCases = [
  {
    name: 'navigation-icons',
    path: '/',
    selector: '[data-testid="navigation"]',
    description: 'Navigation bar icons should be consistently small (w-4 h-4)',
  },
  {
    name: 'homepage-feature-icons',
    path: '/',
    selector: '[data-testid="feature-cards"]',
    description: 'Homepage feature card icons should be medium sized (w-5 h-5)',
  },
  {
    name: 'document-list-icons',
    path: '/documents',
    selector: '[data-testid="document-list"]',
    description: 'Document list file type icons should be appropriately sized (w-6 h-6)',
  },
  {
    name: 'button-icons',
    path: '/export',
    selector: '[data-testid="export-buttons"]',
    description: 'Button icons should be small and consistent (w-4 h-4)',
  },
  {
    name: 'search-icons',
    path: '/search',
    selector: '[data-testid="search-interface"]',
    description: 'Search interface icons should be appropriately sized',
  },
  {
    name: 'empty-state-icons',
    path: '/study',
    selector: '[data-testid="empty-state"]',
    description: 'Empty state icons should be larger but not overwhelming (w-8 h-8)',
  },
  {
    name: 'status-indicators',
    path: '/',
    selector: '[data-testid="connection-status"]',
    description: 'Status indicator icons should be extra small (w-3 h-3 or w-4 h-4)',
  },
];

// Viewport configurations for responsive testing
const viewports = [
  { name: 'desktop', width: 1920, height: 1080 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 390, height: 844 },
];

test.describe('Icon Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set up any necessary authentication or state
    await page.goto('/');

    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Ensure any animations are complete
    await page.waitForTimeout(500);
  });

  test.describe('Icon Size Consistency', () => {
    for (const testCase of iconTestCases) {
      test(`should maintain consistent ${testCase.name} across viewports`, async ({ page }) => {
        for (const viewport of viewports) {
          await page.setViewportSize({ width: viewport.width, height: viewport.height });
          await page.goto(testCase.path);
          await page.waitForLoadState('networkidle');

          // Wait for any layout shifts
          await page.waitForTimeout(300);

          // Take screenshot of the specific icon area
          const element = page.locator(testCase.selector).first();
          if (await element.count() > 0) {
            await expect(element).toHaveScreenshot(`${testCase.name}-${viewport.name}.png`, {
              threshold: 0.2, // Allow for minor rendering differences
              maxDiffPixels: 100,
            });
          }
        }
      });
    }
  });

  test.describe('Icon Context Validation', () => {
    test('navigation icons should be consistently small', async ({ page }) => {
      await page.goto('/');

      // Check navigation icons
      const navIcons = page.locator('[data-testid="navigation"] svg, [data-testid="navigation"] [class*="w-"]');
      const iconCount = await navIcons.count();

      if (iconCount > 0) {
        for (let i = 0; i < iconCount; i++) {
          const icon = navIcons.nth(i);
          const classes = await icon.getAttribute('class') || '';

          // Navigation icons should use w-4 h-4 (small size)
          expect(classes).toMatch(/w-4\s+h-4|w-5\s+h-5/); // Allow sm or md for navigation
        }

        // Take screenshot of navigation area
        await expect(page.locator('[data-testid="navigation"]')).toHaveScreenshot('navigation-icons-validation.png');
      }
    });

    test('button icons should be appropriately sized', async ({ page }) => {
      await page.goto('/export');

      // Check button icons
      const buttonIcons = page.locator('button svg, button [class*="w-"]');
      const iconCount = await buttonIcons.count();

      if (iconCount > 0) {
        for (let i = 0; i < iconCount; i++) {
          const icon = buttonIcons.nth(i);
          const classes = await icon.getAttribute('class') || '';

          // Button icons should use w-4 h-4 or w-5 h-5 (small to medium)
          expect(classes).toMatch(/w-[4-5]\s+h-[4-5]/);
        }

        // Take screenshot of button area
        await expect(page.locator('[data-testid="export-buttons"]')).toHaveScreenshot('button-icons-validation.png');
      }
    });

    test('empty state icons should be appropriately large', async ({ page }) => {
      await page.goto('/study');

      // Wait for empty state to appear
      await page.waitForSelector('[data-testid="empty-state"]', { timeout: 5000 });

      const emptyStateIcons = page.locator('[data-testid="empty-state"] svg, [data-testid="empty-state"] [class*="w-"]');
      const iconCount = await emptyStateIcons.count();

      if (iconCount > 0) {
        for (let i = 0; i < iconCount; i++) {
          const icon = emptyStateIcons.nth(i);
          const classes = await icon.getAttribute('class') || '';

          // Empty state icons should use w-6 h-6 or w-8 h-8 (large to extra large)
          expect(classes).toMatch(/w-[6-8]\s+h-[6-8]/);
        }

        // Take screenshot of empty state
        await expect(page.locator('[data-testid="empty-state"]')).toHaveScreenshot('empty-state-icons-validation.png');
      }
    });

    test('status indicator icons should be small', async ({ page }) => {
      await page.goto('/');

      // Check status indicator icons
      const statusIcons = page.locator('[data-testid="connection-status"] svg, [data-testid="status-indicator"] svg');
      const iconCount = await statusIcons.count();

      if (iconCount > 0) {
        for (let i = 0; i < iconCount; i++) {
          const icon = statusIcons.nth(i);
          const classes = await icon.getAttribute('class') || '';

          // Status icons should use w-3 h-3 or w-4 h-4 (extra small to small)
          expect(classes).toMatch(/w-[3-4]\s+h-[3-4]/);
        }

        // Take screenshot of status indicators
        await expect(page.locator('[data-testid="connection-status"]')).toHaveScreenshot('status-icons-validation.png');
      }
    });
  });

  test.describe('Icon Alignment and Spacing', () => {
    test('icons should be properly aligned with text', async ({ page }) => {
      await page.goto('/');

      // Check icon-text combinations
      const iconTextElements = page.locator('button:has(svg), a:has(svg), [class*="flex"]:has(svg)');
      const elementCount = await iconTextElements.count();

      if (elementCount > 0) {
        // Take screenshot of various icon-text combinations
        for (let i = 0; i < Math.min(elementCount, 5); i++) {
          const element = iconTextElements.nth(i);
          if (await element.isVisible()) {
            await expect(element).toHaveScreenshot(`icon-text-alignment-${i}.png`, {
              threshold: 0.3,
            });
          }
        }
      }
    });

    test('icon containers should have appropriate spacing', async ({ page }) => {
      await page.goto('/');

      // Check feature cards with icons
      const featureCards = page.locator('[data-testid="feature-card"]');
      const cardCount = await featureCards.count();

      if (cardCount > 0) {
        for (let i = 0; i < Math.min(cardCount, 3); i++) {
          const card = featureCards.nth(i);
          if (await card.isVisible()) {
            await expect(card).toHaveScreenshot(`feature-card-spacing-${i}.png`, {
              threshold: 0.2,
            });
          }
        }
      }
    });
  });

  test.describe('Cross-Browser Icon Rendering', () => {
    ['chromium', 'firefox', 'webkit'].forEach(browserName => {
      test(`icons should render consistently in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        // Skip if not the target browser
        if (currentBrowser !== browserName) {
          test.skip();
        }

        await page.goto('/');

        // Take screenshots of key icon areas
        const iconAreas = [
          { selector: '[data-testid="navigation"]', name: 'navigation' },
          { selector: '[data-testid="feature-cards"]', name: 'feature-cards' },
          { selector: '[data-testid="connection-status"]', name: 'status' },
        ];

        for (const area of iconAreas) {
          const element = page.locator(area.selector);
          if (await element.count() > 0) {
            await expect(element.first()).toHaveScreenshot(`${area.name}-${browserName}.png`, {
              threshold: 0.3, // Allow for browser rendering differences
            });
          }
        }
      });
    });
  });

  test.describe('Icon Loading States', () => {
    test('loading spinner icons should be appropriately sized', async ({ page }) => {
      await page.goto('/documents');

      // Trigger a loading state by uploading a document
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.count() > 0) {
        // Create a test file
        const testFile = Buffer.from('test content');
        await fileInput.setInputFiles({
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: testFile,
        });

        // Wait for loading spinner to appear
        const loadingSpinner = page.locator('[data-testid="loading-spinner"], .animate-spin');
        if (await loadingSpinner.count() > 0) {
          await expect(loadingSpinner.first()).toHaveScreenshot('loading-spinner.png', {
            threshold: 0.4, // Allow for animation differences
          });
        }
      }
    });
  });

  test.describe('Responsive Icon Behavior', () => {
    test('icons should maintain proportions across screen sizes', async ({ page }) => {
      const testPaths = ['/', '/documents', '/search'];

      for (const path of testPaths) {
        await page.goto(path);

        for (const viewport of viewports) {
          await page.setViewportSize({ width: viewport.width, height: viewport.height });
          await page.waitForTimeout(300); // Allow for layout adjustment

          // Take full page screenshot to check overall icon proportions
          await expect(page).toHaveScreenshot(`full-page-${path.replace('/', 'home')}-${viewport.name}.png`, {
            fullPage: true,
            threshold: 0.3,
            maxDiffPixels: 500,
          });
        }
      }
    });

    test('touch targets should remain accessible on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 }); // iPhone 12 size
      await page.goto('/');

      // Check that clickable icons have adequate touch targets
      const clickableIcons = page.locator('button:has(svg), a:has(svg)');
      const iconCount = await clickableIcons.count();

      if (iconCount > 0) {
        for (let i = 0; i < Math.min(iconCount, 5); i++) {
          const icon = clickableIcons.nth(i);
          if (await icon.isVisible()) {
            const boundingBox = await icon.boundingBox();
            if (boundingBox) {
              // Touch targets should be at least 44px (iOS) or 48px (Android)
              expect(Math.min(boundingBox.width, boundingBox.height)).toBeGreaterThanOrEqual(44);
            }
          }
        }

        // Take screenshot of mobile interface
        await expect(page).toHaveScreenshot('mobile-touch-targets.png', {
          threshold: 0.2,
        });
      }
    });
  });
});