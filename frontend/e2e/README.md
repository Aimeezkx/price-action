# End-to-End Testing Suite

This directory contains a comprehensive end-to-end testing suite for the Document Learning Application. The tests validate complete user workflows, cross-browser compatibility, mobile responsiveness, accessibility compliance, performance requirements, and error handling scenarios.

## Test Structure

### Test Suites

1. **Complete User Workflows** (`complete-user-workflows.spec.ts`)
   - Document upload to card review workflow
   - Multi-format document processing
   - Search and discovery workflows
   - Chapter browsing and navigation
   - Study sessions with different card types
   - Export and data management
   - Error recovery scenarios
   - Performance requirements validation

2. **Cross-Browser Compatibility** (`cross-browser-compatibility.spec.ts`)
   - Core functionality across Chrome, Firefox, Safari
   - Browser-specific feature testing
   - JavaScript API compatibility
   - CSS rendering consistency
   - Mobile browser compatibility
   - Feature detection and polyfills

3. **Mobile Responsiveness** (`mobile-responsiveness.spec.ts`)
   - Multiple device configurations (iPhone, iPad, Android)
   - Touch interactions and gestures
   - Responsive breakpoints
   - Orientation changes
   - Mobile-specific accessibility
   - Performance on mobile devices

4. **Accessibility Testing** (`accessibility-testing.spec.ts`)
   - WCAG 2.1 AA compliance
   - Screen reader support
   - Keyboard navigation
   - Color contrast validation
   - Focus management
   - Alternative text for images
   - Dynamic content accessibility

5. **Performance Validation** (`performance-validation.spec.ts`)
   - Page load time requirements
   - Document processing performance
   - Search response times
   - Card interaction responsiveness
   - Memory usage monitoring
   - Concurrent user simulation

6. **Error Handling** (`error-handling.spec.ts`)
   - Network failure recovery
   - File upload error scenarios
   - Processing failure handling
   - Browser compatibility issues
   - Data integrity problems
   - Graceful degradation

### Utilities

- **Test Helpers** (`utils/test-helpers.ts`)
  - Common test operations
  - Document upload utilities
  - Study session helpers
  - Search functionality
  - Accessibility testing tools
  - Performance measurement
  - Cross-browser utilities

## Running Tests

### Prerequisites

1. **Backend Server**: Ensure the backend is running on `http://localhost:8000`
2. **Frontend Server**: Ensure the frontend is running on `http://localhost:3000`
3. **Test Data**: Create test files in the `test-data/` directory (see test-data/README.md)

### Command Line Options

#### Run All Tests
```bash
npm run test:e2e:all
```

#### Run Specific Test Suites
```bash
npm run test:e2e:workflows      # Complete user workflows
npm run test:e2e:cross-browser  # Cross-browser compatibility
npm run test:e2e:mobile         # Mobile responsiveness
npm run test:e2e:accessibility  # Accessibility compliance
npm run test:e2e:performance    # Performance validation
npm run test:e2e:errors         # Error handling
```

#### Browser-Specific Testing
```bash
npm run test:e2e:chrome         # Chrome only
npm run test:e2e:firefox        # Firefox only
npm run test:e2e:safari         # Safari only
```

#### Development and Debugging
```bash
npm run test:e2e:headed         # Run with visible browser
npm run test:e2e:debug          # Debug mode with breakpoints
npm run test:e2e:report         # Generate detailed HTML report
```

### Advanced Usage

#### Custom Test Runner
```bash
node e2e/run-e2e-tests.js [options] [test-suite]

Options:
  --all                 Run all test suites
  --browser <name>      Run tests on specific browser
  --headed              Run tests in headed mode
  --debug               Run tests in debug mode
  --report              Generate detailed HTML report
  --parallel            Run tests in parallel
```

#### Examples
```bash
# Run accessibility tests in Chrome with visible browser
node e2e/run-e2e-tests.js accessibility --browser chromium --headed

# Run all tests with detailed reporting
node e2e/run-e2e-tests.js --all --report

# Debug complete workflows
node e2e/run-e2e-tests.js complete-workflows --debug --headed
```

## Test Data Requirements

### Required Test Files

Create these files in the `test-data/` directory:

#### PDF Files
- `sample.pdf` - Small PDF (5 pages) with searchable text
- `medium.pdf` - Medium PDF (20 pages) for performance testing
- `large.pdf` - Large PDF (50+ pages) for stress testing
- `multi-chapter.pdf` - PDF with clear chapter structure
- `with-images.pdf` - PDF containing images and figures
- `with-charts.pdf` - PDF with charts and diagrams
- `comprehensive.pdf` - PDF that generates various card types
- `hotspot-images.pdf` - PDF with images suitable for hotspot testing

#### Other Formats
- `document.docx` - Word document
- `notes.md` - Markdown file

#### Test Files for Error Scenarios
- `invalid.txt` - Text file (unsupported format)
- `corrupted.pdf` - Corrupted PDF file
- `oversized.pdf` - File exceeding size limits
- `malicious.exe` - Executable file for security testing

### Content Guidelines

Test files should contain:
- Searchable text with terms like "machine learning", "algorithm", "AI"
- Clear chapter/section structure for navigation testing
- Various content types (text, images, formulas, tables)
- Different complexity levels for card generation testing

## Configuration

### Playwright Configuration

The test suite uses a comprehensive Playwright configuration (`playwright.config.ts`) with:

