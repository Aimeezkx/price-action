/**
 * Retry Configuration System
 * Defines retry configuration interface and default values
 * Implements configurable retry parameters (attempts, delays, timeouts)
 * Adds environment-specific retry settings
 */

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
  jitterEnabled: boolean;
  jitterFactor: number;
  timeoutMs: number;
  retryableStatusCodes: number[];
  retryableErrorTypes: string[];
}

export interface CircuitBreakerConfig {
  enabled: boolean;
  failureThreshold: number;
  recoveryTimeout: number;
  monitoringWindow: number;
}

export interface RetryEnvironmentConfig {
  development: RetryConfig;
  staging: RetryConfig;
  production: RetryConfig;
  circuitBreaker: CircuitBreakerConfig;
}

export class RetryConfigManager {
  private static instance: RetryConfigManager;
  private currentConfig: RetryConfig;
  private circuitBreakerConfig: CircuitBreakerConfig;
  private environment: string;

  private constructor() {
    this.environment = import.meta.env.VITE_ENVIRONMENT || 'development';
    this.currentConfig = this.loadRetryConfig();
    this.circuitBreakerConfig = this.loadCircuitBreakerConfig();
  }

  public static getInstance(): RetryConfigManager {
    if (!RetryConfigManager.instance) {
      RetryConfigManager.instance = new RetryConfigManager();
    }
    return RetryConfigManager.instance;
  }

  private getDefaultRetryConfig(): RetryEnvironmentConfig {
    return {
      development: {
        maxAttempts: 3,
        baseDelay: 1000, // 1 second
        maxDelay: 10000, // 10 seconds
        backoffFactor: 2,
        jitterEnabled: true,
        jitterFactor: 0.1,
        timeoutMs: 30000, // 30 seconds
        retryableStatusCodes: [408, 429, 500, 502, 503, 504],
        retryableErrorTypes: ['NetworkError', 'TimeoutError', 'ConnectionError']
      },
      staging: {
        maxAttempts: 5,
        baseDelay: 1500,
        maxDelay: 15000,
        backoffFactor: 2,
        jitterEnabled: true,
        jitterFactor: 0.15,
        timeoutMs: 45000,
        retryableStatusCodes: [408, 429, 500, 502, 503, 504],
        retryableErrorTypes: ['NetworkError', 'TimeoutError', 'ConnectionError']
      },
      production: {
        maxAttempts: 3,
        baseDelay: 2000,
        maxDelay: 20000,
        backoffFactor: 2.5,
        jitterEnabled: true,
        jitterFactor: 0.2,
        timeoutMs: 60000,
        retryableStatusCodes: [408, 429, 500, 502, 503, 504],
        retryableErrorTypes: ['NetworkError', 'TimeoutError', 'ConnectionError']
      },
      circuitBreaker: {
        enabled: true,
        failureThreshold: 5,
        recoveryTimeout: 60000, // 1 minute
        monitoringWindow: 300000 // 5 minutes
      }
    };
  }

  private loadRetryConfig(): RetryConfig {
    const defaults = this.getDefaultRetryConfig();
    const envConfig: RetryConfig = (defaults[this.environment as keyof typeof defaults] || defaults.development) as RetryConfig;

    // Override with environment variables if provided
    return {
      maxAttempts: parseInt(import.meta.env.VITE_RETRY_MAX_ATTEMPTS || envConfig.maxAttempts.toString()),
      baseDelay: parseInt(import.meta.env.VITE_RETRY_BASE_DELAY || envConfig.baseDelay.toString()),
      maxDelay: parseInt(import.meta.env.VITE_RETRY_MAX_DELAY || envConfig.maxDelay.toString()),
      backoffFactor: parseFloat(import.meta.env.VITE_RETRY_BACKOFF_FACTOR || envConfig.backoffFactor.toString()),
      jitterEnabled: import.meta.env.VITE_RETRY_JITTER_ENABLED !== 'false',
      jitterFactor: parseFloat(import.meta.env.VITE_RETRY_JITTER_FACTOR || envConfig.jitterFactor.toString()),
      timeoutMs: parseInt(import.meta.env.VITE_RETRY_TIMEOUT_MS || envConfig.timeoutMs.toString()),
      retryableStatusCodes: this.parseStatusCodes(import.meta.env.VITE_RETRY_STATUS_CODES) || envConfig.retryableStatusCodes,
      retryableErrorTypes: this.parseErrorTypes(import.meta.env.VITE_RETRY_ERROR_TYPES) || envConfig.retryableErrorTypes
    };
  }

