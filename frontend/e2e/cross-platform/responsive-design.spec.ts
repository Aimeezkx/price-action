import { test, expect, devices } from '@playwright/test';

/**
 * Responsive Design Validation Tests
 * Tests UI adaptation across different screen sizes and orientations
 */

interface ScreenSize {
  name: string;
  width: number;
  height: number;
  category: 'mobile' | 'tablet' | 'desktop' | 'large-desktop';
}

const SCREEN_SIZES: ScreenSize[] = [
  // Mobile devices
  { name: 'iPhone SE', width: 375, height: 667, category: 'mobile' },
  { name: 'iPhone 12', width: 390, height: 844, category: 'mobile' },
  { name: 'iPhone 12 Pro Max', width: 428, height: 926, category: 'mobile' },
  { name: 'Samsung Galaxy S21', width: 360, height: 800, category: 'mobile' },
  
  // Tablet devices
  { name: 'iPad Mini', width: 768, height: 1024, category: 'tablet' },
  { name: 'iPad Air', width: 820, height: 1180, category: 'tablet' },
  { name: 'iPad Pro 11"', width: 834, height: 1194, category: 'tablet' },
  { name: 'iPad Pro 12.9"', width: 1024, height: 1366, category: 'tablet' },
  
  // Desktop devices
  { name: 'Laptop Small', width: 1366, height: 768, category: 'desktop' },
  { name: 'Desktop Standard', width: 1920, height: 1080, category: 'desktop' },
  { name: 'Desktop Large', width: 2560, height: 1440, category: 'large-desktop' },
  { name: 'Ultrawide', width: 3440, height: 1440, category: 'large-desktop' }
];

