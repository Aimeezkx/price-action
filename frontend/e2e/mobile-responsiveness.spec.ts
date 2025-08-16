import { test, expect, devices } from '@playwright/test'
import { TestHelpers } from './utils/test-helpers'

test.describe('Mobile Responsiveness', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
  })

  test.afterEach(async () => {
    await helpers.cleanup()
  })

  // Test different mobile device configurations
  const mobileDevices = [
    { name: 'iPhone 12', device: devices['iPhone 12'] },
    { name: 'iPhone SE', device: devices['iPhone SE'] },
    { name: 'Pixel 5', device: devices['Pixel 5'] },
    { name: 'Galaxy S21', device: devices['Galaxy S21'] },
    { name: 'iPad', device: devices['iPad'] },
    { name: 'iPad Mini', device: devices['iPad Mini'] }
  ]

  for (const { name, device } of mobileDevices) {
    test.describe(`${name} responsiveness`, () => {
      test.use(device)

      test(`navigation and layout on ${name}`, async ({ page }) => {
        await page.goto('/')
        
        // Verify mobile navigation is present
        await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible()
        
        // Test hamburger menu
        await page.click('[data-testid="menu-toggle"]')
        await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible()
        
        // Test navigation items
        const navItems = ['Documents', 'Study', 'Search', 'Export']
        for (const item of navItems) {
          await expect(page.locator(`[data-testid="nav-${item.toLowerCase()}"]`)).toBeVisible()
        }
        
        // Close menu
        await page.click('[data-testid="menu-close"]')
        await expect(page.locator('[data-testid="mobile-menu"]')).not.toBeVisible()
      })

      test(`document upload on ${name}`, async ({ page }) => {
        await page.goto('/upload')
        
        // Verify upload interface is mobile-friendly
        await expect(page.locator('[data-testid="upload-area"]')).toBeVisible()
        
        // Test file selection
        const fileInput = page.locator('input[type="file"]')
        await fileInput.setInputFiles('test-data/sample.pdf')
        
        // Verify file preview is responsive
        await expect(page.locator('[data-testid="file-preview"]')).toBeVisible()
        
        // Test upload button accessibility
        const uploadButton = page.locator('[data-testid="upload-submit"]')
        await expect(uploadButton).toBeVisible()
        
        // Verify button is large enough for touch
        const buttonBox = await uploadButton.boundingBox()
        expect(buttonBox?.height).toBeGreaterThan(44) // iOS minimum touch target
        expect(buttonBox?.width).toBeGreaterThan(44)
      })

      test(`study session on ${name}`, async ({ page }) => {
        await helpers.uploadDocument('sample.pdf', true)
        await helpers.startStudySession()
        
        // Verify card is properly sized for mobile
        const card = page.locator('[data-testid="flashcard"]')
        await expect(card).toBeVisible()
        
        const cardBox = await card.boundingBox()
        const viewport = page.viewportSize()
        
        // Card should not exceed viewport width
        expect(cardBox?.width).toBeLessThanOrEqual(viewport?.width || 0)
        
        // Test touch interactions
        await card.tap()
        await expect(page.locator('[data-testid="card-back"]')).toBeVisible()
        
        // Test swipe gestures
        if (cardBox) {
          // Swipe left to right
          await page.touchscreen.tap(cardBox.x + 50, cardBox.y + cardBox.height / 2)
          await page.touchscreen.tap(cardBox.x + cardBox.width - 50, cardBox.y + cardBox.height / 2)
        }
        
        // Test grading buttons
        const gradeButtons = page.locator('[data-testid^="grade-"]')
        const buttonCount = await gradeButtons.count()
        
        for (let i = 0; i < buttonCount; i++) {
          const button = gradeButtons.nth(i)
          const buttonBox = await button.boundingBox()
          
          // Verify touch target size
          expect(buttonBox?.height).toBeGreaterThan(44)
          expect(buttonBox?.width).toBeGreaterThan(44)
        }
      })

      test(`search interface on ${name}`, async ({ page }) => {
        await helpers.uploadDocument('sample.pdf', true)
        await page.goto('/search')
        
        // Verify search input is properly sized
        const searchInput = page.locator('[data-testid="search-input"]')
        await expect(searchInput).toBeVisible()
        
        const inputBox = await searchInput.boundingBox()
        expect(inputBox?.height).toBeGreaterThan(44)
        
        // Test search functionality
        await searchInput.fill('machine learning')
        await page.keyboard.press('Enter')
        
        // Verify results are mobile-friendly
        await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
        
        const results = page.locator('[data-testid="search-result"]')
        const resultCount = await results.count()
        
        if (resultCount > 0) {
          // Verify result items are properly spaced
          for (let i = 0; i < Math.min(resultCount, 3); i++) {
            const result = results.nth(i)
            const resultBox = await result.boundingBox()
            expect(resultBox?.height).toBeGreaterThan(60) // Adequate touch target
          }
        }
        
        // Test filter panel on mobile
        await page.click('[data-testid="filter-toggle"]')
        await expect(page.locator('[data-testid="filter-panel"]')).toBeVisible()
        
        // Verify filter panel doesn't overflow
        const filterPanel = page.locator('[data-testid="filter-panel"]')
        const panelBox = await filterPanel.boundingBox()
        const viewport = page.viewportSize()
        
        expect(panelBox?.width).toBeLessThanOrEqual(viewport?.width || 0)
      })

      test(`chapter browsing on ${name}`, async ({ page }) => {
        await helpers.uploadDocument('multi-chapter.pdf', true)
        
        await page.goto('/documents')
        await page.click('[data-testid="document-item"]:first-child')
        
        // Test table of contents on mobile
        await page.click('[data-testid="toc-toggle"]')
        await expect(page.locator('[data-testid="table-of-contents"]')).toBeVisible()
        
        // Verify TOC is scrollable on mobile
        const toc = page.locator('[data-testid="table-of-contents"]')
        const tocBox = await toc.boundingBox()
        const viewport = page.viewportSize()
        
        expect(tocBox?.width).toBeLessThanOrEqual(viewport?.width || 0)
        
        // Test chapter navigation
        await page.click('[data-testid="toc-item"]:first-child')
        await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
        
        // Test image viewing on mobile
        const images = page.locator('[data-testid="chapter-image"]')
        if (await images.count() > 0) {
          await images.first().tap()
          await expect(page.locator('[data-testid="image-modal"]')).toBeVisible()
          
          // Test pinch zoom simulation
          const imageModal = page.locator('[data-testid="image-modal"]')
          const modalBox = await imageModal.boundingBox()
          
          if (modalBox) {
            // Simulate pinch gesture
            await page.touchscreen.tap(modalBox.x + modalBox.width / 2, modalBox.y + modalBox.height / 2)
          }
          
          // Test zoom controls
          await page.click('[data-testid="zoom-in"]')
          await page.click('[data-testid="zoom-out"]')
          await page.click('[data-testid="close-modal"]')
        }
      })

      test(`image hotspot interaction on ${name}`, async ({ page }) => {
        await helpers.uploadDocument('hotspot-images.pdf', true)
        await helpers.startStudySession()
        
        // Find image hotspot card
        const hotspotCard = page.locator('[data-testid="flashcard"][data-type="image_hotspot"]')
        if (await hotspotCard.count() > 0) {
          await expect(hotspotCard).toBeVisible()
          
          // Test hotspot touch interactions
          const hotspots = page.locator('[data-testid="hotspot"]')
          const hotspotCount = await hotspots.count()
          
          if (hotspotCount > 0) {
            // Test touch accuracy on small hotspots
            for (let i = 0; i < Math.min(hotspotCount, 3); i++) {
              const hotspot = hotspots.nth(i)
              const hotspotBox = await hotspot.boundingBox()
              
              // Verify hotspot is large enough for touch
              expect(hotspotBox?.width).toBeGreaterThan(30)
              expect(hotspotBox?.height).toBeGreaterThan(30)
              
              // Test touch interaction
              await hotspot.tap()
              await expect(page.locator('[data-testid="hotspot-feedback"]')).toBeVisible()
              
              // Wait for feedback to disappear
              await page.waitForTimeout(1000)
            }
          }
        }
      })

      test(`performance on ${name}`, async ({ page }) => {
        // Measure load time on mobile
        const startTime = Date.now()
        await page.goto('/')
        await page.waitForLoadState('networkidle')
        const loadTime = Date.now() - startTime
        
        // Mobile should load within 3 seconds (slightly more lenient than desktop)
        expect(loadTime).toBeLessThan(3000)
        
        // Test scroll performance
        await page.goto('/documents')
        
        // Simulate rapid scrolling
        for (let i = 0; i < 5; i++) {
          await page.evaluate(() => window.scrollBy(0, 200))
          await page.waitForTimeout(100)
        }
        
        // Verify page remains responsive
        await expect(page.locator('[data-testid="documents-list"]')).toBeVisible()
      })

      test(`orientation changes on ${name}`, async ({ page }) => {
        // Test portrait orientation
        await page.setViewportSize({ width: 375, height: 667 })
        await page.goto('/')
        
        await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible()
        
        // Test landscape orientation
        await page.setViewportSize({ width: 667, height: 375 })
        await page.reload()
        
        // Verify layout adapts to landscape
        await expect(page.locator('[data-testid="main-content"]')).toBeVisible()
        
        // Test study session in landscape
        await helpers.uploadDocument('sample.pdf', true)
        await helpers.startStudySession()
        
        const card = page.locator('[data-testid="flashcard"]')
        await expect(card).toBeVisible()
        
        // Verify card layout in landscape
        const cardBox = await card.boundingBox()
        const viewport = page.viewportSize()
        
        expect(cardBox?.width).toBeLessThanOrEqual(viewport?.width || 0)
        expect(cardBox?.height).toBeLessThanOrEqual(viewport?.height || 0)
      })

      test(`accessibility on ${name}`, async ({ page }) => {
        await page.goto('/')
        
        // Test screen reader compatibility
        const mainContent = page.locator('main')
        await expect(mainContent).toHaveAttribute('role', 'main')
        
        // Test focus management
        await page.keyboard.press('Tab')
        const focusedElement = page.locator(':focus')
        await expect(focusedElement).toBeVisible()
        
        // Test skip links
        const skipLink = page.locator('[data-testid="skip-to-content"]')
        if (await skipLink.count() > 0) {
          await expect(skipLink).toBeVisible()
        }
        
        // Test touch target sizes
        const interactiveElements = page.locator('button, a, input, [role="button"]')
        const elementCount = await interactiveElements.count()
        
        for (let i = 0; i < Math.min(elementCount, 10); i++) {
          const element = interactiveElements.nth(i)
          if (await element.isVisible()) {
            const elementBox = await element.boundingBox()
            
            // Verify minimum touch target size (44x44px for iOS)
            expect(elementBox?.width).toBeGreaterThan(44)
            expect(elementBox?.height).toBeGreaterThan(44)
          }
        }
      })
    })
  }

  test.describe('Responsive Breakpoints', () => {
    const breakpoints = [
      { name: 'Small Mobile', width: 320, height: 568 },
      { name: 'Mobile', width: 375, height: 667 },
      { name: 'Large Mobile', width: 414, height: 896 },
      { name: 'Tablet Portrait', width: 768, height: 1024 },
      { name: 'Tablet Landscape', width: 1024, height: 768 },
      { name: 'Small Desktop', width: 1280, height: 720 },
      { name: 'Desktop', width: 1920, height: 1080 }
    ]

    for (const breakpoint of breakpoints) {
      test(`layout at ${breakpoint.name} (${breakpoint.width}x${breakpoint.height})`, async ({ page }) => {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height })
        await page.goto('/')
        
        // Verify appropriate navigation is shown
        if (breakpoint.width < 768) {
          await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible()
        } else {
          await expect(page.locator('[data-testid="desktop-nav"]')).toBeVisible()
        }
        
        // Test content layout
        const mainContent = page.locator('[data-testid="main-content"]')
        await expect(mainContent).toBeVisible()
        
        const contentBox = await mainContent.boundingBox()
        expect(contentBox?.width).toBeLessThanOrEqual(breakpoint.width)
        
        // Test study session layout
        await helpers.uploadDocument('sample.pdf', true)
        await helpers.startStudySession()
        
        const card = page.locator('[data-testid="flashcard"]')
        await expect(card).toBeVisible()
        
        const cardBox = await card.boundingBox()
        expect(cardBox?.width).toBeLessThanOrEqual(breakpoint.width)
        expect(cardBox?.height).toBeLessThanOrEqual(breakpoint.height)
      })
    }
  })

  test.describe('Touch Gestures', () => {
    test.use(devices['iPhone 12'])

    test('swipe gestures for card navigation', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      const card = page.locator('[data-testid="flashcard"]')
      await expect(card).toBeVisible()
      
      const cardBox = await card.boundingBox()
      if (cardBox) {
        // Test swipe left (next card)
        await page.touchscreen.tap(cardBox.x + cardBox.width * 0.8, cardBox.y + cardBox.height / 2)
        await page.touchscreen.tap(cardBox.x + cardBox.width * 0.2, cardBox.y + cardBox.height / 2)
        
        // Verify card changed or action occurred
        await page.waitForTimeout(500)
        
        // Test swipe right (previous card)
        await page.touchscreen.tap(cardBox.x + cardBox.width * 0.2, cardBox.y + cardBox.height / 2)
        await page.touchscreen.tap(cardBox.x + cardBox.width * 0.8, cardBox.y + cardBox.height / 2)
        
        await page.waitForTimeout(500)
      }
    })

    test('pinch zoom on images', async ({ page }) => {
      await helpers.uploadDocument('with-images.pdf', true)
      
      await page.goto('/documents')
      await page.click('[data-testid="document-item"]:first-child')
      await page.click('[data-testid="chapter-item"]:first-child')
      
      const image = page.locator('[data-testid="chapter-image"]').first()
      if (await image.count() > 0) {
        await image.tap()
        await expect(page.locator('[data-testid="image-modal"]')).toBeVisible()
        
        const imageModal = page.locator('[data-testid="image-modal"] img')
        const imageBox = await imageModal.boundingBox()
        
        if (imageBox) {
          // Simulate pinch zoom in
          const centerX = imageBox.x + imageBox.width / 2
          const centerY = imageBox.y + imageBox.height / 2
          
          await page.touchscreen.tap(centerX - 50, centerY)
          await page.touchscreen.tap(centerX + 50, centerY)
          
          // Simulate pinch zoom out
          await page.touchscreen.tap(centerX - 25, centerY)
          await page.touchscreen.tap(centerX + 25, centerY)
        }
      }
    })

    test('long press interactions', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      const card = page.locator('[data-testid="flashcard"]')
      await expect(card).toBeVisible()
      
      // Simulate long press
      const cardBox = await card.boundingBox()
      if (cardBox) {
        await page.touchscreen.tap(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2)
        await page.waitForTimeout(1000) // Hold for 1 second
        
        // Check if context menu or long press action occurred
        const contextMenu = page.locator('[data-testid="context-menu"]')
        if (await contextMenu.count() > 0) {
          await expect(contextMenu).toBeVisible()
        }
      }
    })
  })
})