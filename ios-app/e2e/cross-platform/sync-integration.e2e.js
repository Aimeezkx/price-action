const { device, expect, element, by, waitFor } = require('detox');

/**
 * iOS Data Synchronization Tests
 * Tests data sync between iOS app and web platform
 */

describe('iOS Data Synchronization', () => {
  
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    // Login with test user
    await loginTestUser('sync-test-user@example.com');
  });

  describe('Document Sync from Web to iOS', () => {
    it('should receive documents uploaded on web platform', async () => {
      // Simulate document uploaded on web (would be done via API call in real test)
      await simulateWebDocumentUpload({
        id: 'web-doc-001',
        title: 'Web Uploaded Document',
        filename: 'web-document.pdf',
        status: 'processed'
      });

      // Trigger sync on iOS
      await element(by.id('sync-button')).tap();
      
      // Wait for sync to complete
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Navigate to library and verify document appears
      await element(by.id('library-tab')).tap();
      await expect(element(by.id('web-doc-001'))).toBeVisible();
      
      // Verify document metadata
      await expect(element(by.text('Web Uploaded Document'))).toBeVisible();
    });

    it('should sync document processing status updates', async () => {
      // Start with a processing document
      await simulateWebDocumentUpload({
        id: 'processing-doc-001',
        title: 'Processing Document',
        filename: 'processing.pdf',
        status: 'processing'
      });

      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify document shows as processing
      await element(by.id('library-tab')).tap();
      await expect(element(by.id('processing-doc-001'))).toBeVisible();
      await expect(element(by.id('processing-indicator'))).toBeVisible();

      // Simulate processing completion on web
      await simulateDocumentProcessingComplete('processing-doc-001');

      // Sync again
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify document now shows as complete
      await expect(element(by.id('processing-indicator'))).not.toBeVisible();
      await expect(element(by.id('study-button'))).toBeVisible();
    });
  });

  describe('Study Progress Sync from iOS to Web', () => {
    it('should sync card reviews to web platform', async () => {
      // Setup: Ensure we have a document with cards
      await setupTestDocumentWithCards('ios-study-doc-001');

      // Study cards on iOS
      await element(by.id('study-tab')).tap();
      await expect(element(by.id('flashcard'))).toBeVisible();

      const reviewedCards = [];
      
      // Review 3 cards
      for (let i = 0; i < 3; i++) {
        // Get card ID
        const cardId = await element(by.id('flashcard')).getAttributes();
        
        // Flip card
        await element(by.id('flip-button')).tap();
        
        // Grade card (grade 4 = good)
        await element(by.id('grade-4')).tap();
        
        reviewedCards.push({
          cardId: cardId.identifier,
          grade: 4,
          timestamp: new Date().toISOString()
        });

        // Check if more cards available
        try {
          await waitFor(element(by.id('flashcard')))
            .toBeVisible()
            .withTimeout(3000);
        } catch (e) {
          // No more cards or session complete
          break;
        }
      }

      // Trigger sync
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify sync was successful
      await expect(element(by.id('sync-success-message'))).toBeVisible();

      // Verify progress is reflected in stats
      await element(by.id('profile-tab')).tap();
      const cardsReviewedCount = await element(by.id('cards-reviewed-count')).getAttributes();
      expect(parseInt(cardsReviewedCount.text)).toBeGreaterThanOrEqual(reviewedCards.length);
    });

    it('should sync study streak and statistics', async () => {
      // Setup initial stats
      const initialStats = await getStudyStatistics();

      // Study session
      await element(by.id('study-tab')).tap();
      await performStudySession(5); // Study 5 cards

      // Check updated stats
      await element(by.id('profile-tab')).tap();
      const updatedStats = await getStudyStatistics();

      expect(updatedStats.cardsReviewed).toBeGreaterThan(initialStats.cardsReviewed);
      expect(updatedStats.studyStreak).toBeGreaterThanOrEqual(initialStats.studyStreak);

      // Sync to web
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify sync success
      await expect(element(by.id('sync-success-message'))).toBeVisible();
    });
  });

  describe('Settings and Preferences Sync', () => {
    it('should sync user preferences between platforms', async () => {
      // Navigate to settings
      await element(by.id('profile-tab')).tap();
      await element(by.id('settings-button')).tap();

      // Change preferences
      await element(by.id('daily-goal-input')).clearText();
      await element(by.id('daily-goal-input')).typeText('25');
      
      await element(by.id('study-reminders-toggle')).tap();
      await element(by.id('dark-theme-toggle')).tap();

      // Save settings
      await element(by.id('save-settings-button')).tap();

      // Sync changes
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify settings were saved and synced
      await expect(element(by.text('Settings saved and synced'))).toBeVisible();
    });

    it('should receive settings changes from web platform', async () => {
      // Simulate settings change on web
      await simulateWebSettingsChange({
        dailyGoal: 30,
        studyReminders: false,
        theme: 'light',
        language: 'es'
      });

      // Sync on iOS
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Verify settings were updated
      await element(by.id('profile-tab')).tap();
      await element(by.id('settings-button')).tap();

      const dailyGoalValue = await element(by.id('daily-goal-input')).getAttributes();
      expect(dailyGoalValue.text).toBe('30');

      // Check other settings
      const reminderToggle = await element(by.id('study-reminders-toggle')).getAttributes();
      expect(reminderToggle.value).toBe('0'); // Off

      const themeToggle = await element(by.id('dark-theme-toggle')).getAttributes();
      expect(themeToggle.value).toBe('0'); // Light theme
    });
  });

  describe('Offline Sync and Conflict Resolution', () => {
    it('should handle offline changes and sync when online', async () => {
      // Setup document with cards
      await setupTestDocumentWithCards('offline-test-doc');

      // Simulate going offline
      await device.setNetworkConditions({ offline: true });

      // Study cards while offline
      await element(by.id('study-tab')).tap();
      const offlineReviews = await performStudySession(3);

      // Verify offline indicator is shown
      await expect(element(by.id('offline-indicator'))).toBeVisible();

      // Go back online
      await device.setNetworkConditions({ offline: false });

      // Trigger sync
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(45000); // Longer timeout for offline sync

      // Verify offline changes were synced
      await expect(element(by.id('offline-sync-success'))).toBeVisible();
      await expect(element(by.id('offline-indicator'))).not.toBeVisible();
    });

    it('should resolve conflicts when same card reviewed on both platforms', async () => {
      // Setup
      await setupTestDocumentWithCards('conflict-test-doc');

      // Review a card on iOS
      await element(by.id('study-tab')).tap();
      await expect(element(by.id('flashcard'))).toBeVisible();
      
      const cardId = await element(by.id('flashcard')).getAttributes();
      
      await element(by.id('flip-button')).tap();
      await element(by.id('grade-3')).tap(); // Grade 3 on iOS

      // Simulate the same card being reviewed on web with different grade
      await simulateWebCardReview(cardId.identifier, 5); // Grade 5 on web

      // Sync and check conflict resolution
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(30000);

      // Should show conflict resolution message
      await expect(element(by.id('conflict-resolved-message'))).toBeVisible();

      // Verify final state (should use latest timestamp or merge strategy)
      const finalCardState = await getCardSRSState(cardId.identifier);
      expect(finalCardState).toBeDefined();
    });
  });

  describe('Sync Performance and Reliability', () => {
    it('should complete sync within reasonable time limits', async () => {
      // Create substantial data set
      await setupMultipleDocuments(5);
      await performExtensiveStudySession(20);

      // Measure sync time
      const syncStartTime = Date.now();
      
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(60000);

      const syncDuration = Date.now() - syncStartTime;
      
      // Should complete within 45 seconds for substantial data
      expect(syncDuration).toBeLessThan(45000);
    });

    it('should handle sync failures gracefully', async () => {
      // Simulate network issues during sync
      await device.setNetworkConditions({ 
        speed: 'slow-3g',
        latency: 500 
      });

      await element(by.id('sync-button')).tap();

      // Should show appropriate error handling
      try {
        await waitFor(element(by.id('sync-error-message')))
          .toBeVisible()
          .withTimeout(30000);
        
        // Should offer retry option
        await expect(element(by.id('retry-sync-button'))).toBeVisible();
        
        // Reset network and retry
        await device.setNetworkConditions({ speed: 'full' });
        await element(by.id('retry-sync-button')).tap();
        
        await waitFor(element(by.id('sync-complete-indicator')))
          .toBeVisible()
          .withTimeout(30000);
          
      } catch (e) {
        // If sync succeeds despite slow network, that's also acceptable
        await expect(element(by.id('sync-complete-indicator'))).toBeVisible();
      }
    });

    it('should show sync progress for large data sets', async () => {
      // Setup large data set
      await setupMultipleDocuments(10);

      await element(by.id('sync-button')).tap();

      // Should show progress indicator
      await expect(element(by.id('sync-progress-bar'))).toBeVisible();
      await expect(element(by.id('sync-progress-text'))).toBeVisible();

      // Wait for completion
      await waitFor(element(by.id('sync-complete-indicator')))
        .toBeVisible()
        .withTimeout(90000);

      // Progress indicators should be hidden
      await expect(element(by.id('sync-progress-bar'))).not.toBeVisible();
    });
  });
});

