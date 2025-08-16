import { test, expect } from '@playwright/test'
import { injectAxe, checkA11y, getViolations } from '@axe-core/playwright'
import { TestHelpers } from './utils/test-helpers'

test.describe('Accessibility Testing', () => {
  let helpers: TestHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page)
    await page.goto('/')
    await injectAxe(page)
  })

  test.afterEach(async () => {
    await helpers.cleanup()
  })

  test.describe('WCAG Compliance', () => {
    const pages = [
      { url: '/', name: 'Home' },
      { url: '/upload', name: 'Upload' },
      { url: '/documents', name: 'Documents' },
      { url: '/study', name: 'Study' },
      { url: '/search', name: 'Search' },
      { url: '/export', name: 'Export' }
    ]

    for (const { url, name } of pages) {
      test(`${name} page WCAG compliance`, async ({ page }) => {
        await page.goto(url)
        
        // Wait for page to fully load
        await page.waitForLoadState('networkidle')
        
        // Run axe accessibility tests
        await checkA11y(page, null, {
          detailedReport: true,
          detailedReportOptions: { html: true },
          rules: {
            // Enable all WCAG 2.1 AA rules
            'color-contrast': { enabled: true },
            'keyboard-navigation': { enabled: true },
            'focus-management': { enabled: true },
            'aria-labels': { enabled: true },
            'semantic-markup': { enabled: true }
          }
        })
        
        // Check for specific accessibility features
        await test.step('Check semantic HTML structure', async () => {
          // Verify main landmarks
          await expect(page.locator('main')).toHaveCount(1)
          await expect(page.locator('nav')).toHaveCount({ min: 1 })
          
          // Verify heading hierarchy
          const headings = page.locator('h1, h2, h3, h4, h5, h6')
          const headingCount = await headings.count()
          
          if (headingCount > 0) {
            // Should have at least one h1
            await expect(page.locator('h1')).toHaveCount({ min: 1 })
          }
        })
        
        await test.step('Check ARIA labels and roles', async () => {
          // Interactive elements should have accessible names
          const buttons = page.locator('button')
          const buttonCount = await buttons.count()
          
          for (let i = 0; i < buttonCount; i++) {
            const button = buttons.nth(i)
            const hasAriaLabel = await button.getAttribute('aria-label')
            const hasText = await button.textContent()
            const hasAriaLabelledBy = await button.getAttribute('aria-labelledby')
            
            expect(hasAriaLabel || hasText?.trim() || hasAriaLabelledBy).toBeTruthy()
          }
          
          // Form inputs should have labels
          const inputs = page.locator('input')
          const inputCount = await inputs.count()
          
          for (let i = 0; i < inputCount; i++) {
            const input = inputs.nth(i)
            const inputId = await input.getAttribute('id')
            const hasAriaLabel = await input.getAttribute('aria-label')
            const hasAriaLabelledBy = await input.getAttribute('aria-labelledby')
            
            if (inputId) {
              const label = page.locator(`label[for="${inputId}"]`)
              const hasLabel = await label.count() > 0
              
              expect(hasLabel || hasAriaLabel || hasAriaLabelledBy).toBeTruthy()
            }
          }
        })
      })
    }
  })

  test.describe('Keyboard Navigation', () => {
    test('tab navigation through all interactive elements', async ({ page }) => {
      await page.goto('/')
      
      // Start from the beginning
      await page.keyboard.press('Tab')
      
      const interactiveElements = []
      let currentElement = page.locator(':focus')
      
      // Navigate through all focusable elements
      for (let i = 0; i < 20; i++) { // Limit to prevent infinite loop
        if (await currentElement.count() > 0) {
          const tagName = await currentElement.evaluate(el => el.tagName.toLowerCase())
          const role = await currentElement.getAttribute('role')
          const ariaLabel = await currentElement.getAttribute('aria-label')
          const text = await currentElement.textContent()
          
          interactiveElements.push({
            tagName,
            role,
            ariaLabel,
            text: text?.trim().substring(0, 50)
          })
          
          // Verify element is visible
          await expect(currentElement).toBeVisible()
          
          // Move to next element
          await page.keyboard.press('Tab')
          currentElement = page.locator(':focus')
        } else {
          break
        }
      }
      
      // Should have found interactive elements
      expect(interactiveElements.length).toBeGreaterThan(0)
      
      // Test reverse tab navigation
      await page.keyboard.press('Shift+Tab')
      const previousElement = page.locator(':focus')
      await expect(previousElement).toBeVisible()
    })

    test('keyboard navigation in study session', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      // Focus should be on the card or first interactive element
      await page.keyboard.press('Tab')
      const focusedElement = page.locator(':focus')
      await expect(focusedElement).toBeVisible()
      
      // Test card interaction with keyboard
      await page.keyboard.press('Space') // Should flip card
      await expect(page.locator('[data-testid="card-back"]')).toBeVisible()
      
      // Test grading with keyboard
      await page.keyboard.press('4') // Should grade card with 4
      await page.waitForTimeout(500)
      
      // Should move to next card or show completion
      const nextCard = page.locator('[data-testid="flashcard"]')
      if (await nextCard.count() > 0) {
        await expect(nextCard).toBeVisible()
      }
    })

    test('keyboard navigation in search', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await page.goto('/search')
      
      // Focus search input
      await page.keyboard.press('Tab')
      const searchInput = page.locator(':focus')
      await expect(searchInput).toHaveAttribute('data-testid', 'search-input')
      
      // Type search query
      await page.keyboard.type('machine learning')
      await page.keyboard.press('Enter')
      
      // Navigate to search results
      await page.keyboard.press('Tab')
      await page.keyboard.press('Tab') // Skip to first result
      
      const focusedResult = page.locator(':focus')
      await expect(focusedResult).toBeVisible()
      
      // Should be able to activate result with Enter
      await page.keyboard.press('Enter')
      
      // Should navigate to content
      await expect(page.locator('[data-testid="chapter-content"]')).toBeVisible()
    })

    test('skip links functionality', async ({ page }) => {
      await page.goto('/')
      
      // Focus first element (should reveal skip link)
      await page.keyboard.press('Tab')
      
      const skipLink = page.locator('[data-testid="skip-to-content"]')
      if (await skipLink.count() > 0) {
        await expect(skipLink).toBeVisible()
        
        // Activate skip link
        await page.keyboard.press('Enter')
        
        // Should focus main content
        const mainContent = page.locator('main')
        await expect(mainContent).toBeFocused()
      }
    })
  })

  test.describe('Screen Reader Support', () => {
    test('ARIA live regions for dynamic content', async ({ page }) => {
      await helpers.uploadDocument('sample.pdf', true)
      await helpers.startStudySession()
      
      // Check for live regions
      const liveRegions = page.locator('[aria-live]')
      const liveRegionCount = await liveRegions.count()
      
      if (liveRegionCount > 0) {
        // Verify live regions have appropriate politeness levels
        for (let i = 0; i < liveRegionCount; i++) {
          const region = liveRegions.nth(i)
          const politeness = await region.getAttribute('aria-live')
          expect(['polite', 'assertive', 'off']).toContain(politeness)
        }
      }
      
      // Test dynamic content updates
      await page.click('[data-testid="flip-button"]')
      
      // Check if status is announced
      const statusRegion = page.locator('[data-testid="sr-status"]')
      if (await statusRegion.count() > 0) {
        await expect(statusRegion).toHaveAttribute('aria-live', 'polite')
      }
    })

    test('form labels and descriptions', async ({ page }) => {
      await page.goto('/upload')
      
      // Check file input has proper labeling
      const fileInput = page.locator('input[type="file"]')
      const inputId = await fileInput.getAttribute('id')
      
      if (inputId) {
        const label = page.locator(`label[for="${inputId}"]`)
        await expect(label).toBeVisible()
        
        const labelText = await label.textContent()
        expect(labelText?.trim()).toBeTruthy()
      }
      
      // Check for help text
      const helpText = page.locator('[data-testid="upload-help"]')
      if (await helpText.count() > 0) {
        const helpId = await helpText.getAttribute('id')
        const describedBy = await fileInput.getAttribute('aria-describedby')
        
        expect(describedBy).toContain(helpId)
      }
    })

    test('error messages and validation', async ({ page }) => {
      await page.goto('/upload')
      
      // Try to upload invalid file
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/invalid.txt')
      await page.click('[data-testid="upload-submit"]')
      
      // Check error message accessibility
      const errorMessage = page.locator('[data-testid="error-message"]')
      await expect(errorMessage).toBeVisible()
      
      // Error should be associated with the input
      const errorId = await errorMessage.getAttribute('id')
      const inputDescribedBy = await fileInput.getAttribute('aria-describedby')
      
      if (errorId && inputDescribedBy) {
        expect(inputDescribedBy).toContain(errorId)
      }
      
      // Error should have appropriate role
      const errorRole = await errorMessage.getAttribute('role')
      expect(['alert', 'status']).toContain(errorRole)
    })

    test('progress indicators', async ({ page }) => {
      await page.goto('/upload')
      
      // Upload large file to trigger progress indicator
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/large.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Check progress bar accessibility
      const progressBar = page.locator('[data-testid="upload-progress"]')
      if (await progressBar.count() > 0) {
        await expect(progressBar).toHaveAttribute('role', 'progressbar')
        
        const ariaValueNow = await progressBar.getAttribute('aria-valuenow')
        const ariaValueMin = await progressBar.getAttribute('aria-valuemin')
        const ariaValueMax = await progressBar.getAttribute('aria-valuemax')
        
        expect(ariaValueNow).toBeTruthy()
        expect(ariaValueMin).toBe('0')
        expect(ariaValueMax).toBe('100')
      }
    })
  })

  test.describe('Color Contrast and Visual Accessibility', () => {
    test('color contrast ratios', async ({ page }) => {
      await page.goto('/')
      
      // Test will be handled by axe-core, but we can do additional checks
      const textElements = page.locator('p, span, div, button, a, label')
      const elementCount = await textElements.count()
      
      // Sample a few elements for manual contrast checking
      for (let i = 0; i < Math.min(elementCount, 5); i++) {
        const element = textElements.nth(i)
        if (await element.isVisible()) {
          const styles = await element.evaluate(el => {
            const computed = window.getComputedStyle(el)
            return {
              color: computed.color,
              backgroundColor: computed.backgroundColor,
              fontSize: computed.fontSize
            }
          })
          
          // Log for manual verification if needed
          console.log(`Element ${i} styles:`, styles)
        }
      }
    })

    test('focus indicators', async ({ page }) => {
      await page.goto('/')
      
      // Test focus indicators on interactive elements
      const interactiveElements = page.locator('button, a, input, [tabindex]')
      const elementCount = await interactiveElements.count()
      
      for (let i = 0; i < Math.min(elementCount, 5); i++) {
        const element = interactiveElements.nth(i)
        if (await element.isVisible()) {
          // Focus the element
          await element.focus()
          
          // Check if focus indicator is visible
          const focusStyles = await element.evaluate(el => {
            const computed = window.getComputedStyle(el)
            return {
              outline: computed.outline,
              outlineWidth: computed.outlineWidth,
              outlineStyle: computed.outlineStyle,
              outlineColor: computed.outlineColor,
              boxShadow: computed.boxShadow
            }
          })
          
          // Should have some form of focus indicator
          const hasFocusIndicator = 
            focusStyles.outline !== 'none' ||
            focusStyles.outlineWidth !== '0px' ||
            focusStyles.boxShadow !== 'none'
          
          expect(hasFocusIndicator).toBe(true)
        }
      }
    })

    test('text scaling and zoom', async ({ page }) => {
      await page.goto('/')
      
      // Test 200% zoom (WCAG requirement)
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.evaluate(() => {
        document.body.style.zoom = '2'
      })
      
      // Verify content is still accessible
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible()
      
      // Test text scaling
      await page.evaluate(() => {
        document.body.style.fontSize = '200%'
      })
      
      // Verify text is still readable
      const textElements = page.locator('p, span, div')
      const firstText = textElements.first()
      if (await firstText.count() > 0) {
        await expect(firstText).toBeVisible()
      }
      
      // Reset zoom
      await page.evaluate(() => {
        document.body.style.zoom = '1'
        document.body.style.fontSize = ''
      })
    })
  })

  test.describe('Alternative Text and Media', () => {
    test('image alternative text', async ({ page }) => {
      await helpers.uploadDocument('with-images.pdf', true)
      
      await page.goto('/documents')
      await page.click('[data-testid="document-item"]:first-child')
      await page.click('[data-testid="chapter-item"]:first-child')
      
      // Check all images have alt text
      const images = page.locator('img')
      const imageCount = await images.count()
      
      for (let i = 0; i < imageCount; i++) {
        const image = images.nth(i)
        const altText = await image.getAttribute('alt')
        const ariaLabel = await image.getAttribute('aria-label')
        const ariaLabelledBy = await image.getAttribute('aria-labelledby')
        
        // Image should have alt text or aria labeling
        expect(altText !== null || ariaLabel || ariaLabelledBy).toBe(true)
        
        // Alt text should be descriptive (not just filename)
        if (altText) {
          expect(altText.length).toBeGreaterThan(0)
          expect(altText).not.toMatch(/\.(jpg|jpeg|png|gif|svg)$/i)
        }
      }
    })

    test('decorative images', async ({ page }) => {
      await page.goto('/')
      
      // Check for decorative images (should have empty alt or role="presentation")
      const decorativeImages = page.locator('img[alt=""], img[role="presentation"]')
      const decorativeCount = await decorativeImages.count()
      
      // If decorative images exist, verify they're properly marked
      for (let i = 0; i < decorativeCount; i++) {
        const image = decorativeImages.nth(i)
        const alt = await image.getAttribute('alt')
        const role = await image.getAttribute('role')
        
        expect(alt === '' || role === 'presentation').toBe(true)
      }
    })

    test('complex images and charts', async ({ page }) => {
      await helpers.uploadDocument('with-charts.pdf', true)
      
      await page.goto('/documents')
      await page.click('[data-testid="document-item"]:first-child')
      await page.click('[data-testid="chapter-item"]:first-child')
      
      // Check for complex images (charts, diagrams)
      const complexImages = page.locator('[data-testid="chart"], [data-testid="diagram"]')
      const complexCount = await complexImages.count()
      
      for (let i = 0; i < complexCount; i++) {
        const image = complexImages.nth(i)
        
        // Complex images should have detailed descriptions
        const ariaDescribedBy = await image.getAttribute('aria-describedby')
        if (ariaDescribedBy) {
          const description = page.locator(`#${ariaDescribedBy}`)
          await expect(description).toBeVisible()
          
          const descriptionText = await description.textContent()
          expect(descriptionText?.length).toBeGreaterThan(20)
        }
      }
    })
  })

  test.describe('Mobile Accessibility', () => {
    test.use({ viewport: { width: 375, height: 667 } })

    test('touch target sizes', async ({ page }) => {
      await page.goto('/')
      
      // Check touch target sizes (minimum 44x44px for iOS)
      const touchTargets = page.locator('button, a, input, [role="button"]')
      const targetCount = await touchTargets.count()
      
      for (let i = 0; i < targetCount; i++) {
        const target = touchTargets.nth(i)
        if (await target.isVisible()) {
          const boundingBox = await target.boundingBox()
          
          if (boundingBox) {
            expect(boundingBox.width).toBeGreaterThanOrEqual(44)
            expect(boundingBox.height).toBeGreaterThanOrEqual(44)
          }
        }
      }
    })

    test('mobile screen reader navigation', async ({ page }) => {
      await page.goto('/')
      
      // Test swipe navigation simulation
      const landmarks = page.locator('[role="main"], [role="navigation"], [role="banner"]')
      const landmarkCount = await landmarks.count()
      
      expect(landmarkCount).toBeGreaterThan(0)
      
      // Verify landmarks are properly labeled
      for (let i = 0; i < landmarkCount; i++) {
        const landmark = landmarks.nth(i)
        const ariaLabel = await landmark.getAttribute('aria-label')
        const ariaLabelledBy = await landmark.getAttribute('aria-labelledby')
        
        if (await landmark.getAttribute('role') === 'navigation') {
          expect(ariaLabel || ariaLabelledBy).toBeTruthy()
        }
      }
    })
  })

  test.describe('Dynamic Content Accessibility', () => {
    test('modal dialogs', async ({ page }) => {
      await helpers.uploadDocument('with-images.pdf', true)
      
      await page.goto('/documents')
      await page.click('[data-testid="document-item"]:first-child')
      await page.click('[data-testid="chapter-item"]:first-child')
      
      // Open image modal
      const image = page.locator('[data-testid="chapter-image"]').first()
      if (await image.count() > 0) {
        await image.click()
        
        const modal = page.locator('[data-testid="image-modal"]')
        await expect(modal).toBeVisible()
        
        // Check modal accessibility
        await expect(modal).toHaveAttribute('role', 'dialog')
        await expect(modal).toHaveAttribute('aria-modal', 'true')
        
        // Should have accessible name
        const ariaLabel = await modal.getAttribute('aria-label')
        const ariaLabelledBy = await modal.getAttribute('aria-labelledby')
        expect(ariaLabel || ariaLabelledBy).toBeTruthy()
        
        // Focus should be trapped in modal
        await page.keyboard.press('Tab')
        const focusedElement = page.locator(':focus')
        const isInsideModal = await focusedElement.evaluate(el => {
          const modal = document.querySelector('[data-testid="image-modal"]')
          return modal?.contains(el) || false
        })
        expect(isInsideModal).toBe(true)
        
        // Escape should close modal
        await page.keyboard.press('Escape')
        await expect(modal).not.toBeVisible()
      }
    })

    test('loading states', async ({ page }) => {
      await page.goto('/upload')
      
      // Upload file to trigger loading state
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/sample.pdf')
      await page.click('[data-testid="upload-submit"]')
      
      // Check loading indicator accessibility
      const loadingIndicator = page.locator('[data-testid="loading-spinner"]')
      if (await loadingIndicator.count() > 0) {
        await expect(loadingIndicator).toHaveAttribute('role', 'status')
        await expect(loadingIndicator).toHaveAttribute('aria-live', 'polite')
        
        const ariaLabel = await loadingIndicator.getAttribute('aria-label')
        expect(ariaLabel).toContain('loading')
      }
    })

    test('error states', async ({ page }) => {
      await page.goto('/upload')
      
      // Trigger error
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles('test-data/invalid.txt')
      await page.click('[data-testid="upload-submit"]')
      
      // Check error accessibility
      const errorMessage = page.locator('[data-testid="error-message"]')
      await expect(errorMessage).toBeVisible()
      await expect(errorMessage).toHaveAttribute('role', 'alert')
      
      // Error should be announced
      const ariaLive = await errorMessage.getAttribute('aria-live')
      expect(['assertive', 'polite']).toContain(ariaLive)
    })
  })
})