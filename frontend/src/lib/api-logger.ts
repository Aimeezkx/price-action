/**
 * Comprehensive API logging system for debugging connectivity issues
 * Provides structured logging with filtering and search capabilities
 */

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

export enum LogCategory {
  API_REQUEST = 'api_request',
  API_RESPONSE = 'api_response',
  NETWORK_ERROR = 'network_error',
  RETRY_ATTEMPT = 'retry_attempt',
  HEALTH_CHECK = 'health_check',
  CONNECTION_STATUS = 'connection_status'
}

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  category: LogCategory;
  message: string;
  data?: Record<string, any>;
  requestId?: string;
  url?: string;
  method?: string;
  statusCode?: number;
  responseTime?: number;
  error?: {
    name: string;
    message: string;
    stack?: string;
    code?: string;
  };
}

export interface LogFilter {
  level?: LogLevel[];
  category?: LogCategory[];
  timeRange?: {
    start: Date;
    end: Date;
  };
  searchTerm?: string;
  requestId?: string;
  url?: string;
}

class ApiLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private listeners: ((entry: LogEntry) => void)[] = [];

  /**
   * Log an API request
   */
  logRequest(url: string, method: string, requestId: string, data?: any): void {
    const entry: LogEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      level: LogLevel.INFO,
      category: LogCategory.API_REQUEST,
      message: `API Request: ${method} ${url}`,
      requestId,
      url,
      method,
      data: data ? this.sanitizeData(data) : undefined
    };

    this.addLog(entry);
  }

  /**
   * Log an API response
   */
  logResponse(
    url: string,
    method: string,
    requestId: string,
    statusCode: number,
    responseTime: number,
    data?: any
  ): void {
    const entry: LogEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      level: statusCode >= 400 ? LogLevel.ERROR : LogLevel.INFO,
      category: LogCategory.API_RESPONSE,
      message: `API Response: ${method} ${url} - ${statusCode} (${responseTime}ms)`,
      requestId,
      url,
      method,
      statusCode,
      responseTime,
      data: data ? this.sanitizeData(data) : undefined
    };

    this.addLog(entry);
  }

  /**
   * Log a network error with detailed diagnostic information
   */
  logNetworkError(
    url: string,
    method: string,
    requestId: string,
    error: Error,
    diagnostics?: Record<string, any>
  ): void {
    const entry: LogEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      level: LogLevel.ERROR,
      category: LogCategory.NETWORK_ERROR,
      message: `Network Error: ${method} ${url} - ${error.message}`,
      requestId,
      url,
      method,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack,
        code: (error as any).code
      },
      data: {
        ...diagnostics,
        userAgent: navigator.userAgent,
        connectionType: (navigator as any).connection?.effectiveType,
        onLine: navigator.onLine,
        timestamp: Date.now()
      }
    };

    this.addLog(entry);
  }

  /**
   * Log a retry attempt
   */
  logRetryAttempt(
    url: string,
    method: string,
    requestId: string,
    attempt: number,
    maxAttempts: number,
    delay: number,
    reason: string
  ): void {
    const entry: LogEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      level: LogLevel.WARN,
      category: LogCategory.RETRY_ATTEMPT,
      message: `Retry Attempt ${attempt}/${maxAttempts}: ${method} ${url} - ${reason}`,
      requestId,
      url,
      method,
      data: {
        attempt,
        maxAttempts,
        delay,
        reason
      }
    };

    this.addLog(entry);
  }

  /**
   * Log health check results
   */
  logHealthCheck(
    url: string,
    isHealthy: boolean,
    responseTime?: number,
    error?: Error
  ): void {
    const entry: LogEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      level: isHealthy ? LogLevel.INFO : LogLevel.ERROR,
      category: LogCategory.HEALTH_CHECK,
      message: `Health Check: ${url} - ${isHealthy ? 'Healthy' : 'Unhealthy'}`,
      url,
      responseTime,
      data: {
        isHealthy,
        responseTime
      },
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } : undefined
    };

    this.addLog(entry);
  }

  /**
   * Log connection status changes
   */
  logConnectionStatus(
    status: 'connected' | 'connecting' | 'disconnected' | 'error',
    message: string,
    data?: Record<string, any>
  ): void {
    const entry: LogEntry = {
      id: this.generateId(),
      timestamp: new Date(),
      level: status === 'error' ? LogLevel.ERROR : LogLevel.INFO,
      category: LogCategory.CONNECTION_STATUS,
      message: `Connection Status: ${status} - ${message}`,
      data
    };

    this.addLog(entry);
  }

  /**
   * Get filtered logs
   */
  getLogs(filter?: LogFilter): LogEntry[] {
    let filteredLogs = [...this.logs];

    if (filter) {
      if (filter.level && filter.level.length > 0) {
        filteredLogs = filteredLogs.filter(log => filter.level!.includes(log.level));
      }

      if (filter.category && filter.category.length > 0) {
        filteredLogs = filteredLogs.filter(log => filter.category!.includes(log.category));
      }

      if (filter.timeRange) {
        filteredLogs = filteredLogs.filter(log =>
          log.timestamp >= filter.timeRange!.start &&
          log.timestamp <= filter.timeRange!.end
        );
      }

      if (filter.searchTerm) {
        const searchTerm = filter.searchTerm.toLowerCase();
        filteredLogs = filteredLogs.filter(log =>
          log.message.toLowerCase().includes(searchTerm) ||
          log.url?.toLowerCase().includes(searchTerm) ||
          log.requestId?.toLowerCase().includes(searchTerm)
        );
      }

      if (filter.requestId) {
        filteredLogs = filteredLogs.filter(log => log.requestId === filter.requestId);
      }

      if (filter.url) {
        filteredLogs = filteredLogs.filter(log => log.url?.includes(filter.url!));
      }
    }

    return filteredLogs.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Export logs as JSON
   */
  exportLogs(filter?: LogFilter): string {
    const logs = this.getLogs(filter);
    return JSON.stringify(logs, null, 2);
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = [];
    this.notifyListeners();
  }

  /**
   * Subscribe to new log entries
   */
  subscribe(listener: (entry: LogEntry) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Get log statistics
   */
  getStats(): {
    total: number;
    byLevel: Record<LogLevel, number>;
    byCategory: Record<LogCategory, number>;
    errorRate: number;
    avgResponseTime: number;
  } {
    const stats = {
      total: this.logs.length,
      byLevel: {} as Record<LogLevel, number>,
      byCategory: {} as Record<LogCategory, number>,
      errorRate: 0,
      avgResponseTime: 0
    };

    // Initialize counters
    Object.values(LogLevel).forEach(level => {
      stats.byLevel[level] = 0;
    });
    Object.values(LogCategory).forEach(category => {
      stats.byCategory[category] = 0;
    });

    let totalResponseTime = 0;
    let responseTimeCount = 0;
    let errorCount = 0;

    this.logs.forEach(log => {
      stats.byLevel[log.level]++;
      stats.byCategory[log.category]++;

      if (log.level === LogLevel.ERROR) {
        errorCount++;
      }

      if (log.responseTime) {
        totalResponseTime += log.responseTime;
        responseTimeCount++;
      }
    });

    stats.errorRate = this.logs.length > 0 ? (errorCount / this.logs.length) * 100 : 0;
    stats.avgResponseTime = responseTimeCount > 0 ? totalResponseTime / responseTimeCount : 0;

    return stats;
  }

  private addLog(entry: LogEntry): void {
    this.logs.push(entry);

    // Maintain max logs limit
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    this.notifyListeners(entry);
  }

  private notifyListeners(entry?: LogEntry): void {
    if (entry) {
      this.listeners.forEach(listener => listener(entry));
    }
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private sanitizeData(data: any): any {
    // Remove sensitive information from logged data
    if (typeof data !== 'object' || data === null) {
      return data;
    }

    const sanitized = { ...data };
    const sensitiveKeys = ['password', 'token', 'authorization', 'cookie', 'session'];

    const sanitizeObject = (obj: any): any => {
      if (typeof obj !== 'object' || obj === null) {
        return obj;
      }

      const result = Array.isArray(obj) ? [] : {};

      for (const [key, value] of Object.entries(obj)) {
        const lowerKey = key.toLowerCase();
        if (sensitiveKeys.some(sensitive => lowerKey.includes(sensitive))) {
          (result as any)[key] = '[REDACTED]';
        } else if (typeof value === 'object' && value !== null) {
          (result as any)[key] = sanitizeObject(value);
        } else {
          (result as any)[key] = value;
        }
      }

      return result;
    };

    return sanitizeObject(sanitized);
  }
}

// Export singleton instance
export const apiLogger = new ApiLogger();