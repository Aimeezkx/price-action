import { Page, expect } from '@playwright/test'
import { injectAxe, checkA11y } from '@axe-core/playwright'

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Upload a test document and wait for processing
   */
  async uploadDocument(filename: string, waitForProcessing = true): Promise<string> {
    await this.page.goto('/upload')
    
    const fileInput = this.page.locator('input[type="file"]')
    await fileInput.setInputFiles(`test-data/${filename}`)
    
    await expect(this.page.locator(`text=${filename}`)).toBeVisible()
    await this.page.click('[data-testid="upload-submit"]')
    
    await expect(this.page.locator('text=Upload successful')).toBeVisible({ timeout: 10000 })
    
    if (waitForProcessing) {
      await this.waitForDocumentProcessing(filename)
    }
    
    return filename
  }

  /**
   * Wait for document processing to complete
   */
  async waitForDocumentProcessing(filename: string): Promise<void> {
    await this.page.goto('/documents')
    await this.page.click(`[data-testid="document-item"]:has-text("${filename}")`)
    await expect(this.page.locator('text=Processing complete')).toBeVisible({ timeout: 60000 })
  }

  /**
   * Navigate to study session and verify cards are available
   */
  async startStudySession(): Promise<void> {
    await this.page.goto('/study')
    await expect(this.page.locator('[data-testid="flashcard"]')).toBeVisible({ timeout: 10000 })
  }

  /**
   * Study multiple cards with specified grades
   */
  async studyCards(count: number, grades: number[] = [4, 3, 4, 5, 3]): Promise<void> {
    for (let i = 0; i < count; i++) {
      await expect(this.page.locator('[data-testid="flashcard"]')).toBeVisible()
      
      // Flip card
      await this.page.click('[data-testid="flip-button"]')
      await expect(this.page.locator('[data-testid="card-back"]')).toBeVisible()
      
      // Grade card
      const grade = grades[i % grades.length]
      await this.page.click(`[data-testid="grade-${grade}"]`)
      
      // Wait for next card or completion
      await this.page.waitForTimeout(500)
    }
  }

  /**
   * Perform search with optional filters
   */
  async performSearch(query: string, filters?: { [key: string]: boolean }): Promise<void> {
    await this.page.goto('/search')
    
    await this.page.fill('[data-testid="search-input"]', query)
    await this.page.press('[data-testid="search-input"]', 'Enter')
    
    await expect(this.page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 5000 })
    
    if (filters) {
      await this.page.click('[data-testid="filter-button"]')
      
      for (const [filterName, enabled] of Object.entries(filters)) {
        const checkbox = this.page.locator(`[data-testid="filter-${filterName}"]`)
        if (enabled) {
          await checkbox.check()
        } else {
          await checkbox.uncheck()
        }
      }
      
      await this.page.click('[data-testid="apply-filters"]')
      await this.page.waitForTimeout(1000)
    }
  }

  /**
   * Test accessibility on current page
   */
  async checkAccessibility(): Promise<void> {
    await injectAxe(this.page)
    await checkA11y(this.page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true }
    })
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation(): Promise<void> {
    // Test tab navigation
    await this.page.keyboard.press('Tab')
    await expect(this.page.locator(':focus')).toBeVisible()
    
    // Test escape key
    await this.page.keyboard.press('Escape')
    
    // Test enter key on focused element
    const focusedElement = this.page.locator(':focus')
    if (await focusedElement.count() > 0) {
      await this.page.keyboard.press('Enter')
    }
  }

  /**
   * Test responsive design at different viewport sizes
   */
  async testResponsiveDesign(): Promise<void> {
    const viewports = [
      { width: 1920, height: 1080, name: 'desktop' },
      { width: 1024, height: 768, name: 'tablet' },
      { width: 375, height: 667, name: 'mobile' }
    ]
    
    for (const viewport of viewports) {
      await this.page.setViewportSize({ width: viewport.width, height: viewport.height })
      await this.page.reload()
      
      // Verify responsive navigation
      const navSelector = `[data-testid="${viewport.name}-nav"]`
      await expect(this.page.locator(navSelector)).toBeVisible()
      
      // Test touch interactions on mobile
      if (viewport.name === 'mobile') {
        await this.testMobileInteractions()
      }
    }
  }

  /**
   * Test mobile-specific interactions
   */
  async testMobileInteractions(): Promise<void> {
    // Test swipe gestures if cards are present
    const card = this.page.locator('[data-testid="flashcard"]')
    if (await card.count() > 0) {
      const cardBox = await card.boundingBox()
      if (cardBox) {
        // Swipe left
        await this.page.touchscreen.tap(cardBox.x + cardBox.width * 0.8, cardBox.y + cardBox.height / 2)
        await this.page.touchscreen.tap(cardBox.x + cardBox.width * 0.2, cardBox.y + cardBox.height / 2)
      }
    }
    
    // Test pinch zoom on images
    const image = this.page.locator('[data-testid="chapter-image"]').first()
    if (await image.count() > 0) {
      const imageBox = await image.boundingBox()
      if (imageBox) {
        // Simulate pinch zoom
        await this.page.touchscreen.tap(imageBox.x + imageBox.width / 2, imageBox.y + imageBox.height / 2)
      }
    }
  }

  /**
   * Measure and verify performance metrics
   */
  async measurePerformance(): Promise<{ [key: string]: number }> {
    const metrics: { [key: string]: number } = {}
    
    // Measure page load time
    const startTime = Date.now()
    await this.page.reload()
    await this.page.waitForLoadState('networkidle')
    metrics.pageLoadTime = Date.now() - startTime
    
    // Measure search response time
    if (this.page.url().includes('/search')) {
      const searchStart = Date.now()
      await this.page.fill('[data-testid="search-input"]', 'test query')
      await this.page.press('[data-testid="search-input"]', 'Enter')
      await this.page.locator('[data-testid="search-results"]').waitFor()
      metrics.searchResponseTime = Date.now() - searchStart
    }
    
    // Measure card interaction time
    if (this.page.url().includes('/study')) {
      const card = this.page.locator('[data-testid="flashcard"]')
      if (await card.count() > 0) {
        const interactionStart = Date.now()
        await this.page.click('[data-testid="flip-button"]')
        await this.page.locator('[data-testid="card-back"]').waitFor()
        metrics.cardInteractionTime = Date.now() - interactionStart
      }
    }
    
    return metrics
  }

  /**
   * Test error handling scenarios
   */
  async testErrorHandling(): Promise<void> {
    // Test network error
    await this.page.route('**/api/**', route => route.abort())
    await this.page.reload()
    
    await expect(this.page.locator('[data-testid="error-message"]')).toBeVisible({ timeout: 5000 })
    
    // Test retry functionality
    await this.page.unroute('**/api/**')
    const retryButton = this.page.locator('[data-testid="retry-button"]')
    if (await retryButton.count() > 0) {
      await retryButton.click()
      await this.page.waitForTimeout(2000)
    }
  }

  /**
   * Simulate slow network conditions
   */
  async simulateSlowNetwork(): Promise<void> {
    await this.page.route('**/*', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.continue()
    })
  }

  /**
   * Clean up test data
   */
  async cleanup(): Promise<void> {
    // Clear any uploaded test documents
    await this.page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
  }
}