  private loadCircuitBreakerConfig(): CircuitBreakerConfig {
    const defaults = this.getDefaultRetryConfig().circuitBreaker;

    return {
      enabled: import.meta.env.VITE_CIRCUIT_BREAKER_ENABLED !== 'false',
      failureThreshold: parseInt(import.meta.env.VITE_CIRCUIT_BREAKER_THRESHOLD || defaults.failureThreshold.toString()),
      recoveryTimeout: parseInt(import.meta.env.VITE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT || defaults.recoveryTimeout.toString()),
      monitoringWindow: parseInt(import.meta.env.VITE_CIRCUIT_BREAKER_MONITORING_WINDOW || defaults.monitoringWindow.toString())
    };
  }

  private parseStatusCodes(statusCodesStr?: string): number[] | null {
    if (!statusCodesStr) return null;
    try {
      return statusCodesStr.split(',').map(code => parseInt(code.trim())).filter(code => !isNaN(code));
    } catch {
      return null;
    }
  }

  private parseErrorTypes(errorTypesStr?: string): string[] | null {
    if (!errorTypesStr) return null;
    return errorTypesStr.split(',').map(type => type.trim()).filter(type => type.length > 0);
  }

  public getRetryConfig(): RetryConfig {
    return { ...this.currentConfig };
  }

  public getCircuitBreakerConfig(): CircuitBreakerConfig {
    return { ...this.circuitBreakerConfig };
  }

  public updateRetryConfig(updates: Partial<RetryConfig>): void {
    this.currentConfig = { ...this.currentConfig, ...updates };
  }

  public updateCircuitBreakerConfig(updates: Partial<CircuitBreakerConfig>): void {
    this.circuitBreakerConfig = { ...this.circuitBreakerConfig, ...updates };
  }

  public resetToDefaults(): void {
    this.currentConfig = this.loadRetryConfig();
    this.circuitBreakerConfig = this.loadCircuitBreakerConfig();
  }

  public isRetryableStatusCode(statusCode: number): boolean {
    return this.currentConfig.retryableStatusCodes.includes(statusCode);
  }

  public isRetryableError(error: Error): boolean {
    const errorType = error.constructor.name;
    const errorMessage = error.message.toLowerCase();

    return this.currentConfig.retryableErrorTypes.some(type =>
      errorType.includes(type) ||
      errorMessage.includes(type.toLowerCase()) ||
      errorMessage.includes('network') ||
      errorMessage.includes('timeout') ||
      errorMessage.includes('connection') ||
      errorMessage.includes('fetch')
    );
  }

  public calculateDelay(attempt: number): number {
    const { baseDelay, maxDelay, backoffFactor, jitterEnabled, jitterFactor } = this.currentConfig;

    // Calculate exponential backoff delay
    let delay = Math.min(baseDelay * Math.pow(backoffFactor, attempt - 1), maxDelay);

    // Add jitter if enabled
    if (jitterEnabled) {
      const jitter = delay * jitterFactor * (Math.random() * 2 - 1); // Random between -jitterFactor and +jitterFactor
      delay = Math.max(0, delay + jitter);
    }

    return Math.floor(delay);
  }

  public logConfiguration(): void {
    if (import.meta.env.VITE_DEBUG === 'true') {
      console.group('🔄 Retry Configuration Manager');
      console.log('Environment:', this.environment);
      console.log('Max Attempts:', this.currentConfig.maxAttempts);
      console.log('Base Delay:', this.currentConfig.baseDelay);
      console.log('Max Delay:', this.currentConfig.maxDelay);
      console.log('Backoff Factor:', this.currentConfig.backoffFactor);
      console.log('Jitter Enabled:', this.currentConfig.jitterEnabled);
      console.log('Timeout:', this.currentConfig.timeoutMs);
      console.log('Retryable Status Codes:', this.currentConfig.retryableStatusCodes);
      console.log('Circuit Breaker Enabled:', this.circuitBreakerConfig.enabled);
      console.log('Circuit Breaker Threshold:', this.circuitBreakerConfig.failureThreshold);
      console.groupEnd();
    }
  }
}

// Export singleton instance
export const retryConfigManager = RetryConfigManager.getInstance();

// Export convenience functions
export const getRetryConfig = () => retryConfigManager.getRetryConfig();
export const getCircuitBreakerConfig = () => retryConfigManager.getCircuitBreakerConfig();
export const isRetryableStatusCode = (statusCode: number) => retryConfigManager.isRetryableStatusCode(statusCode);
export const isRetryableError = (error: Error) => retryConfigManager.isRetryableError(error);
export const calculateRetryDelay = (attempt: number) => retryConfigManager.calculateDelay(attempt);

// Initialize configuration logging in development
if (import.meta.env.VITE_DEBUG === 'true') {
  retryConfigManager.logConfiguration();
}