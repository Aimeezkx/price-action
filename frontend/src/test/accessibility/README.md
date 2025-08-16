# Accessibility & Usability Testing Framework

This comprehensive testing framework validates the accessibility and usability of the Document Learning Application. It includes automated testing for WCAG compliance, keyboard navigation, screen reader compatibility, color contrast, and user experience scenarios.

## Features

### 🔍 Automated Accessibility Testing
- **axe-core integration** for WCAG 2.1 AA/AAA compliance
- **Violation detection** with severity levels (critical, serious, moderate, minor)
- **Comprehensive coverage** of all application pages
- **Detailed reporting** with remediation suggestions

### ⌨️ Keyboard Navigation Testing
- **Tab order validation** for logical navigation flow
- **Focus management** testing for modals and dynamic content
- **Keyboard shortcuts** and interaction testing
- **Skip links** and accessibility shortcuts validation

### 🔊 Screen Reader Compatibility
- **ARIA attributes** validation (labels, roles, properties)
- **Semantic HTML** structure verification
- **Accessible names** for interactive elements
- **Live regions** and dynamic content announcements

### 🎨 Color Contrast Validation
- **WCAG AA/AAA** contrast ratio compliance
- **Automated color detection** from rendered elements
- **Text size consideration** for contrast requirements
- **Background color inheritance** handling

### 👤 Usability Testing
- **User scenario simulation** with realistic workflows
- **Performance measurement** for interaction responsiveness
- **Error handling** validation for edge cases
- **User experience scoring** based on completion and efficiency

## Quick Start

### Prerequisites

```bash
# Install dependencies
npm install

# Ensure the application is running
npm run dev  # Should be accessible at http://localhost:3000
```

### Running Tests

```bash
# Run all accessibility and usability tests
npm run test:accessibility-usability

# Run only accessibility tests
npm run test:accessibility

# Run only usability tests
npm run test:usability

# Run comprehensive test suite with reports
npm run test:accessibility-full

# Run tests in watch mode during development
npm run test:accessibility-usability:watch

# Run tests for CI/CD pipeline
npm run test:accessibility-usability:ci
```

### Viewing Reports

```bash
# Generate and open comprehensive report
npm run test:accessibility-report

# Reports are saved to:
./test-reports/accessibility-usability/
```

## Test Configuration

### Environment Variables

```bash
# Base URL for testing (default: http://localhost:3000)
TEST_BASE_URL=http://localhost:8080

# Output directory for reports
OUTPUT_DIR=./custom-reports

# Test execution options
TEST_HEADLESS=false          # Run with visible browser
TEST_SLOW_MO=100            # Slow down interactions (ms)
TEST_DEVTOOLS=true          # Open browser devtools
VERBOSE_TESTS=true          # Enable verbose logging
```

### Custom Configuration

Edit `frontend/src/test/accessibility/test-configs/document-learning-app-config.ts` to customize:

- Pages to test
- Accessibility rules and exclusions
- Keyboard navigation scenarios
- Screen reader test cases
- Color contrast requirements
- Usability scenarios

## Test Structure

```
src/test/accessibility/
├── accessibility-test-runner.ts      # Axe-core integration
├── keyboard-navigation-tester.ts     # Keyboard testing
├── screen-reader-tester.ts          # Screen reader testing
├── color-contrast-validator.ts      # Color contrast validation
├── accessibility-usability-suite.ts # Main test orchestrator
├── run-accessibility-usability-tests.ts # CLI runner
├── test-configs/
│   └── document-learning-app-config.ts # Test configuration
├── __tests__/
│   └── accessibility.test.ts        # Jest test cases
└── usability/
    ├── usability-test-framework.ts   # Usability testing
    └── __tests__/
        └── usability.test.ts         # Usability test cases
```

## Writing Custom Tests

### Adding Accessibility Tests

```typescript
// In accessibility.test.ts
test('Custom page should be accessible', async () => {
  const result = await accessibilityRunner.runAccessibilityTest({
    url: `${baseUrl}/custom-page`,
    tags: ['wcag2a', 'wcag2aa'],
    excludeSelectors: ['.loading-spinner']
  });

  expect(result).toHaveNoAccessibilityViolations();
});
```

### Adding Keyboard Navigation Tests