export class CrossBrowserTestHelpers {
  /**
   * Test browser-specific features
   */
  static async testBrowserSpecificFeatures(page: Page, browserName: string): Promise<void> {
    switch (browserName) {
      case 'chromium':
        await CrossBrowserTestHelpers.testChromeFeatures(page)
        break
      case 'firefox':
        await CrossBrowserTestHelpers.testFirefoxFeatures(page)
        break
      case 'webkit':
        await CrossBrowserTestHelpers.testSafariFeatures(page)
        break
    }
  }

  private static async testChromeFeatures(page: Page): Promise<void> {
    // Test Chrome-specific features like file system access
    const fileInput = page.locator('input[type="file"]')
    if (await fileInput.count() > 0) {
      // Test drag and drop
      await page.evaluate(() => {
        const event = new DragEvent('dragover', { bubbles: true })
        document.querySelector('input[type="file"]')?.dispatchEvent(event)
      })
    }
  }

  private static async testFirefoxFeatures(page: Page): Promise<void> {
    // Test Firefox-specific behaviors
    await page.keyboard.press('F11') // Test fullscreen
    await page.waitForTimeout(1000)
    await page.keyboard.press('F11') // Exit fullscreen
  }

  private static async testSafariFeatures(page: Page): Promise<void> {
    // Test Safari-specific behaviors
    const images = page.locator('img')
    if (await images.count() > 0) {
      // Test image loading behavior in Safari
      await images.first().waitFor({ state: 'visible' })
    }
  }
}