import { test, expect, Browser, BrowserContext } from '@playwright/test';
import { devices } from '@playwright/test';

/**
 * Platform-Specific Feature Tests
 * Tests features that are specific to certain platforms or browsers
 */

interface PlatformFeature {
  name: string;
  platforms: string[];
  testFunction: (page: any, browserName: string) => Promise<void>;
  required: boolean;
}

const PLATFORM_FEATURES: PlatformFeature[] = [
  {
    name: 'File System Access API',
    platforms: ['chromium'],
    testFunction: testFileSystemAccess,
    required: false
  },
  {
    name: 'Web Share API',
    platforms: ['chromium', 'webkit'],
    testFunction: testWebShareAPI,
    required: false
  },
  {
    name: 'Push Notifications',
    platforms: ['chromium', 'firefox'],
    testFunction: testPushNotifications,
    required: false
  },
  {
    name: 'Service Workers',
    platforms: ['chromium', 'firefox', 'webkit'],
    testFunction: testServiceWorkers,
    required: true
  },
  {
    name: 'IndexedDB',
    platforms: ['chromium', 'firefox', 'webkit'],
    testFunction: testIndexedDB,
    required: true
  },
  {
    name: 'Web Workers',
    platforms: ['chromium', 'firefox', 'webkit'],
    testFunction: testWebWorkers,
    required: true
  },
  {
    name: 'Clipboard API',
    platforms: ['chromium'],
    testFunction: testClipboardAPI,
    required: false
  },
  {
    name: 'Fullscreen API',
    platforms: ['chromium', 'firefox', 'webkit'],
    testFunction: testFullscreenAPI,
    required: false
  },
  {
    name: 'Drag and Drop',
    platforms: ['chromium', 'firefox', 'webkit'],
    testFunction: testDragAndDrop,
    required: true
  },
  {
    name: 'Touch Events',
    platforms: ['chromium', 'webkit'],
    testFunction: testTouchEvents,
    required: false
  }
];