- **Multiple browsers**: Chrome, Firefox, Safari
- **Device emulation**: iPhone, iPad, Android devices
- **Timeouts**: Extended timeouts for document processing
- **Reporters**: HTML, JSON, JUnit, Allure
- **Screenshots/Videos**: Captured on failure
- **Parallel execution**: Configurable worker count

### Environment Variables

- `CI=true` - Enables CI-specific settings
- `PLAYWRIGHT_BROWSERS_PATH` - Custom browser installation path
- `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` - Skip browser download

## Continuous Integration

### GitHub Actions Workflow

The E2E tests run automatically on:
- Push to main/develop branches
- Pull requests
- Nightly schedule (2 AM UTC)
- Manual workflow dispatch

### Test Matrix

- **Operating Systems**: Ubuntu, Windows, macOS
- **Browsers**: Chrome, Firefox, Safari (where available)
- **Devices**: Desktop, tablet, mobile
- **Test Suites**: All 6 test suites run in parallel

### Artifacts

The CI pipeline generates:
- HTML test reports
- Screenshots of failed tests
- Video recordings of failures
- Accessibility audit reports
- Performance metrics
- Cross-browser compatibility results

## Debugging Failed Tests

### Local Debugging

1. **Run in headed mode**:
   ```bash
   npm run test:e2e:debug
   ```

2. **Use Playwright Inspector**:
   ```bash
   npx playwright test --debug
   ```

3. **Generate trace files**:
   ```bash
   npx playwright test --trace on
   ```

### CI Debugging

1. **Download artifacts** from the GitHub Actions run
2. **View HTML reports** for detailed test results
3. **Check screenshots/videos** for visual debugging
4. **Review console logs** in the test output

### Common Issues

#### Test Data Missing
- Ensure all required test files exist in `test-data/`
- Check file permissions and content

#### Server Not Running
- Verify backend is accessible at `http://localhost:8000/health`
- Verify frontend is accessible at `http://localhost:3000`

#### Timing Issues
- Increase timeouts in `playwright.config.ts`
- Add explicit waits for dynamic content
- Use `page.waitForLoadState('networkidle')`

#### Browser-Specific Issues
- Test in isolation with single browser
- Check browser console for JavaScript errors
- Verify CSS compatibility

## Performance Benchmarks

### Target Metrics

- **Page Load Time**: < 2 seconds
- **Document Processing**: < 30 seconds for 10-page PDF
- **Search Response**: < 500ms
- **Card Interactions**: < 200ms
- **Memory Usage**: < 100MB increase during intensive operations

### Monitoring

The performance tests automatically:
- Measure and validate response times
- Monitor memory usage
- Test concurrent user scenarios
- Validate under network throttling
- Check resource cleanup

## Accessibility Standards

### WCAG 2.1 AA Compliance

The accessibility tests verify:
- **Perceivable**: Alt text, color contrast, text scaling
- **Operable**: Keyboard navigation, focus management
- **Understandable**: Clear labels, error messages
- **Robust**: Screen reader compatibility, semantic markup

### Testing Tools

- **axe-core**: Automated accessibility testing
- **Playwright accessibility**: Built-in accessibility features
- **Manual testing**: Keyboard navigation, screen reader simulation

## Contributing

### Adding New Tests

1. **Create test file** in appropriate category
2. **Use test helpers** for common operations
3. **Follow naming conventions**: `feature-name.spec.ts`
4. **Add to test runner** if creating new suite
5. **Update documentation**

### Test Writing Guidelines

1. **Use descriptive test names**
2. **Group related tests** with `test.describe()`
3. **Clean up after tests** with `test.afterEach()`
4. **Use data-testid attributes** for reliable selectors
5. **Add appropriate timeouts** for async operations
6. **Validate both success and error scenarios**

### Code Review Checklist

- [ ] Tests cover happy path and edge cases
- [ ] Appropriate assertions and error handling
- [ ] Clean up resources after tests
- [ ] Cross-browser compatibility considered
- [ ] Accessibility requirements validated
- [ ] Performance implications assessed
- [ ] Documentation updated

## Troubleshooting

### Common Error Messages

#### "Target page, context or browser has been closed"
- Increase test timeout
- Check for memory leaks
- Ensure proper cleanup in `afterEach`

#### "Timeout exceeded while waiting for element"
- Verify element selector
- Check if element is dynamically loaded
- Add explicit waits

#### "Navigation timeout exceeded"
- Increase navigation timeout
- Check network connectivity
- Verify server is running

#### "Browser not found"
- Run `npx playwright install`
- Check browser installation path
- Verify system dependencies

### Getting Help

1. **Check existing issues** in the repository
2. **Review Playwright documentation**
3. **Run tests locally** to reproduce issues
4. **Create detailed bug reports** with:
   - Test command used
   - Error messages
   - Screenshots/videos
   - Environment details

## Maintenance

### Regular Tasks

- **Update test data** as application evolves
- **Review performance benchmarks** quarterly
- **Update browser versions** monthly
- **Audit accessibility compliance** with each release
- **Clean up old test artifacts** regularly

### Monitoring

- **Track test execution times** for performance regression
- **Monitor flaky tests** and improve stability
- **Review test coverage** and add missing scenarios
- **Update dependencies** regularly for security

This comprehensive E2E testing suite ensures the Document Learning Application meets all functional, performance, accessibility, and compatibility requirements across different platforms and user scenarios.