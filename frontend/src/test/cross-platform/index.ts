/**
 * Cross-Platform Compatibility Testing
 * Main exports for cross-platform testing framework
 */

// Main test runner
export { CrossPlatformTestRunner } from './cross-platform-test-runner';

// Individual test components
export { BrowserCompatibilityTester } from './browser-compatibility-tester';
export { IOSDeviceSimulator } from './ios-device-simulator';
export { DataSyncTester } from './data-sync-tester';
export { ResponsiveDesignValidator } from './responsive-design-validator';
export { PlatformFeatureTester } from './platform-feature-tester';

// Configuration
export { defaultConfig, loadConfig } from './cross-platform.config';
export type { 
  CrossPlatformConfig,
  BrowserConfig,
  DeviceConfig,
  ScreenSize,
  FeatureConfig,
  ReportingConfig
} from './cross-platform.config';

// Types
export type {
  TestResults,
  BrowserTestResult,
  DeviceTestResult,
  SyncTestResult,
  ResponsiveTestResult,
  PlatformFeatureTestResult,
  TestError,
  FeatureTestResult,
  PerformanceMetrics,
  LayoutIssue,
  TestScenario,
  TestStep
} from './types';

// CLI runner
export { runCrossPlatformTests } from './run-cross-platform-tests';