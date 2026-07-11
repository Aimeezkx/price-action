/**
 * Error Handling and Classification System
 * Classifies network errors and provides user-friendly messaging
 */

export enum NetworkErrorType {
  CONNECTION_TIMEOUT = 'CONNECTION_TIMEOUT',
  SERVER_ERROR = 'SERVER_ERROR',
  NETWORK_UNREACHABLE = 'NETWORK_UNREACHABLE',
  DNS_RESOLUTION_FAILED = 'DNS_RESOLUTION_FAILED',
  CORS_ERROR = 'CORS_ERROR',
  RATE_LIMITED = 'RATE_LIMITED',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  CLIENT_ERROR = 'CLIENT_ERROR',
}

export interface ClassifiedError {
  type: NetworkErrorType;
  userMessage: string;
  technicalMessage: string;
  canRetry: boolean;
  isRetryable: boolean;
  requestId: string;
  timestamp: Date;
  statusCode?: number;
}

class NetworkErrorClassifier {
  classifyError(
    error: Error,
    statusCode?: number,
    url?: string
  ): ClassifiedError {
    const timestamp = new Date();
    const requestId = `req_${timestamp.getTime()}_${Math.random().toString(36).substr(2, 9)}`;

    // Classify based on status code
    if (statusCode) {
      if (statusCode >= 500) {
        return {
          type: NetworkErrorType.SERVER_ERROR,
          userMessage: 'Server is temporarily unavailable',
          technicalMessage: error.message,
          canRetry: true,
          isRetryable: true,
          requestId,
          timestamp,
          statusCode,
        };
      } else if (statusCode === 429) {
        return {
          type: NetworkErrorType.RATE_LIMITED,
          userMessage: 'Too many requests. Please wait a moment.',
          technicalMessage: error.message,
          canRetry: true,
          isRetryable: true,
          requestId,
          timestamp,
          statusCode,
        };
      } else if (statusCode === 503) {
        return {
          type: NetworkErrorType.SERVICE_UNAVAILABLE,
          userMessage: 'Service is temporarily unavailable',
          technicalMessage: error.message,
          canRetry: true,
          isRetryable: true,
          requestId,
          timestamp,
          statusCode,
        };
      } else if (statusCode >= 400) {
        return {
          type: NetworkErrorType.CLIENT_ERROR,
          userMessage: 'Invalid request',
          technicalMessage: error.message,
          canRetry: false,
          isRetryable: false,
          requestId,
          timestamp,
          statusCode,
        };
      }
    }

    // Classify based on error message/type
    const errorMessage = error.message.toLowerCase();

    if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
      return {
        type: NetworkErrorType.CONNECTION_TIMEOUT,
        userMessage: 'Connection timed out. Please try again.',
        technicalMessage: error.message,
        canRetry: true,
        isRetryable: true,
        requestId,
        timestamp,
      };
    }

    if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
      return {
        type: NetworkErrorType.NETWORK_UNREACHABLE,
        userMessage: 'Network connection failed',
        technicalMessage: error.message,
        canRetry: true,
        isRetryable: true,
        requestId,
        timestamp,
      };
    }

    if (errorMessage.includes('cors')) {
      return {
        type: NetworkErrorType.CORS_ERROR,
        userMessage: 'Cross-origin request blocked',
        technicalMessage: error.message,
        canRetry: false,
        isRetryable: false,
        requestId,
        timestamp,
      };
    }

    // Default classification
    return {
      type: NetworkErrorType.CLIENT_ERROR,
      userMessage: 'An unexpected error occurred',
      technicalMessage: error.message,
      canRetry: false,
      isRetryable: false,
      requestId,
      timestamp,
    };
  }
}

const internalNetworkErrorClassifier = new NetworkErrorClassifier();

// Error handling utilities
export class ErrorLogger {
  private static logs: ClassifiedError[] = [];
  private static maxLogs = 100;

  public static addLog(error: ClassifiedError): void {
    this.logs.unshift(error);
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }
  }

  public static getLogs(limit?: number): ClassifiedError[] {
    return limit ? this.logs.slice(0, limit) : [...this.logs];
  }

  public static getLogsByType(errorType: NetworkErrorType): ClassifiedError[] {
    return this.logs.filter(log => log.type === errorType);
  }

  public static clearLogs(): void {
    this.logs = [];
  }

  public static exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

// Export singleton instance
export const networkErrorClassifier = internalNetworkErrorClassifier;

// Convenience functions
export const classifyError = (error: Error, statusCode?: number, requestUrl?: string) =>
  networkErrorClassifier.classifyError(error, statusCode, requestUrl);

export const isRetryableError = (error: Error, statusCode?: number) => {
  const classified = classifyError(error, statusCode);
  return classified.isRetryable;
};