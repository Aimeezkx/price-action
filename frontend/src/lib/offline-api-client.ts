/**
 * Offline-Aware API Client
 * Enhanced API client that integrates with offline manager and error handling
 * Provides automatic caching, queue management, and graceful degradation
 */

import { offlineManager } from './offline-manager';
import { classifyError, ClassifiedError } from './error-handling';
import { showErrorFromException } from './error-notification-manager';

export interface ApiClientOptions {
  baseURL?: string;
  timeout?: number;
  retries?: number;
  cacheEnabled?: boolean;
  cacheTTL?: number;
  offlineQueueEnabled?: boolean;
  showErrorNotifications?: boolean;
}

export interface RequestOptions extends Omit<RequestInit, 'cache'> {
  timeout?: number;
  retries?: number;
  enableCache?: boolean;
  cacheTTL?: number;
  queueWhenOffline?: boolean;
  priority?: 'low' | 'medium' | 'high';
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Headers;
  fromCache: boolean;
  timestamp: Date;
}

export class OfflineApiClient {
  private baseURL: string;
  private defaultOptions: ApiClientOptions;

  constructor(options: ApiClientOptions = {}) {
    this.baseURL = options.baseURL || '';
    this.defaultOptions = {
      timeout: 30000,
      retries: 3,
      cacheEnabled: true,
      cacheTTL: 5 * 60 * 1000, // 5 minutes
      offlineQueueEnabled: true,
      showErrorNotifications: true,
      ...options
    };
  }