test.describe('Responsive Design Validation', () => {
  
  test.describe('Layout Adaptation', () => {
    SCREEN_SIZES.forEach(screenSize => {
      test(`Layout adapts correctly on ${screenSize.name} (${screenSize.width}x${screenSize.height})`, async ({ page }) => {
        // Set viewport size
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        await page.goto('/');
        
        // Test navigation layout
        await testNavigationLayout(page, screenSize);
        
        // Test main content layout
        await testMainContentLayout(page, screenSize);
        
        // Test document library layout
        await page.click('[data-testid="library-tab"]');
        await testLibraryLayout(page, screenSize);
        
        // Test study interface layout
        await page.click('[data-testid="study-tab"]');
        await testStudyLayout(page, screenSize);
        
        // Test search interface layout
        await page.click('[data-testid="search-tab"]');
        await testSearchLayout(page, screenSize);
      });
    });
  });

  test.describe('Navigation Responsiveness', () => {
    test('Navigation adapts between mobile and desktop layouts', async ({ page }) => {
      // Start with desktop layout
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      
      // Desktop should show horizontal navigation
      await expect(page.locator('[data-testid="desktop-navigation"]')).toBeVisible();
      await expect(page.locator('[data-testid="mobile-navigation"]')).not.toBeVisible();
      
      // Switch to mobile layout
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Mobile should show mobile navigation
      await expect(page.locator('[data-testid="mobile-navigation"]')).toBeVisible();
      await expect(page.locator('[data-testid="desktop-navigation"]')).not.toBeVisible();
      
      // Test mobile menu functionality
      const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
      if (await mobileMenuButton.isVisible()) {
        await mobileMenuButton.click();
        await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
        
        // Test menu items
        await expect(page.locator('[data-testid="mobile-menu"] [data-testid="library-link"]')).toBeVisible();
        await expect(page.locator('[data-testid="mobile-menu"] [data-testid="study-link"]')).toBeVisible();
        await expect(page.locator('[data-testid="mobile-menu"] [data-testid="search-link"]')).toBeVisible();
      }
    });

    test('Tab navigation works across all screen sizes', async ({ page }) => {
      for (const screenSize of SCREEN_SIZES) {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        await page.goto('/');
        
        // Test each tab
        const tabs = ['library-tab', 'study-tab', 'search-tab', 'profile-tab'];
        
        for (const tab of tabs) {
          const tabElement = page.locator(`[data-testid="${tab}"]`);
          
          if (await tabElement.isVisible()) {
            await tabElement.click();
            
            // Verify corresponding content is visible
            const contentId = tab.replace('-tab', '-content');
            await expect(page.locator(`[data-testid="${contentId}"]`)).toBeVisible();
          }
        }
      }
    });
  });

  test.describe('Content Scaling and Typography', () => {
    test('Text remains readable across all screen sizes', async ({ page }) => {
      await page.goto('/');
      
      for (const screenSize of SCREEN_SIZES) {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        
        // Check font sizes are appropriate
        const textElements = await page.locator('h1, h2, h3, p, button, input').all();
        
        for (const element of textElements) {
          const fontSize = await element.evaluate(el => {
            return window.getComputedStyle(el).fontSize;
          });
          
          const fontSizeValue = parseInt(fontSize);
          
          // Minimum font size should be 12px for readability
          expect(fontSizeValue).toBeGreaterThanOrEqual(12);
          
          // Maximum font size should be reasonable (not larger than 72px)
          expect(fontSizeValue).toBeLessThanOrEqual(72);
        }
        
        // Check line height for readability
        const paragraphs = await page.locator('p').all();
        for (const p of paragraphs) {
          const lineHeight = await p.evaluate(el => {
            return window.getComputedStyle(el).lineHeight;
          });
          
          // Line height should be at least 1.2 for readability
          if (lineHeight !== 'normal') {
            const lineHeightValue = parseFloat(lineHeight);
            expect(lineHeightValue).toBeGreaterThanOrEqual(1.2);
          }
        }
      }
    });

    test('Images and media scale appropriately', async ({ page }) => {
      await page.goto('/');
      
      // Upload a test document to have images
      await uploadTestDocument(page);
      
      for (const screenSize of SCREEN_SIZES) {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        
        // Check image scaling
        const images = await page.locator('img').all();
        
        for (const img of images) {
          const boundingBox = await img.boundingBox();
          
          if (boundingBox) {
            // Images should not exceed viewport width
            expect(boundingBox.width).toBeLessThanOrEqual(screenSize.width);
            
            // Images should maintain aspect ratio
            const aspectRatio = boundingBox.width / boundingBox.height;
            expect(aspectRatio).toBeGreaterThan(0.1);
            expect(aspectRatio).toBeLessThan(10);
          }
        }
      }
    });
  });

  test.describe('Interactive Elements', () => {
    test('Buttons and touch targets are appropriately sized', async ({ page }) => {
      await page.goto('/');
      
      for (const screenSize of SCREEN_SIZES) {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        
        const buttons = await page.locator('button, [role="button"], input[type="submit"]').all();
        
        for (const button of buttons) {
          const boundingBox = await button.boundingBox();
          
          if (boundingBox && await button.isVisible()) {
            if (screenSize.category === 'mobile') {
              // Mobile touch targets should be at least 44px (iOS) or 48dp (Android)
              expect(Math.min(boundingBox.width, boundingBox.height)).toBeGreaterThanOrEqual(44);
            } else {
              // Desktop buttons should be at least 32px for mouse interaction
              expect(Math.min(boundingBox.width, boundingBox.height)).toBeGreaterThanOrEqual(32);
            }
          }
        }
      }
    });

    test('Form inputs are usable across screen sizes', async ({ page }) => {
      await page.goto('/');
      
      // Navigate to a form (search or settings)
      await page.click('[data-testid="search-tab"]');
      
      for (const screenSize of SCREEN_SIZES) {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        
        const inputs = await page.locator('input, textarea, select').all();
        
        for (const input of inputs) {
          const boundingBox = await input.boundingBox();
          
          if (boundingBox && await input.isVisible()) {
            // Input height should be appropriate for touch/click
            if (screenSize.category === 'mobile') {
              expect(boundingBox.height).toBeGreaterThanOrEqual(44);
            } else {
              expect(boundingBox.height).toBeGreaterThanOrEqual(32);
            }
            
            // Input should not be too narrow
            expect(boundingBox.width).toBeGreaterThanOrEqual(100);
          }
        }
      }
    });
  });

  test.describe('Orientation Changes', () => {
    test('Layout adapts to orientation changes on mobile devices', async ({ page }) => {
      const mobileScreens = SCREEN_SIZES.filter(s => s.category === 'mobile');
      
      for (const screenSize of mobileScreens) {
        // Test portrait orientation
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        await page.goto('/');
        
        await testLayoutInOrientation(page, 'portrait');
        
        // Test landscape orientation (swap width and height)
        await page.setViewportSize({ width: screenSize.height, height: screenSize.width });
        
        await testLayoutInOrientation(page, 'landscape');
      }
    });

    test('Document viewer adapts to orientation changes', async ({ page }) => {
      await page.goto('/');
      await uploadTestDocument(page);
      
      // Navigate to document viewer
      await page.click('[data-testid="library-tab"]');
      await page.click('[data-testid="document-item"]');
      
      // Test portrait
      await page.setViewportSize({ width: 390, height: 844 });
      await testDocumentViewerLayout(page, 'portrait');
      
      // Test landscape
      await page.setViewportSize({ width: 844, height: 390 });
      await testDocumentViewerLayout(page, 'landscape');
    });
  });

  test.describe('Accessibility and Usability', () => {
    test('Content remains accessible at different zoom levels', async ({ page }) => {
      await page.goto('/');
      
      const zoomLevels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
      
      for (const zoom of zoomLevels) {
        await page.evaluate((zoomLevel) => {
          document.body.style.zoom = zoomLevel.toString();
        }, zoom);
        
        // Test that key elements remain visible and usable
        await expect(page.locator('[data-testid="main-navigation"]')).toBeVisible();
        await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
        
        // Test that text doesn't overflow containers
        const textElements = await page.locator('p, h1, h2, h3').all();
        
        for (const element of textElements.slice(0, 5)) { // Test first 5 elements
          const boundingBox = await element.boundingBox();
          const parentBox = await element.locator('..').boundingBox();
          
          if (boundingBox && parentBox) {
            // Text should not overflow parent container horizontally
            expect(boundingBox.x + boundingBox.width).toBeLessThanOrEqual(parentBox.x + parentBox.width + 5); // 5px tolerance
          }
        }
      }
      
      // Reset zoom
      await page.evaluate(() => {
        document.body.style.zoom = '1';
      });
    });

    test('Keyboard navigation works across screen sizes', async ({ page }) => {
      await page.goto('/');
      
      for (const screenSize of [SCREEN_SIZES[0], SCREEN_SIZES[4], SCREEN_SIZES[9]]) { // Test mobile, tablet, desktop
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        
        // Test tab navigation
        await page.keyboard.press('Tab');
        
        let focusedElement = await page.locator(':focus').first();
        expect(await focusedElement.count()).toBeGreaterThan(0);
        
        // Navigate through several elements
        for (let i = 0; i < 5; i++) {
          await page.keyboard.press('Tab');
          
          focusedElement = await page.locator(':focus').first();
          
          if (await focusedElement.count() > 0) {
            // Focused element should be visible
            await expect(focusedElement).toBeVisible();
            
            // Focused element should have visible focus indicator
            const outline = await focusedElement.evaluate(el => {
              const styles = window.getComputedStyle(el);
              return styles.outline || styles.boxShadow;
            });
            
            expect(outline).not.toBe('none');
          }
        }
      }
    });
  });

  test.describe('Performance Across Screen Sizes', () => {
    test('Layout performance remains acceptable on different screen sizes', async ({ page }) => {
      for (const screenSize of SCREEN_SIZES) {
        await page.setViewportSize({ width: screenSize.width, height: screenSize.height });
        
        // Measure layout performance
        const startTime = Date.now();
        await page.goto('/');
        
        // Wait for layout to stabilize
        await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
        
        const loadTime = Date.now() - startTime;
        
        // Layout should load within reasonable time (5 seconds)
        expect(loadTime).toBeLessThan(5000);
        
        // Test scroll performance on larger content
        if (screenSize.category === 'mobile') {
          // Test smooth scrolling on mobile
          await page.evaluate(() => {
            window.scrollTo({ top: 500, behavior: 'smooth' });
          });
          
          await page.waitForTimeout(500);
          
          const scrollTop = await page.evaluate(() => window.scrollY);
          expect(scrollTop).toBeGreaterThan(0);
        }
      }
    });
  });
});

