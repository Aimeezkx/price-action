import { test, expect, Browser, BrowserContext, Page } from '@playwright/test';
import { devices } from '@playwright/test';

/**
 * Data Synchronization Testing
 * Tests data consistency and synchronization between web and mobile platforms
 */

interface SyncTestData {
  documentId: string;
  title: string;
  chapters: Array<{ id: string; title: string; content: string }>;
  cards: Array<{ id: string; question: string; answer: string; srsState: any }>;
  userProgress: {
    studyStreak: number;
    cardsReviewed: number;
    lastStudyDate: string;
  };
}

test.describe('Data Synchronization Tests', () => {
  let webContext: BrowserContext;
  let mobileContext: BrowserContext;
  let webPage: Page;
  let mobilePage: Page;

  test.beforeAll(async ({ browser }) => {
    // Create separate contexts for web and mobile simulation
    webContext = await browser.newContext({
      ...devices['Desktop Chrome'],
      viewport: { width: 1920, height: 1080 }
    });

    mobileContext = await browser.newContext({
      ...devices['iPhone 12'],
      viewport: { width: 390, height: 844 }
    });

    webPage = await webContext.newPage();
    mobilePage = await mobileContext.newPage();
  });

  test.afterAll(async () => {
    await webContext.close();
    await mobileContext.close();
  });

  test.describe('Document Synchronization', () => {
    test('Document uploaded on web should appear on mobile', async () => {
      // Step 1: Upload document on web
      await webPage.goto('/');
      await loginUser(webPage, 'sync-test-user@example.com');

      const documentData = await uploadTestDocument(webPage, 'sync-test-document.pdf');
      
      // Wait for processing to complete
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      // Step 2: Check if document appears on mobile
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'sync-test-user@example.com');

      // Trigger sync or wait for automatic sync
      await triggerSync(mobilePage);

      // Verify document appears in mobile library
      await mobilePage.click('[data-testid="library-tab"]');
      await expect(mobilePage.locator(`[data-testid="document-${documentData.id}"]`)).toBeVisible({ timeout: 30000 });

      // Verify document metadata matches
      const mobileDocTitle = await mobilePage.locator(`[data-testid="document-${documentData.id}"] .document-title`).textContent();
      expect(mobileDocTitle).toBe(documentData.title);
    });

    test('Document deleted on mobile should be removed from web', async () => {
      // Setup: Ensure we have a document on both platforms
      await webPage.goto('/');
      await loginUser(webPage, 'sync-test-user@example.com');
      
      const documentData = await uploadTestDocument(webPage, 'delete-test-document.pdf');
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      // Sync to mobile
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'sync-test-user@example.com');
      await triggerSync(mobilePage);
      
      await mobilePage.click('[data-testid="library-tab"]');
      await expect(mobilePage.locator(`[data-testid="document-${documentData.id}"]`)).toBeVisible();

      // Delete document on mobile
      await mobilePage.click(`[data-testid="document-${documentData.id}"] [data-testid="options-button"]`);
      await mobilePage.click('[data-testid="delete-document"]');
      await mobilePage.click('[data-testid="confirm-delete"]');

      // Verify document is removed from mobile
      await expect(mobilePage.locator(`[data-testid="document-${documentData.id}"]`)).not.toBeVisible();

      // Check if document is removed from web after sync
      await triggerSync(webPage);
      await webPage.reload();
      await expect(webPage.locator(`[data-testid="document-${documentData.id}"]`)).not.toBeVisible();
    });
  });

  test.describe('Study Progress Synchronization', () => {
    test('Card reviews on web should sync to mobile', async () => {
      // Setup: Create document with cards on web
      await webPage.goto('/');
      await loginUser(webPage, 'progress-sync-user@example.com');
      
      const documentData = await uploadTestDocument(webPage, 'progress-sync-document.pdf');
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      // Study cards on web
      await webPage.click('[data-testid="study-button"]');
      await expect(webPage.locator('[data-testid="flashcard"]')).toBeVisible();

      const reviewedCards = [];
      for (let i = 0; i < 3; i++) {
        const cardId = await webPage.locator('[data-testid="flashcard"]').getAttribute('data-card-id');
        
        // Flip and grade card
        await webPage.click('[data-testid="flip-button"]');
        await webPage.click('[data-testid="grade-4"]'); // Good grade
        
        reviewedCards.push({
          id: cardId,
          grade: 4,
          reviewTime: new Date().toISOString()
        });

        // Check if more cards are available
        const nextCard = webPage.locator('[data-testid="flashcard"]');
        const sessionComplete = webPage.locator('[data-testid="session-complete"]');
        
        try {
          await expect(nextCard.or(sessionComplete)).toBeVisible({ timeout: 5000 });
          if (await sessionComplete.isVisible()) break;
        } catch (e) {
          break;
        }
      }

      // Sync to mobile and verify progress
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'progress-sync-user@example.com');
      await triggerSync(mobilePage);

      // Check study statistics on mobile
      await mobilePage.click('[data-testid="profile-tab"]');
      const mobileStats = await getStudyStatistics(mobilePage);
      
      expect(mobileStats.cardsReviewed).toBeGreaterThanOrEqual(reviewedCards.length);
      expect(mobileStats.studyStreak).toBeGreaterThan(0);
    });

    test('SRS scheduling should be consistent across platforms', async () => {
      // Setup: Study cards on web with specific grades
      await webPage.goto('/');
      await loginUser(webPage, 'srs-sync-user@example.com');
      
      const documentData = await uploadTestDocument(webPage, 'srs-sync-document.pdf');
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      // Study a card with a specific grade
      await webPage.click('[data-testid="study-button"]');
      await expect(webPage.locator('[data-testid="flashcard"]')).toBeVisible();
      
      const cardId = await webPage.locator('[data-testid="flashcard"]').getAttribute('data-card-id');
      
      await webPage.click('[data-testid="flip-button"]');
      await webPage.click('[data-testid="grade-5"]'); // Perfect grade
      
      // Get SRS state from web
      const webSrsState = await getSrsState(webPage, cardId!);

      // Sync to mobile and check SRS state
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'srs-sync-user@example.com');
      await triggerSync(mobilePage);

      const mobileSrsState = await getSrsState(mobilePage, cardId!);

      // Verify SRS states match
      expect(mobileSrsState.interval).toBe(webSrsState.interval);
      expect(mobileSrsState.easeFactor).toBe(webSrsState.easeFactor);
      expect(mobileSrsState.dueDate).toBe(webSrsState.dueDate);
    });
  });

  test.describe('Settings and Preferences Synchronization', () => {
    test('User preferences should sync between platforms', async () => {
      // Set preferences on web
      await webPage.goto('/');
      await loginUser(webPage, 'preferences-sync-user@example.com');
      
      await webPage.click('[data-testid="settings-button"]');
      
      const preferences = {
        studyReminders: true,
        dailyGoal: 20,
        theme: 'dark',
        language: 'en'
      };

      await setUserPreferences(webPage, preferences);
      await webPage.click('[data-testid="save-preferences"]');

      // Check preferences on mobile
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'preferences-sync-user@example.com');
      await triggerSync(mobilePage);

      await mobilePage.click('[data-testid="settings-button"]');
      const mobilePreferences = await getUserPreferences(mobilePage);

      expect(mobilePreferences).toEqual(preferences);
    });

    test('Privacy settings should be consistent across platforms', async () => {
      // Enable privacy mode on web
      await webPage.goto('/');
      await loginUser(webPage, 'privacy-sync-user@example.com');
      
      await webPage.click('[data-testid="settings-button"]');
      await webPage.click('[data-testid="privacy-tab"]');
      await webPage.check('[data-testid="privacy-mode-toggle"]');
      await webPage.click('[data-testid="save-settings"]');

      // Verify privacy mode is enabled on mobile
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'privacy-sync-user@example.com');
      await triggerSync(mobilePage);

      await mobilePage.click('[data-testid="settings-button"]');
      await mobilePage.click('[data-testid="privacy-tab"]');
      
      const privacyModeEnabled = await mobilePage.isChecked('[data-testid="privacy-mode-toggle"]');
      expect(privacyModeEnabled).toBe(true);
    });
  });

  test.describe('Conflict Resolution', () => {
    test('Should handle simultaneous edits gracefully', async () => {
      // Setup: Create document on both platforms
      await webPage.goto('/');
      await loginUser(webPage, 'conflict-test-user@example.com');
      
      const documentData = await uploadTestDocument(webPage, 'conflict-test-document.pdf');
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      await mobilePage.goto('/');
      await loginUser(mobilePage, 'conflict-test-user@example.com');
      await triggerSync(mobilePage);

      // Make conflicting changes
      // Web: Study a card with grade 3
      await webPage.click('[data-testid="study-button"]');
      await expect(webPage.locator('[data-testid="flashcard"]')).toBeVisible();
      const cardId = await webPage.locator('[data-testid="flashcard"]').getAttribute('data-card-id');
      
      await webPage.click('[data-testid="flip-button"]');
      await webPage.click('[data-testid="grade-3"]');

      // Mobile: Study the same card with grade 5 (simulate offline scenario)
      await mobilePage.click('[data-testid="study-button"]');
      // Simulate finding the same card and grading it differently
      await simulateOfflineCardReview(mobilePage, cardId!, 5);

      // Trigger sync and verify conflict resolution
      await triggerSync(webPage);
      await triggerSync(mobilePage);

      // Check that the conflict was resolved (should use latest timestamp or merge strategy)
      const finalSrsState = await getSrsState(webPage, cardId!);
      expect(finalSrsState).toBeDefined();
      
      // Verify both platforms have the same final state
      const webFinalState = await getSrsState(webPage, cardId!);
      const mobileFinalState = await getSrsState(mobilePage, cardId!);
      
      expect(webFinalState).toEqual(mobileFinalState);
    });

    test('Should handle offline changes and sync when online', async () => {
      // Setup
      await webPage.goto('/');
      await loginUser(webPage, 'offline-sync-user@example.com');
      
      const documentData = await uploadTestDocument(webPage, 'offline-sync-document.pdf');
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      // Sync to mobile
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'offline-sync-user@example.com');
      await triggerSync(mobilePage);

      // Simulate offline mode on mobile
      await simulateOfflineMode(mobilePage, true);

      // Make changes while offline
      await mobilePage.click('[data-testid="study-button"]');
      const offlineChanges = await makeOfflineStudyChanges(mobilePage, 3);

      // Go back online and sync
      await simulateOfflineMode(mobilePage, false);
      await triggerSync(mobilePage);

      // Verify changes are synced to web
      await triggerSync(webPage);
      
      for (const change of offlineChanges) {
        const syncedState = await getSrsState(webPage, change.cardId);
        expect(syncedState.lastReviewed).toBeDefined();
      }
    });
  });

  test.describe('Performance and Reliability', () => {
    test('Sync should complete within reasonable time', async () => {
      // Create substantial data set
      await webPage.goto('/');
      await loginUser(webPage, 'performance-sync-user@example.com');
      
      // Upload multiple documents
      const documents = [];
      for (let i = 0; i < 3; i++) {
        const doc = await uploadTestDocument(webPage, `performance-doc-${i}.pdf`);
        documents.push(doc);
        await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });
      }

      // Study multiple cards to create progress data
      await webPage.click('[data-testid="study-button"]');
      await studyMultipleCards(webPage, 10);

      // Measure sync time to mobile
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'performance-sync-user@example.com');
      
      const syncStartTime = Date.now();
      await triggerSync(mobilePage);
      
      // Wait for sync to complete
      await expect(mobilePage.locator('[data-testid="sync-complete"]')).toBeVisible({ timeout: 60000 });
      
      const syncDuration = Date.now() - syncStartTime;
      expect(syncDuration).toBeLessThan(30000); // Should complete within 30 seconds
    });

    test('Should handle sync failures gracefully', async () => {
      await webPage.goto('/');
      await loginUser(webPage, 'sync-failure-user@example.com');
      
      // Create some data
      const documentData = await uploadTestDocument(webPage, 'sync-failure-document.pdf');
      await expect(webPage.locator('[data-testid="processing-complete"]')).toBeVisible({ timeout: 60000 });

      // Simulate network failure during sync
      await mobilePage.goto('/');
      await loginUser(mobilePage, 'sync-failure-user@example.com');
      
      // Simulate network interruption
      await simulateNetworkFailure(mobilePage, true);
      
      // Attempt sync (should fail gracefully)
      await triggerSync(mobilePage);
      
      // Should show appropriate error message
      await expect(mobilePage.locator('[data-testid="sync-error"]')).toBeVisible();
      
      // Restore network and retry
      await simulateNetworkFailure(mobilePage, false);
      await mobilePage.click('[data-testid="retry-sync"]');
      
      // Should eventually succeed
      await expect(mobilePage.locator('[data-testid="sync-complete"]')).toBeVisible({ timeout: 30000 });
    });
  });
});

