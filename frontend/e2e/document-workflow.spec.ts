import { test, expect } from '@playwright/test'
import { injectAxe, checkA11y } from '@axe-core/playwright'

test.describe('Document Learning Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await injectAxe(page)
  })

  test('complete document upload and study workflow', async ({ page }) => {
    // Navigate to upload page
    await page.click('[data-testid="upload-button"]')
    await expect(page).toHaveURL('/upload')

    // Upload a document
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('test-data/sample.pdf')

    // Wait for file to be selected
    await expect(page.locator('text=sample.pdf')).toBeVisible()

    // Click upload button
    await page.click('[data-testid="upload-submit"]')

    // Wait for upload to complete
    await expect(page.locator('text=Upload successful')).toBeVisible({ timeout: 10000 })

    // Navigate to documents page
    await page.click('[data-testid="documents-tab"]')
    await expect(page).toHaveURL('/documents')

    // Verify document appears in list
    await expect(page.locator('text=sample.pdf')).toBeVisible()

    // Click on document to view details
    await page.click('[data-testid="document-item"]:has-text("sample.pdf")')

    // Wait for processing to complete
    await expect(page.locator('text=Processing complete')).toBeVisible({ timeout: 30000 })

    // Verify chapters are displayed
    await expect(page.locator('[data-testid="chapter-list"]')).toBeVisible()
    await expect(page.locator('[data-testid="chapter-item"]')).toHaveCount({ min: 1 })

    // Navigate to study page
    await page.click('[data-testid="study-button"]')
    await expect(page).toHaveURL('/study')

    // Verify cards are available
    await expect(page.locator('[data-testid="flashcard"]')).toBeVisible()

    // Study a few cards
    for (let i = 0; i < 3; i++) {
      // Flip card
      await page.click('[data-testid="flip-button"]')
      await expect(page.locator('[data-testid="card-back"]')).toBeVisible()

      // Grade card
      await page.click('[data-testid="grade-4"]')

      // Wait for next card
      await page.waitForTimeout(500)
    }

    // Verify progress tracking
    await expect(page.locator('[data-testid="progress-indicator"]')).toBeVisible()
  })

  test('search functionality', async ({ page }) => {
    // Assume we have some processed documents
    await page.goto('/search')

    // Enter search query
    await page.fill('[data-testid="search-input"]', 'machine learning')
    await page.press('[data-testid="search-input"]', 'Enter')

    // Wait for search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    await expect(page.locator('[data-testid="search-result"]')).toHaveCount({ min: 1 })

    // Test search filters
    await page.click('[data-testid="filter-button"]')
    await page.check('[data-testid="filter-definitions"]')
    await page.click('[data-testid="apply-filters"]')

    // Verify filtered results
    await expect(page.locator('[data-testid="search-result"][data-type="definition"]')).toHaveCount({ min: 1 })

    // Test semantic search
    await page.click('[data-testid="semantic-search-toggle"]')
    await page.fill('[data-testid="search-input"]', 'AI algorithms')
    await page.press('[data-testid="search-input"]', 'Enter')

    // Verify semantic results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
  })

  test('chapter browsing', async ({ page }) => {
    // Navigate to a document with chapters
    await page.goto('/documents')
    await page.click('[data-testid="document-item"]:first-child')

    // Wait for document to load
    await expect(page.locator('[data-testid="chapter-list"]')).toBeVisible()

    // Click on first chapter
    await page.click('[data-testid="chapter-item"]:first-child')

    // Verify chapter content
    await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
    await expect(page.locator('[data-testid="knowledge-points"]')).toBeVisible()

    // Test image viewer
    const imageElement = page.locator('[data-testid="chapter-image"]:first-child')
    if (await imageElement.count() > 0) {
      await imageElement.click()
      await expect(page.locator('[data-testid="image-modal"]')).toBeVisible()
      
      // Test image zoom
      await page.click('[data-testid="zoom-in"]')
      await page.click('[data-testid="zoom-out"]')
      
      // Close modal
      await page.click('[data-testid="close-modal"]')
    }

    // Test table of contents navigation
    await page.click('[data-testid="toc-toggle"]')
    await expect(page.locator('[data-testid="table-of-contents"]')).toBeVisible()
    
    // Navigate to different chapter via TOC
    await page.click('[data-testid="toc-item"]:nth-child(2)')
    await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
  })

  test('image hotspot interaction', async ({ page }) => {
    // Navigate to a card with image hotspots
    await page.goto('/study')
    
    // Find an image hotspot card
    await page.locator('[data-testid="flashcard"][data-type="image_hotspot"]').first().waitFor()
    
    // Click on hotspot regions
    const hotspots = page.locator('[data-testid="hotspot"]')
    const hotspotCount = await hotspots.count()
    
    if (hotspotCount > 0) {
      // Click first hotspot
      await hotspots.first().click()
      await expect(page.locator('[data-testid="hotspot-feedback"]')).toBeVisible()
      
      // Test touch gestures on mobile
      if (await page.evaluate(() => window.innerWidth < 768)) {
        await page.touchscreen.tap(100, 200)
        await expect(page.locator('[data-testid="touch-feedback"]')).toBeVisible()
      }
    }
  })

  test('performance requirements', async ({ page }) => {
    // Test page load time
    const startTime = Date.now()
    await page.goto('/')
    const loadTime = Date.now() - startTime
    
    expect(loadTime).toBeLessThan(2000) // Should load within 2 seconds

    // Test search response time
    await page.goto('/search')
    const searchStart = Date.now()
    await page.fill('[data-testid="search-input"]', 'test query')
    await page.press('[data-testid="search-input"]', 'Enter')
    await page.locator('[data-testid="search-results"]').waitFor()
    const searchTime = Date.now() - searchStart
    
    expect(searchTime).toBeLessThan(500) // Should respond within 500ms

    // Test card interaction response time
    await page.goto('/study')
    await page.locator('[data-testid="flashcard"]').waitFor()
    
    const interactionStart = Date.now()
    await page.click('[data-testid="flip-button"]')
    await page.locator('[data-testid="card-back"]').waitFor()
    const interactionTime = Date.now() - interactionStart
    
    expect(interactionTime).toBeLessThan(200) // Should respond within 200ms
  })

  test('accessibility compliance', async ({ page }) => {
    // Test main pages for accessibility
    const pages = ['/', '/documents', '/study', '/search']
    
    for (const url of pages) {
      await page.goto(url)
      await checkA11y(page, null, {
        detailedReport: true,
        detailedReportOptions: { html: true }
      })
    }
  })

  test('keyboard navigation', async ({ page }) => {
    await page.goto('/')
    
    // Test tab navigation
    await page.keyboard.press('Tab')
    await expect(page.locator(':focus')).toBeVisible()
    
    // Navigate to study page via keyboard
    await page.goto('/study')
    await page.locator('[data-testid="flashcard"]').waitFor()
    
    // Test card navigation with keyboard
    await page.keyboard.press('Space') // Flip card
    await expect(page.locator('[data-testid="card-back"]')).toBeVisible()
    
    await page.keyboard.press('4') // Grade card
    await page.waitForTimeout(500)
    
    // Test search with keyboard
    await page.goto('/search')
    await page.keyboard.press('Tab') // Focus search input
    await page.keyboard.type('test query')
    await page.keyboard.press('Enter')
    
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
  })

  test('responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')
    await expect(page.locator('[data-testid="desktop-nav"]')).toBeVisible()
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.reload()
    await expect(page.locator('[data-testid="tablet-nav"]')).toBeVisible()
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 })
    await page.reload()
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible()
    
    // Test mobile interactions
    await page.goto('/study')
    await page.locator('[data-testid="flashcard"]').waitFor()
    
    // Test swipe gestures
    const card = page.locator('[data-testid="flashcard"]')
    await card.hover()
    await page.mouse.down()
    await page.mouse.move(100, 0)
    await page.mouse.up()
    
    // Should navigate to next card
    await page.waitForTimeout(500)
  })

  test('error handling', async ({ page }) => {
    // Test network error handling
    await page.route('**/api/**', route => route.abort())
    
    await page.goto('/documents')
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('text=Network error')).toBeVisible()
    
    // Test retry functionality
    await page.unroute('**/api/**')
    await page.click('[data-testid="retry-button"]')
    await expect(page.locator('[data-testid="documents-list"]')).toBeVisible()
    
    // Test invalid file upload
    await page.goto('/upload')
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('test-data/invalid.txt')
    
    await expect(page.locator('text=Unsupported file type')).toBeVisible()
  })
})