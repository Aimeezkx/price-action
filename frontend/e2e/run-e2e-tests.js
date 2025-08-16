#!/usr/bin/env node

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

/**
 * Comprehensive E2E Test Runner
 * Runs all end-to-end tests with proper setup and reporting
 */

const TEST_SUITES = {
  'complete-workflows': {
    file: 'complete-user-workflows.spec.ts',
    description: 'Complete user workflow tests',
    timeout: 300000 // 5 minutes
  },
  'cross-browser': {
    file: 'cross-browser-compatibility.spec.ts',
    description: 'Cross-browser compatibility tests',
    timeout: 600000 // 10 minutes
  },
  'mobile': {
    file: 'mobile-responsiveness.spec.ts',
    description: 'Mobile responsiveness tests',
    timeout: 300000 // 5 minutes
  },
  'accessibility': {
    file: 'accessibility-testing.spec.ts',
    description: 'Accessibility compliance tests',
    timeout: 240000 // 4 minutes
  },
  'performance': {
    file: 'performance-validation.spec.ts',
    description: 'Performance validation tests',
    timeout: 300000 // 5 minutes
  },
  'error-handling': {
    file: 'error-handling.spec.ts',
    description: 'Error handling and recovery tests',
    timeout: 240000 // 4 minutes
  }
}

function printUsage() {
  console.log(`
Usage: node run-e2e-tests.js [options] [test-suite]

Test Suites:
${Object.entries(TEST_SUITES).map(([key, suite]) => 
  `  ${key.padEnd(20)} - ${suite.description}`
).join('\n')}

Options:
  --all                 Run all test suites
  --browser <name>      Run tests on specific browser (chromium, firefox, webkit)
  --headed              Run tests in headed mode (visible browser)
  --debug               Run tests in debug mode
  --report              Generate detailed HTML report
  --parallel            Run tests in parallel (default: sequential)
  --help                Show this help message

Examples:
  node run-e2e-tests.js --all
  node run-e2e-tests.js complete-workflows --browser chromium --headed
  node run-e2e-tests.js accessibility --debug
  node run-e2e-tests.js cross-browser --report
`)
}

function parseArgs() {
  const args = process.argv.slice(2)
  const options = {
    all: false,
    browser: null,
    headed: false,
    debug: false,
    report: false,
    parallel: false,
    testSuite: null
  }

  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    
    switch (arg) {
      case '--all':
        options.all = true
        break
      case '--browser':
        options.browser = args[++i]
        break
      case '--headed':
        options.headed = true
        break
      case '--debug':
        options.debug = true
        break
      case '--report':
        options.report = true
        break
      case '--parallel':
        options.parallel = true
        break
      case '--help':
        printUsage()
        process.exit(0)
        break
      default:
        if (!arg.startsWith('--') && !options.testSuite) {
          options.testSuite = arg
        }
        break
    }
  }

  return options
}

function validateOptions(options) {
  if (!options.all && !options.testSuite) {
    console.error('Error: Must specify either --all or a specific test suite')
    printUsage()
    process.exit(1)
  }

  if (options.testSuite && !TEST_SUITES[options.testSuite]) {
    console.error(`Error: Unknown test suite "${options.testSuite}"`)
    console.error(`Available suites: ${Object.keys(TEST_SUITES).join(', ')}`)
    process.exit(1)
  }

  if (options.browser && !['chromium', 'firefox', 'webkit'].includes(options.browser)) {
    console.error('Error: Browser must be one of: chromium, firefox, webkit')
    process.exit(1)
  }
}

function setupTestEnvironment() {
  console.log('🔧 Setting up test environment...')
  
  // Ensure test-results directory exists
  const testResultsDir = path.join(__dirname, '..', 'test-results')
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true })
  }

  // Ensure test-data directory exists
  const testDataDir = path.join(__dirname, 'test-data')
  if (!fs.existsSync(testDataDir)) {
    fs.mkdirSync(testDataDir, { recursive: true })
    console.log('⚠️  Test data directory created. Please add test files as described in test-data/README.md')
  }

  // Check if backend is running
  try {
    execSync('curl -f http://localhost:8000/health', { stdio: 'ignore' })
    console.log('✅ Backend server is running')
  } catch (error) {
    console.log('⚠️  Backend server not detected. Make sure it\'s running on port 8000')
  }

  // Check if frontend is running
  try {
    execSync('curl -f http://localhost:3000', { stdio: 'ignore' })
    console.log('✅ Frontend server is running')
  } catch (error) {
    console.log('⚠️  Frontend server not detected. Make sure it\'s running on port 3000')
  }
}