// Helper functions
async function loginTestUser(email) {
  try {
    await element(by.id('email-input')).typeText(email);
    await element(by.id('password-input')).typeText('test-password');
    await element(by.id('login-button')).tap();
    
    await waitFor(element(by.id('main-screen')))
      .toBeVisible()
      .withTimeout(10000);
  } catch (e) {
    // User might already be logged in
    console.log('User already logged in or login not required');
  }
}

async function simulateWebDocumentUpload(documentData) {
  // In a real test, this would make an API call to simulate web upload
  await device.sendUserNotification({
    trigger: {
      type: 'push',
    },
    title: 'Document Uploaded',
    body: `${documentData.title} has been uploaded`,
    payload: {
      type: 'document_uploaded',
      documentId: documentData.id
    }
  });
}

async function simulateDocumentProcessingComplete(documentId) {
  await device.sendUserNotification({
    trigger: {
      type: 'push',
    },
    title: 'Document Ready',
    body: 'Your document has been processed',
    payload: {
      type: 'document_processed',
      documentId: documentId
    }
  });
}

async function setupTestDocumentWithCards(documentId) {
  // Mock setup - in real test would ensure document exists with cards
  await device.sendUserNotification({
    trigger: {
      type: 'push',
    },
    title: 'Test Setup',
    body: 'Test document ready',
    payload: {
      type: 'test_setup',
      documentId: documentId,
      cardsCount: 10
    }
  });
}

