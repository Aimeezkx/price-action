/**
 * Exponential Backoff Retry Logic
 * Creates retry mechanism with exponential backoff algorithm
 * Adds jitter to prevent thundering herd problems
 * Implements maximum retry limits and circuit breaker logic
 */

import { retryConfigManager, RetryConfig, CircuitBreakerConfig } from './retry-config';
import { apiLogger } from './api-logger';

export interface RetryAttempt {
  attempt: number;
  delay: number;
  error?: Error;
  timestamp: Date;
}

export interface RetryResult<T> {
  success: boolean;
  data?: T;
  error?: Error;
  attempts: RetryAttempt[];
  totalTime: number;
  circuitBreakerTripped?: boolean;
}

export enum CircuitBreakerState {
  CLOSED = 'CLOSED',     // Normal operation
  OPEN = 'OPEN',         // Circuit breaker is open, failing fast
  HALF_OPEN = 'HALF_OPEN' // Testing if service has recovered
}

export class CircuitBreaker {
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private successCount: number = 0;
  private config: CircuitBreakerConfig;

  constructor(config: CircuitBreakerConfig) {
    this.config = config;
  }

  public canExecute(): boolean {
    if (!this.config.enabled) return true;

    const now = Date.now();

    switch (this.state) {
      case CircuitBreakerState.CLOSED:
        return true;

      case CircuitBreakerState.OPEN:
        if (now - this.lastFailureTime >= this.config.recoveryTimeout) {
          this.state = CircuitBreakerState.HALF_OPEN;
          this.successCount = 0;
          return true;
        }
        return false;

      case CircuitBreakerState.HALF_OPEN:
        return true;

      default:
        return false;
    }
  }

  public recordSuccess(): void {
    if (!this.config.enabled) return;

    this.failureCount = 0;

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= 3) { // Require 3 successful calls to close circuit
        this.state = CircuitBreakerState.CLOSED;
      }
    }
  }

  public recordFailure(): void {
    if (!this.config.enabled) return;

    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.OPEN;
    } else if (this.failureCount >= this.config.failureThreshold) {
      this.state = CircuitBreakerState.OPEN;
    }
  }

  public getState(): CircuitBreakerState {
    return this.state;
  }

  public getFailureCount(): number {
    return this.failureCount;
  }

  public reset(): void {
    this.state = CircuitBreakerState.CLOSED;
    this.failureCount = 0;
    this.lastFailureTime = 0;
    this.successCount = 0;
  }
}

export class RetryExecutor {
  private retryConfig: RetryConfig;
  private circuitBreaker: CircuitBreaker;

  constructor() {
    this.retryConfig = retryConfigManager.getRetryConfig();
    this.circuitBreaker = new CircuitBreaker(retryConfigManager.getCircuitBreakerConfig());
  }

