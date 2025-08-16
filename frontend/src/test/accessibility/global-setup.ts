import { execSync } from 'child_process';
import { existsSync } from 'fs';
import { mkdir } from 'fs/promises';

export default async function globalSetup() {
  console.log('🚀 Setting up Accessibility & Usability Test Environment');
  
  // Create test reports directory
  const reportsDir = './test-reports/accessibility-usability';
  if (!existsSync(reportsDir)) {
    await mkdir(reportsDir, { recursive: true });
    console.log(`📁 Created reports directory: ${reportsDir}`);
  }
  
  // Check if the application is running
  const baseUrl = process.env.TEST_BASE_URL || 'http://localhost:3000';
  console.log(`🌐 Testing against: ${baseUrl}`);
  
  try {
    // Simple health check
    const response = await fetch(baseUrl);
    if (response.ok) {
      console.log('✅ Application is running and accessible');
    } else {
      console.warn(`⚠️  Application responded with status: ${response.status}`);
    }
  } catch (error) {
    console.warn('⚠️  Could not connect to application. Make sure it is running.');
    console.warn('   Start the application with: npm run dev');
    console.warn(`   Expected URL: ${baseUrl}`);
  }
  
  // Install required dependencies if not present
  try {
    // Check if puppeteer is available
    require('puppeteer');
    console.log('✅ Puppeteer is available');
  } catch (error) {
    console.log('📦 Installing Puppeteer...');
    try {
      execSync('npm install puppeteer', { stdio: 'inherit' });
      console.log('✅ Puppeteer installed successfully');
    } catch (installError) {
      console.error('❌ Failed to install Puppeteer:', installError);
    }
  }
  
  try {
    // Check if axe-core is available
    require('@axe-core/puppeteer');
    console.log('✅ Axe-core is available');
  } catch (error) {
    console.log('📦 Installing Axe-core...');
    try {
      execSync('npm install @axe-core/puppeteer', { stdio: 'inherit' });
      console.log('✅ Axe-core installed successfully');
    } catch (installError) {
      console.error('❌ Failed to install Axe-core:', installError);
    }
  }
  
  // Set environment variables for tests
  process.env.TEST_REPORTS_DIR = reportsDir;
  process.env.TEST_START_TIME = new Date().toISOString();
  
  console.log('🎯 Test environment setup complete');
  console.log('');
}