```typescript
// Custom keyboard scenario
const keyboardScenario = {
  name: 'Custom Navigation',
  description: 'Test custom keyboard interaction',
  keySequence: [
    { type: 'tab', repeat: 3 },
    { type: 'enter' },
    { type: 'arrow', direction: 'down' }
  ],
  expectedOutcome: {
    focusedElement: '[data-testid="target-element"]'
  }
};
```

### Adding Usability Tests

```typescript
// Custom usability scenario
const usabilityScenario = {
  name: 'Custom User Flow',
  description: 'Test custom user workflow',
  userGoal: 'Complete specific task',
  steps: [
    {
      action: 'click',
      target: '[data-testid="start-button"]',
      description: 'Start the workflow'
    },
    {
      action: 'type',
      target: '[data-testid="input-field"]',
      value: 'test input',
      description: 'Enter test data'
    }
  ],
  successCriteria: {
    requiredElements: ['[data-testid="success-message"]'],
    performanceThresholds: {
      maxInteractionTime: 2000
    }
  },
  difficulty: 'medium'
};
```

## Best Practices

### For Developers

1. **Test Early and Often**
   - Run accessibility tests during development
   - Use watch mode for immediate feedback
   - Fix violations as they're introduced

2. **Semantic HTML**
   - Use proper heading hierarchy (h1, h2, h3...)
   - Include alt text for images
   - Use semantic elements (nav, main, article, etc.)

3. **ARIA Attributes**
   - Add aria-label for buttons without text
   - Use aria-describedby for additional context
   - Implement aria-live for dynamic content

4. **Keyboard Navigation**
   - Ensure all interactive elements are focusable
   - Implement logical tab order
   - Provide keyboard shortcuts for complex interactions

5. **Color and Contrast**
   - Don't rely solely on color to convey information
   - Ensure sufficient contrast ratios
   - Test with color blindness simulators

### For Testing

1. **Comprehensive Coverage**
   - Test all user-facing pages
   - Include different user states (logged in/out)
   - Test error states and edge cases

2. **Real User Scenarios**
   - Base tests on actual user workflows
   - Include both novice and expert user paths
   - Test with assistive technologies

3. **Performance Considerations**
   - Set realistic performance thresholds
   - Test on different devices and network conditions
   - Monitor interaction responsiveness

## Troubleshooting

### Common Issues

**Tests failing with timeout errors:**
```bash
# Increase timeout in jest.setup.ts
jest.setTimeout(120000);

# Or set environment variable
TEST_TIMEOUT=120000 npm run test:accessibility
```

**Puppeteer installation issues:**
```bash
# Install Puppeteer manually
npm install puppeteer

# Or use system Chrome
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm install puppeteer
```

**Application not accessible:**
```bash
# Ensure application is running
npm run dev

# Check correct port
TEST_BASE_URL=http://localhost:3001 npm run test:accessibility
```

**Memory issues with large test suites:**
```bash
# Reduce parallel workers
NODE_OPTIONS="--max-old-space-size=4096" npm run test:accessibility

# Run tests sequentially
npm run test:accessibility -- --runInBand
```

### Debugging Tests

1. **Enable Visual Mode**
   ```bash
   TEST_HEADLESS=false npm run test:accessibility
   ```

2. **Slow Down Interactions**
   ```bash
   TEST_SLOW_MO=500 npm run test:accessibility
   ```

3. **Enable DevTools**
   ```bash
   TEST_DEVTOOLS=true npm run test:accessibility
   ```

4. **Verbose Logging**
   ```bash
   VERBOSE_TESTS=true npm run test:accessibility
   ```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Accessibility Tests
on: [push, pull_request]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Start application
        run: npm run dev &
        
      - name: Wait for application
        run: npx wait-on http://localhost:3000
      
      - name: Run accessibility tests
        run: npm run test:accessibility-usability:ci
      
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: accessibility-reports
          path: test-reports/accessibility-usability/
```

## Contributing

1. **Adding New Test Types**
   - Create new tester class following existing patterns
   - Add configuration options to test config
   - Include Jest integration tests
   - Update documentation

2. **Improving Existing Tests**
   - Add more comprehensive scenarios
   - Improve error messages and suggestions
   - Optimize performance and reliability
   - Enhance reporting capabilities

3. **Bug Reports**
   - Include test configuration used
   - Provide browser and environment details
   - Include relevant log output
   - Describe expected vs actual behavior

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [Keyboard Navigation Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)
- [Color Contrast Guidelines](https://webaim.org/articles/contrast/)
- [Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)

## License

This testing framework is part of the Document Learning Application and follows the same license terms.