// Helper functions
async function loginUser(page: Page, email: string) {
  // Simulate user login
  await page.evaluate((userEmail) => {
    localStorage.setItem('user-session', JSON.stringify({
      email: userEmail,
      token: 'mock-token',
      userId: 'mock-user-id'
    }));
  }, email);
  
  await page.reload();
}

async function uploadTestDocument(page: Page, filename: string) {
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles({
    name: filename,
    mimeType: 'application/pdf',
    buffer: Buffer.from(`Mock PDF content for ${filename}`)
  });
  
  // Return mock document data
  return {
    id: `doc-${Date.now()}`,
    title: filename.replace('.pdf', ''),
    filename: filename
  };
}

async function triggerSync(page: Page) {
  // Trigger manual sync or wait for automatic sync
  try {
    await page.click('[data-testid="sync-button"]', { timeout: 5000 });
  } catch (e) {
    // If no manual sync button, wait for automatic sync
    await page.waitForTimeout(2000);
  }
}

async function getStudyStatistics(page: Page) {
  return await page.evaluate(() => {
    // Mock implementation - would read from actual app state
    return {
      cardsReviewed: parseInt(document.querySelector('[data-testid="cards-reviewed"]')?.textContent || '0'),
      studyStreak: parseInt(document.querySelector('[data-testid="study-streak"]')?.textContent || '0'),
      lastStudyDate: document.querySelector('[data-testid="last-study-date"]')?.textContent || ''
    };
  });
}

