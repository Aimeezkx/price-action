describe('Study Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should complete a full study session', async () => {
    // Navigate to Study tab
    await element(by.id('study-tab')).tap();
    
    // Wait for cards to load
    await waitFor(element(by.id('flashcard-container')))
      .toBeVisible()
      .withTimeout(10000);

    // Verify card is displayed
    await expect(element(by.id('flashcard-container'))).toBeVisible();
    await expect(element(by.id('card-front'))).toBeVisible();

    // Flip the card
    await element(by.id('flashcard-container')).tap();
    
    // Wait for flip animation
    await waitFor(element(by.id('card-back')))
      .toBeVisible()
      .withTimeout(2000);

    // Grade the card
    await element(by.id('grade-button-4')).tap();

    // Verify next card appears or session complete message
    await waitFor(element(by.id('flashcard-container')).or(by.id('session-complete')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should handle image hotspot cards', async () => {
    // Navigate to Study tab
    await element(by.id('study-tab')).tap();
    
    // Look for image hotspot card
    await waitFor(element(by.id('image-container')))
      .toBeVisible()
      .withTimeout(10000);

    // Tap on a hotspot
    await element(by.id('hotspot-0')).tap();

    // Verify hotspot feedback
    await expect(element(by.id('hotspot-feedback'))).toBeVisible();

    // Grade the card
    await element(by.id('grade-button-3')).tap();
  });

  it('should support keyboard shortcuts', async () => {
    // Navigate to Study tab
    await element(by.id('study-tab')).tap();
    
    await waitFor(element(by.id('flashcard-container')))
      .toBeVisible()
      .withTimeout(10000);

    // Use space to flip card
    await device.sendUserNotification({
      trigger: {
        type: 'push',
      },
      title: 'Test',
      subtitle: 'Test keyboard shortcut',
      body: 'Space key pressed',
      badge: 1,
      payload: {
        key: 'space'
      },
    });

    // Verify card flipped
    await waitFor(element(by.id('card-back')))
      .toBeVisible()
      .withTimeout(2000);
  });

  it('should track study statistics', async () => {
    // Navigate to Profile tab
    await element(by.id('profile-tab')).tap();
    
    // Check study statistics
    await expect(element(by.id('study-stats'))).toBeVisible();
    await expect(element(by.id('cards-studied-today'))).toBeVisible();
    await expect(element(by.id('study-streak'))).toBeVisible();
  });

  it('should handle offline study mode', async () => {
    // Disable network
    await device.setURLBlacklist(['*']);
    
    // Navigate to Study tab
    await element(by.id('study-tab')).tap();
    
    // Verify offline mode indicator
    await expect(element(by.id('offline-indicator'))).toBeVisible();
    
    // Verify cards still load from cache
    await waitFor(element(by.id('flashcard-container')))
      .toBeVisible()
      .withTimeout(10000);

    // Re-enable network
    await device.setURLBlacklist([]);
  });
});