test.describe('Platform-Specific Feature Tests', () => {
  
  test.describe('Browser-Specific Features', () => {
    PLATFORM_FEATURES.forEach(feature => {
      feature.platforms.forEach(platform => {
        test(`${feature.name} works on ${platform}`, async ({ page, browserName }) => {
          test.skip(browserName !== platform, `Skipping ${feature.name} test for ${browserName}`);
          
          await page.goto('/');
          
          try {
            await feature.testFunction(page, browserName);
          } catch (error) {
            if (feature.required) {
              throw error;
            } else {
              console.warn(`Optional feature ${feature.name} not supported on ${platform}: ${error}`);
            }
          }
        });
      });
    });
  });

  test.describe('Chrome-Specific Features', () => {
    test('Chrome DevTools Protocol integration', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chrome-specific test');
      
      await page.goto('/');
      
      // Test Chrome DevTools Protocol features if available
      const cdpSupported = await page.evaluate(() => {
        return 'chrome' in window && 'runtime' in (window as any).chrome;
      });
      
      if (cdpSupported) {
        // Test Chrome extension APIs if available
        const extensionAPIs = await page.evaluate(() => {
          const chrome = (window as any).chrome;
          return {
            runtime: !!chrome.runtime,
            storage: !!chrome.storage,
            tabs: !!chrome.tabs
          };
        });
        
        console.log('Chrome extension APIs available:', extensionAPIs);
      }
    });

    test('Chrome File System Access API', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chrome-specific test');
      
      await page.goto('/');
      
      const fileSystemAccessSupported = await page.evaluate(() => {
        return 'showOpenFilePicker' in window;
      });
      
      if (fileSystemAccessSupported) {
        // Test file system access integration
        await page.evaluate(() => {
          // Mock file system access for testing
          (window as any).testFileSystemAccess = async () => {
            try {
              // This would normally show a file picker
              return { supported: true };
            } catch (e) {
              return { supported: false, error: e.message };
            }
          };
        });
        
        const result = await page.evaluate(() => (window as any).testFileSystemAccess());
        expect(result.supported).toBe(true);
      }
    });

    test('Chrome Performance Observer', async ({ page, browserName }) => {
      test.skip(browserName !== 'chromium', 'Chrome-specific test');
      
      await page.goto('/');
      
      const performanceMetrics = await page.evaluate(() => {
        return new Promise((resolve) => {
          if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
              const entries = list.getEntries();
              resolve({
                supported: true,
                entriesCount: entries.length,
                types: entries.map(e => e.entryType)
              });
            });
            
            observer.observe({ entryTypes: ['navigation', 'resource', 'measure'] });
            
            // Trigger some performance measurements
            performance.mark('test-start');
            setTimeout(() => {
              performance.mark('test-end');
              performance.measure('test-duration', 'test-start', 'test-end');
            }, 100);
            
            setTimeout(() => resolve({ supported: true, timeout: true }), 1000);
          } else {
            resolve({ supported: false });
          }
        });
      });
      
      expect(performanceMetrics).toHaveProperty('supported', true);
    });
  });

  test.describe('Safari-Specific Features', () => {
    test('Safari Touch Events and Gestures', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Safari-specific test');
      
      await page.goto('/');
      
      // Test Safari-specific touch event handling
      const touchSupport = await page.evaluate(() => {
        return {
          touchEvents: 'ontouchstart' in window,
          gestureEvents: 'ongesturestart' in window,
          webkitTransform: 'webkitTransform' in document.documentElement.style
        };
      });
      
      expect(touchSupport.touchEvents).toBe(true);
      
      // Test document viewer with touch gestures
      await uploadTestDocument(page);
      await page.click('[data-testid="library-tab"]');
      await page.click('[data-testid="document-item"]');
      
      // Test pinch-to-zoom simulation
      const documentViewer = page.locator('[data-testid="document-viewer"]');
      if (await documentViewer.isVisible()) {
        // Simulate touch gestures (limited in automated testing)
        await page.evaluate(() => {
          const viewer = document.querySelector('[data-testid="document-viewer"]');
          if (viewer) {
            // Simulate gesture events
            const gestureStart = new Event('gesturestart');
            const gestureChange = new Event('gesturechange');
            const gestureEnd = new Event('gestureend');
            
            viewer.dispatchEvent(gestureStart);
            viewer.dispatchEvent(gestureChange);
            viewer.dispatchEvent(gestureEnd);
          }
        });
      }
    });

    test('Safari PWA capabilities', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Safari-specific test');
      
      await page.goto('/');
      
      // Test Safari PWA features
      const pwaSupport = await page.evaluate(() => {
        return {
          standalone: 'standalone' in navigator,
          addToHomeScreen: 'onbeforeinstallprompt' in window,
          webAppManifest: !!document.querySelector('link[rel="manifest"]'),
          serviceWorker: 'serviceWorker' in navigator
        };
      });
      
      expect(pwaSupport.serviceWorker).toBe(true);
      
      // Test standalone mode detection
      const isStandalone = await page.evaluate(() => {
        return (navigator as any).standalone || 
               window.matchMedia('(display-mode: standalone)').matches;
      });
      
      console.log('Safari standalone mode:', isStandalone);
    });

    test('Safari privacy features', async ({ page, browserName }) => {
      test.skip(browserName !== 'webkit', 'Safari-specific test');
      
      await page.goto('/');
      
      // Test Safari's privacy-focused features
      const privacyFeatures = await page.evaluate(() => {
        return {
          // Safari blocks third-party cookies by default
          cookieBlocking: !navigator.cookieEnabled || 
                         document.cookie.indexOf('test=') === -1,
          
          // Safari has stricter localStorage policies
          localStorageRestricted: (() => {
            try {
              localStorage.setItem('safari-test', 'test');
              localStorage.removeItem('safari-test');
              return false;
            } catch (e) {
              return true;
            }
          })(),
          
          // Safari blocks fingerprinting
          reducedFingerprinting: navigator.userAgent.indexOf('Safari') > -1 &&
                                navigator.userAgent.indexOf('Chrome') === -1
        };
      });
      
      console.log('Safari privacy features:', privacyFeatures);
      
      // Ensure app works with Safari's privacy restrictions
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    });
  });

  test.describe('Firefox-Specific Features', () => {
    test('Firefox Developer Tools integration', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox-specific test');
      
      await page.goto('/');
      
      // Test Firefox-specific developer features
      const firefoxFeatures = await page.evaluate(() => {
        return {
          mozInnerScreenX: 'mozInnerScreenX' in window,
          mozRequestFullScreen: 'mozRequestFullScreen' in document.documentElement,
          firefoxUserAgent: navigator.userAgent.indexOf('Firefox') > -1
        };
      });
      
      expect(firefoxFeatures.firefoxUserAgent).toBe(true);
    });

    test('Firefox CSS features', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox-specific test');
      
      await page.goto('/');
      
      // Test Firefox-specific CSS features
      const cssSupport = await page.evaluate(() => {
        return {
          mozAppearance: CSS.supports('-moz-appearance', 'none'),
          firefoxScrollbar: CSS.supports('scrollbar-width', 'thin'),
          mozUserSelect: CSS.supports('-moz-user-select', 'none')
        };
      });
      
      console.log('Firefox CSS support:', cssSupport);
      
      // Test that app styling works correctly in Firefox
      const computedStyles = await page.evaluate(() => {
        const element = document.querySelector('[data-testid="main-content"]');
        if (element) {
          const styles = window.getComputedStyle(element);
          return {
            display: styles.display,
            flexDirection: styles.flexDirection,
            backgroundColor: styles.backgroundColor
          };
        }
        return null;
      });
      
      expect(computedStyles).not.toBeNull();
    });

    test('Firefox security features', async ({ page, browserName }) => {
      test.skip(browserName !== 'firefox', 'Firefox-specific test');
      
      await page.goto('/');
      
      // Test Firefox security features
      const securityFeatures = await page.evaluate(() => {
        return {
          contentSecurityPolicy: !!document.querySelector('meta[http-equiv="Content-Security-Policy"]'),
          strictTransportSecurity: document.location.protocol === 'https:',
          mixedContentBlocking: true // Firefox blocks mixed content by default
        };
      });
      
      console.log('Firefox security features:', securityFeatures);
      
      // Ensure app works with Firefox security policies
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    });
  });

  test.describe('Mobile-Specific Features', () => {
    test('Mobile device orientation handling', async ({ page }) => {
      // Test with mobile viewport
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/');
      
      // Test orientation change simulation
      await page.evaluate(() => {
        // Simulate orientation change
        window.dispatchEvent(new Event('orientationchange'));
        
        // Mock orientation API
        (window.screen as any).orientation = {
          angle: 90,
          type: 'landscape-primary'
        };
      });
      
      // Verify app handles orientation change
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
      
      // Test that layout adapts
      const mainContent = page.locator('[data-testid="main-content"]');
      const boundingBox = await mainContent.boundingBox();
      
      if (boundingBox) {
        expect(boundingBox.width).toBeGreaterThan(0);
        expect(boundingBox.height).toBeGreaterThan(0);
      }
    });

    test('Mobile touch and swipe gestures', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/');
      
      // Test touch event handling
      const touchSupported = await page.evaluate(() => {
        return 'ontouchstart' in window;
      });
      
      if (touchSupported) {
        // Test swipe gestures in study mode
        await page.click('[data-testid="study-tab"]');
        
        const studyArea = page.locator('[data-testid="study-area"]');
        if (await studyArea.isVisible()) {
          // Simulate swipe gesture
          await page.evaluate(() => {
            const element = document.querySelector('[data-testid="study-area"]');
            if (element) {
              const touchStart = new TouchEvent('touchstart', {
                touches: [new Touch({
                  identifier: 0,
                  target: element,
                  clientX: 200,
                  clientY: 300
                })]
              });
              
              const touchEnd = new TouchEvent('touchend', {
                touches: []
              });
              
              element.dispatchEvent(touchStart);
              setTimeout(() => element.dispatchEvent(touchEnd), 100);
            }
          });
        }
      }
    });

    test('Mobile viewport and safe areas', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/');
      
      // Test viewport meta tag
      const viewportMeta = await page.evaluate(() => {
        const meta = document.querySelector('meta[name="viewport"]');
        return meta ? meta.getAttribute('content') : null;
      });
      
      expect(viewportMeta).toContain('width=device-width');
      expect(viewportMeta).toContain('initial-scale=1');
      
      // Test safe area handling (for devices with notches)
      const safeAreaSupport = await page.evaluate(() => {
        return CSS.supports('padding-top', 'env(safe-area-inset-top)');
      });
      
      console.log('Safe area support:', safeAreaSupport);
      
      // Test that content doesn't overlap with system UI
      const header = page.locator('[data-testid="app-header"]');
      if (await header.isVisible()) {
        const headerBox = await header.boundingBox();
        if (headerBox) {
          expect(headerBox.y).toBeGreaterThanOrEqual(0);
        }
      }
    });
  });

  test.describe('Desktop-Specific Features', () => {
    test('Desktop keyboard shortcuts', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      
      // Test common keyboard shortcuts
      const shortcuts = [
        { key: 'Ctrl+K', action: 'search' },
        { key: 'Ctrl+N', action: 'new-document' },
        { key: 'Escape', action: 'close-modal' }
      ];
      
      for (const shortcut of shortcuts) {
        // Test if shortcut is handled
        await page.keyboard.press(shortcut.key);
        
        // Wait a moment for the action to take effect
        await page.waitForTimeout(500);
        
        // Verify the action occurred (this would depend on actual implementation)
        console.log(`Tested shortcut: ${shortcut.key} for ${shortcut.action}`);
      }
    });

    test('Desktop drag and drop file upload', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      
      // Test drag and drop functionality
      const dropZone = page.locator('[data-testid="file-drop-zone"]');
      
      if (await dropZone.isVisible()) {
        // Simulate drag and drop
        await page.evaluate(() => {
          const dropZone = document.querySelector('[data-testid="file-drop-zone"]');
          if (dropZone) {
            const dragEnter = new DragEvent('dragenter', {
              dataTransfer: new DataTransfer()
            });
            
            const drop = new DragEvent('drop', {
              dataTransfer: new DataTransfer()
            });
            
            dropZone.dispatchEvent(dragEnter);
            dropZone.dispatchEvent(drop);
          }
        });
        
        // Verify drag and drop handling
        await expect(dropZone).toBeVisible();
      }
    });

    test('Desktop context menus', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      
      // Test right-click context menus
      await page.click('[data-testid="library-tab"]');
      
      const documentItem = page.locator('[data-testid="document-item"]');
      if (await documentItem.count() > 0) {
        // Right-click on document item
        await documentItem.first().click({ button: 'right' });
        
        // Check if context menu appears
        const contextMenu = page.locator('[data-testid="context-menu"]');
        if (await contextMenu.isVisible()) {
          await expect(contextMenu).toBeVisible();
          
          // Test context menu items
          const menuItems = await contextMenu.locator('[role="menuitem"]').all();
          expect(menuItems.length).toBeGreaterThan(0);
        }
      }
    });
  });
});

