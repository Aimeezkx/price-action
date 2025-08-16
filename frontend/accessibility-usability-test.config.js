module.exports = {
  // Test environment configuration
  testEnvironment: 'node',
  
  // Test patterns
  testMatch: [
    '<rootDir>/src/test/accessibility/__tests__/**/*.test.ts',
    '<rootDir>/src/test/usability/__tests__/**/*.test.ts'
  ],
  
  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/src/test/accessibility/jest.setup.ts'
  ],
  
  // Transform configuration
  transform: {
    '^.+\\.tsx?$': 'ts-jest'
  },
  
  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/test/accessibility/**/*.ts',
    'src/test/usability/**/*.ts',
    '!src/test/**/__tests__/**',
    '!src/test/**/test-configs/**'
  ],
  
  // Test timeout (accessibility tests can take longer)
  testTimeout: 60000,
  
  // Global setup and teardown
  globalSetup: '<rootDir>/src/test/accessibility/global-setup.ts',
  globalTeardown: '<rootDir>/src/test/accessibility/global-teardown.ts',
  
  // Environment variables
  testEnvironmentOptions: {
    url: 'http://localhost:3000'
  },
  
  // Reporters
  reporters: [
    'default',
    [
      'jest-html-reporters',
      {
        publicPath: './test-reports/accessibility-usability',
        filename: 'jest-report.html',
        expand: true,
        hideIcon: false,
        pageTitle: 'Accessibility & Usability Test Report'
      }
    ]
  ],
  
  // Verbose output
  verbose: true,
  
  // Bail on first failure for CI
  bail: process.env.CI ? 1 : 0,
  
  // Max workers for parallel execution
  maxWorkers: process.env.CI ? 2 : '50%'
};