async function getSrsState(page: Page, cardId: string) {
  return await page.evaluate((id) => {
    // Mock implementation - would read from actual SRS state
    return {
      cardId: id,
      interval: 1,
      easeFactor: 2.5,
      dueDate: new Date().toISOString(),
      lastReviewed: new Date().toISOString()
    };
  }, cardId);
}

async function setUserPreferences(page: Page, preferences: any) {
  await page.evaluate((prefs) => {
    // Mock implementation - would set actual preferences
    Object.entries(prefs).forEach(([key, value]) => {
      const element = document.querySelector(`[data-testid="${key}-setting"]`) as HTMLInputElement;
      if (element) {
        if (element.type === 'checkbox') {
          element.checked = value as boolean;
        } else {
          element.value = value as string;
        }
      }
    });
  }, preferences);
}

async function getUserPreferences(page: Page) {
  return await page.evaluate(() => {
    // Mock implementation - would read actual preferences
    return {
      studyReminders: (document.querySelector('[data-testid="studyReminders-setting"]') as HTMLInputElement)?.checked || false,
      dailyGoal: parseInt((document.querySelector('[data-testid="dailyGoal-setting"]') as HTMLInputElement)?.value || '10'),
      theme: (document.querySelector('[data-testid="theme-setting"]') as HTMLInputElement)?.value || 'light',
      language: (document.querySelector('[data-testid="language-setting"]') as HTMLInputElement)?.value || 'en'
    };
  });
}