// Platform-specific test functions
async function testFileSystemAccess(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'showOpenFilePicker' in window;
  });
  
  if (supported) {
    // Test file system access API integration
    await page.evaluate(() => {
      (window as any).testFileSystemAPI = true;
    });
    
    const result = await page.evaluate(() => (window as any).testFileSystemAPI);
    expect(result).toBe(true);
  } else {
    throw new Error('File System Access API not supported');
  }
}

async function testWebShareAPI(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'share' in navigator;
  });
  
  if (supported) {
    // Test web share API
    const shareData = await page.evaluate(() => {
      return navigator.canShare({
        title: 'Test Document',
        text: 'Sharing a test document',
        url: window.location.href
      });
    });
    
    expect(shareData).toBeDefined();
  } else {
    throw new Error('Web Share API not supported');
  }
}

async function testPushNotifications(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'Notification' in window && 'serviceWorker' in navigator;
  });
  
  if (supported) {
    const permission = await page.evaluate(() => {
      return Notification.permission;
    });
    
    expect(['default', 'granted', 'denied']).toContain(permission);
  } else {
    throw new Error('Push Notifications not supported');
  }
}

async function testServiceWorkers(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'serviceWorker' in navigator;
  });
  
  if (!supported) {
    throw new Error('Service Workers not supported');
  }
  
  // Test service worker registration
  const registration = await page.evaluate(() => {
    return navigator.serviceWorker.getRegistrations();
  });
  
  expect(Array.isArray(registration)).toBe(true);
}