  public async executeWithRetry<T>(
    operation: () => Promise<T>,
    customConfig?: Partial<RetryConfig>,
    context?: { url?: string; method?: string; requestId?: string }
  ): Promise<RetryResult<T>> {
    const config = { ...this.retryConfig, ...customConfig };
    const attempts: RetryAttempt[] = [];
    const startTime = Date.now();

    // Check circuit breaker before starting
    if (!this.circuitBreaker.canExecute()) {
      return {
        success: false,
        error: new Error('Circuit breaker is open - service unavailable'),
        attempts: [],
        totalTime: 0,
        circuitBreakerTripped: true
      };
    }

    for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
      const attemptStart = Date.now();

      try {
        // Create timeout promise
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), config.timeoutMs);
        });

        // Race between operation and timeout
        const result = await Promise.race([operation(), timeoutPromise]);

        // Success - record attempt and return
        attempts.push({
          attempt,
          delay: 0,
          timestamp: new Date(attemptStart)
        });

        this.circuitBreaker.recordSuccess();

        return {
          success: true,
          data: result,
          attempts,
          totalTime: Date.now() - startTime
        };

      } catch (error) {
        const attemptError = error as Error;

        // Record the failed attempt
        attempts.push({
          attempt,
          delay: 0,
          error: attemptError,
          timestamp: new Date(attemptStart)
        });

        // Check if error is retryable
        const isRetryable = this.isRetryableError(attemptError, config);

        // If this is the last attempt or error is not retryable, fail
        if (attempt === config.maxAttempts || !isRetryable) {
          this.circuitBreaker.recordFailure();

          return {
            success: false,
            error: attemptError,
            attempts,
            totalTime: Date.now() - startTime
          };
        }

        // Calculate delay for next attempt
        const delay = this.calculateDelay(attempt, config);
        attempts[attempts.length - 1].delay = delay;

        // Log retry attempt
        if (context?.url && context?.method && context?.requestId) {
          apiLogger.logRetryAttempt(
            context.url,
            context.method,
            context.requestId,
            attempt,
            config.maxAttempts,
            delay,
            attemptError.message
          );
        }

        // Wait before next attempt
        await this.sleep(delay);

        // Check circuit breaker before next attempt
        if (!this.circuitBreaker.canExecute()) {
          this.circuitBreaker.recordFailure();

          return {
            success: false,
            error: new Error('Circuit breaker opened during retry sequence'),
            attempts,
            totalTime: Date.now() - startTime,
            circuitBreakerTripped: true
          };
        }
      }
    }

    // This should never be reached, but just in case
    return {
      success: false,
      error: new Error('Retry logic error - unexpected end of execution'),
      attempts,
      totalTime: Date.now() - startTime
    };
  }

  private isRetryableError(error: Error, config: RetryConfig): boolean {
    // Check if it's a fetch error with status code
    if ('status' in error && typeof error.status === 'number') {
      return config.retryableStatusCodes.includes(error.status);
    }

    // Check error type/message
    const errorType = error.constructor.name;
    const errorMessage = error.message.toLowerCase();

    return config.retryableErrorTypes.some(type =>
      errorType.includes(type) ||
      errorMessage.includes(type.toLowerCase()) ||
      errorMessage.includes('network') ||
      errorMessage.includes('timeout') ||
      errorMessage.includes('connection') ||
      errorMessage.includes('fetch')
    );
  }

  private calculateDelay(attempt: number, config: RetryConfig): number {
    const { baseDelay, maxDelay, backoffFactor, jitterEnabled, jitterFactor } = config;

    // Calculate exponential backoff delay
    let delay = Math.min(baseDelay * Math.pow(backoffFactor, attempt - 1), maxDelay);

    // Add jitter if enabled to prevent thundering herd
    if (jitterEnabled) {
      const jitterRange = delay * jitterFactor;
      const jitter = (Math.random() * 2 - 1) * jitterRange; // Random between -jitterRange and +jitterRange
      delay = Math.max(baseDelay * 0.1, delay + jitter); // Ensure minimum delay
    }

    return Math.floor(delay);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  public getCircuitBreakerState(): CircuitBreakerState {
    return this.circuitBreaker.getState();
  }

  public getCircuitBreakerFailureCount(): number {
    return this.circuitBreaker.getFailureCount();
  }

  public resetCircuitBreaker(): void {
    this.circuitBreaker.reset();
  }

  public updateConfig(newConfig: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...newConfig };
  }
}

// Utility function for creating retry-enabled fetch requests
export async function retryFetch(
  url: string,
  options: RequestInit = {},
  customRetryConfig?: Partial<RetryConfig>
): Promise<RetryResult<Response>> {
  const executor = new RetryExecutor();

  return executor.executeWithRetry(async () => {
    const response = await fetch(url, options);

    // Convert HTTP error status codes to errors for retry logic
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`) as Error & { status: number };
      error.status = response.status;
      throw error;
    }

    return response;
  }, customRetryConfig);
}

// Export singleton instance for global use
export const globalRetryExecutor = new RetryExecutor();