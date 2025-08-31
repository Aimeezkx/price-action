#!/usr/bin/env node

/**
 * Simple unit test runner script to capture vitest output
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Create output directory if it doesn't exist
const outputDir = path.join(__dirname, 'test-results');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

console.log('🚀 Running frontend unit tests...');

// Run vitest with verbose output
const vitestProcess = spawn('npx', ['vitest', 'run', '--reporter=verbose'], {
  stdio: ['pipe', 'pipe', 'pipe'],
  cwd: __dirname
});

let output = '';
let errorOutput = '';

vitestProcess.stdout.on('data', (data) => {
  const text = data.toString();
  output += text;
  console.log(text);
});

vitestProcess.stderr.on('data', (data) => {
  const text = data.toString();
  errorOutput += text;
  console.error(text);
});

vitestProcess.on('close', (code) => {
  console.log(`\nTest process exited with code ${code}`);
  
  // Save output to files
  const timestamp = new Date().toISOString().replace(/:/g, '-');
  const outputFile = path.join(outputDir, `unit-test-output-${timestamp}.txt`);
  const errorFile = path.join(outputDir, `unit-test-errors-${timestamp}.txt`);
  
  fs.writeFileSync(outputFile, output);
  if (errorOutput) {
    fs.writeFileSync(errorFile, errorOutput);
  }
  
  console.log(`📄 Output saved to: ${outputFile}`);
  if (errorOutput) {
    console.log(`📄 Errors saved to: ${errorFile}`);
  }
  
  // Analyze output for pass/fail counts
  const passMatch = output.match(/(\d+)\s+passed/);
  const failMatch = output.match(/(\d+)\s+failed/);
  const totalMatch = output.match(/Test Files\s+\d+\s+passed.*?(\d+)/);
  
  if (passMatch || failMatch) {
    const passed = passMatch ? parseInt(passMatch[1]) : 0;
    const failed = failMatch ? parseInt(failMatch[1]) : 0;
    const total = passed + failed;
    const percentage = total > 0 ? ((passed / total) * 100).toFixed(1) : '0.0';
    
    console.log('\n📊 Test Summary:');
    console.log(`   Passed: ${passed}`);
    console.log(`   Failed: ${failed}`);
    console.log(`   Total: ${total}`);
    console.log(`   Pass Rate: ${percentage}%`);
  }
  
  process.exit(code);
});

vitestProcess.on('error', (err) => {
  console.error('Failed to start vitest:', err);
  process.exit(1);
});