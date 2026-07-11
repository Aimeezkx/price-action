/**
 * Example usage of the Robust API Client with retry logic
 * Demonstrates how to use the enhanced API client with error handling and retry mechanisms
 */

import { robustApiClient, apiClient } from './api';
import { ErrorLogger } from './error-handling';
import { retryConfigManager } from './retry-config';

// Example 1: Basic usage (backward compatible)
export async function basicDocumentUpload(file: File) {
  try {
    console.log('📤 Starting document upload...');
    const result = await apiClient.uploadDocument(file);
    console.log('✅ Upload successful:', result);
    return result;
  } catch (error) {
    console.error('❌ Upload failed:', error);

    // Check if it's a classified error with retry info
    if ('classifiedError' in error && 'retryInfo' in error) {
      console.log('🔄 Retry attempts:', (error as any).retryInfo.attempts);
      console.log('⏱️ Total time:', (error as any).retryInfo.totalTime, 'ms');
      console.log('🚨 Error type:', (error as any).classifiedError.type);
      console.log('💡 Suggested action:', (error as any).classifiedError.suggestedAction);
    }

    throw error;
  }
}

// Example 2: Using the robust client with detailed response
export async function robustDocumentUpload(file: File) {
  console.log('📤 Starting robust document upload...');

  const response = await robustApiClient.uploadDocumentWithDetails(file);

  if (response.success) {
    console.log('✅ Upload successful:', response.data);
    console.log('🔄 Retry attempts:', response.retryInfo?.attempts);
    console.log('⏱️ Total time:', response.retryInfo?.totalTime, 'ms');
    return response.data;
  } else {
    console.error('❌ Upload failed:', response.error?.userMessage);
    console.log('🚨 Error type:', response.error?.type);
    console.log('💡 Suggested action:', response.error?.suggestedAction);
    console.log('🔄 Retry attempts:', response.retryInfo?.attempts);
    console.log('⚡ Circuit breaker tripped:', response.retryInfo?.circuitBreakerTripped);

    throw new Error(response.error?.userMessage || 'Upload failed');
  }
}

// Example 3: Health check with monitoring
export async function checkApiHealth() {
  console.log('🏥 Checking API health...');

  const response = await robustApiClient.checkHealth();

  if (response.success) {
    console.log('✅ API is healthy:', response.data);
    console.log('⏱️ Response time:', response.retryInfo?.totalTime, 'ms');
    return true;
  } else {
    console.error('❌ API health check failed:', response.error?.userMessage);
    console.log('🚨 Error type:', response.error?.type);
    return false;
  }
}

// Example 4: Circuit breaker monitoring
export function monitorCircuitBreaker() {
  const state = robustApiClient.getCircuitBreakerState();
  const failureCount = robustApiClient.getCircuitBreakerFailureCount();

  console.log('🔌 Circuit Breaker Status:');
  console.log('  State:', state);
  console.log('  Failure Count:', failureCount);

  if (state === 'OPEN') {
    console.warn('⚠️ Circuit breaker is OPEN - API calls will fail fast');
    console.log('💡 Consider calling robustApiClient.resetCircuitBreaker() if service is restored');
  }

  return { state, failureCount };
}

// Example 5: Error log analysis
export function analyzeErrorLogs() {
  const recentErrors = ErrorLogger.getLogs(10);

  console.log('📊 Recent API Errors:');
  console.log('  Total errors:', recentErrors.length);

  const errorsByType = recentErrors.reduce((acc, error) => {
    acc[error.type] = (acc[error.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  console.log('  Errors by type:', errorsByType);

  const retryableErrors = recentErrors.filter(error => error.isRetryable);
  console.log('  Retryable errors:', retryableErrors.length);

  return {
    totalErrors: recentErrors.length,
    errorsByType,
    retryableCount: retryableErrors.length,
    recentErrors: recentErrors.slice(0, 5) // Return 5 most recent
  };
}

// Example 6: Configuration management
export function updateRetryConfiguration() {
  console.log('⚙️ Current retry configuration:');
  const currentConfig = retryConfigManager.getRetryConfig();
  console.log(currentConfig);

  // Example: Increase retry attempts for production
  if (import.meta.env.VITE_ENVIRONMENT === 'production') {
    retryConfigManager.updateRetryConfig({
      maxAttempts: 5,
      baseDelay: 2000
    });
    console.log('✅ Updated retry configuration for production');
  }

  // Example: Enable more aggressive retries for development
  if (import.meta.env.VITE_ENVIRONMENT === 'development') {
    retryConfigManager.updateRetryConfig({
      maxAttempts: 2,
      baseDelay: 500
    });
    console.log('✅ Updated retry configuration for development');
  }
}

// Example 7: Comprehensive error handling workflow
export async function robustApiWorkflow() {
  console.log('🚀 Starting robust API workflow...');

  try {
    // 1. Check API health first
    const isHealthy = await checkApiHealth();
    if (!isHealthy) {
      console.warn('⚠️ API appears unhealthy, but continuing...');
    }

    // 2. Monitor circuit breaker
    const { state } = monitorCircuitBreaker();
    if (state === 'OPEN') {
      throw new Error('Circuit breaker is open - aborting workflow');
    }

    // 3. Perform API operations
    const documents = await robustApiClient.getDocuments();
    console.log('📄 Retrieved documents:', (documents as any).length);

    // 4. Analyze any errors that occurred
    const errorAnalysis = analyzeErrorLogs();
    if (errorAnalysis.totalErrors > 0) {
      console.log('📊 Error analysis:', errorAnalysis);
    }

    return {
      success: true,
      documentsCount: (documents as any).length,
      errorAnalysis
    };

  } catch (error) {
    console.error('❌ Workflow failed:', error);

    // Final error analysis
    const errorAnalysis = analyzeErrorLogs();

    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      errorAnalysis
    };
  }
}

// Export all examples for easy testing
export const examples = {
  basicDocumentUpload,
  robustDocumentUpload,
  checkApiHealth,
  monitorCircuitBreaker,
  analyzeErrorLogs,
  updateRetryConfiguration,
  robustApiWorkflow
};