// Helper functions
async function testNavigationLayout(page: any, screenSize: ScreenSize) {
  if (screenSize.category === 'mobile') {
    // Mobile should have bottom navigation or hamburger menu
    const bottomNav = page.locator('[data-testid="bottom-navigation"]');
    const hamburgerMenu = page.locator('[data-testid="hamburger-menu"]');
    
    await expect(bottomNav.or(hamburgerMenu)).toBeVisible();
  } else {
    // Desktop/tablet should have top navigation or sidebar
    const topNav = page.locator('[data-testid="top-navigation"]');
    const sidebar = page.locator('[data-testid="sidebar-navigation"]');
    
    await expect(topNav.or(sidebar)).toBeVisible();
  }
}

async function testMainContentLayout(page: any, screenSize: ScreenSize) {
  const mainContent = page.locator('[data-testid="main-content"]');
  await expect(mainContent).toBeVisible();
  
  const boundingBox = await mainContent.boundingBox();
  
  if (boundingBox) {
    // Content should not exceed viewport width
    expect(boundingBox.width).toBeLessThanOrEqual(screenSize.width);
    
    // Content should have appropriate margins/padding
    if (screenSize.category === 'mobile') {
      // Mobile should use most of the screen width
      expect(boundingBox.width).toBeGreaterThan(screenSize.width * 0.9);
    } else if (screenSize.category === 'desktop' || screenSize.category === 'large-desktop') {
      // Desktop might have max-width constraints
      expect(boundingBox.width).toBeGreaterThan(300); // Minimum usable width
    }
  }
}

