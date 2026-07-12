# API Monitoring and Debugging System

This document describes the comprehensive monitoring and debugging capabilities implemented for API connectivity issues.

## Overview

The monitoring system provides three main components:

1. **Comprehensive Logging** - Structured logging for all API requests, responses, and errors
2. **Performance Monitoring** - Real-time tracking of API performance metrics and alerts
3. **Debug Tools** - Interactive debugging console and performance dashboard

## Components

### 1. API Logger (`api-logger.ts`)

Provides structured logging for all API activities with filtering and search capabilities.

#### Features:
- **Request/Response Logging**: Logs all API requests and responses with timing information
- **Error Logging**: Detailed network error logging with diagnostic information
- **Retry Tracking**: Logs retry attempts with exponential backoff details
- **Health Check Logging**: Tracks API health check results
- **Connection Status**: Logs connection state changes
- **Data Sanitization**: Automatically redacts sensitive information (passwords, tokens, etc.)
- **Filtering & Search**: Advanced filtering by level, category, time range, and search terms
- **Export Capabilities**: Export logs as JSON for external analysis

#### Usage:
```typescript
import { apiLogger } from './lib/api-logger';

// Log an API request
apiLogger.logRequest(url, method, requestId, requestData);

// Log a successful response
apiLogger.logResponse(url, method, requestId, statusCode, responseTime);

// Log a network error
apiLogger.logNetworkError(url, method, requestId, error, diagnostics);

// Get filtered logs
const errorLogs = apiLogger.getLogs({ level: [LogLevel.ERROR] });

// Subscribe to new log entries
const unsubscribe = apiLogger.subscribe((entry) => {
  console.log('New log entry:', entry);
});
```

### 2. API Performance Monitor (`api-performance-monitor.ts`)

Tracks API performance metrics, generates alerts, and provides performance analytics.

#### Features:
- **Response Time Tracking**: Monitors API response times with percentile calculations
- **Success Rate Monitoring**: Tracks success/failure rates per endpoint
- **Retry Pattern Analysis**: Monitors retry attempts and patterns
- **Performance Alerts**: Configurable alerts for high response times, error rates, and retry rates
- **Trend Analysis**: Identifies performance trends (improving/degrading/stable)
- **Dashboard Data**: Provides comprehensive performance dashboard data
- **Export Capabilities**: Export performance data as JSON or CSV

#### Usage:
```typescript
import { apiPerformanceMonitor } from './lib/api-performance-monitor';

// Record a performance metric
apiPerformanceMonitor.recordMetric(endpoint, method, responseTime, statusCode, {
  retryAttempts: 2,
  totalTime: 1500,
  error: 'Timeout error'
});

// Get endpoint statistics
const stats = apiPerformanceMonitor.getEndpointStats('/api/documents', 'GET');

// Get dashboard data
const dashboard = apiPerformanceMonitor.getDashboardData();

// Subscribe to performance alerts
const unsubscribe = apiPerformanceMonitor.onAlert((alert) => {
  console.log('Performance alert:', alert);
});
```

### 3. Debug Console (`DebugConsole.tsx`)

Interactive debugging console for viewing and analyzing logs.

#### Features:
- **Real-time Log Viewing**: Live updates of new log entries
- **Advanced Filtering**: Filter by level, category, time range, and search terms
- **Log Details**: Detailed view of individual log entries with full context
- **Export Functionality**: Export filtered logs for external analysis
- **Statistics Dashboard**: Overview of log statistics and error rates

### 4. Performance Dashboard (`ApiPerformanceDashboard.tsx`)

Comprehensive performance monitoring dashboard.

#### Features:
- **Overview Metrics**: Total requests, success rate, average response time, retry count
- **Endpoint Analysis**: Detailed performance metrics per endpoint
- **Alert Management**: View and manage performance alerts
- **Trend Visualization**: Performance trends over time
- **Slowest Endpoints**: Identify performance bottlenecks
- **Error-Prone Endpoints**: Identify reliability issues

### 5. Debug Toolbar (`DebugToolbar.tsx`)

Floating debug toolbar for easy access to debugging tools (development mode only).

