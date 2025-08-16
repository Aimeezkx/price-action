import { test, expect, devices } from '@playwright/test'
import { TestHelpers, CrossBrowserTestHelpers } from './utils/test-helpers'

test.describe('Cross-Browser Compatibility', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
    await page.goto('/')
  })

  test.afterEach(async () => {
    await helpers.cleanup()
  })

  // Test core functionality across all browsers
  for (const browserName of ['chromium', 'firefox', 'webkit']) {
    test.describe(`${browserName} compatibility`, () => {
      test.use({ 
        ...devices[browserName === 'webkit' ? 'Desktop Safari' : 
                  browserName === 'firefox' ? 'Desktop Firefox' : 'Desktop Chrome'] 
      })

      test(`document upload and processing in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
        // Upload document
        await helpers.uploadDocument('sample.pdf', true)
        
        // Verify document appears in list
        await page.goto('/documents')
        await expect(page.locator('[data-testid="document-item"]')).toHaveCount({ min: 1 })
        
        // Test browser-specific features
        await CrossBrowserTestHelpers.testBrowserSpecificFeatures(page, currentBrowser)
        
        // Verify processing completed
        await page.click('[data-testid="document-item"]:first-child')
        await expect(page.locator('text=Processing complete')).toBeVisible()
      })

      test(`study session functionality in ${browserName}`, async ({ page }) => {
        await helpers.uploadDocument('sample.pdf', true)
        await helpers.startStudySession()
        
        // Test card interactions
        await helpers.studyCards(3)
        
        // Verify progress tracking works
        await expect(page.locator('[data-testid="progress-indicator"]')).toBeVisible()
      })

      test(`search functionality in ${browserName}`, async ({ page }) => {
        await helpers.uploadDocument('sample.pdf', true)
        
        // Test search
        await helpers.performSearch('machine learning')
        await expect(page.locator('[data-testid="search-result"]')).toHaveCount({ min: 1 })
        
        // Test search filters
        await helpers.performSearch('algorithm', { 'definitions': true })
        await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
      })

      test(`responsive design in ${browserName}`, async ({ page }) => {
        await helpers.testResponsiveDesign()
      })

      test(`keyboard navigation in ${browserName}`, async ({ page }) => {
        await helpers.testKeyboardNavigation()
        
        // Test browser-specific keyboard shortcuts
        if (browserName === 'firefox') {
          await page.keyboard.press('Alt+Left') // Back navigation
        } else if (browserName === 'webkit') {
          await page.keyboard.press('Meta+Left') // Back navigation on Safari
        }
      })

      test(`file upload drag and drop in ${browserName}`, async ({ page }) => {
        await page.goto('/upload')
        
        const dropZone = page.locator('[data-testid="drop-zone"]')
        await expect(dropZone).toBeVisible()
        
        // Simulate drag and drop
        await page.evaluate(() => {
          const dropZone = document.querySelector('[data-testid="drop-zone"]')
          if (dropZone) {
            const dragEnterEvent = new DragEvent('dragenter', { bubbles: true })
            const dragOverEvent = new DragEvent('dragover', { bubbles: true })
            const dropEvent = new DragEvent('drop', { bubbles: true })
            
            dropZone.dispatchEvent(dragEnterEvent)
            dropZone.dispatchEvent(dragOverEvent)
            dropZone.dispatchEvent(dropEvent)
          }
        })
        
        // Verify drag and drop visual feedback
        await expect(dropZone).toHaveClass(/drag-over/)
      })

      test(`image rendering and interaction in ${browserName}`, async ({ page }) => {
        await helpers.uploadDocument('with-images.pdf', true)
        
        await page.goto('/documents')
        await page.click('[data-testid="document-item"]:first-child')
        await page.click('[data-testid="chapter-item"]:first-child')
        
        // Test image loading
        const images = page.locator('[data-testid="chapter-image"]')
        if (await images.count() > 0) {
          await expect(images.first()).toBeVisible()
          
          // Test image modal
          await images.first().click()
          await expect(page.locator('[data-testid="image-modal"]')).toBeVisible()
          
          // Test zoom controls
          await page.click('[data-testid="zoom-in"]')
          await page.click('[data-testid="zoom-out"]')
          await page.click('[data-testid="close-modal"]')
        }
      })

      test(`local storage and session management in ${browserName}`, async ({ page }) => {
        // Test data persistence
        await helpers.uploadDocument('sample.pdf', false)
        
        // Refresh page
        await page.reload()
        
        // Verify upload state is maintained
        await expect(page.locator('[data-testid="upload-status"]')).toBeVisible()
        
        // Test session storage
        await page.evaluate(() => {
          sessionStorage.setItem('test-key', 'test-value')
        })
        
        const sessionValue = await page.evaluate(() => {
          return sessionStorage.getItem('test-key')
        })
        
        expect(sessionValue).toBe('test-value')
      })

      test(`CSS and styling consistency in ${browserName}`, async ({ page }) => {
        // Test critical UI elements
        const elements = [
          '[data-testid="main-nav"]',
          '[data-testid="upload-button"]',
          '[data-testid="search-input"]',
          '[data-testid="flashcard"]'
        ]
        
        for (const selector of elements) {
          const element = page.locator(selector)
          if (await element.count() > 0) {
            // Verify element is visible and properly styled
            await expect(element).toBeVisible()
            
            // Check computed styles
            const styles = await element.evaluate(el => {
              const computed = window.getComputedStyle(el)
              return {
                display: computed.display,
                visibility: computed.visibility,
                opacity: computed.opacity
              }
            })
            
            expect(styles.display).not.toBe('none')
            expect(styles.visibility).not.toBe('hidden')
            expect(parseFloat(styles.opacity)).toBeGreaterThan(0)
          }
        }
      })

      test(`JavaScript API compatibility in ${browserName}`, async ({ page }) => {
        // Test modern JavaScript features
        const jsFeatures = await page.evaluate(() => {
          return {
            fetch: typeof fetch !== 'undefined',
            promises: typeof Promise !== 'undefined',
            asyncAwait: (async () => true)() instanceof Promise,
            modules: typeof import !== 'undefined',
            localStorage: typeof localStorage !== 'undefined',
            sessionStorage: typeof sessionStorage !== 'undefined',
            webWorkers: typeof Worker !== 'undefined',
            fileAPI: typeof File !== 'undefined'
          }
        })
        
        // Verify all required features are supported
        expect(jsFeatures.fetch).toBe(true)
        expect(jsFeatures.promises).toBe(true)
        expect(jsFeatures.asyncAwait).toBe(true)
        expect(jsFeatures.localStorage).toBe(true)
        expect(jsFeatures.sessionStorage).toBe(true)
        expect(jsFeatures.fileAPI).toBe(true)
      })
    })
  }

  test.describe('Mobile Browser Compatibility', () => {
    test('iOS Safari compatibility', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1')
      
      await helpers.uploadDocument('sample.pdf', true)
      
      // Test touch interactions
      await helpers.startStudySession()
      
      const card = page.locator('[data-testid="flashcard"]')
      await expect(card).toBeVisible()
      
      // Test touch events
      await card.tap()
      await expect(page.locator('[data-testid="card-back"]')).toBeVisible()
      
      // Test swipe gestures
      const cardBox = await card.boundingBox()
      if (cardBox) {
        await page.touchscreen.tap(cardBox.x + cardBox.width * 0.8, cardBox.y + cardBox.height / 2)
        await page.touchscreen.tap(cardBox.x + cardBox.width * 0.2, cardBox.y + cardBox.height / 2)
      }
    })

    test('Android Chrome compatibility', async ({ page }) => {
      await page.setViewportSize({ width: 360, height: 640 })
      await page.setUserAgent('Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36')
      
      await helpers.uploadDocument('sample.pdf', true)
      
      // Test Android-specific interactions
      await helpers.startStudySession()
      
      // Test long press
      const card = page.locator('[data-testid="flashcard"]')
      await card.click({ button: 'right' }) // Simulate long press
      
      // Test pinch zoom on images
      await page.goto('/documents')
      await page.click('[data-testid="document-item"]:first-child')
      await page.click('[data-testid="chapter-item"]:first-child')
      
      const image = page.locator('[data-testid="chapter-image"]').first()
      if (await image.count() > 0) {
        const imageBox = await image.boundingBox()
        if (imageBox) {
          // Simulate pinch gesture
          await page.touchscreen.tap(imageBox.x + imageBox.width / 2, imageBox.y + imageBox.height / 2)
        }
      }
    })
  })

  test.describe('Browser Feature Detection', () => {
    test('feature support detection', async ({ page, browserName }) => {
      const features = await page.evaluate(() => {
        return {
          webGL: !!window.WebGLRenderingContext,
          webGL2: !!window.WebGL2RenderingContext,
          webAssembly: typeof WebAssembly !== 'undefined',
          serviceWorker: 'serviceWorker' in navigator,
          pushNotifications: 'PushManager' in window,
          geolocation: 'geolocation' in navigator,
          camera: 'mediaDevices' in navigator,
          fullscreen: 'requestFullscreen' in document.documentElement,
          clipboard: 'clipboard' in navigator,
          share: 'share' in navigator
        }
      })
      
      // Log feature support for debugging
      console.log(`${browserName} feature support:`, features)
      
      // Verify core features are supported
      expect(features.webGL).toBe(true)
      expect(features.webAssembly).toBe(true)
    })

    test('polyfill requirements', async ({ page, browserName }) => {
      // Check if polyfills are loaded correctly
      const polyfills = await page.evaluate(() => {
        return {
          intersectionObserver: 'IntersectionObserver' in window,
          resizeObserver: 'ResizeObserver' in window,
          mutationObserver: 'MutationObserver' in window,
          customElements: 'customElements' in window
        }
      })
      
      // Verify polyfills are available
      expect(polyfills.intersectionObserver).toBe(true)
      expect(polyfills.mutationObserver).toBe(true)
    })
  })

  test.describe('Performance Across Browsers', () => {
    test('rendering performance comparison', async ({ page, browserName }) => {
      const startTime = Date.now()
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      // Measure rendering time
      const renderTime = Date.now() - startTime
      
      // Log performance for comparison
      console.log(`${browserName} rendering time: ${renderTime}ms`)
      
      // Verify performance meets requirements
      expect(renderTime).toBeLessThan(5000)
    })

    test('memory usage monitoring', async ({ page, browserName }) => {
      // Monitor memory usage during intensive operations
      const initialMemory = await page.evaluate(() => {
        return (performance as any).memory?.usedJSHeapSize || 0
      })
      
      // Perform memory-intensive operations
      await helpers.uploadDocument('large.pdf', true)
      await helpers.startStudySession()
      await helpers.studyCards(10)
      
      const finalMemory = await page.evaluate(() => {
        return (performance as any).memory?.usedJSHeapSize || 0
      })
      
      const memoryIncrease = finalMemory - initialMemory
      console.log(`${browserName} memory increase: ${memoryIncrease} bytes`)
      
      // Verify memory usage is reasonable (less than 100MB increase)
      expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024)
    })
  })
})