  public async get<T = any>(url: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, { ...options, method: 'GET' });
  }

  public async post<T = any>(url: string, data?: any, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
  }

  public async put<T = any>(url: string, data?: any, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
  }

  public async delete<T = any>(url: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    return this.request<T>(url, { ...options, method: 'DELETE' });
  }

  public async upload<T = any>(url: string, file: File, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>(url, {
      ...options,
      method: 'POST',
      body: formData,
      // Don't set Content-Type for FormData, let browser set it with boundary
      headers: {
        ...options.headers
      }
    });
  }

  private async request<T = any>(url: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const fullUrl = this.buildUrl(url);
    const requestOptions = this.buildRequestOptions(options);
    const cacheKey = this.buildCacheKey(fullUrl, requestOptions);

    // Check if we should use cache
    if (this.shouldUseCache(requestOptions)) {
      const cachedResponse = this.getCachedResponse<T>(cacheKey);
      if (cachedResponse) {
        return cachedResponse;
      }
    }

    // Check if we're offline and should queue the request
    if (!offlineManager.isOnline() && this.shouldQueueWhenOffline(requestOptions)) {
      return this.queueRequest<T>(fullUrl, requestOptions);
    }

    // Make the actual request
    try {
      const response = await this.makeRequest(fullUrl, requestOptions);
      const apiResponse = await this.processResponse<T>(response, false);

      // Cache successful GET requests
      if (requestOptions.method === 'GET' && this.shouldCache(requestOptions)) {
        this.cacheResponse(cacheKey, apiResponse, requestOptions.cacheTTL);
      }

      return apiResponse;

    } catch (error) {
      return this.handleRequestError<T>(error, fullUrl, requestOptions, cacheKey);
    }
  }

  private async makeRequest(url: string, options: RequestOptions): Promise<Response> {
    const controller = new AbortController();
    const timeout = options.timeout || this.defaultOptions.timeout!;

    // Set up timeout
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;

    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  private async processResponse<T>(response: Response, fromCache: boolean): Promise<ApiResponse<T>> {
    let data: T;

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text() as any;
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return {
      data,
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
      fromCache,
      timestamp: new Date()
    };
  }

  private async handleRequestError<T>(
    error: any,
    url: string,
    options: RequestOptions,
    cacheKey: string
  ): Promise<ApiResponse<T>> {
    const classifiedError = classifyError(error);

    // Show error notification if enabled
    if (this.defaultOptions.showErrorNotifications) {
      showErrorFromException(error, error.status, {
        operation: this.getOperationFromMethod(options.method),
        userAction: 'api_request'
      });
    }

    // Try to return cached data for GET requests
    if (options.method === 'GET') {
      const cachedResponse = this.getCachedResponse<T>(cacheKey);
      if (cachedResponse) {
        console.warn('API request failed, returning cached data:', classifiedError.userMessage);
        return cachedResponse;
      }
    }

    // Queue request if offline and retryable
    if (!offlineManager.isOnline() && classifiedError.isRetryable && this.shouldQueueWhenOffline(options)) {
      return this.queueRequest<T>(url, options);
    }

    throw error;
  }

  private queueRequest<T>(url: string, options: RequestOptions): Promise<ApiResponse<T>> {
    if (!this.defaultOptions.offlineQueueEnabled) {
      throw new Error('Currently offline and request queuing is disabled');
    }

    const actionId = offlineManager.addToQueue({
      type: 'api_call',
      data: { url, options },
      maxRetries: options.retries || this.defaultOptions.retries!,
      priority: options.priority || 'medium'
    });

    // Return a promise that will be resolved when the request is processed
    return new Promise((resolve, reject) => {
      // For now, reject with a descriptive message
      // In a full implementation, you might want to set up a listener for when the queued action completes
      reject(new Error(`Request queued for when connection is restored (ID: ${actionId})`));
    });
  }

  private shouldUseCache(options: RequestOptions): boolean {
    return (
      this.defaultOptions.cacheEnabled &&
      options.enableCache !== false &&
      options.method === 'GET'
    );
  }

  private shouldCache(options: RequestOptions): boolean {
    return (
      this.defaultOptions.cacheEnabled &&
      options.enableCache !== false &&
      options.method === 'GET'
    );
  }

  private shouldQueueWhenOffline(options: RequestOptions): boolean {
    return (
      this.defaultOptions.offlineQueueEnabled &&
      options.queueWhenOffline !== false &&
      options.method !== 'GET' // Don't queue GET requests
    );
  }

  private getCachedResponse<T>(cacheKey: string): ApiResponse<T> | null {
    const cached = offlineManager.getCachedData(cacheKey);
    if (cached) {
      return {
        ...cached,
        fromCache: true,
        timestamp: new Date(cached.timestamp)
      };
    }
    return null;
  }

  private cacheResponse<T>(cacheKey: string, response: ApiResponse<T>, ttl?: number): void {
    const cacheData = {
      ...response,
      fromCache: false,
      timestamp: response.timestamp.toISOString()
    };

    offlineManager.cacheData(cacheKey, cacheData, ttl || this.defaultOptions.cacheTTL);
  }

  private buildUrl(url: string): string {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return `${this.baseURL}${url.startsWith('/') ? url : `/${url}`}`;
  }

  private buildRequestOptions(options: RequestOptions): RequestOptions {
    return {
      timeout: this.defaultOptions.timeout,
      retries: this.defaultOptions.retries,
      enableCache: this.defaultOptions.cacheEnabled,
      cacheTTL: this.defaultOptions.cacheTTL,
      queueWhenOffline: this.defaultOptions.offlineQueueEnabled,
      priority: 'medium',
      ...options
    };
  }

  private buildCacheKey(url: string, options: RequestOptions): string {
    const method = options.method || 'GET';
    const body = options.body ? JSON.stringify(options.body) : '';
    return `${method}:${url}:${body}`;
  }

  private getOperationFromMethod(method?: string): string {
    switch (method?.toUpperCase()) {
      case 'POST':
        return 'create';
      case 'PUT':
      case 'PATCH':
        return 'update';
      case 'DELETE':
        return 'delete';
      case 'GET':
      default:
        return 'fetch';
    }
  }

  // Configuration methods
  public setBaseURL(baseURL: string): void {
    this.baseURL = baseURL;
  }

  public updateOptions(options: Partial<ApiClientOptions>): void {
    this.defaultOptions = { ...this.defaultOptions, ...options };
  }

  public clearCache(): void {
    offlineManager.clearCache();
  }

  public getCacheStats(): { keys: string[]; size: number } {
    // This would need to be implemented in the offline manager
    return { keys: [], size: 0 };
  }
}

// Export singleton instance
export const apiClient = new OfflineApiClient({
  baseURL: '/api'
});

// Export convenience functions
export const get = <T = any>(url: string, options?: RequestOptions) =>
  apiClient.get<T>(url, options);

export const post = <T = any>(url: string, data?: any, options?: RequestOptions) =>
  apiClient.post<T>(url, data, options);

export const put = <T = any>(url: string, data?: any, options?: RequestOptions) =>
  apiClient.put<T>(url, data, options);

export const del = <T = any>(url: string, options?: RequestOptions) =>
  apiClient.delete<T>(url, options);

export const upload = <T = any>(url: string, file: File, options?: RequestOptions) =>
  apiClient.upload<T>(url, file, options);