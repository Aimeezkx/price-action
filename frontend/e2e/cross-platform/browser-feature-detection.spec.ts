import { test, expect } from '@playwright/test';

/**
 * Browser Feature Detection Tests
 * Validates that required browser features are available across different browsers
 */

interface BrowserFeatures {
  name: string;
  version: string;
  features: {
    [key: string]: boolean;
  };
}

test.describe('Browser Feature Detection', () => {
  
  test('Detect and validate browser capabilities', async ({ page, browserName }) => {
    await page.goto('/');
    
    const browserFeatures: BrowserFeatures = await page.evaluate(() => {
      const nav = navigator as any;
      
      return {
        name: nav.userAgent,
        version: nav.appVersion,
        features: {
          // Core JavaScript features
          es6Support: (() => {
            try {
              eval('const test = () => {}; class Test {}');
              return true;
            } catch (e) {
              return false;
            }
          })(),
          
          // Web APIs
          fileApi: typeof File !== 'undefined' && typeof FileReader !== 'undefined',
          fetchApi: typeof fetch !== 'undefined',
          webWorkers: typeof Worker !== 'undefined',
          serviceWorkers: 'serviceWorker' in navigator,
          webSockets: typeof WebSocket !== 'undefined',
          
          // Storage APIs
          localStorage: (() => {
            try {
              localStorage.setItem('test', 'test');
              localStorage.removeItem('test');
              return true;
            } catch (e) {
              return false;
            }
          })(),
          sessionStorage: (() => {
            try {
              sessionStorage.setItem('test', 'test');
              sessionStorage.removeItem('test');
              return true;
            } catch (e) {
              return false;
            }
          })(),
          indexedDB: 'indexedDB' in window,
          
          // Media APIs
          getUserMedia: !!(nav.mediaDevices && nav.mediaDevices.getUserMedia),
          webRTC: !!(window as any).RTCPeerConnection,
          
          // Graphics APIs
          canvas: (() => {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext && canvas.getContext('2d'));
          })(),
          webGL: (() => {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
          })(),
          
          // CSS Features
          cssGrid: CSS.supports('display', 'grid'),
          cssFlexbox: CSS.supports('display', 'flex'),
          cssCustomProperties: CSS.supports('color', 'var(--test)'),
          cssTransforms: CSS.supports('transform', 'translateX(10px)'),
          cssTransitions: CSS.supports('transition', 'all 1s'),
          cssAnimations: CSS.supports('animation', 'test 1s'),
          
          // Performance APIs
          performanceApi: 'performance' in window,
          performanceObserver: 'PerformanceObserver' in window,
          intersectionObserver: 'IntersectionObserver' in window,
          mutationObserver: 'MutationObserver' in window,
          
          // Security features
          cryptoApi: 'crypto' in window && 'subtle' in crypto,
          
          // Modern JavaScript features
          asyncAwait: (() => {
            try {
              eval('async function test() { await Promise.resolve(); }');
              return true;
            } catch (e) {
              return false;
            }
          })(),
          modules: 'noModule' in document.createElement('script'),
          
          // Touch and pointer events
          touchEvents: 'ontouchstart' in window,
          pointerEvents: 'onpointerdown' in window,
          
          // Clipboard API
          clipboardApi: !!(nav.clipboard && nav.clipboard.writeText),
          
          // Notification API
          notifications: 'Notification' in window,
          
          // Geolocation API
          geolocation: 'geolocation' in navigator,
          
          // Device orientation
          deviceOrientation: 'ondeviceorientation' in window,
          
          // Fullscreen API
          fullscreen: !!(document as any).fullscreenEnabled || !!(document as any).webkitFullscreenEnabled,
          
          // Drag and drop
          dragAndDrop: 'draggable' in document.createElement('div'),
          
          // History API
          historyApi: !!(window.history && window.history.pushState),
          
          // WebAssembly
          webAssembly: 'WebAssembly' in window
        }
      };
    });
    
    console.log(`Browser: ${browserName}`);
    console.log('Features:', browserFeatures.features);
    
    // Critical features that must be supported
    const criticalFeatures = [
      'fileApi',
      'fetchApi',
      'localStorage',
      'cssFlexbox',
      'performanceApi',
      'historyApi'
    ];
    
    // Verify critical features are supported
    for (const feature of criticalFeatures) {
      expect(browserFeatures.features[feature]).toBe(true, 
        `Critical feature '${feature}' is not supported in ${browserName}`);
    }
    
    // Recommended features (warn if not supported but don't fail)
    const recommendedFeatures = [
      'webWorkers',
      'cssGrid',
      'cssCustomProperties',
      'intersectionObserver',
      'asyncAwait',
      'modules'
    ];
    
    const unsupportedRecommended = recommendedFeatures.filter(
      feature => !browserFeatures.features[feature]
    );
    
    if (unsupportedRecommended.length > 0) {
      console.warn(`Recommended features not supported in ${browserName}:`, unsupportedRecommended);
    }
    
    // Store results for reporting
    await page.evaluate((features) => {
      (window as any).browserCompatibilityResults = features;
    }, browserFeatures);
  });
  
  test('Test browser-specific workarounds', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Test Safari-specific issues
    if (browserName === 'webkit') {
      // Test date input support
      const dateInputSupported = await page.evaluate(() => {
        const input = document.createElement('input');
        input.type = 'date';
        return input.type === 'date';
      });
      
      // Safari has limited date input support
      console.log(`Safari date input support: ${dateInputSupported}`);
      
      // Test file input multiple attribute
      const multipleFileSupport = await page.evaluate(() => {
        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        return input.multiple;
      });
      
      expect(multipleFileSupport).toBe(true);
    }
    
    // Test Firefox-specific issues
    if (browserName === 'firefox') {
      // Test clipboard API availability
      const clipboardSupported = await page.evaluate(() => {
        return !!(navigator.clipboard && navigator.clipboard.writeText);
      });
      
      console.log(`Firefox clipboard API support: ${clipboardSupported}`);
    }
    
    // Test Chrome-specific features
    if (browserName === 'chromium') {
      // Test Chrome-specific APIs
      const chromeFeatures = await page.evaluate(() => {
        return {
          webkitSpeechRecognition: 'webkitSpeechRecognition' in window,
          chrome: 'chrome' in window
        };
      });
      
      console.log('Chrome-specific features:', chromeFeatures);
    }
  });
  
  test('Test polyfill requirements', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Check which polyfills might be needed
    const polyfillNeeds = await page.evaluate(() => {
      const needs = {
        fetch: typeof fetch === 'undefined',
        promise: typeof Promise === 'undefined',
        intersectionObserver: typeof IntersectionObserver === 'undefined',
        customElements: typeof customElements === 'undefined',
        webComponents: typeof HTMLTemplateElement === 'undefined',
        objectAssign: typeof Object.assign === 'undefined',
        arrayIncludes: !Array.prototype.includes,
        stringIncludes: !String.prototype.includes,
        arrayFind: !Array.prototype.find,
        arrayFrom: !Array.from
      };
      
      return needs;
    });
    
    const requiredPolyfills = Object.entries(polyfillNeeds)
      .filter(([_, needed]) => needed)
      .map(([polyfill]) => polyfill);
    
    if (requiredPolyfills.length > 0) {
      console.warn(`${browserName} requires polyfills for:`, requiredPolyfills);
    }
    
    // Ensure no critical polyfills are needed
    const criticalPolyfills = ['fetch', 'promise'];
    const missingCritical = criticalPolyfills.filter(p => polyfillNeeds[p as keyof typeof polyfillNeeds]);
    
    expect(missingCritical).toHaveLength(0, 
      `Critical polyfills missing in ${browserName}: ${missingCritical.join(', ')}`);
  });
});