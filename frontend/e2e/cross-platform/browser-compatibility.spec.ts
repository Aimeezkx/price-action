import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';
import { devices } from '@playwright/test';

/**
 * Browser Compatibility Test Suite
 * Tests core functionality across different browsers to ensure consistent behavior
 */

const BROWSERS = ['chromium', 'firefox', 'webkit'] as const;
const TEST_DOCUMENT_PATH = 'test-data/sample-document.pdf';

// Core functionality tests that should work across all browsers
const CORE_FEATURES = [
  'document-upload',
  'chapter-navigation',
  'flashcard-review',
  'search-functionality',
  'responsive-design'
] as const;

test.describe('Browser Compatibility Tests', () => {
  
  test.describe('Document Upload Compatibility', () => {
    BROWSERS.forEach(browserName => {
      test(`Document upload works in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
        
        await page.goto('/');
        
        // Test file upload functionality
        const fileInput = page.locator('input[type="file"]');
        await expect(fileInput).toBeVisible();
        
        // Simulate file upload
        await fileInput.setInputFiles({
          name: 'test-document.pdf',
          mimeType: 'application/pdf',
          buffer: Buffer.from('Mock PDF content for testing')
        });
        
        // Verify upload initiated
        await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible({ timeout: 10000 });
        
        // Wait for processing to complete
        await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });
        
        // Verify document appears in library
        await expect(page.locator('[data-testid="document-item"]')).toBeVisible();
      });
    });
  });

  test.describe('Chapter Navigation Compatibility', () => {
    BROWSERS.forEach(browserName => {
      test(`Chapter navigation works in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
        
        // Setup: Ensure we have a document with chapters
        await page.goto('/');
        await setupTestDocument(page);
        
        // Navigate to chapters view
        await page.click('[data-testid="chapters-tab"]');
        
        // Verify chapters are displayed
        const chapters = page.locator('[data-testid="chapter-item"]');
        await expect(chapters.first()).toBeVisible();
        
        // Test chapter navigation
        await chapters.first().click();
        
        // Verify chapter content loads
        await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible();
        
        // Test chapter navigation controls
        const nextButton = page.locator('[data-testid="next-chapter"]');
        if (await nextButton.isVisible()) {
          await nextButton.click();
          await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible();
        }
      });
    });
  });

  test.describe('Flashcard Review Compatibility', () => {
    BROWSERS.forEach(browserName => {
      test(`Flashcard review works in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
        
        // Setup: Ensure we have cards to review
        await page.goto('/');
        await setupTestDocument(page);
        
        // Navigate to study mode
        await page.click('[data-testid="study-button"]');
        
        // Verify flashcard is displayed
        await expect(page.locator('[data-testid="flashcard"]')).toBeVisible();
        
        // Test card flip functionality
        await page.click('[data-testid="flip-button"]');
        await expect(page.locator('[data-testid="card-back"]')).toBeVisible();
        
        // Test grading functionality
        await page.click('[data-testid="grade-4"]');
        
        // Verify next card loads or session completes
        await page.waitForTimeout(1000);
        const nextCard = page.locator('[data-testid="flashcard"]');
        const sessionComplete = page.locator('[data-testid="session-complete"]');
        
        await expect(nextCard.or(sessionComplete)).toBeVisible();
      });
    });
  });

  test.describe('Search Functionality Compatibility', () => {
    BROWSERS.forEach(browserName => {
      test(`Search functionality works in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
        
        // Setup: Ensure we have searchable content
        await page.goto('/');
        await setupTestDocument(page);
        
        // Navigate to search
        await page.click('[data-testid="search-tab"]');
        
        // Test search input
        const searchInput = page.locator('[data-testid="search-input"]');
        await expect(searchInput).toBeVisible();
        
        await searchInput.fill('test query');
        await searchInput.press('Enter');
        
        // Verify search results or no results message
        const searchResults = page.locator('[data-testid="search-results"]');
        const noResults = page.locator('[data-testid="no-results"]');
        
        await expect(searchResults.or(noResults)).toBeVisible({ timeout: 10000 });
        
        // Test search filters if available
        const filterButton = page.locator('[data-testid="filter-button"]');
        if (await filterButton.isVisible()) {
          await filterButton.click();
          await expect(page.locator('[data-testid="filter-panel"]')).toBeVisible();
        }
      });
    });
  });

  test.describe('JavaScript API Compatibility', () => {
    BROWSERS.forEach(browserName => {
      test(`JavaScript APIs work in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
        
        await page.goto('/');
        
        // Test localStorage
        await page.evaluate(() => {
          localStorage.setItem('test-key', 'test-value');
        });
        
        const storedValue = await page.evaluate(() => {
          return localStorage.getItem('test-key');
        });
        
        expect(storedValue).toBe('test-value');
        
        // Test File API
        const fileApiSupported = await page.evaluate(() => {
          return typeof File !== 'undefined' && typeof FileReader !== 'undefined';
        });
        
        expect(fileApiSupported).toBe(true);
        
        // Test Fetch API
        const fetchSupported = await page.evaluate(() => {
          return typeof fetch !== 'undefined';
        });
        
        expect(fetchSupported).toBe(true);
        
        // Test modern JavaScript features
        const modernJsSupported = await page.evaluate(() => {
          try {
            // Test async/await, arrow functions, destructuring
            const testAsync = async () => {
              const obj = { a: 1, b: 2 };
              const { a, b } = obj;
              return a + b;
            };
            return typeof testAsync === 'function';
          } catch (e) {
            return false;
          }
        });
        
        expect(modernJsSupported).toBe(true);
      });
    });
  });

  test.describe('CSS Feature Compatibility', () => {
    BROWSERS.forEach(browserName => {
      test(`CSS features work in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        test.skip(currentBrowser !== browserName, `Skipping ${browserName} test in ${currentBrowser}`);
        
        await page.goto('/');
        
        // Test CSS Grid support
        const gridSupported = await page.evaluate(() => {
          const testElement = document.createElement('div');
          testElement.style.display = 'grid';
          return testElement.style.display === 'grid';
        });
        
        expect(gridSupported).toBe(true);
        
        // Test Flexbox support
        const flexSupported = await page.evaluate(() => {
          const testElement = document.createElement('div');
          testElement.style.display = 'flex';
          return testElement.style.display === 'flex';
        });
        
        expect(flexSupported).toBe(true);
        
        // Test CSS Custom Properties (variables)
        const customPropsSupported = await page.evaluate(() => {
          return CSS.supports('color', 'var(--test-color)');
        });
        
        expect(customPropsSupported).toBe(true);
        
        // Test CSS transforms
        const transformSupported = await page.evaluate(() => {
          return CSS.supports('transform', 'translateX(10px)');
        });
        
        expect(transformSupported).toBe(true);
      });
    });
  });
});

// Helper function to setup test document
async function setupTestDocument(page: Page) {
  // Check if we already have a test document
  const existingDoc = page.locator('[data-testid="document-item"]');
  
  if (await existingDoc.count() === 0) {
    // Upload a test document
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Mock PDF content for testing')
    });
    
    // Wait for processing to complete
    await expect(page.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });
  }
}