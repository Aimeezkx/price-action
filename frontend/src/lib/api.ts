import { performanceMonitor } from './performance';
import { configManager } from './config';
import { RetryExecutor, RetryResult } from './retry-logic';
import { networkErrorClassifier, ClassifiedError, ErrorLogger } from './error-handling';
import { retryConfigManager } from './retry-config';
import { apiLogger } from './api-logger';
import { apiPerformanceMonitor } from './api-performance-monitor';

// API client configuration
const API_BASE_URL = import.meta.env.DEV 
  ? '/api'  // Relative path for proxy in development
  : (import.meta.env.VITE_API_BASE_URL || '/api'); // Use environment variable for production

export interface ApiRequestOptions extends RequestInit {
  skipRetry?: boolean;
  customTimeout?: number;
  maxRetries?: number;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: ClassifiedError;
  retryInfo?: {
    attempts: number;
    totalTime: number;
    circuitBreakerTripped?: boolean;
  };
}

export class RobustApiClient {
  private baseUrl: string;
  private retryExecutor: RetryExecutor;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || configManager.getApiConfig().baseUrl || API_BASE_URL;
    this.retryExecutor = new RetryExecutor();
  }

  private async request<T>(
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const { skipRetry = false, customTimeout, maxRetries, ...fetchOptions } = options;
    const url = `${this.baseUrl}${endpoint}`;
    const startTime = performance.now();
    const requestId = this.generateRequestId();
    const method = fetchOptions.method || 'GET';
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
      ...fetchOptions,
    };

    // Log the API request
    console.log('🔧 API Request:', method, url, requestId);
    apiLogger.logRequest(url, method, requestId, {
      headers: this.sanitizeHeaders(config.headers as Record<string, string>),
      body: config.body ? this.sanitizeBody(config.body) : undefined
    });

    // Create the fetch operation
    const fetchOperation = async (): Promise<Response> => {
      const timeoutMs = customTimeout || retryConfigManager.getRetryConfig().timeoutMs;
      
      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), timeoutMs);
      });

      // Race between fetch and timeout
      const response = await Promise.race([fetch(url, config), timeoutPromise]);
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`) as Error & { status: number };
        error.status = response.status;
        throw error;
      }

      return response;
    };

    try {
      let result: RetryResult<Response>;

      if (skipRetry) {
        // Execute without retry
        try {
          const response = await fetchOperation();
          result = {
            success: true,
            data: response,
            attempts: [],
            totalTime: performance.now() - startTime
          };
        } catch (error) {
          result = {
            success: false,
            error: error as Error,
            attempts: [],
            totalTime: performance.now() - startTime
          };
        }
      } else {
        // Execute with retry logic
        const retryConfig = maxRetries ? { maxAttempts: maxRetries } : undefined;
        result = await this.retryExecutor.executeWithRetry(
          fetchOperation, 
          retryConfig,
          { url, method, requestId }
        );
      }

      const endTime = performance.now();
      const duration = endTime - startTime;

      if (result.success && result.data) {
        // Track successful API call
        performanceMonitor.trackAPICall(endpoint, duration, result.data.status);

        // Log successful response
        apiLogger.logResponse(url, method, requestId, result.data.status, duration);

        // Record performance metric
        apiPerformanceMonitor.recordMetric(endpoint, method, duration, result.data.status, {
          retryAttempts: result.attempts.length,
          totalTime: result.totalTime
        });

        // Parse JSON response
        const jsonData = await result.data.json();
        
        return {
          data: jsonData,
          success: true,
          retryInfo: {
            attempts: result.attempts.length,
            totalTime: result.totalTime,
            circuitBreakerTripped: result.circuitBreakerTripped
          }
        };
      } else {
        // Handle error case
        const statusCode = 'status' in (result.error || {}) ? (result.error as any).status : undefined;
        const classifiedError = networkErrorClassifier.classifyError(
          result.error || new Error('Unknown error'),
          statusCode,
          url
        );

        // Log network error with diagnostics
        apiLogger.logNetworkError(url, method, requestId, result.error || new Error('Unknown error'), {
          statusCode,
          attempts: result.attempts.length,
          totalTime: result.totalTime,
          circuitBreakerTripped: result.circuitBreakerTripped,
          retryAttempts: result.attempts.map(attempt => ({
            attempt: attempt.attempt,
            delay: attempt.delay,
            error: attempt.error?.message
          }))
        });

        // Log the error
        ErrorLogger.addLog(classifiedError);

        // Track failed API call
        performanceMonitor.trackAPICall(endpoint, duration, statusCode || 0);

        // Record performance metric for failed request
        apiPerformanceMonitor.recordMetric(endpoint, method, duration, statusCode || 0, {
          retryAttempts: result.attempts.length,
          totalTime: result.totalTime,
          error: result.error?.message
        });

        return {
          data: {} as T,
          success: false,
          error: classifiedError,
          retryInfo: {
            attempts: result.attempts.length,
            totalTime: result.totalTime,
            circuitBreakerTripped: result.circuitBreakerTripped
          }
        };
      }
    } catch (error) {
      // Fallback error handling
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      const classifiedError = networkErrorClassifier.classifyError(error as Error, undefined, url);
      
      // Log network error
      apiLogger.logNetworkError(url, method, requestId, error as Error, {
        duration,
        fallbackError: true
      });
      
      ErrorLogger.addLog(classifiedError);
      
      performanceMonitor.trackAPICall(endpoint, duration, 0);

      // Record performance metric for fallback error
      apiPerformanceMonitor.recordMetric(endpoint, method, duration, 0, {
        error: (error as Error).message
      });
      
      return {
        data: {} as T,
        success: false,
        error: classifiedError,
        retryInfo: {
          attempts: 0,
          totalTime: duration
        }
      };
    }
  }

  // Helper method for handling API responses
  private async handleResponse<T>(response: ApiResponse<T>): Promise<T> {
    if (response.success) {
      return response.data;
    } else {
      // Throw the classified error for backward compatibility
      const error = new Error(response.error?.userMessage || 'API request failed');
      (error as any).classifiedError = response.error;
      (error as any).retryInfo = response.retryInfo;
      throw error;
    }
  }

  // Health check method
  async checkHealth(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request('/health', { skipRetry: true, customTimeout: 5000 });
  }

  // Document endpoints
  async getDocuments() {
    const response = await this.request('/documents');
    return this.handleResponse(response);
  }

  async getDocument(id: string) {
    const response = await this.request(`/documents/${id}`);
    return this.handleResponse(response);
  }

  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.request('/ingest', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
      customTimeout: 120000, // 2 minutes for file uploads
      maxRetries: 2 // Fewer retries for uploads
    });
    return this.handleResponse(response);
  }

  // Chapter endpoints
  async getChapters(documentId: string) {
    const response = await this.request(`/doc/${documentId}/toc`);
    return this.handleResponse(response);
  }

  async getChapterFigures(chapterId: string) {
    const response = await this.request(`/chapter/${chapterId}/fig`);
    return this.handleResponse(response);
  }

  async getChapterKnowledge(chapterId: string, params?: {
    knowledge_type?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = params ? `?${new URLSearchParams(params as Record<string, string>)}` : '';
    const response = await this.request(`/chapter/${chapterId}/k${query}`);
    return this.handleResponse(response);
  }

  // Card endpoints
  async getCards(params?: Record<string, string>) {
    const query = params ? `?${new URLSearchParams(params)}` : '';
    const response = await this.request(`/cards${query}`);
    return this.handleResponse(response);
  }

  async generateCards(documentId: string) {
    const response = await this.request('/card/gen', {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId }),
      customTimeout: 60000, // 1 minute for card generation
    });
    return this.handleResponse(response);
  }

  // Review endpoints
  async getTodayReview() {
    const response = await this.request('/review/today');
    return this.handleResponse(response);
  }

  async gradeCard(cardId: string, grade: number) {
    const response = await this.request('/review/grade', {
      method: 'POST',
      body: JSON.stringify({ card_id: cardId, grade }),
    });
    return this.handleResponse(response);
  }

  // Search endpoints
  async search(query: string, filters?: Record<string, string>) {
    const params = new URLSearchParams({ q: query, ...filters });
    const response = await this.request(`/search?${params}`);
    return this.handleResponse(response);
  }

  // Export endpoints
  async exportCsv(format: 'anki' | 'notion' = 'anki') {
    const response = await this.request(`/export/csv?format=${format}`, {
      customTimeout: 60000, // 1 minute for exports
    });
    return this.handleResponse(response);
  }

  async exportJsonl() {
    const response = await this.request('/export/jsonl', {
      customTimeout: 60000, // 1 minute for exports
    });
    return this.handleResponse(response);
  }

  // Utility methods for debugging and monitoring
  getCircuitBreakerState() {
    return this.retryExecutor.getCircuitBreakerState();
  }

  getCircuitBreakerFailureCount() {
    return this.retryExecutor.getCircuitBreakerFailureCount();
  }

  resetCircuitBreaker() {
    this.retryExecutor.resetCircuitBreaker();
  }

  // Method to get detailed response with retry info (for debugging)
  async getDocumentsWithDetails() {
    return this.request('/documents');
  }

  async uploadDocumentWithDetails(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/ingest', {
      method: 'POST',
      headers: {},
      body: formData,
      customTimeout: 120000,
      maxRetries: 2
    });
  }

  // Helper methods for logging
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private sanitizeHeaders(headers: Record<string, string> | undefined): Record<string, string> {
    if (!headers) return {};
    
    const sanitized = { ...headers };
    const sensitiveHeaders = ['authorization', 'cookie', 'x-api-key', 'x-auth-token'];
    
    for (const key of Object.keys(sanitized)) {
      if (sensitiveHeaders.some(sensitive => key.toLowerCase().includes(sensitive))) {
        sanitized[key] = '[REDACTED]';
      }
    }
    
    return sanitized;
  }

  private sanitizeBody(body: any): any {
    if (body instanceof FormData) {
      return '[FormData]';
    }
    
    if (typeof body === 'string') {
      try {
        const parsed = JSON.parse(body);
        return this.sanitizeObject(parsed);
      } catch {
        return '[String Body]';
      }
    }
    
    return this.sanitizeObject(body);
  }

  private sanitizeObject(obj: any): any {
    if (typeof obj !== 'object' || obj === null) {
      return obj;
    }

    const sanitized = Array.isArray(obj) ? [] : {};
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'auth'];

    for (const [key, value] of Object.entries(obj)) {
      const lowerKey = key.toLowerCase();
      if (sensitiveKeys.some(sensitive => lowerKey.includes(sensitive))) {
        (sanitized as any)[key] = '[REDACTED]';
      } else if (typeof value === 'object' && value !== null) {
        (sanitized as any)[key] = this.sanitizeObject(value);
      } else {
        (sanitized as any)[key] = value;
      }
    }

    return sanitized;
  }
}

// Backward compatibility - keep the old ApiClient class
export class ApiClient extends RobustApiClient {
  constructor(baseUrl?: string) {
    super(baseUrl);
  }
}

// Export both the robust client and the backward-compatible client
export const robustApiClient = new RobustApiClient();
export const apiClient = new ApiClient();