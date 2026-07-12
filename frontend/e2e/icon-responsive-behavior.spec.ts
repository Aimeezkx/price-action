/**
 * Icon Responsive Behavior Tests
 *
 * This test suite validates that icons behave correctly across different screen sizes
 * and maintain appropriate sizing and spacing in responsive layouts.
 */

import { test, expect, Page } from '@playwright/test';

// Responsive breakpoints based on Tailwind CSS defaults
const breakpoints = [
  { name: 'mobile-sm', width: 320, height: 568 },   // iPhone SE
  { name: 'mobile-md', width: 375, height: 667 },   // iPhone 8
  { name: 'mobile-lg', width: 414, height: 896 },   // iPhone 11 Pro Max
  { name: 'tablet-sm', width: 768, height: 1024 },  // iPad Portrait
  { name: 'tablet-lg', width: 1024, height: 768 },  // iPad Landscape
  { name: 'desktop-sm', width: 1280, height: 720 }, // Small Desktop
  { name: 'desktop-md', width: 1440, height: 900 }, // Medium Desktop
  { name: 'desktop-lg', width: 1920, height: 1080 }, // Large Desktop
];

// Icon size expectations for different contexts
const iconSizeExpectations = {
  navigation: {
    expectedClasses: ['w-4 h-4', 'w-5 h-5'], // sm or md
    minSize: 16,
    maxSize: 20,
  },
  button: {
    expectedClasses: ['w-4 h-4', 'w-5 h-5'], // sm or md
    minSize: 16,
    maxSize: 20,
  },
  feature: {
    expectedClasses: ['w-5 h-5', 'w-6 h-6'], // md or lg
    minSize: 20,
    maxSize: 24,
  },
  status: {
    expectedClasses: ['w-3 h-3', 'w-4 h-4'], // xs or sm
    minSize: 12,
    maxSize: 16,
  },
  emptyState: {
    expectedClasses: ['w-6 h-6', 'w-8 h-8'], // lg or xl
    minSize: 24,
    maxSize: 32,
  },
};

async function getIconDimensions(page: Page, selector: string): Promise<{ width: number; height: number } | null> {
  const element = page.locator(selector).first();
  if (await element.count() === 0) return null;

  const boundingBox = await element.boundingBox();
  return boundingBox ? { width: boundingBox.width, height: boundingBox.height } : null;
}

async function getIconClasses(page: Page, selector: string): Promise<string[]> {
  const element = page.locator(selector).first();
  if (await element.count() === 0) return [];

  const className = await element.getAttribute('class') || '';
  return className.split(/\s+/).filter(cls => cls.length > 0);
}