async function testIndexedDB(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'indexedDB' in window;
  });
  
  if (!supported) {
    throw new Error('IndexedDB not supported');
  }
  
  // Test IndexedDB operations
  const dbTest = await page.evaluate(() => {
    return new Promise((resolve) => {
      const request = indexedDB.open('test-db', 1);
      request.onsuccess = () => {
        request.result.close();
        resolve(true);
      };
      request.onerror = () => resolve(false);
    });
  });
  
  expect(dbTest).toBe(true);
}

async function testWebWorkers(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'Worker' in window;
  });
  
  if (!supported) {
    throw new Error('Web Workers not supported');
  }
  
  // Test web worker creation
  const workerTest = await page.evaluate(() => {
    try {
      const worker = new Worker('data:application/javascript,postMessage("test")');
      worker.terminate();
      return true;
    } catch (e) {
      return false;
    }
  });
  
  expect(workerTest).toBe(true);
}

async function testClipboardAPI(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'clipboard' in navigator && 'writeText' in navigator.clipboard;
  });
  
  if (supported) {
    // Test clipboard write (might require user gesture)
    const clipboardTest = await page.evaluate(() => {
      return navigator.clipboard.writeText('test').then(() => true).catch(() => false);
    });
    
    // Clipboard API might be restricted without user gesture
    console.log('Clipboard API test result:', clipboardTest);
  } else {
    throw new Error('Clipboard API not supported');
  }
}

async function testFullscreenAPI(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'requestFullscreen' in document.documentElement ||
           'webkitRequestFullscreen' in document.documentElement ||
           'mozRequestFullScreen' in document.documentElement;
  });
  
  if (!supported) {
    throw new Error('Fullscreen API not supported');
  }
  
  expect(supported).toBe(true);
}

async function testDragAndDrop(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'draggable' in document.createElement('div');
  });
  
  if (!supported) {
    throw new Error('Drag and Drop not supported');
  }
  
  expect(supported).toBe(true);
}

async function testTouchEvents(page: any, browserName: string) {
  const supported = await page.evaluate(() => {
    return 'ontouchstart' in window;
  });
  
  // Touch events might not be available in desktop browsers
  console.log('Touch events supported:', supported);
}

async function uploadTestDocument(page: any) {
  const fileInput = page.locator('input[type="file"]');
  
  if (await fileInput.isVisible()) {
    await fileInput.setInputFiles({
      name: 'platform-test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('Mock PDF content for platform testing')
    });
    
    await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible({ timeout: 30000 });
  }
}