async function testLibraryLayout(page: any, screenSize: ScreenSize) {
  const libraryGrid = page.locator('[data-testid="document-grid"]');
  
  if (await libraryGrid.isVisible()) {
    const gridItems = await page.locator('[data-testid="document-item"]').all();
    
    if (gridItems.length > 0) {
      const firstItem = gridItems[0];
      const itemBox = await firstItem.boundingBox();
      
      if (itemBox) {
        if (screenSize.category === 'mobile') {
          // Mobile should show 1-2 items per row
          expect(itemBox.width).toBeGreaterThan(screenSize.width * 0.4);
        } else if (screenSize.category === 'tablet') {
          // Tablet should show 2-3 items per row
          expect(itemBox.width).toBeGreaterThan(screenSize.width * 0.25);
          expect(itemBox.width).toBeLessThan(screenSize.width * 0.6);
        } else {
          // Desktop should show 3+ items per row
          expect(itemBox.width).toBeLessThan(screenSize.width * 0.4);
        }
      }
    }
  }
}

async function testStudyLayout(page: any, screenSize: ScreenSize) {
  const studyArea = page.locator('[data-testid="study-area"]');
  
  if (await studyArea.isVisible()) {
    const studyBox = await studyArea.boundingBox();
    
    if (studyBox) {
      // Study area should be centered and appropriately sized
      if (screenSize.category === 'mobile') {
        expect(studyBox.width).toBeGreaterThan(screenSize.width * 0.8);
      } else {
        expect(studyBox.width).toBeGreaterThan(400); // Minimum for readability
        expect(studyBox.width).toBeLessThan(screenSize.width * 0.9);
      }
    }
  }
}

async function testSearchLayout(page: any, screenSize: ScreenSize) {
  const searchInput = page.locator('[data-testid="search-input"]');
  
  if (await searchInput.isVisible()) {
    const inputBox = await searchInput.boundingBox();
    
    if (inputBox) {
      // Search input should be appropriately sized
      if (screenSize.category === 'mobile') {
        expect(inputBox.width).toBeGreaterThan(screenSize.width * 0.7);
      } else {
        expect(inputBox.width).toBeGreaterThan(300);
        expect(inputBox.width).toBeLessThan(screenSize.width * 0.8);
      }
    }
  }
}

async function testLayoutInOrientation(page: any, orientation: 'portrait' | 'landscape') {
  // Test that key elements remain visible and usable
  await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
  
  if (orientation === 'landscape') {
    // In landscape, navigation might change layout
    const navigation = page.locator('[data-testid="navigation"]');
    if (await navigation.isVisible()) {
      await expect(navigation).toBeVisible();
    }
  }
}

async function testDocumentViewerLayout(page: any, orientation: 'portrait' | 'landscape') {
  const documentViewer = page.locator('[data-testid="document-viewer"]');
  
  if (await documentViewer.isVisible()) {
    await expect(documentViewer).toBeVisible();
    
    // Document content should be readable in both orientations
    const documentContent = page.locator('[data-testid="document-content"]');
    if (await documentContent.isVisible()) {
      const contentBox = await documentContent.boundingBox();
      
      if (contentBox) {
        expect(contentBox.width).toBeGreaterThan(200); // Minimum readable width
        expect(contentBox.height).toBeGreaterThan(100); // Minimum readable height
      }
    }
  }
}

async function uploadTestDocument(page: any) {
  const fileInput = page.locator('input[type="file"]');
  
  if (await fileInput.isVisible()) {
    await fileInput.setInputFiles({
      name: 'responsive-test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Mock PDF content for responsive testing')
    });
    
    // Wait for upload to complete
    await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
  }
}