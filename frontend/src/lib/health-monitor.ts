/**
 * Health monitoring service for API connectivity
 * Provides periodic health checks, status tracking, and change notifications
 */

import { configManager } from './config';
import { networkErrorClassifier, ClassifiedError } from './error-handling';
import { apiLogger } from './api-logger';

export interface HealthStatus {
  isHealthy: boolean;
  lastCheck: Date;
  responseTime: number;
  error?: ClassifiedError;
  details?: {
    status: string;
    timestamp: string;
    version?: string;
    environment?: string;
    services?: Record<string, any>;
    system?: Record<string, any>;
  };
}

export interface HealthCheckOptions {
  timeout?: number;
  includeDetails?: boolean;
  endpoint?: 'simple' | 'full';
}

export type HealthChangeCallback = (status: HealthStatus) => void;

export class HealthMonitor {
  private currentStatus: HealthStatus;
  private checkInterval: number;
  private intervalId: NodeJS.Timeout | null = null;
  private callbacks: Set<HealthChangeCallback> = new Set();
  private isChecking = false;
  private consecutiveFailures = 0;
  private lastSuccessfulCheck: Date | null = null;

  constructor(checkInterval?: number) {
    this.checkInterval = checkInterval || configManager.getApiConfig().healthCheckInterval;
    this.currentStatus = {
      isHealthy: false,
      lastCheck: new Date(0), // Use epoch to indicate no check has been performed
      responseTime: 0,
      error: undefined
    };
  }

  /**
   * Perform a single health check
   */
  async checkHealth(options: HealthCheckOptions = {}): Promise<HealthStatus> {
    if (this.isChecking) {
      return this.currentStatus;
    }

    this.isChecking = true;
    const startTime = performance.now();
    const timeout = options.timeout || configManager.getApiConfig().healthCheckTimeout;
    const endpoint = options.endpoint || 'simple';
    const includeDetails = options.includeDetails || false;

    try {
      const healthUrl = endpoint === 'simple'
        ? `${configManager.getHealthCheckUrl()}/simple`
        : configManager.getHealthCheckUrl();

      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Health check timeout')), timeout);
      });

