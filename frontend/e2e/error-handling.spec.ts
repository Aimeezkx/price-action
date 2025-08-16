import { test, expect } from '@playwright/test'
import { TestHelpers } from './utils/test-helpers'

test.describe('Error Handling and Recovery', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
  })

  test.afterEach(async () => {
    await helpers.cleanup()
  })

  test.describe('Network Error Handling', () => {
    test('API failure recovery', async ({ page }) => {
      // Start with working API
      await page.goto('/')
      
      // Simulate API failure
      await page.route('**/api/**', route => route.abort())
      
      // Try to load documents page
      await page.goto('/documents')
      
      // Should show error message
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
      await expect(page.locator('text=Network error')).toBeVisible()
      
      // Should show retry button
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()
      
      // Restore API and test retry
      await page.unroute('**/api/**')
      await page.click('[data-testid="retry-button"]')
      
      // Should recover and show content
      await expect(page.locator('[data-testid="documents-list"]')).toBeVisible()
    })

    test('partial network failure handling', async ({ page }) => {
      // Allow some API calls to succeed, others to fail
      await page.route('**/api/documents/**', route => route.abort())
      await page.route('**/api/search/**', route => route.continue())
      
      await page.goto('/documents')
      
      // Should show specific error for documents
      await expect(page.locator('[data-testid="documents-error"]')).toBeVisible()
      
      // But search should still work
      await page.goto('/search')
      await helpers.performSearch('test')
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    })

    test('slow network handling', async ({ page }) => {
      // Simulate very slow network
      await page.route('**/api/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 5000))
        await route.continue()
      })
      
      await page.goto('/documents')
      
      // Should show loading indicator
      await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible()
      
      // Should eventually load or timeout gracefully
      await page.waitForTimeout(6000)
      
      const hasContent = await page.locator('[data-testid="documents-list"]').count() > 0
      const hasError = await page.locator('[data-testid="error-message"]').count() > 0
      
      expect(hasContent || hasError).toBe(true)
    })

    test('intermittent connection handling', async ({ page }) => {
      let requestCount = 0
      
      // Fail every other request
      await page.route('**/api/**', route => {
        requestCount++
        if (requestCount % 2 === 0) {
          route.abort()
        } else {
          route.continue()
        }
      })
      
      await helpers.uploadDocument('sample.pdf', false)
      
      // Should handle intermittent failures gracefully
      await page.waitForTimeout(2000)
      
      // Should show appropriate status
      const hasSuccess = await page.locator('[data-testid="upload-success"]').count() > 0
      const hasError = await page.locator('[data-testid="upload-error"]').count() > 0
      const hasRetry = await page.locator('[data-testid="retry-upload"]').count() > 0
      
      expect(hasSuccess || hasError || hasRetry).toBe(true)
    })
  })

  test.describe('File Upload Error Handling', () => {
    test('invalid file type rejection', async ({ page }) => {
      await page.goto('/upload')
      
      const invalidFiles = [
        'invalid.txt',
        'script.js',
        'image.jpg',
        'data.csv'
      ]
      
      for (const filename of invalidFiles) {
        const fileInput = page.locator('input[type="file"]')
        await fileInput.setInputFiles(`test-data/${filename}`)
        await page.click('[data-testid="upload-submit"]')
        
        // Should show error message
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
        await expect(page.locator('text=Unsupported file type')).toBeVisible()
        
        // Clear the error for next test
        await page.reload()
      }
    })

    test('file size limit handling', async ({ page }) => {
      await page.goto('/upload')
      
      // Try to upload oversized file
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/oversized.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Should show size error
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
      await expect(page.locator('text=File too large')).toBeVisible()
      
      // Should suggest file size limit
      await expect(page.locator('text=maximum')).toBeVisible()
    })

    test('corrupted file handling', async ({ page }) => {
      await page.goto('/upload')
      
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/corrupted.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Should detect corruption during processing
      await expect(page.locator('[data-testid="processing-error"]')).toBeVisible({ timeout: 30000 })
      await expect(page.locator('text=corrupted')).toBeVisible()
      
      // Should offer to try again
      await expect(page.locator('[data-testid="retry-upload"]')).toBeVisible()
    })

    test('upload interruption recovery', async ({ page }) => {
      await page.goto('/upload')
      
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/large.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Wait for upload to start
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible()
      
      // Simulate network interruption
      await page.route('**/api/upload/**', route => route.abort())
      
      // Should detect interruption
      await expect(page.locator('[data-testid="upload-error"]')).toBeVisible({ timeout: 10000 })
      
      // Should offer resume option
      await expect(page.locator('[data-testid="resume-upload"]')).toBeVisible()
      
      // Restore network and test resume
      await page.unroute('**/api/upload/**')
      await page.click('[data-testid="resume-upload"]')
      
      // Should continue from where it left off
      await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible()
    })
  })

  test.describe('Processing Error Handling', () => {
    test('document processing failure', async ({ page }) => {
      // Upload document that will fail processing
      await page.goto('/upload')
      
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/unprocessable.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Wait for processing to fail
      await expect(page.locator('[data-testid="processing-error"]')).toBeVisible({ timeout: 60000 })
      
      // Should show specific error message
      await expect(page.locator('text=processing failed')).toBeVisible()
      
      // Should offer options
      await expect(page.locator('[data-testid="retry-processing"]')).toBeVisible()
      await expect(page.locator('[data-testid="contact-support"]')).toBeVisible()
    })

    test('partial processing recovery', async ({ page }) => {
      await helpers.uploadDocument('partially-processable.pdf', false)
      
      // Should show partial success
      await expect(page.locator('[data-testid="partial-success"]')).toBeVisible({ timeout: 60000 })
      
      // Should indicate what was processed
      await expect(page.locator('text=Some content processed')).toBeVisible()
      
      // Should allow user to proceed with partial results
      await expect(page.locator('[data-testid="use-partial-results"]')).toBeVisible()
      
      // Should offer to retry failed parts
      await expect(page.locator('[data-testid="retry-failed-parts"]')).toBeVisible()
    })

    test('memory exhaustion handling', async ({ page }) => {
      // Try to process very large document
      await page.goto('/upload')
      
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/huge.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Should detect memory issues
      await expect(page.locator('[data-testid="memory-error"]')).toBeVisible({ timeout: 120000 })
      
      // Should suggest alternatives
      await expect(page.locator('text=too large to process')).toBeVisible()
      await expect(page.locator('[data-testid="split-document"]')).toBeVisible()
    })
  })

  test.describe('Study Session Error Handling', () => {
    test('card loading failure', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      
      // Start study session
      await helpers.startStudySession()
      
      // Simulate card loading failure
      await page.route('**/api/cards/**', route => route.abort())
      
      // Try to get next card
      await page.click('[data-testid="grade-4"]')
      
      // Should handle card loading error
      await expect(page.locator('[data-testid="card-error"]')).toBeVisible()
      await expect(page.locator('text=Unable to load next card')).toBeVisible()
      
      // Should offer retry
      await expect(page.locator('[data-testid="retry-card"]')).toBeVisible()
    })

    test('progress saving failure', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      // Simulate progress saving failure
      await page.route('**/api/progress/**', route => route.abort())
      
      // Grade a card
      await page.click('[data-testid="flip-button"]')
      await page.click('[data-testid="grade-4"]')
      
      // Should show save error
      await expect(page.locator('[data-testid="save-error"]')).toBeVisible()
      await expect(page.locator('text=Progress not saved')).toBeVisible()
      
      // Should offer to retry saving
      await expect(page.locator('[data-testid="retry-save"]')).toBeVisible()
    })

    test('session timeout handling', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      // Simulate session timeout
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 401,
          body: JSON.stringify({ error: 'Session expired' })
        })
      })
      
      // Try to grade a card
      await page.click('[data-testid="flip-button"]')
      await page.click('[data-testid="grade-4"]')
      
      // Should detect session timeout
      await expect(page.locator('[data-testid="session-expired"]')).toBeVisible()
      
      // Should offer to refresh session
      await expect(page.locator('[data-testid="refresh-session"]')).toBeVisible()
    })
  })

  test.describe('Search Error Handling', () => {
    test('search service failure', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await page.goto('/search')
      
      // Simulate search service failure
      await page.route('**/api/search/**', route => route.abort())
      
      // Try to search
      await page.fill('[data-testid="search-input"]', 'machine learning')
      await page.press('[data-testid="search-input"]', 'Enter')
      
      // Should show search error
      await expect(page.locator('[data-testid="search-error"]')).toBeVisible()
      await expect(page.locator('text=Search unavailable')).toBeVisible()
      
      // Should offer retry
      await expect(page.locator('[data-testid="retry-search"]')).toBeVisible()
    })

    test('empty search results handling', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      
      // Search for something that won't be found
      await helpers.performSearch('xyzabc123nonexistent')
      
      // Should show no results message
      await expect(page.locator('[data-testid="no-results"]')).toBeVisible()
      await expect(page.locator('text=No results found')).toBeVisible()
      
      // Should suggest alternatives
      await expect(page.locator('[data-testid="search-suggestions"]')).toBeVisible()
    })

    test('search timeout handling', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await page.goto('/search')
      
      // Simulate very slow search
      await page.route('**/api/search/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 10000))
        await route.continue()
      })
      
      // Start search
      await page.fill('[data-testid="search-input"]', 'test')
      await page.press('[data-testid="search-input"]', 'Enter')
      
      // Should show loading initially
      await expect(page.locator('[data-testid="search-loading"]')).toBeVisible()
      
      // Should timeout and show error
      await expect(page.locator('[data-testid="search-timeout"]')).toBeVisible({ timeout: 15000 })
      
      // Should offer to try again
      await expect(page.locator('[data-testid="retry-search"]')).toBeVisible()
    })
  })

  test.describe('Browser Compatibility Error Handling', () => {
    test('unsupported browser features', async ({ page }) => {
      // Simulate missing browser features
      await page.addInitScript(() => {
        // Remove File API support
        delete (window as any).File
        delete (window as any).FileReader
      })
      
      await page.goto('/upload')
      
      // Should detect missing features
      await expect(page.locator('[data-testid="browser-compatibility-warning"]')).toBeVisible()
      await expect(page.locator('text=browser not fully supported')).toBeVisible()
      
      // Should suggest alternatives
      await expect(page.locator('[data-testid="browser-upgrade-suggestion"]')).toBeVisible()
    })

    test('JavaScript disabled fallback', async ({ page }) => {
      // Disable JavaScript
      await page.setJavaScriptEnabled(false)
      
      await page.goto('/')
      
      // Should show noscript message
      const noscriptContent = await page.locator('noscript').textContent()
      expect(noscriptContent).toContain('JavaScript')
      
      // Re-enable JavaScript for cleanup
      await page.setJavaScriptEnabled(true)
    })
  })

  test.describe('Data Integrity Error Handling', () => {
    test('corrupted local storage recovery', async ({ page }) => {
      await page.goto('/')
      
      // Corrupt local storage
      await page.evaluate(() => {
        localStorage.setItem('app-data', 'corrupted-json-{invalid')
      })
      
      // Reload page
      await page.reload()
      
      // Should detect and handle corrupted data
      await expect(page.locator('[data-testid="data-recovery"]')).toBeVisible()
      
      // Should offer to reset data
      await expect(page.locator('[data-testid="reset-data"]')).toBeVisible()
      
      // Should offer to restore from backup
      await expect(page.locator('[data-testid="restore-backup"]')).toBeVisible()
    })

    test('sync conflict resolution', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      
      // Simulate sync conflict
      await page.evaluate(() => {
        // Create conflicting data
        localStorage.setItem('sync-conflict', 'true')
      })
      
      await page.goto('/study')
      
      // Should detect sync conflict
      await expect(page.locator('[data-testid="sync-conflict"]')).toBeVisible()
      
      // Should offer resolution options
      await expect(page.locator('[data-testid="use-local-data"]')).toBeVisible()
      await expect(page.locator('[data-testid="use-server-data"]')).toBeVisible()
      await expect(page.locator('[data-testid="merge-data"]')).toBeVisible()
    })
  })

  test.describe('Graceful Degradation', () => {
    test('offline mode functionality', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      
      // Go offline
      await page.context().setOffline(true)
      
      await page.goto('/study')
      
      // Should show offline indicator
      await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible()
      
      // Should still allow basic functionality
      const card = page.locator('[data-testid="flashcard"]')
      if (await card.count() > 0) {
        await card.click()
        await expect(page.locator('[data-testid="card-back"]')).toBeVisible()
      }
      
      // Should queue actions for when online
      await page.click('[data-testid="grade-4"]')
      await expect(page.locator('[data-testid="queued-actions"]')).toBeVisible()
      
      // Go back online
      await page.context().setOffline(false)
      
      // Should sync queued actions
      await expect(page.locator('[data-testid="sync-complete"]')).toBeVisible({ timeout: 10000 })
    })

    test('reduced functionality mode', async ({ page }) => {
      // Simulate limited resources
      await page.route('**/api/ai/**', route => route.abort())
      
      await helpers.uploadDocument('sample.pdf', true)
      
      // Should show reduced functionality warning
      await expect(page.locator('[data-testid="reduced-functionality"]')).toBeVisible()
      
      // Should still provide basic features
      await page.goto('/documents')
      await expect(page.locator('[data-testid="documents-list"]')).toBeVisible()
      
      // AI-dependent features should be disabled
      await page.goto('/study')
      const aiFeatures = page.locator('[data-testid="ai-generated-content"]')
      if (await aiFeatures.count() > 0) {
        await expect(aiFeatures).toHaveClass(/disabled/)
      }
    })
  })
})