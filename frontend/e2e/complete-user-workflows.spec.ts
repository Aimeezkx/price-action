import { test, expect } from '@playwright/test'
import { TestHelpers } from './utils/test-helpers'

test.describe('Complete User Workflows', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
    await page.goto('/')
  })

  test.afterEach(async () => {
    await helpers.cleanup()
  })

  test('complete document upload to card review workflow', async ({ page }) => {
    // Upload document
    const filename = await helpers.uploadDocument('sample.pdf', true)
    
    // Verify document appears in documents list
    await page.goto('/documents')
    await expect(page.locator(`text=${filename}`)).toBeVisible()
    
    // Click on document to view details
    await page.click(`[data-testid="document-item"]:has-text("${filename}")`)
    
    // Verify chapters are generated
    await expect(page.locator('[data-testid="chapter-list"]')).toBeVisible()
    await expect(page.locator('[data-testid="chapter-item"]')).toHaveCount({ min: 1 })
    
    // Verify knowledge points are extracted
    await page.click('[data-testid="chapter-item"]:first-child')
    await expect(page.locator('[data-testid="knowledge-points"]')).toBeVisible()
    await expect(page.locator('[data-testid="knowledge-point"]')).toHaveCount({ min: 1 })
    
    // Navigate to study session
    await helpers.startStudySession()
    
    // Verify cards are generated and functional
    await expect(page.locator('[data-testid="flashcard"]')).toBeVisible()
    
    // Study multiple cards
    await helpers.studyCards(5)
    
    // Verify progress tracking
    await expect(page.locator('[data-testid="progress-indicator"]')).toBeVisible()
    const progressText = await page.locator('[data-testid="progress-text"]').textContent()
    expect(progressText).toContain('5')
    
    // Test SRS scheduling
    await page.goto('/study')
    const scheduledCards = page.locator('[data-testid="scheduled-cards-count"]')
    if (await scheduledCards.count() > 0) {
      const count = await scheduledCards.textContent()
      expect(parseInt(count || '0')).toBeGreaterThan(0)
    }
  })

  test('document processing with multiple formats', async ({ page }) => {
    const testFiles = ['sample.pdf', 'document.docx', 'notes.md']
    
    for (const filename of testFiles) {
      await helpers.uploadDocument(filename, true)
      
      // Verify processing completed successfully
      await page.goto('/documents')
      await page.click(`[data-testid="document-item"]:has-text("${filename}")`)
      await expect(page.locator('text=Processing complete')).toBeVisible()
      
      // Verify content extraction
      await expect(page.locator('[data-testid="chapter-list"]')).toBeVisible()
      
      // Verify cards were generated
      await page.goto('/study')
      await expect(page.locator('[data-testid="flashcard"]')).toBeVisible()
      
      // Study at least one card to verify functionality
      await helpers.studyCards(1)
    }
  })

  test('search and discovery workflow', async ({ page }) => {
    // Upload and process a document first
    await helpers.uploadDocument('sample.pdf', true)
    
    // Test full-text search
    await helpers.performSearch('machine learning')
    await expect(page.locator('[data-testid="search-result"]')).toHaveCount({ min: 1 })
    
    // Verify search result content
    const firstResult = page.locator('[data-testid="search-result"]').first()
    await expect(firstResult).toContainText('machine learning', { ignoreCase: true })
    
    // Test search with filters
    await helpers.performSearch('algorithm', {
      'definitions': true,
      'examples': false,
      'formulas': true
    })
    
    // Verify filtered results
    const filteredResults = page.locator('[data-testid="search-result"][data-type="definition"], [data-testid="search-result"][data-type="formula"]')
    await expect(filteredResults).toHaveCount({ min: 1 })
    
    // Test semantic search
    await page.click('[data-testid="semantic-search-toggle"]')
    await helpers.performSearch('AI techniques')
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Click on search result to navigate to content
    await page.click('[data-testid="search-result"]:first-child')
    await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
    
    // Test search history
    await page.goto('/search')
    await expect(page.locator('[data-testid="search-history"]')).toBeVisible()
    await expect(page.locator('[data-testid="history-item"]')).toHaveCount({ min: 2 })
  })

  test('chapter browsing and navigation workflow', async ({ page }) => {
    // Upload document with multiple chapters
    await helpers.uploadDocument('multi-chapter.pdf', true)
    
    // Navigate to document
    await page.goto('/documents')
    await page.click('[data-testid="document-item"]:first-child')
    
    // Verify table of contents
    await page.click('[data-testid="toc-toggle"]')
    await expect(page.locator('[data-testid="table-of-contents"]')).toBeVisible()
    await expect(page.locator('[data-testid="toc-item"]')).toHaveCount({ min: 2 })
    
    // Navigate through chapters
    const tocItems = page.locator('[data-testid="toc-item"]')
    const itemCount = await tocItems.count()
    
    for (let i = 0; i < Math.min(itemCount, 3); i++) {
      await tocItems.nth(i).click()
      await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
      
      // Verify chapter-specific content
      await expect(page.locator('[data-testid="chapter-title"]')).toBeVisible()
      await expect(page.locator('[data-testid="knowledge-points"]')).toBeVisible()
      
      // Test image viewer if images are present
      const images = page.locator('[data-testid="chapter-image"]')
      if (await images.count() > 0) {
        await images.first().click()
        await expect(page.locator('[data-testid="image-modal"]')).toBeVisible()
        
        // Test zoom functionality
        await page.click('[data-testid="zoom-in"]')
        await page.click('[data-testid="zoom-out"]')
        await page.click('[data-testid="close-modal"]')
      }
    }
    
    // Test chapter navigation buttons
    await page.click('[data-testid="next-chapter"]')
    await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
    
    await page.click('[data-testid="prev-chapter"]')
    await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
  })

  test('study session with different card types', async ({ page }) => {
    // Upload document that generates various card types
    await helpers.uploadDocument('comprehensive.pdf', true)
    
    await helpers.startStudySession()
    
    const cardTypes = ['definition', 'example', 'formula', 'image_hotspot']
    const encounteredTypes = new Set<string>()
    
    // Study cards and track different types
    for (let i = 0; i < 10; i++) {
      const card = page.locator('[data-testid="flashcard"]')
      if (await card.count() === 0) break
      
      const cardType = await card.getAttribute('data-type')
      if (cardType) {
        encounteredTypes.add(cardType)
      }
      
      // Handle different card types
      switch (cardType) {
        case 'image_hotspot':
          // Test hotspot interactions
          const hotspots = page.locator('[data-testid="hotspot"]')
          if (await hotspots.count() > 0) {
            await hotspots.first().click()
            await expect(page.locator('[data-testid="hotspot-feedback"]')).toBeVisible()
          }
          break
        
        case 'formula':
          // Test formula rendering
          await expect(page.locator('[data-testid="formula-content"]')).toBeVisible()
          break
        
        default:
          // Standard card interaction
          await page.click('[data-testid="flip-button"]')
          await expect(page.locator('[data-testid="card-back"]')).toBeVisible()
      }
      
      // Grade the card
      await page.click('[data-testid="grade-4"]')
      await page.waitForTimeout(500)
    }
    
    // Verify we encountered multiple card types
    expect(encounteredTypes.size).toBeGreaterThan(1)
  })

  test('export and data management workflow', async ({ page }) => {
    // Upload and process document
    await helpers.uploadDocument('sample.pdf', true)
    
    // Study some cards to generate progress data
    await helpers.startStudySession()
    await helpers.studyCards(3)
    
    // Navigate to export page
    await page.goto('/export')
    
    // Test different export formats
    const exportFormats = ['anki', 'csv', 'json']
    
    for (const format of exportFormats) {
      await page.click(`[data-testid="export-${format}"]`)
      
      // Wait for export to complete
      await expect(page.locator('[data-testid="export-success"]')).toBeVisible({ timeout: 10000 })
      
      // Verify download was initiated
      const downloadPromise = page.waitForEvent('download')
      await page.click('[data-testid="download-button"]')
      const download = await downloadPromise
      
      expect(download.suggestedFilename()).toContain(format)
    }
    
    // Test data synchronization
    await page.goto('/settings')
    await page.click('[data-testid="sync-data"]')
    await expect(page.locator('[data-testid="sync-success"]')).toBeVisible({ timeout: 5000 })
  })

  test('error recovery and resilience workflow', async ({ page }) => {
    // Test upload error recovery
    await page.goto('/upload')
    
    // Try to upload invalid file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('test-data/invalid.txt')
    await page.click('[data-testid="upload-submit"]')
    
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('text=Unsupported file type')).toBeVisible()
    
    // Test network error recovery
    await helpers.testErrorHandling()
    
    // Test large file handling
    await fileInput.setInputFiles('test-data/large.pdf')
    await page.click('[data-testid="upload-submit"]')
    
    // Should show progress indicator for large files
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible()
    
    // Test session recovery after page refresh
    await helpers.uploadDocument('sample.pdf', false)
    await page.reload()
    
    // Should maintain upload state
    await expect(page.locator('[data-testid="upload-status"]')).toBeVisible()
  })

  test('performance requirements validation', async ({ page }) => {
    const metrics = await helpers.measurePerformance()
    
    // Validate page load time (Requirement 2.3)
    expect(metrics.pageLoadTime).toBeLessThan(2000)
    
    // Test search performance (Requirement 2.2)
    await helpers.performSearch('test query')
    const searchMetrics = await helpers.measurePerformance()
    expect(searchMetrics.searchResponseTime).toBeLessThan(500)
    
    // Test card interaction performance (Requirement 2.4)
    await helpers.startStudySession()
    const studyMetrics = await helpers.measurePerformance()
    expect(studyMetrics.cardInteractionTime).toBeLessThan(200)
    
    // Test document processing performance (Requirement 2.1)
    const processingStart = Date.now()
    await helpers.uploadDocument('medium.pdf', true)
    const processingTime = Date.now() - processingStart
    
    // Should process 10-page document within 30 seconds
    expect(processingTime).toBeLessThan(30000)
  })
})