function buildPlaywrightCommand(testFile, options) {
  const cmd = ['npx', 'playwright', 'test']
  
  // Add test file
  cmd.push(`e2e/${testFile}`)
  
  // Add browser selection
  if (options.browser) {
    cmd.push('--project', options.browser)
  }
  
  // Add headed mode
  if (options.headed) {
    cmd.push('--headed')
  }
  
  // Add debug mode
  if (options.debug) {
    cmd.push('--debug')
  }
  
  // Add reporter options
  if (options.report) {
    cmd.push('--reporter=html,json,junit')
  } else {
    cmd.push('--reporter=list')
  }
  
  // Add parallel execution
  if (options.parallel) {
    cmd.push('--workers=4')
  } else {
    cmd.push('--workers=1')
  }
  
  return cmd.join(' ')
}

function runTestSuite(suiteName, suite, options) {
  console.log(`\n🧪 Running ${suite.description}...`)
  console.log(`📁 Test file: ${suite.file}`)
  
  const command = buildPlaywrightCommand(suite.file, options)
  console.log(`🔧 Command: ${command}`)
  
  const startTime = Date.now()
  
  try {
    execSync(command, { 
      stdio: 'inherit',
      timeout: suite.timeout,
      cwd: path.join(__dirname, '..')
    })
    
    const duration = ((Date.now() - startTime) / 1000).toFixed(2)
    console.log(`✅ ${suite.description} completed successfully in ${duration}s`)
    
    return { success: true, duration: parseFloat(duration) }
  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2)
    console.log(`❌ ${suite.description} failed after ${duration}s`)
    console.log(`Error: ${error.message}`)
    
    return { success: false, duration: parseFloat(duration), error: error.message }
  }
}

function generateSummaryReport(results) {
  console.log('\n📊 Test Execution Summary')
  console.log('=' .repeat(50))
  
  let totalTests = 0
  let passedTests = 0
  let totalDuration = 0
  
  for (const [suiteName, result] of Object.entries(results)) {
    const status = result.success ? '✅ PASS' : '❌ FAIL'
    const duration = result.duration.toFixed(2)
    
    console.log(`${status} ${suiteName.padEnd(20)} ${duration}s`)
    
    totalTests++
    if (result.success) passedTests++
    totalDuration += result.duration
  }
  
  console.log('=' .repeat(50))
  console.log(`Total: ${totalTests} suites, ${passedTests} passed, ${totalTests - passedTests} failed`)
  console.log(`Total duration: ${totalDuration.toFixed(2)}s`)
  
  if (passedTests === totalTests) {
    console.log('\n🎉 All test suites passed!')
    return true
  } else {
    console.log('\n💥 Some test suites failed!')
    return false
  }
}

function main() {
  const options = parseArgs()
  validateOptions(options)
  
  console.log('🚀 Starting E2E Test Execution')
  console.log(`Options: ${JSON.stringify(options, null, 2)}`)
  
  setupTestEnvironment()
  
  const suitesToRun = options.all 
    ? Object.keys(TEST_SUITES)
    : [options.testSuite]
  
  console.log(`\n📋 Test suites to run: ${suitesToRun.join(', ')}`)
  
  const results = {}
  const startTime = Date.now()
  
  for (const suiteName of suitesToRun) {
    const suite = TEST_SUITES[suiteName]
    results[suiteName] = runTestSuite(suiteName, suite, options)
    
    // Add delay between test suites to allow cleanup
    if (suitesToRun.length > 1) {
      console.log('⏳ Waiting 5 seconds before next suite...')
      execSync('sleep 5')
    }
  }
  
  const totalDuration = ((Date.now() - startTime) / 1000).toFixed(2)
  console.log(`\n⏱️  Total execution time: ${totalDuration}s`)
  
  const allPassed = generateSummaryReport(results)
  
  // Generate detailed report if requested
  if (options.report) {
    console.log('\n📄 Generating detailed HTML report...')
    try {
      execSync('npx playwright show-report', { stdio: 'inherit' })
    } catch (error) {
      console.log('⚠️  Could not open HTML report automatically')
      console.log('   Run "npx playwright show-report" to view the report')
    }
  }
  
  process.exit(allPassed ? 0 : 1)
}

if (require.main === module) {
  main()
}