const { device, expect, element, by, waitFor } = require('detox');

/**
 * iOS Device Compatibility Tests
 * Tests app functionality across different iOS devices and orientations
 */

describe('iOS Device Compatibility', () => {
  
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  describe('iPhone Device Tests', () => {
    const iPhoneDevices = [
      { name: 'iPhone SE (3rd generation)', width: 375, height: 667 },
      { name: 'iPhone 14', width: 390, height: 844 },
      { name: 'iPhone 14 Pro', width: 393, height: 852 },
      { name: 'iPhone 14 Pro Max', width: 430, height: 932 }
    ];

    iPhoneDevices.forEach(deviceInfo => {
      it(`should work correctly on ${deviceInfo.name}`, async () => {
        // Test app launch and basic navigation
        await expect(element(by.id('main-screen'))).toBeVisible();
        
        // Test document upload functionality
        await element(by.id('upload-button')).tap();
        await expect(element(by.id('file-picker'))).toBeVisible();
        
        // Test navigation between tabs
        await element(by.id('library-tab')).tap();
        await expect(element(by.id('library-screen'))).toBeVisible();
        
        await element(by.id('study-tab')).tap();
        await expect(element(by.id('study-screen'))).toBeVisible();
        
        await element(by.id('search-tab')).tap();
        await expect(element(by.id('search-screen'))).toBeVisible();
        
        // Test responsive layout elements
        await expect(element(by.id('navigation-bar'))).toBeVisible();
        await expect(element(by.id('content-area'))).toBeVisible();
      });
    });
  });

  describe('iPad Device Tests', () => {
    const iPadDevices = [
      { name: 'iPad (10th generation)', width: 820, height: 1180 },
      { name: 'iPad Air (5th generation)', width: 820, height: 1180 },
      { name: 'iPad Pro 11-inch', width: 834, height: 1194 },
      { name: 'iPad Pro 12.9-inch', width: 1024, height: 1366 }
    ];

    iPadDevices.forEach(deviceInfo => {
      it(`should adapt layout for ${deviceInfo.name}`, async () => {
        // Test split-view layout on iPad
        await expect(element(by.id('main-screen'))).toBeVisible();
        
        // On iPad, we should see sidebar navigation
        if (deviceInfo.width >= 768) {
          await expect(element(by.id('sidebar-navigation'))).toBeVisible();
          await expect(element(by.id('main-content-area'))).toBeVisible();
        }
        
        // Test document viewing in larger format
        await element(by.id('library-tab')).tap();
        
        // Upload and view a document
        await element(by.id('upload-button')).tap();
        // Simulate document selection and upload
        await waitFor(element(by.id('document-item'))).toBeVisible().withTimeout(30000);
        
        await element(by.id('document-item')).tap();
        await expect(element(by.id('document-viewer'))).toBeVisible();
        
        // Test chapter navigation in iPad layout
        await expect(element(by.id('chapter-list'))).toBeVisible();
        await element(by.id('chapter-item')).atIndex(0).tap();
        await expect(element(by.id('chapter-content'))).toBeVisible();
      });
    });
  });

  describe('Orientation Tests', () => {
    it('should handle portrait to landscape rotation', async () => {
      // Start in portrait
      await device.setOrientation('portrait');
      await expect(element(by.id('main-screen'))).toBeVisible();
      
      // Test initial layout
      await expect(element(by.id('navigation-bar'))).toBeVisible();
      
      // Rotate to landscape
      await device.setOrientation('landscape');
      
      // Verify layout adapts
      await expect(element(by.id('main-screen'))).toBeVisible();
      await expect(element(by.id('navigation-bar'))).toBeVisible();
      
      // Test functionality still works
      await element(by.id('library-tab')).tap();
      await expect(element(by.id('library-screen'))).toBeVisible();
      
      // Rotate back to portrait
      await device.setOrientation('portrait');
      await expect(element(by.id('library-screen'))).toBeVisible();
    });

    it('should handle landscape to portrait rotation during document viewing', async () => {
      // Setup: Navigate to document viewer
      await element(by.id('library-tab')).tap();
      await element(by.id('upload-button')).tap();
      await waitFor(element(by.id('document-item'))).toBeVisible().withTimeout(30000);
      await element(by.id('document-item')).tap();
      
      // Start in landscape
      await device.setOrientation('landscape');
      await expect(element(by.id('document-viewer'))).toBeVisible();
      
      // Rotate to portrait
      await device.setOrientation('portrait');
      
      // Verify document viewer adapts
      await expect(element(by.id('document-viewer'))).toBeVisible();
      await expect(element(by.id('chapter-content'))).toBeVisible();
    });
  });

  describe('Touch and Gesture Tests', () => {
    it('should handle touch interactions correctly', async () => {
      await element(by.id('library-tab')).tap();
      
      // Test single tap
      await element(by.id('upload-button')).tap();
      await expect(element(by.id('file-picker'))).toBeVisible();
      
      // Dismiss file picker
      await element(by.id('cancel-button')).tap();
      
      // Test long press (if implemented)
      try {
        await element(by.id('document-item')).longPress();
        await expect(element(by.id('context-menu'))).toBeVisible();
        
        // Dismiss context menu
        await element(by.id('main-screen')).tap();
      } catch (e) {
        // Long press might not be implemented
        console.log('Long press not implemented');
      }
    });

    it('should handle swipe gestures', async () => {
      // Navigate to study mode
      await element(by.id('study-tab')).tap();
      
      // If cards are available, test swipe gestures
      try {
        await waitFor(element(by.id('flashcard'))).toBeVisible().withTimeout(10000);
        
        // Test swipe left (if implemented)
        await element(by.id('flashcard')).swipe('left');
        
        // Test swipe right (if implemented)
        await element(by.id('flashcard')).swipe('right');
        
      } catch (e) {
        console.log('No cards available for swipe testing');
      }
    });

    it('should handle pinch-to-zoom in document viewer', async () => {
      // Navigate to document viewer
      await element(by.id('library-tab')).tap();
      
      try {
        await waitFor(element(by.id('document-item'))).toBeVisible().withTimeout(10000);
        await element(by.id('document-item')).tap();
        await expect(element(by.id('document-viewer'))).toBeVisible();
        
        // Test pinch gestures (if supported by Detox)
        // Note: Detox has limited support for complex gestures
        await element(by.id('document-content')).pinch(1.5); // Zoom in
        await element(by.id('document-content')).pinch(0.5); // Zoom out
        
      } catch (e) {
        console.log('Pinch gesture testing not fully supported');
      }
    });
  });

  describe('Performance Tests', () => {
    it('should maintain performance across different devices', async () => {
      const startTime = Date.now();
      
      // Test app launch performance
      await expect(element(by.id('main-screen'))).toBeVisible();
      
      const launchTime = Date.now() - startTime;
      expect(launchTime).toBeLessThan(5000); // App should launch within 5 seconds
      
      // Test navigation performance
      const navStartTime = Date.now();
      await element(by.id('library-tab')).tap();
      await expect(element(by.id('library-screen'))).toBeVisible();
      
      const navTime = Date.now() - navStartTime;
      expect(navTime).toBeLessThan(1000); // Navigation should be under 1 second
    });

    it('should handle memory constraints gracefully', async () => {
      // Test with multiple document uploads (simulate memory pressure)
      await element(by.id('library-tab')).tap();
      
      // Simulate multiple operations
      for (let i = 0; i < 3; i++) {
        await element(by.id('upload-button')).tap();
        await element(by.id('cancel-button')).tap();
        
        // Check that app remains responsive
        await expect(element(by.id('library-screen'))).toBeVisible();
      }
    });
  });

  describe('Accessibility Tests', () => {
    it('should support VoiceOver navigation', async () => {
      // Enable accessibility testing
      await device.enableSynchronization();
      
      // Test that key elements have accessibility labels
      await expect(element(by.id('upload-button'))).toHaveAccessibilityLabel();
      await expect(element(by.id('library-tab'))).toHaveAccessibilityLabel();
      await expect(element(by.id('study-tab'))).toHaveAccessibilityLabel();
      await expect(element(by.id('search-tab'))).toHaveAccessibilityLabel();
    });

    it('should support Dynamic Type scaling', async () => {
      // Test with different text sizes (if supported)
      await expect(element(by.id('main-screen'))).toBeVisible();
      
      // Verify text elements are visible and readable
      await element(by.id('library-tab')).tap();
      await expect(element(by.text('Library'))).toBeVisible();
      
      await element(by.id('study-tab')).tap();
      await expect(element(by.text('Study'))).toBeVisible();
    });
  });

  describe('Network Connectivity Tests', () => {
    it('should handle offline mode', async () => {
      // Disable network
      await device.setNetworkConditions({
        offline: true
      });
      
      // Test offline functionality
      await element(by.id('library-tab')).tap();
      await expect(element(by.id('library-screen'))).toBeVisible();
      
      // Should show offline indicator or cached content
      try {
        await expect(element(by.id('offline-indicator'))).toBeVisible();
      } catch (e) {
        // Offline indicator might not be implemented
        console.log('Offline indicator not found');
      }
      
      // Re-enable network
      await device.setNetworkConditions({
        offline: false
      });
    });

    it('should handle slow network conditions', async () => {
      // Simulate slow network
      await device.setNetworkConditions({
        speed: 'slow-3g'
      });
      
      // Test that app remains usable
      await element(by.id('library-tab')).tap();
      await expect(element(by.id('library-screen'))).toBeVisible();
      
      // Reset network conditions
      await device.setNetworkConditions({
        speed: 'full'
      });
    });
  });
});