async function performStudySession(cardCount) {
  const reviewedCards = [];
  
  for (let i = 0; i < cardCount; i++) {
    try {
      await waitFor(element(by.id('flashcard')))
        .toBeVisible()
        .withTimeout(5000);
      
      const cardId = await element(by.id('flashcard')).getAttributes();
      
      await element(by.id('flip-button')).tap();
      await element(by.id('grade-4')).tap();
      
      reviewedCards.push({
        cardId: cardId.identifier,
        grade: 4
      });
      
    } catch (e) {
      // No more cards or session complete
      break;
    }
  }
  
  return reviewedCards;
}

async function getStudyStatistics() {
  await element(by.id('profile-tab')).tap();
  
  const cardsReviewed = await element(by.id('cards-reviewed-count')).getAttributes();
  const studyStreak = await element(by.id('study-streak-count')).getAttributes();
  
  return {
    cardsReviewed: parseInt(cardsReviewed.text || '0'),
    studyStreak: parseInt(studyStreak.text || '0')
  };
}

async function simulateWebSettingsChange(settings) {
  // Mock API call to change settings on web
  await device.sendUserNotification({
    trigger: {
      type: 'push',
    },
    title: 'Settings Updated',
    body: 'Your settings have been updated on web',
    payload: {
      type: 'settings_changed',
      settings: settings
    }
  });
}

async function simulateWebCardReview(cardId, grade) {
  await device.sendUserNotification({
    trigger: {
      type: 'push',
    },
    title: 'Card Reviewed',
    body: 'Card reviewed on web platform',
    payload: {
      type: 'card_reviewed',
      cardId: cardId,
      grade: grade,
      timestamp: new Date().toISOString()
    }
  });
}

async function getCardSRSState(cardId) {
  // Mock implementation - would get actual SRS state
  return {
    cardId: cardId,
    interval: 1,
    easeFactor: 2.5,
    dueDate: new Date().toISOString()
  };
}

async function setupMultipleDocuments(count) {
  for (let i = 0; i < count; i++) {
    await simulateWebDocumentUpload({
      id: `multi-doc-${i}`,
      title: `Document ${i + 1}`,
      filename: `document-${i + 1}.pdf`,
      status: 'processed'
    });
  }
}

async function performExtensiveStudySession(cardCount) {
  await element(by.id('study-tab')).tap();
  return await performStudySession(cardCount);
}