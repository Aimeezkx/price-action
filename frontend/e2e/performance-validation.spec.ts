import { test, expect } from '@playwright/test'
import { TestHelpers } from './utils/test-helpers'

test.describe('Performance Validation', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
  })

  test.afterEach(async () => {
    await helpers.cleanup()
  })

  test('page load performance requirements', async ({ page }) => {
    // Requirement 2.3: Frontend should load within 2 seconds
    const pages = [
      { url: '/', name: 'Home' },
      { url: '/documents', name: 'Documents' },
      { url: '/study', name: 'Study' },
      { url: '/search', name: 'Search' },
      { url: '/upload', name: 'Upload' }
    ]

    for (const { url, name } of pages) {
      const startTime = Date.now()
      await page.goto(url)
      await page.waitForLoadState('networkidle')
      const loadTime = Date.now() - startTime

      console.log(`${name} page load time: ${loadTime}ms`)
      expect(loadTime).toBeLessThan(2000)
    }
  })

  test('document processing performance', async ({ page }) => {
    // Requirement 2.1: Process 10-page PDF within 30 seconds
    const testCases = [
      { file: 'sample.pdf', pages: 5, maxTime: 15000 },
      { file: 'medium.pdf', pages: 20, maxTime: 45000 },
      { file: 'large.pdf', pages: 50, maxTime: 120000 }
    ]

    for (const { file, pages, maxTime } of testCases) {
      const startTime = Date.now()
      
      await helpers.uploadDocument(file, true)
      
      const processingTime = Date.now() - startTime
      console.log(`${file} (${pages} pages) processing time: ${processingTime}ms`)
      
      expect(processingTime).toBeLessThan(maxTime)
    }
  })

  test('search response time performance', async ({ page }) => {
    // Requirement 2.2: Search should return results within 500ms
    await helpers.uploadDocument('sample.pdf', true)
    
    const searchQueries = [
      'machine learning',
      'algorithm',
      'data structure',
      'artificial intelligence',
      'neural network'
    ]

    for (const query of searchQueries) {
      await page.goto('/search')
      
      const startTime = Date.now()
      await page.fill('[data-testid="search-input"]', query)
      await page.press('[data-testid="search-input"]', 'Enter')
      await page.locator('[data-testid="search-results"]').waitFor()
      const responseTime = Date.now() - startTime

      console.log(`Search "${query}" response time: ${responseTime}ms`)
      expect(responseTime).toBeLessThan(500)
    }
  })

  test('card interaction response time', async ({ page }) => {
    // Requirement 2.4: Card interactions should respond within 200ms
    await helpers.uploadDocument('sample.pdf', true)
    await helpers.startStudySession()

    const interactions = [
      { action: 'flip', selector: '[data-testid="flip-button"]' },
      { action: 'grade', selector: '[data-testid="grade-4"]' }
    ]

    for (const { action, selector } of interactions) {
      const startTime = Date.now()
      await page.click(selector)
      
      // Wait for visual feedback
      if (action === 'flip') {
        await page.locator('[data-testid="card-back"]').waitFor()
      } else {
        await page.waitForTimeout(100) // Wait for grade animation
      }
      
      const responseTime = Date.now() - startTime
      console.log(`${action} interaction response time: ${responseTime}ms`)
      
      expect(responseTime).toBeLessThan(200)
      
      // Reset for next test
      if (action === 'grade') {
        await page.waitForTimeout(500) // Wait for next card
      }
    }
  })

  test('memory usage monitoring', async ({ page }) => {
    // Monitor memory usage during intensive operations
    const getMemoryUsage = async () => {
      return await page.evaluate(() => {
        const memory = (performance as any).memory
        return memory ? {
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize,
          limit: memory.jsHeapSizeLimit
        } : null
      })
    }

    const initialMemory = await getMemoryUsage()
    console.log('Initial memory usage:', initialMemory)

    // Perform memory-intensive operations
    await helpers.uploadDocument('large.pdf', true)
    await helpers.startStudySession()
    
    // Study multiple cards
    for (let i = 0; i < 20; i++) {
      const card = page.locator('[data-testid="flashcard"]')
      if (await card.count() === 0) break
      
      await helpers.studyCards(1)
    }

    const finalMemory = await getMemoryUsage()
    console.log('Final memory usage:', finalMemory)

    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.used - initialMemory.used
      console.log(`Memory increase: ${memoryIncrease} bytes`)
      
      // Memory increase should be reasonable (less than 100MB)
      expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024)
    }
  })

  test('concurrent user simulation', async ({ browser }) => {
    // Simulate multiple users accessing the system
    const userCount = 5
    const contexts = []
    const pages = []

    try {
      // Create multiple browser contexts
      for (let i = 0; i < userCount; i++) {
        const context = await browser.newContext()
        const page = await context.newPage()
        contexts.push(context)
        pages.push(page)
      }

      // Simulate concurrent document uploads
      const uploadPromises = pages.map(async (page, index) => {
        const helper = new TestHelpers(page)
        const startTime = Date.now()
        
        await helper.uploadDocument(`sample-${index}.pdf`, true)
        
        const uploadTime = Date.now() - startTime
        return { user: index, uploadTime }
      })

      const results = await Promise.all(uploadPromises)
      
      // Verify all uploads completed successfully
      for (const result of results) {
        console.log(`User ${result.user} upload time: ${result.uploadTime}ms`)
        expect(result.uploadTime).toBeLessThan(60000) // Should complete within 1 minute
      }

      // Test concurrent study sessions
      const studyPromises = pages.map(async (page, index) => {
        const helper = new TestHelpers(page)
        const startTime = Date.now()
        
        await helper.startStudySession()
        await helper.studyCards(3)
        
        const studyTime = Date.now() - startTime
        return { user: index, studyTime }
      })

      const studyResults = await Promise.all(studyPromises)
      
      for (const result of studyResults) {
        console.log(`User ${result.user} study time: ${result.studyTime}ms`)
        expect(result.studyTime).toBeLessThan(10000) // Should complete within 10 seconds
      }

    } finally {
      // Clean up contexts
      for (const context of contexts) {
        await context.close()
      }
    }
  })

  test('network throttling performance', async ({ page }) => {
    // Test performance under slow network conditions
    await page.route('**/*', async route => {
      // Simulate slow 3G connection
      await new Promise(resolve => setTimeout(resolve, 100))
      await route.continue()
    })

    const startTime = Date.now()
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    const loadTime = Date.now() - startTime

    console.log(`Load time with network throttling: ${loadTime}ms`)
    
    // Should still load within reasonable time even with throttling
    expect(loadTime).toBeLessThan(10000)

    // Test search under throttling
    await helpers.uploadDocument('sample.pdf', true)
    
    const searchStart = Date.now()
    await helpers.performSearch('machine learning')
    const searchTime = Date.now() - searchStart

    console.log(`Search time with network throttling: ${searchTime}ms`)
    expect(searchTime).toBeLessThan(2000)
  })

  test('large dataset performance', async ({ page }) => {
    // Test performance with large amounts of data
    const documentCount = 10
    
    // Upload multiple documents
    for (let i = 0; i < documentCount; i++) {
      await helpers.uploadDocument(`document-${i}.pdf`, true)
    }

    // Test documents list performance
    const startTime = Date.now()
    await page.goto('/documents')
    await page.locator('[data-testid="document-item"]').first().waitFor()
    const listLoadTime = Date.now() - startTime

    console.log(`Documents list load time (${documentCount} docs): ${listLoadTime}ms`)
    expect(listLoadTime).toBeLessThan(3000)

    // Test search performance with large dataset
    const searchStart = Date.now()
    await helpers.performSearch('test')
    const searchTime = Date.now() - searchStart

    console.log(`Search time with large dataset: ${searchTime}ms`)
    expect(searchTime).toBeLessThan(1000)

    // Test study session with large card pool
    const studyStart = Date.now()
    await helpers.startStudySession()
    const studyLoadTime = Date.now() - studyStart

    console.log(`Study session load time with large dataset: ${studyLoadTime}ms`)
    expect(studyLoadTime).toBeLessThan(2000)
  })

  test('resource cleanup and garbage collection', async ({ page }) => {
    // Test that resources are properly cleaned up
    const getResourceCount = async () => {
      return await page.evaluate(() => {
        return {
          images: document.images.length,
          scripts: document.scripts.length,
          stylesheets: document.styleSheets.length,
          eventListeners: (window as any).getEventListeners ? 
            Object.keys((window as any).getEventListeners(document)).length : 0
        }
      })
    }

    const initialResources = await getResourceCount()
    console.log('Initial resources:', initialResources)

    // Perform operations that create resources
    await helpers.uploadDocument('with-images.pdf', true)
    
    await page.goto('/documents')
    await page.click('[data-testid="document-item"]:first-child')
    await page.click('[data-testid="chapter-item"]:first-child')

    // Navigate away and back
    await page.goto('/')
    await page.goto('/documents')

    const finalResources = await getResourceCount()
    console.log('Final resources:', finalResources)

    // Resource count should not grow excessively
    const imageIncrease = finalResources.images - initialResources.images
    expect(imageIncrease).toBeLessThan(50) // Reasonable limit for image growth
  })
})