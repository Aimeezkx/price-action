/**
 * Cross-platform testing configuration
 */

import { BrowserConfig, DeviceConfig, CrossPlatformTestSuite } from './types';

export const BROWSER_CONFIGS: BrowserConfig[] = [
  {
    name: 'Chrome',
    version: 'latest',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 },
    features: ['webgl', 'webrtc', 'serviceworker', 'indexeddb', 'websockets']
  },
  {
    name: 'Firefox',
    version: 'latest',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    viewport: { width: 1920, height: 1080 },
    features: ['webgl', 'webrtc', 'serviceworker', 'indexeddb', 'websockets']
  },
  {
    name: 'Safari',
    version: 'latest',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    viewport: { width: 1920, height: 1080 },
    features: ['webgl', 'serviceworker', 'indexeddb', 'websockets']
  },
  {
    name: 'Edge',
    version: 'latest',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    viewport: { width: 1920, height: 1080 },
    features: ['webgl', 'webrtc', 'serviceworker', 'indexeddb', 'websockets']
  }
];

export const DEVICE_CONFIGS: DeviceConfig[] = [
  // iOS Devices
  {
    name: 'iPhone 15 Pro',
    type: 'mobile',
    os: 'iOS',
    osVersion: '17.0',
    viewport: { width: 393, height: 852 },
    pixelRatio: 3,
    touchEnabled: true
  },
  {
    name: 'iPhone 15',
    type: 'mobile',
    os: 'iOS',
    osVersion: '17.0',
    viewport: { width: 393, height: 852 },
    pixelRatio: 3,
    touchEnabled: true
  },
  {
    name: 'iPad Pro 12.9',
    type: 'tablet',
    os: 'iOS',
    osVersion: '17.0',
    viewport: { width: 1024, height: 1366 },
    pixelRatio: 2,
    touchEnabled: true
  },
  {
    name: 'iPad Air',
    type: 'tablet',
    os: 'iOS',
    osVersion: '17.0',
    viewport: { width: 820, height: 1180 },
    pixelRatio: 2,
    touchEnabled: true
  },
  // Desktop configurations
  {
    name: 'Desktop 1920x1080',
    type: 'desktop',
    os: 'Windows',
    osVersion: '11',
    viewport: { width: 1920, height: 1080 },
    pixelRatio: 1,
    touchEnabled: false
  },
  {
    name: 'Desktop 1366x768',
    type: 'desktop',
    os: 'Windows',
    osVersion: '11',
    viewport: { width: 1366, height: 768 },
    pixelRatio: 1,
    touchEnabled: false
  },
  {
    name: 'MacBook Pro 16"',
    type: 'desktop',
    os: 'macOS',
    osVersion: '14.0',
    viewport: { width: 1728, height: 1117 },
    pixelRatio: 2,
    touchEnabled: false
  }
];

export const RESPONSIVE_BREAKPOINTS = {
  mobile: { width: 375, height: 667 },
  mobileLarge: { width: 414, height: 896 },
  tablet: { width: 768, height: 1024 },
  tabletLarge: { width: 1024, height: 1366 },
  desktop: { width: 1280, height: 800 },
  desktopLarge: { width: 1920, height: 1080 },
  ultrawide: { width: 2560, height: 1440 }
};

export const TEST_TIMEOUTS = {
  pageLoad: 30000,
  elementWait: 10000,
  interaction: 5000,
  sync: 60000
};

export const PLATFORM_FEATURES = [
  'document-upload',
  'pdf-processing',
  'card-generation',
  'search-functionality',
  'offline-mode',
  'data-sync',
  'push-notifications',
  'file-system-access',
  'camera-access',
  'geolocation'
];

export const SYNC_TEST_SCENARIOS = [
  'document-upload-sync',
  'card-progress-sync',
  'settings-sync',
  'offline-changes-sync',
  'conflict-resolution'
];

export const CROSS_PLATFORM_CONFIG: CrossPlatformTestSuite = {
  browsers: BROWSER_CONFIGS,
  devices: DEVICE_CONFIGS,
  testCases: [], // Will be populated by test runners
  syncTests: [], // Will be populated by sync test runner
  responsiveTests: [] // Will be populated by responsive test runner
};