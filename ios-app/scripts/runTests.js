#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function runCommand(command, description) {
  log(`\n${colors.blue}Running: ${description}${colors.reset}`);
  log(`${colors.cyan}Command: ${command}${colors.reset}`);
  
  try {
    const output = execSync(command, { 
      stdio: 'inherit',
      cwd: process.cwd(),
    });
    log(`${colors.green}✓ ${description} completed successfully${colors.reset}`);
    return true;
  } catch (error) {
    log(`${colors.red}✗ ${description} failed${colors.reset}`);
    log(`${colors.red}Error: ${error.message}${colors.reset}`);
    return false;
  }
}

function checkTestFiles() {
  const testDirs = [
    'src/components/__tests__',
    'src/services/__tests__',
    'src/hooks/__tests__',
    'src/__tests__/performance',
    'src/__tests__/integration',
    'e2e',
  ];

  log(`\n${colors.magenta}Checking test file structure...${colors.reset}`);
  
  let totalTests = 0;
  testDirs.forEach(dir => {
    const fullPath = path.join(process.cwd(), dir);
    if (fs.existsSync(fullPath)) {
      const files = fs.readdirSync(fullPath).filter(file => 
        file.endsWith('.test.ts') || 
        file.endsWith('.test.tsx') || 
        file.endsWith('.test.js')
      );
      log(`${colors.cyan}${dir}: ${files.length} test files${colors.reset}`);
      totalTests += files.length;
    } else {
      log(`${colors.yellow}${dir}: Directory not found${colors.reset}`);
    }
  });
  
  log(`${colors.bright}Total test files: ${totalTests}${colors.reset}`);
  return totalTests > 0;
}

function generateTestReport() {
  const reportPath = path.join(process.cwd(), 'test-results');
  if (!fs.existsSync(reportPath)) {
    fs.mkdirSync(reportPath, { recursive: true });
  }
  
  log(`\n${colors.magenta}Test reports will be generated in: ${reportPath}${colors.reset}`);
}

async function main() {
  log(`${colors.bright}${colors.blue}iOS App Testing Suite${colors.reset}`);
  log(`${colors.cyan}Starting comprehensive test execution...${colors.reset}`);
  
  // Check test file structure
  if (!checkTestFiles()) {
    log(`${colors.red}No test files found. Please create tests first.${colors.reset}`);
    process.exit(1);
  }
  
  // Generate test report directory
  generateTestReport();
  
  const testSuites = [
    {
      name: 'Unit Tests',
      command: 'npm run test -- --testPathPattern="(components|services|hooks)/__tests__" --coverage --coverageDirectory=test-results/unit-coverage',
      required: true,
    },
    {
      name: 'Integration Tests',
      command: 'npm run test -- --testPathPattern="__tests__/integration" --coverage --coverageDirectory=test-results/integration-coverage',
      required: true,
    },
    {
      name: 'Performance Tests',
      command: 'npm run test:performance',
      required: false,
    },
    {
      name: 'E2E Tests (Build)',
      command: 'npm run test:e2e:build',
      required: false,
    },
    {
      name: 'E2E Tests (Run)',
      command: 'npm run test:e2e',
      required: false,
    },
    {
      name: 'Lint Check',
      command: 'npm run lint',
      required: true,
    },
  ];
  
  let passedTests = 0;
  let failedTests = 0;
  const results = [];
  
  for (const suite of testSuites) {
    const success = runCommand(suite.command, suite.name);
    results.push({
      name: suite.name,
      success,
      required: suite.required,
    });
    
    if (success) {
      passedTests++;
    } else {
      failedTests++;
      if (suite.required) {
        log(`${colors.red}Required test suite failed: ${suite.name}${colors.reset}`);
      }
    }
  }
  
  // Print summary
  log(`\n${colors.bright}${colors.blue}Test Execution Summary${colors.reset}`);
  log(`${colors.cyan}${'='.repeat(50)}${colors.reset}`);
  
  results.forEach(result => {
    const status = result.success ? 
      `${colors.green}✓ PASSED${colors.reset}` : 
      `${colors.red}✗ FAILED${colors.reset}`;
    const required = result.required ? 
      `${colors.yellow}(Required)${colors.reset}` : 
      `${colors.cyan}(Optional)${colors.reset}`;
    
    log(`${result.name}: ${status} ${required}`);
  });
  
  log(`\n${colors.bright}Total: ${passedTests} passed, ${failedTests} failed${colors.reset}`);
  
  // Check if all required tests passed
  const requiredFailed = results.filter(r => r.required && !r.success).length;
  
  if (requiredFailed > 0) {
    log(`${colors.red}${colors.bright}❌ ${requiredFailed} required test suite(s) failed${colors.reset}`);
    log(`${colors.red}Please fix the failing tests before proceeding.${colors.reset}`);
    process.exit(1);
  } else {
    log(`${colors.green}${colors.bright}✅ All required tests passed!${colors.reset}`);
    
    if (failedTests > 0) {
      log(`${colors.yellow}Note: ${failedTests} optional test suite(s) failed${colors.reset}`);
    }
    
    log(`${colors.green}iOS testing and quality assurance setup is complete.${colors.reset}`);
    process.exit(0);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  log(`\n${colors.yellow}Test execution interrupted by user${colors.reset}`);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  log(`${colors.red}Uncaught exception: ${error.message}${colors.reset}`);
  process.exit(1);
});

main().catch(error => {
  log(`${colors.red}Test runner failed: ${error.message}${colors.reset}`);
  process.exit(1);
});