test.describe('Icon Responsive Behavior Tests', () => {
  test.describe('Navigation Icon Responsiveness', () => {
    test('navigation icons should maintain consistent size across breakpoints', async ({ page }) => {
      await page.goto('/');

      const results: Array<{
        breakpoint: string;
        dimensions: { width: number; height: number } | null;
        classes: string[];
      }> = [];

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300); // Allow for responsive adjustments

        const dimensions = await getIconDimensions(page, '[data-testid="navigation"] svg');
        const classes = await getIconClasses(page, '[data-testid="navigation"] svg');

        results.push({
          breakpoint: breakpoint.name,
          dimensions,
          classes,
        });
      }

      // Validate that navigation icons maintain consistent sizing
      const validResults = results.filter(r => r.dimensions !== null);
      if (validResults.length > 0) {
        const firstDimensions = validResults[0].dimensions!;

        validResults.forEach(result => {
          expect(result.dimensions!.width).toBeCloseTo(firstDimensions.width, 2);
          expect(result.dimensions!.height).toBeCloseTo(firstDimensions.height, 2);

          // Check that size is within expected range
          expect(result.dimensions!.width).toBeGreaterThanOrEqual(iconSizeExpectations.navigation.minSize);
          expect(result.dimensions!.width).toBeLessThanOrEqual(iconSizeExpectations.navigation.maxSize);
        });
      }
    });

    test('navigation should remain accessible on mobile devices', async ({ page }) => {
      const mobileBreakpoints = breakpoints.filter(bp => bp.name.startsWith('mobile'));

      for (const breakpoint of mobileBreakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.goto('/');
        await page.waitForTimeout(300);

        // Check that navigation icons are clickable and have adequate touch targets
        const navButtons = page.locator('[data-testid="navigation"] button, [data-testid="navigation"] a');
        const buttonCount = await navButtons.count();

        if (buttonCount > 0) {
          for (let i = 0; i < buttonCount; i++) {
            const button = navButtons.nth(i);
            if (await button.isVisible()) {
              const boundingBox = await button.boundingBox();
              if (boundingBox) {
                // Touch targets should be at least 44px
                expect(Math.min(boundingBox.width, boundingBox.height)).toBeGreaterThanOrEqual(44);
              }
            }
          }
        }
      }
    });
  });

  test.describe('Feature Card Icon Responsiveness', () => {
    test('feature card icons should scale appropriately', async ({ page }) => {
      await page.goto('/');

      const results: Array<{
        breakpoint: string;
        iconDimensions: { width: number; height: number } | null;
        containerDimensions: { width: number; height: number } | null;
      }> = [];

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300);

        const iconDimensions = await getIconDimensions(page, '[data-testid="feature-card"] svg');
        const containerDimensions = await getIconDimensions(page, '[data-testid="feature-card"]');

        results.push({
          breakpoint: breakpoint.name,
          iconDimensions,
          containerDimensions,
        });
      }

      // Validate that feature icons maintain appropriate proportions
      const validResults = results.filter(r => r.iconDimensions !== null && r.containerDimensions !== null);

      validResults.forEach(result => {
        const iconSize = result.iconDimensions!.width;
        const containerWidth = result.containerDimensions!.width;

        // Icon should not be too large relative to container
        expect(iconSize / containerWidth).toBeLessThan(0.5); // Icon should be less than 50% of container width

        // Icon should be within expected size range
        expect(iconSize).toBeGreaterThanOrEqual(iconSizeExpectations.feature.minSize);
        expect(iconSize).toBeLessThanOrEqual(iconSizeExpectations.feature.maxSize);
      });
    });
  });

  test.describe('Button Icon Responsiveness', () => {
    test('button icons should maintain readability across screen sizes', async ({ page }) => {
      await page.goto('/export');

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300);

        const buttonIcons = page.locator('button svg');
        const iconCount = await buttonIcons.count();

        if (iconCount > 0) {
          for (let i = 0; i < Math.min(iconCount, 3); i++) {
            const icon = buttonIcons.nth(i);
            if (await icon.isVisible()) {
              const dimensions = await icon.boundingBox();
              if (dimensions) {
                // Button icons should be readable but not overwhelming
                expect(dimensions.width).toBeGreaterThanOrEqual(iconSizeExpectations.button.minSize);
                expect(dimensions.width).toBeLessThanOrEqual(iconSizeExpectations.button.maxSize);

                // Icons should be square
                expect(Math.abs(dimensions.width - dimensions.height)).toBeLessThan(2);
              }
            }
          }
        }
      }
    });

    test('button text and icons should remain aligned', async ({ page }) => {
      await page.goto('/export');

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300);

        // Check buttons with both text and icons
        const textIconButtons = page.locator('button:has(svg):has-text(/\\w+/)');
        const buttonCount = await textIconButtons.count();

        if (buttonCount > 0) {
          for (let i = 0; i < Math.min(buttonCount, 3); i++) {
            const button = textIconButtons.nth(i);
            if (await button.isVisible()) {
              const buttonBox = await button.boundingBox();
              const iconBox = await button.locator('svg').boundingBox();

              if (buttonBox && iconBox) {
                // Icon should be vertically centered within button
                const buttonCenter = buttonBox.y + buttonBox.height / 2;
                const iconCenter = iconBox.y + iconBox.height / 2;
                expect(Math.abs(buttonCenter - iconCenter)).toBeLessThan(5); // Allow 5px tolerance
              }
            }
          }
        }
      }
    });
  });

  test.describe('Empty State Icon Responsiveness', () => {
    test('empty state icons should be prominent but not overwhelming', async ({ page }) => {
      await page.goto('/study');

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(500); // Allow for empty state to render

        const emptyStateIcon = page.locator('[data-testid="empty-state"] svg').first();
        if (await emptyStateIcon.count() > 0) {
          const dimensions = await emptyStateIcon.boundingBox();
          if (dimensions) {
            // Empty state icons should be larger but within reasonable bounds
            expect(dimensions.width).toBeGreaterThanOrEqual(iconSizeExpectations.emptyState.minSize);
            expect(dimensions.width).toBeLessThanOrEqual(iconSizeExpectations.emptyState.maxSize);

            // On mobile, icons might be slightly smaller but still prominent
            if (breakpoint.name.startsWith('mobile')) {
              expect(dimensions.width).toBeGreaterThanOrEqual(20); // At least 20px on mobile
            }
          }
        }
      }
    });
  });

  test.describe('Status Icon Responsiveness', () => {
    test('status indicators should remain visible but unobtrusive', async ({ page }) => {
      await page.goto('/');

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300);

        const statusIcons = page.locator('[data-testid="connection-status"] svg, [data-testid="status-indicator"] svg');
        const iconCount = await statusIcons.count();

        if (iconCount > 0) {
          for (let i = 0; i < iconCount; i++) {
            const icon = statusIcons.nth(i);
            if (await icon.isVisible()) {
              const dimensions = await icon.boundingBox();
              if (dimensions) {
                // Status icons should be small and unobtrusive
                expect(dimensions.width).toBeGreaterThanOrEqual(iconSizeExpectations.status.minSize);
                expect(dimensions.width).toBeLessThanOrEqual(iconSizeExpectations.status.maxSize);
              }
            }
          }
        }
      }
    });
  });

  test.describe('Icon Spacing and Layout', () => {
    test('icon spacing should adapt to screen size', async ({ page }) => {
      await page.goto('/');

      const spacingResults: Array<{
        breakpoint: string;
        iconSpacing: number[];
      }> = [];

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300);

        // Measure spacing between navigation icons
        const navIcons = page.locator('[data-testid="navigation"] svg');
        const iconCount = await navIcons.count();
        const spacing: number[] = [];

        if (iconCount > 1) {
          for (let i = 0; i < iconCount - 1; i++) {
            const currentIcon = await navIcons.nth(i).boundingBox();
            const nextIcon = await navIcons.nth(i + 1).boundingBox();

            if (currentIcon && nextIcon) {
              const gap = nextIcon.x - (currentIcon.x + currentIcon.width);
              spacing.push(gap);
            }
          }
        }

        spacingResults.push({
          breakpoint: breakpoint.name,
          iconSpacing: spacing,
        });
      }

      // Validate that spacing is consistent and appropriate
      spacingResults.forEach(result => {
        result.iconSpacing.forEach(gap => {
          // Spacing should be reasonable (not too tight, not too loose)
          expect(gap).toBeGreaterThanOrEqual(8); // At least 8px gap
          expect(gap).toBeLessThanOrEqual(32); // At most 32px gap
        });
      });
    });

    test('icon containers should maintain aspect ratios', async ({ page }) => {
      await page.goto('/');

      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.waitForTimeout(300);

        // Check feature card icon containers
        const iconContainers = page.locator('[data-testid="feature-card"] [class*="w-"][class*="h-"]');
        const containerCount = await iconContainers.count();

        if (containerCount > 0) {
          for (let i = 0; i < Math.min(containerCount, 3); i++) {
            const container = iconContainers.nth(i);
            if (await container.isVisible()) {
              const dimensions = await container.boundingBox();
              if (dimensions) {
                // Icon containers should be square or nearly square
                const aspectRatio = dimensions.width / dimensions.height;
                expect(aspectRatio).toBeCloseTo(1, 1); // Allow 10% deviation from square
              }
            }
          }
        }
      }
    });
  });

  test.describe('Performance Impact', () => {
    test('icon rendering should not impact page performance', async ({ page }) => {
      for (const breakpoint of [breakpoints[0], breakpoints[breakpoints.length - 1]]) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });

        // Measure page load performance
        const startTime = Date.now();
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        const loadTime = Date.now() - startTime;

        // Page should load within reasonable time
        expect(loadTime).toBeLessThan(5000); // 5 seconds max

        // Measure layout shift during resize
        const startResize = Date.now();
        await page.setViewportSize({
          width: breakpoint.width + 200,
          height: breakpoint.height + 100
        });
        await page.waitForTimeout(300);
        const resizeTime = Date.now() - startResize;

        // Resize should be smooth
        expect(resizeTime).toBeLessThan(1000); // 1 second max for resize
      }
    });
  });

  test.describe('Accessibility Compliance', () => {
    test('icons should maintain accessibility across screen sizes', async ({ page }) => {
      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.goto('/');
        await page.waitForTimeout(300);

        // Check that interactive icons have adequate touch targets
        const interactiveIcons = page.locator('button:has(svg), a:has(svg), [role="button"]:has(svg)');
        const iconCount = await interactiveIcons.count();

        if (iconCount > 0) {
          for (let i = 0; i < Math.min(iconCount, 5); i++) {
            const icon = interactiveIcons.nth(i);
            if (await icon.isVisible()) {
              const boundingBox = await icon.boundingBox();
              if (boundingBox) {
                // Touch targets should meet accessibility guidelines
                const minDimension = Math.min(boundingBox.width, boundingBox.height);
                if (breakpoint.name.startsWith('mobile')) {
                  expect(minDimension).toBeGreaterThanOrEqual(44); // iOS guideline
                } else {
                  expect(minDimension).toBeGreaterThanOrEqual(24); // Desktop minimum
                }
              }
            }
          }
        }
      }
    });
  });
});