#### Features:
- **Quick Status**: Shows API health, error count, and alert count
- **One-Click Access**: Quick access to debug console and performance dashboard
- **Health Check**: Manual health check trigger
- **Export/Clear**: Quick log export and clearing

## Integration

The monitoring system is automatically integrated with the existing API client:

```typescript
// In api.ts - automatically logs all requests
const response = await this.request('/documents');

// Logs are automatically created for:
// - API requests (with sanitized data)
// - API responses (with timing)
// - Network errors (with diagnostics)
// - Retry attempts (with backoff details)
// - Performance metrics (with alerts)
```

## Configuration

### Performance Thresholds

Configure performance alert thresholds:

```typescript
apiPerformanceMonitor.updateThresholds({
  responseTime: { warning: 1000, critical: 3000 },
  errorRate: { warning: 5, critical: 10 },
  retryRate: { warning: 20, critical: 50 },
  successRate: { warning: 95, critical: 90 }
});
```

### Log Filtering

Filter logs by various criteria:

```typescript
const filter = {
  level: [LogLevel.ERROR, LogLevel.WARN],
  category: [LogCategory.NETWORK_ERROR],
  timeRange: {
    start: new Date(Date.now() - 3600000), // Last hour
    end: new Date()
  },
  searchTerm: 'timeout',
  requestId: 'req_123'
};

const filteredLogs = apiLogger.getLogs(filter);
```

## Development Mode

In development mode, the debug toolbar is automatically enabled and provides:

- Floating debug toolbar in bottom-right corner
- Real-time status indicators
- Quick access to all debugging tools
- Automatic health monitoring

## Production Considerations

- Logging is optimized for performance with configurable limits
- Sensitive data is automatically sanitized
- Memory usage is controlled with rolling log buffers
- Export capabilities for production debugging
- Configurable alert thresholds for different environments

## Troubleshooting Common Issues

### High Response Times
1. Check the Performance Dashboard for slowest endpoints
2. Review retry patterns for specific endpoints
3. Analyze error logs for network issues
4. Check health check results for API availability

### Connection Failures
1. Review network error logs for detailed diagnostics
2. Check retry attempt patterns
3. Monitor health check results
4. Analyze connection status changes

### Performance Degradation
1. Use trend analysis to identify degrading performance
2. Compare current metrics with historical data
3. Check for increased error rates or retry attempts
4. Review alert history for patterns

## API Reference

### Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General information (requests, responses)
- `WARN`: Warning conditions (retries, slow responses)
- `ERROR`: Error conditions (network errors, failures)

### Log Categories
- `API_REQUEST`: API request logging
- `API_RESPONSE`: API response logging
- `NETWORK_ERROR`: Network error logging
- `RETRY_ATTEMPT`: Retry attempt logging
- `HEALTH_CHECK`: Health check logging
- `CONNECTION_STATUS`: Connection status changes

### Performance Alert Types
- `high_response_time`: Response time exceeds thresholds
- `high_error_rate`: Error rate exceeds thresholds
- `high_retry_rate`: Retry rate exceeds thresholds
- `endpoint_down`: Endpoint appears to be unavailable

### Alert Severities
- `low`: Minor performance issues
- `medium`: Moderate performance issues
- `high`: Significant performance issues
- `critical`: Critical performance issues requiring immediate attention

## Testing

The monitoring system includes comprehensive unit tests and integration tests:

```bash
# Run monitoring tests
npm test -- --run src/lib/__tests__/api-logger.test.ts
npm test -- --run src/lib/__tests__/api-performance-monitor.test.ts
npm test -- --run src/lib/__tests__/monitoring-integration.test.ts
```

## Future Enhancements

Potential future improvements:

1. **Real-time Dashboards**: WebSocket-based real-time updates
2. **Advanced Analytics**: Machine learning-based anomaly detection
3. **Integration with External Tools**: Export to monitoring services
4. **Mobile Debugging**: Mobile-optimized debugging interface
5. **Automated Remediation**: Automatic retry policy adjustments
6. **Performance Budgets**: Configurable performance budgets with alerts