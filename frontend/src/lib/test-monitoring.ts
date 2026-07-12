/**
 * Test script to verify monitoring system is working
 * Run this in browser console to test the monitoring system
 */

import { apiLogger } from './api-logger';
import { apiPerformanceMonitor } from './api-performance-monitor';

// Test function to verify monitoring is working
export function testMonitoring() {
  console.log('🔧 Testing monitoring system...');

  // Test API logger
  apiLogger.logRequest('https://test.example.com/api/test', 'GET', 'test-req-123', { test: true });
  apiLogger.logResponse('https://test.example.com/api/test', 'GET', 'test-req-123', 200, 150);
  apiLogger.logNetworkError('https://test.example.com/api/error', 'POST', 'test-req-456', new Error('Test error'));

  // Test performance monitor
  apiPerformanceMonitor.recordMetric('/api/test', 'GET', 150, 200);
  apiPerformanceMonitor.recordMetric('/api/slow', 'POST', 5000, 500, { error: 'Timeout' });

  // Check logs
  const logs = apiLogger.getLogs();
  const stats = apiLogger.getStats();
  const perfStats = apiPerformanceMonitor.getEndpointStats();

  console.log('📊 Monitoring test results:');
  console.log('- API Logs:', logs.length);
  console.log('- Log Stats:', stats);
  console.log('- Performance Stats:', perfStats);

  if (logs.length > 0) {
    console.log('✅ Monitoring system is working!');
    return true;
  } else {
    console.log('❌ Monitoring system not working');
    return false;
  }
}

// Auto-run test in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  // Add to window for manual testing
  (window as any).testMonitoring = testMonitoring;

  // Auto-test after a short delay
  setTimeout(() => {
    console.log('🔧 Auto-testing monitoring system...');
    testMonitoring();
  }, 2000);
}