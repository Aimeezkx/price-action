import { writeFile } from 'fs/promises';
import { join } from 'path';

export default async function globalTeardown() {
  console.log('🧹 Cleaning up Accessibility & Usability Test Environment');
  
  const reportsDir = process.env.TEST_REPORTS_DIR || './test-reports/accessibility-usability';
  const startTime = process.env.TEST_START_TIME;
  const endTime = new Date().toISOString();
  
  // Generate test session summary
  const sessionSummary = {
    startTime,
    endTime,
    duration: startTime ? new Date(endTime).getTime() - new Date(startTime).getTime() : 0,
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      baseUrl: process.env.TEST_BASE_URL || 'http://localhost:3000',
      headless: process.env.TEST_HEADLESS !== 'false',
      ci: !!process.env.CI
    },
    configuration: {
      timeout: 60000,
      maxWorkers: process.env.CI ? 2 : '50%',
      reportsDirectory: reportsDir
    }
  };
  
  try {
    await writeFile(
      join(reportsDir, 'test-session-summary.json'),
      JSON.stringify(sessionSummary, null, 2)
    );
    console.log('📄 Test session summary saved');
  } catch (error) {
    console.warn('⚠️  Could not save test session summary:', error);
  }
  
  // Log final summary
  console.log('');
  console.log('📊 Test Session Complete');
  console.log('========================');
  console.log(`Duration: ${Math.round(sessionSummary.duration / 1000)}s`);
  console.log(`Reports: ${reportsDir}`);
  console.log(`Base URL: ${sessionSummary.environment.baseUrl}`);
  console.log('');
  
  // Cleanup any global resources
  if (global.gc) {
    global.gc();
  }
  
  console.log('✅ Cleanup complete');
}