      // Perform health check request
      const fetchPromise = fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache'
        },
        credentials: 'omit' // Don't send cookies for health checks
      });

      const response = await Promise.race([fetchPromise, timeoutPromise]);
      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      if (response.ok) {
        const data = includeDetails ? await response.json() : null;

        const newStatus: HealthStatus = {
          isHealthy: true,
          lastCheck: new Date(),
          responseTime,
          error: undefined,
          details: data
        };

        // Log successful health check
        apiLogger.logHealthCheck(healthUrl, true, responseTime);

        this.updateStatus(newStatus);
        this.consecutiveFailures = 0;
        this.lastSuccessfulCheck = new Date();

        return newStatus;
      } else {
        // Server returned error status
        const errorText = await response.text().catch(() => 'Unknown error');
        const error = new Error(`Health check failed: ${response.status} ${response.statusText}`);
        (error as any).status = response.status;
        (error as any).responseText = errorText;

        const classifiedError = networkErrorClassifier.classifyError(
          error,
          response.status,
          healthUrl
        );

        const newStatus: HealthStatus = {
          isHealthy: false,
          lastCheck: new Date(),
          responseTime,
          error: classifiedError
        };

        // Log failed health check
        apiLogger.logHealthCheck(healthUrl, false, responseTime, error);

        this.updateStatus(newStatus);
        this.consecutiveFailures++;

        return newStatus;
      }
    } catch (error) {
      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      const classifiedError = networkErrorClassifier.classifyError(
        error as Error,
        undefined,
        configManager.getHealthCheckUrl()
      );

      const newStatus: HealthStatus = {
        isHealthy: false,
        lastCheck: new Date(),
        responseTime,
        error: classifiedError
      };

      // Log failed health check
      apiLogger.logHealthCheck(configManager.getHealthCheckUrl(), false, responseTime, error as Error);

      this.updateStatus(newStatus);
      this.consecutiveFailures++;

      return newStatus;
    } finally {
      this.isChecking = false;
    }
  }

  /**
   * Start periodic health checks
   */
  startPeriodicChecks(): void {
    if (this.intervalId) {
      this.stopPeriodicChecks();
    }

    // Perform initial check
    this.checkHealth({ endpoint: 'simple' });

    // Set up periodic checks
    this.intervalId = setInterval(() => {
      this.checkHealth({ endpoint: 'simple' });
    }, this.checkInterval);

    console.log(`🏥 Health monitoring started (interval: ${this.checkInterval}ms)`);
  }

  /**
   * Stop periodic health checks
   */
  stopPeriodicChecks(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      console.log('🏥 Health monitoring stopped');
    }
  }

  /**
   * Get current health status
   */
  getCurrentStatus(): HealthStatus {
    return { ...this.currentStatus };
  }

  /**
   * Subscribe to health status changes
   */
  onHealthChange(callback: HealthChangeCallback): () => void {
    this.callbacks.add(callback);

    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback);
    };
  }

  /**
   * Get health statistics
   */
  getHealthStats() {
    return {
      consecutiveFailures: this.consecutiveFailures,
      lastSuccessfulCheck: this.lastSuccessfulCheck,
      isMonitoring: this.intervalId !== null,
      checkInterval: this.checkInterval,
      currentStatus: this.getCurrentStatus()
    };
  }

  /**
   * Update check interval
   */
  updateCheckInterval(newInterval: number): void {
    this.checkInterval = newInterval;

    if (this.intervalId) {
      // Restart with new interval
      this.stopPeriodicChecks();
      this.startPeriodicChecks();
    }
  }

  /**
   * Perform detailed health check with full system information
   */
  async checkDetailedHealth(): Promise<HealthStatus> {
    return this.checkHealth({
      endpoint: 'full',
      includeDetails: true,
      timeout: 10000 // Longer timeout for detailed checks
    });
  }

  /**
   * Check if API is likely to be available based on recent history
   */
  isLikelyAvailable(): boolean {
    const now = new Date();
    const timeSinceLastCheck = now.getTime() - this.currentStatus.lastCheck.getTime();
    const checkIntervalBuffer = this.checkInterval * 2; // Allow some buffer

    // If we haven't checked recently, we don't know
    if (timeSinceLastCheck > checkIntervalBuffer) {
      return false;
    }

    // If current status is healthy, likely available
    if (this.currentStatus.isHealthy) {
      return true;
    }

    // If we have too many consecutive failures, likely not available
    if (this.consecutiveFailures >= 3) {
      return false;
    }

    // Otherwise, it's uncertain
    return false;
  }

  /**
   * Force a health check and return the result
   */
  async forceHealthCheck(): Promise<HealthStatus> {
    return this.checkHealth({ endpoint: 'simple', timeout: 5000 });
  }

  /**
   * Update internal status and notify callbacks
   */
  private updateStatus(newStatus: HealthStatus): void {
    const previousStatus = this.currentStatus;
    this.currentStatus = newStatus;

    // Notify callbacks if status changed or this is the first real status update
    const isFirstUpdate = previousStatus.lastCheck.getTime() === 0;
    const statusChanged = previousStatus.isHealthy !== newStatus.isHealthy;

    if (statusChanged || isFirstUpdate) {
      this.callbacks.forEach(callback => {
        try {
          callback(newStatus);
        } catch (error) {
          console.error('Error in health status callback:', error);
        }
      });
    }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.stopPeriodicChecks();
    this.callbacks.clear();
  }
}

// Create singleton instance
export const healthMonitor = new HealthMonitor();

// Auto-start monitoring in development mode
if (configManager.getEnvironmentConfig().isDevelopment) {
  // Start monitoring after a short delay to allow app initialization
  setTimeout(() => {
    healthMonitor.startPeriodicChecks();
  }, 1000);
}