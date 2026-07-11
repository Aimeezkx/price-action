# Robust API Client with Retry Logic

This implementation provides a comprehensive solution for handling API connectivity issues with automatic retry mechanisms, error classification, and circuit breaker patterns.

## Features

### 🔄 Retry Configuration System
- Environment-specific retry settings (development, staging, production)
- Configurable retry parameters (attempts, delays, timeouts)
- Support for environment variable overrides
- Exponential backoff with jitter to prevent thundering herd problems

### 🚨 Error Classification and Handling
- Automatic error type classification (timeout, server error, network, etc.)
- User-friendly error messages with suggested actions
- Comprehensive logging for debugging connectivity issues
- Error history tracking and analysis

### ⚡ Circuit Breaker Pattern
- Automatic circuit breaker to prevent cascading failures
- Configurable failure thresholds and recovery timeouts
- Half-open state for testing service recovery
- Manual circuit breaker reset capability

### 📊 Monitoring and Debugging
- Detailed retry attempt tracking
- Performance monitoring integration
- Error log analysis and export
- Circuit breaker state monitoring

## Usage

### Basic Usage (Backward Compatible)

```typescript
import { apiClient } from './lib/api';

// Existing code continues to work
const documents = await apiClient.getDocuments();
const result = await apiClient.uploadDocument(file);
```

### Enhanced Usage with Detailed Response

```typescript
import { robustApiClient } from './lib/api';

// Get detailed response with retry information
const response = await robustApiClient.getDocumentsWithDetails();

if (response.success) {
  console.log('Data:', response.data);
  console.log('Retry attempts:', response.retryInfo?.attempts);
  console.log('Total time:', response.retryInfo?.totalTime);
} else {
  console.error('Error:', response.error?.userMessage);
  console.log('Error type:', response.error?.type);
  console.log('Suggested action:', response.error?.suggestedAction);
}
```

### Health Monitoring

```typescript
import { robustApiClient } from './lib/api';

// Check API health
const healthResponse = await robustApiClient.checkHealth();

// Monitor circuit breaker
const state = robustApiClient.getCircuitBreakerState();
const failureCount = robustApiClient.getCircuitBreakerFailureCount();

// Reset circuit breaker if needed
if (state === 'OPEN') {
  robustApiClient.resetCircuitBreaker();
}
```

### Error Analysis

```typescript
import { ErrorLogger } from './lib/error-handling';

// Get recent errors
const recentErrors = ErrorLogger.getLogs(10);

// Get errors by type
const timeoutErrors = ErrorLogger.getLogsByType('CONNECTION_TIMEOUT');

// Export error logs for analysis
const errorReport = ErrorLogger.exportLogs();
```

### Configuration Management

```typescript
import { retryConfigManager } from './lib/retry-config';

// Get current configuration
const config = retryConfigManager.getRetryConfig();

// Update configuration
retryConfigManager.updateRetryConfig({
  maxAttempts: 5,
  baseDelay: 2000
});

// Check if error is retryable
const isRetryable = retryConfigManager.isRetryableError(error);
```

## Configuration

### Environment Variables

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_FALLBACK_URL=http://127.0.0.1:8000
VITE_API_TIMEOUT=30000

# Retry Configuration
VITE_RETRY_MAX_ATTEMPTS=3
VITE_RETRY_BASE_DELAY=1000
VITE_RETRY_MAX_DELAY=10000
VITE_RETRY_BACKOFF_FACTOR=2
VITE_RETRY_JITTER_ENABLED=true
VITE_RETRY_JITTER_FACTOR=0.1
VITE_RETRY_TIMEOUT_MS=30000
VITE_RETRY_STATUS_CODES=408,429,500,502,503,504
VITE_RETRY_ERROR_TYPES=NetworkError,TimeoutError,ConnectionError

# Circuit Breaker Configuration
VITE_CIRCUIT_BREAKER_ENABLED=true
VITE_CIRCUIT_BREAKER_THRESHOLD=5
VITE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60000
VITE_CIRCUIT_BREAKER_MONITORING_WINDOW=300000

# Debug Configuration
VITE_DEBUG=true
VITE_ENVIRONMENT=development
```

### Default Configurations by Environment

#### Development
- Max Attempts: 3
- Base Delay: 1000ms
- Backoff Factor: 2
- Timeout: 30 seconds

#### Staging
- Max Attempts: 5
- Base Delay: 1500ms
- Backoff Factor: 2
- Timeout: 45 seconds

#### Production
- Max Attempts: 3
- Base Delay: 2000ms
- Backoff Factor: 2.5
- Timeout: 60 seconds

## Error Types

The system classifies errors into the following types:

- `CONNECTION_TIMEOUT`: Request timed out
- `SERVER_ERROR`: 5xx HTTP status codes
- `CLIENT_ERROR`: 4xx HTTP status codes
- `NETWORK_UNREACHABLE`: Network connectivity issues
- `DNS_RESOLUTION_FAILED`: DNS lookup failures
- `CORS_ERROR`: Cross-origin request blocked
- `RATE_LIMITED`: 429 Too Many Requests
- `SERVICE_UNAVAILABLE`: 503 Service Unavailable
- `UNKNOWN_ERROR`: Unclassified errors

## Circuit Breaker States

- `CLOSED`: Normal operation, requests pass through
- `OPEN`: Circuit breaker is open, requests fail fast
- `HALF_OPEN`: Testing if service has recovered

## Testing

Run the test suite to verify the implementation:

```bash
npm test -- --run src/lib/__tests__/retry-system.test.ts
```

## Examples

See `api-client-example.ts` for comprehensive usage examples including:

- Basic document upload with error handling
- Robust API operations with detailed responses
- Health monitoring and circuit breaker management
- Error log analysis and configuration management
- Complete workflow examples

## Architecture

The implementation consists of several key components:

1. **RetryConfigManager**: Manages retry configuration and environment-specific settings
2. **RetryExecutor**: Implements exponential backoff retry logic with circuit breaker
3. **NetworkErrorClassifier**: Classifies and handles different types of network errors
4. **RobustApiClient**: Enhanced API client that integrates all retry and error handling logic
5. **ErrorLogger**: Tracks and analyzes error history for debugging

## Requirements Satisfied

This implementation satisfies the following requirements from the API connectivity fix specification:

- **Requirement 2.1**: Retry logic with exponential backoff ✅
- **Requirement 2.2**: Connection timeout and error classification ✅
- **Requirement 2.3**: Specific handling strategies for each error type ✅

The system provides robust error handling, automatic retry mechanisms, and comprehensive monitoring capabilities to ensure reliable API connectivity even in challenging network conditions.