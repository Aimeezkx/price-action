/**
 * Cross-platform compatibility testing types and interfaces
 */

export interface BrowserConfig {
  name: string;
  version?: string;
  userAgent: string;
  viewport: {
    width: number;
    height: number;
  };
  features: string[];
}

export interface DeviceConfig {
  name: string;
  type: 'mobile' | 'tablet' | 'desktop';
  os: string;
  osVersion: string;
  viewport: {
    width: number;
    height: number;
  };
  pixelRatio: number;
  touchEnabled: boolean;
}

export interface TestResult {
  testName: string;
  platform: string;
  browser?: string;
  device?: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
  screenshot?: string;
  metrics?: {
    loadTime?: number;
    renderTime?: number;
    interactionTime?: number;
  };
}

export interface SyncTestResult {
  testName: string;
  platforms: string[];
  dataConsistency: boolean;
  syncLatency: number;
  conflicts: number;
  error?: string;
}

export interface ResponsiveTestResult {
  testName: string;
  breakpoint: string;
  viewport: {
    width: number;
    height: number;
  };
  layoutValid: boolean;
  elementsVisible: boolean;
  interactionsWorking: boolean;
  error?: string;
}

export interface CrossPlatformTestSuite {
  browsers: BrowserConfig[];
  devices: DeviceConfig[];
  testCases: TestCase[];
  syncTests: SyncTestCase[];
  responsiveTests: ResponsiveTestCase[];
}

export interface TestCase {
  name: string;
  description: string;
  category: 'functionality' | 'ui' | 'performance' | 'compatibility';
  platforms: string[];
  execute: (context: TestContext) => Promise<TestResult>;
}

export interface SyncTestCase {
  name: string;
  description: string;
  platforms: string[];
  execute: (contexts: TestContext[]) => Promise<SyncTestResult>;
}

export interface ResponsiveTestCase {
  name: string;
  description: string;
  breakpoints: string[];
  execute: (context: TestContext, viewport: { width: number; height: number }) => Promise<ResponsiveTestResult>;
}

export interface TestContext {
  browser?: any; // Playwright browser instance
  page?: any; // Playwright page instance
  device?: DeviceConfig;
  platform: string;
  baseUrl: string;
}

export interface PlatformFeature {
  name: string;
  platforms: string[];
  testFunction: (context: TestContext) => Promise<boolean>;
  fallbackBehavior?: string;
}