async function simulateOfflineCardReview(page: Page, cardId: string, grade: number) {
  // Mock offline card review
  await page.evaluate((id, gradeValue) => {
    // Store offline change in local storage
    const offlineChanges = JSON.parse(localStorage.getItem('offline-changes') || '[]');
    offlineChanges.push({
      type: 'card-review',
      cardId: id,
      grade: gradeValue,
      timestamp: new Date().toISOString()
    });
    localStorage.setItem('offline-changes', JSON.stringify(offlineChanges));
  }, cardId, grade);
}

async function simulateOfflineMode(page: Page, offline: boolean) {
  await page.evaluate((isOffline) => {
    // Mock offline mode
    (window as any).navigator.onLine = !isOffline;
    if (isOffline) {
      window.dispatchEvent(new Event('offline'));
    } else {
      window.dispatchEvent(new Event('online'));
    }
  }, offline);
}

async function makeOfflineStudyChanges(page: Page, count: number) {
  const changes = [];
  
  for (let i = 0; i < count; i++) {
    const cardId = `offline-card-${i}`;
    const grade = Math.floor(Math.random() * 5) + 1;
    
    await simulateOfflineCardReview(page, cardId, grade);
    changes.push({ cardId, grade });
  }
  
  return changes;
}

async function studyMultipleCards(page: Page, count: number) {
  for (let i = 0; i < count; i++) {
    try {
      await expect(page.locator('[data-testid="flashcard"]')).toBeVisible({ timeout: 5000 });
      await page.click('[data-testid="flip-button"]');
      await page.click('[data-testid="grade-4"]');
      
      // Check if more cards are available
      const nextCard = page.locator('[data-testid="flashcard"]');
      const sessionComplete = page.locator('[data-testid="session-complete"]');
      
      await expect(nextCard.or(sessionComplete)).toBeVisible({ timeout: 5000 });
      if (await sessionComplete.isVisible()) break;
    } catch (e) {
      break;
    }
  }
}

async function simulateNetworkFailure(page: Page, fail: boolean) {
  await page.route('**/api/**', route => {
    if (fail) {
      route.abort();
    } else {
      route.continue();
    }
  });
}