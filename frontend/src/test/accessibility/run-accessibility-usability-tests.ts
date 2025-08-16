#!/usr/bin/env node

import { AccessibilityUsabilitySuite } from './accessibility-usability-suite';
import { documentLearningAppConfig } from './test-configs/document-learning-app-config';

async function runTests() {
  console.log('🚀 Starting Accessibility & Usability Test Suite');
  console.log('================================================\n');

  const suite = new AccessibilityUsabilitySuite();
  
  try {
    const results = await suite.runFullSuite(documentLearningAppConfig);
    
    console.log('\n📊 Test Results Summary');
    console.log('========================');
    console.log(`Pages Tested: ${results.summary.totalPages}`);
    console.log(`Accessibility Score: ${results.overallScore.accessibility.toFixed(1)}/100`);
    console.log(`Usability Score: ${results.overallScore.usability.toFixed(1)}/100`);
    console.log(`Combined Score: ${results.overallScore.combined.toFixed(1)}/100`);
    
    // Detailed breakdown
    console.log('\n📋 Test Breakdown');
    console.log('==================');
    console.log(`Accessibility Tests: ${results.summary.accessibilityResults.length}`);
    console.log(`Keyboard Tests: ${results.summary.keyboardResults.length}`);
    console.log(`Screen Reader Tests: ${results.summary.screenReaderResults.length}`);
    console.log(`Color Contrast Tests: ${results.summary.colorContrastResults.length}`);
    console.log(`Usability Tests: ${results.summary.usabilityResults.length}`);
    
    // Issues summary
    const totalViolations = results.summary.accessibilityResults.reduce(
      (sum, result) => sum + result.summary.violationCount, 0
    );
    const keyboardFailures = results.summary.keyboardResults.filter(r => !r.passed).length;
    const screenReaderFailures = results.summary.screenReaderResults.filter(r => !r.passed).length;
    const colorContrastFailures = results.summary.colorContrastResults.reduce(
      (sum, report) => sum + report.summary.failed, 0
    );
    const usabilityFailures = results.summary.usabilityResults.filter(r => !r.success).length;
    
    console.log('\n🔍 Issues Found');
    console.log('================');
    console.log(`Accessibility Violations: ${totalViolations}`);
    console.log(`Keyboard Navigation Issues: ${keyboardFailures}`);
    console.log(`Screen Reader Issues: ${screenReaderFailures}`);
    console.log(`Color Contrast Failures: ${colorContrastFailures}`);
    console.log(`Usability Failures: ${usabilityFailures}`);
    
    // Recommendations
    console.log('\n💡 Recommendations');
    console.log('===================');
    
    if (results.overallScore.combined >= 90) {
      console.log('✅ Excellent! Your application has great accessibility and usability.');
    } else if (results.overallScore.combined >= 80) {
      console.log('✅ Good! Minor improvements needed for optimal accessibility and usability.');
    } else if (results.overallScore.combined >= 70) {
      console.log('⚠️  Moderate issues found. Address key accessibility and usability concerns.');
    } else {
      console.log('❌ Significant issues found. Prioritize accessibility and usability improvements.');
    }
    
    if (totalViolations > 0) {
      console.log(`- Fix ${totalViolations} accessibility violations`);
    }
    if (keyboardFailures > 0) {
      console.log(`- Improve keyboard navigation (${keyboardFailures} issues)`);
    }
    if (screenReaderFailures > 0) {
      console.log(`- Enhance screen reader compatibility (${screenReaderFailures} issues)`);
    }
    if (colorContrastFailures > 0) {
      console.log(`- Improve color contrast ratios (${colorContrastFailures} failures)`);
    }
    if (usabilityFailures > 0) {
      console.log(`- Enhance user experience flows (${usabilityFailures} failures)`);
    }
    
    console.log('\n📄 Detailed reports have been generated in: ./test-reports/accessibility-usability/');
    
    // Exit with appropriate code
    const hasSignificantIssues = results.overallScore.combined < 70 || totalViolations > 10;
    process.exit(hasSignificantIssues ? 1 : 0);
    
  } catch (error) {
    console.error('❌ Test suite failed:', error);
    process.exit(1);
  }
}

// Handle command line arguments
const args = process.argv.slice(2);
const helpFlag = args.includes('--help') || args.includes('-h');

if (helpFlag) {
  console.log(`
Accessibility & Usability Test Suite
====================================

Usage: npm run test:accessibility-usability [options]

Options:
  --help, -h     Show this help message
  
Environment Variables:
  BASE_URL       Base URL for testing (default: http://localhost:3000)
  OUTPUT_DIR     Output directory for reports (default: ./test-reports/accessibility-usability)
  
Examples:
  npm run test:accessibility-usability
  BASE_URL=http://localhost:8080 npm run test:accessibility-usability
  
The test suite will:
1. Run automated accessibility tests using axe-core
2. Test keyboard navigation functionality
3. Validate screen reader compatibility
4. Check color contrast ratios
5. Execute usability scenarios
6. Generate comprehensive reports

Reports will be saved to the output directory with detailed findings and recommendations.
`);
  process.exit(0);
}

// Override config with environment variables if provided
if (process.env.BASE_URL) {
  documentLearningAppConfig.baseUrl = process.env.BASE_URL;
}
if (process.env.OUTPUT_DIR) {
  documentLearningAppConfig.outputDir = process.env.OUTPUT_DIR;
}

// Run the tests
runTests().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});