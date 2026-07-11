/**
 * API Performance Monitoring System
 * Tracks API response times, success rates, retry patterns, and performance dashboards
 */

import { apiLogger } from './api-logger';

export interface ApiPerformanceMetric {
  id: string;
  timestamp: Date;
  endpoint: string;
  method: string;
  responseTime: number;
  statusCode: number;
  success: boolean;
  retryAttempts: number;
  totalTime: number;
  requestSize?: number;
  responseSize?: number;
  cacheHit?: boolean;
  error?: string;
}

export interface EndpointStats {
  endpoint: string;
  method: string;
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  successRate: number;
  avgResponseTime: number;
  minResponseTime: number;
  maxResponseTime: number;
  p50ResponseTime: number;
  p95ResponseTime: number;
  p99ResponseTime: number;
  totalRetries: number;
  avgRetries: number;
  errorRate: number;
  lastRequest: Date;
  recentErrors: string[];
}

export interface PerformanceDashboardData {
  overview: {
    totalRequests: number;
    successRate: number;
    avgResponseTime: number;
    errorRate: number;
    totalRetries: number;
  };
  endpoints: EndpointStats[];
  timeSeriesData: {
    timestamp: Date;
    responseTime: number;
    successRate: number;
    requestCount: number;
  }[];
  slowestEndpoints: EndpointStats[];
  mostErrorProneEndpoints: EndpointStats[];
  retryPatterns: {
    endpoint: string;
    avgRetries: number;
    maxRetries: number;
    retrySuccessRate: number;
  }[];
}

export interface PerformanceAlert {
  id: string;
  timestamp: Date;
  type: 'high_response_time' | 'high_error_rate' | 'high_retry_rate' | 'endpoint_down';
  severity: 'low' | 'medium' | 'high' | 'critical';
  endpoint: string;
  message: string;
  value: number;
  threshold: number;
  metadata?: Record<string, any>;
}

export interface PerformanceThresholds {
  responseTime: {
    warning: number;
    critical: number;
  };
  errorRate: {
    warning: number;
    critical: number;
  };
  retryRate: {
    warning: number;
    critical: number;
  };
  successRate: {
    warning: number;
    critical: number;
  };
}

class ApiPerformanceMonitor {
  private metrics: ApiPerformanceMetric[] = [];
  private maxMetrics = 1000;
  private alerts: PerformanceAlert[] = [];
  private thresholds: PerformanceThresholds;
  private listeners: ((alert: PerformanceAlert) => void)[] = [];

  constructor() {
    this.thresholds = {
      responseTime: { warning: 1000, critical: 3000 },
      errorRate: { warning: 5, critical: 10 },
      retryRate: { warning: 20, critical: 50 },
      successRate: { warning: 95, critical: 90 }
    };
  }

  /**
   * Record an API performance metric
   */
  recordMetric(
    endpoint: string,
    method: string,
    responseTime: number,
    statusCode: number,
    options: {
      retryAttempts?: number;
      totalTime?: number;
      requestSize?: number;
      responseSize?: number;
      cacheHit?: boolean;
      error?: string;
    } = {}
  ): void {
    const metric: ApiPerformanceMetric = {
      id: this.generateId(),
      timestamp: new Date(),
      endpoint,
      method,
      responseTime,
      statusCode,
      success: statusCode >= 200 && statusCode < 300,
      retryAttempts: options.retryAttempts || 0,
      totalTime: options.totalTime || responseTime,
      requestSize: options.requestSize,
      responseSize: options.responseSize,
      cacheHit: options.cacheHit,
      error: options.error
    };

    this.metrics.push(metric);

    // Maintain max metrics limit
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }

    // Check for performance alerts
    this.checkPerformanceAlerts(metric);
  }

  /**
   * Get endpoint statistics
   */
  getEndpointStats(endpoint?: string, method?: string): EndpointStats[] {
    const filteredMetrics = this.metrics.filter(m =>
      (!endpoint || m.endpoint === endpoint) &&
      (!method || m.method === method)
    );

    const groupedMetrics = this.groupMetricsByEndpoint(filteredMetrics);

    return Object.entries(groupedMetrics).map(([key, metrics]) => {
      const [endpointPath, methodName] = key.split('|');
      return this.calculateEndpointStats(endpointPath, methodName, metrics);
    });
  }

  /**
   * Get performance dashboard data
   */
  getDashboardData(timeRange?: { start: Date; end: Date }): PerformanceDashboardData {
    let filteredMetrics = this.metrics;

    if (timeRange) {
      filteredMetrics = this.metrics.filter(m =>
        m.timestamp >= timeRange.start && m.timestamp <= timeRange.end
      );
    }

    const endpointStats = this.getEndpointStats();
    const overview = this.calculateOverviewStats(filteredMetrics);
    const timeSeriesData = this.generateTimeSeriesData(filteredMetrics);

    return {
      overview,
      endpoints: endpointStats,
      timeSeriesData,
      slowestEndpoints: endpointStats
        .sort((a, b) => b.avgResponseTime - a.avgResponseTime)
        .slice(0, 5),
      mostErrorProneEndpoints: endpointStats
        .sort((a, b) => b.errorRate - a.errorRate)
        .slice(0, 5),
      retryPatterns: this.calculateRetryPatterns(filteredMetrics)
    };
  }

  /**
   * Get performance alerts
   */
  getAlerts(severity?: PerformanceAlert['severity']): PerformanceAlert[] {
    let alerts = [...this.alerts];

    if (severity) {
      alerts = alerts.filter(alert => alert.severity === severity);
    }

    return alerts.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Subscribe to performance alerts
   */
  onAlert(callback: (alert: PerformanceAlert) => void): () => void {
    this.listeners.push(callback);
    return () => {
      const index = this.listeners.indexOf(callback);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Update performance thresholds
   */
  updateThresholds(newThresholds: Partial<PerformanceThresholds>): void {
    this.thresholds = { ...this.thresholds, ...newThresholds };
  }

  /**
   * Export performance data
   */
  exportData(format: 'json' | 'csv' = 'json'): string {
    const data = {
      metrics: this.metrics,
      alerts: this.alerts,
      dashboard: this.getDashboardData(),
      thresholds: this.thresholds,
      exportedAt: new Date().toISOString()
    };

    if (format === 'json') {
      return JSON.stringify(data, null, 2);
    } else {
      return this.convertToCSV(this.metrics);
    }
  }

  /**
   * Clear all metrics and alerts
   */
  clear(): void {
    this.metrics = [];
    this.alerts = [];
  }

  /**
   * Get performance trends
   */
  getPerformanceTrends(hours: number = 24): {
    responseTimeTrend: 'improving' | 'degrading' | 'stable';
    errorRateTrend: 'improving' | 'degrading' | 'stable';
    throughputTrend: 'increasing' | 'decreasing' | 'stable';
  } {
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    const recentMetrics = this.metrics.filter(m => m.timestamp >= cutoff);

    if (recentMetrics.length < 10) {
      return {
        responseTimeTrend: 'stable',
        errorRateTrend: 'stable',
        throughputTrend: 'stable'
      };
    }

    const halfPoint = Math.floor(recentMetrics.length / 2);
    const firstHalf = recentMetrics.slice(0, halfPoint);
    const secondHalf = recentMetrics.slice(halfPoint);

    const firstHalfAvgResponse = firstHalf.reduce((sum, m) => sum + m.responseTime, 0) / firstHalf.length;
    const secondHalfAvgResponse = secondHalf.reduce((sum, m) => sum + m.responseTime, 0) / secondHalf.length;

    const firstHalfErrorRate = (firstHalf.filter(m => !m.success).length / firstHalf.length) * 100;
    const secondHalfErrorRate = (secondHalf.filter(m => !m.success).length / secondHalf.length) * 100;

    const responseTimeTrend = this.calculateTrend(firstHalfAvgResponse, secondHalfAvgResponse, 50);
    const errorRateTrend = this.calculateTrend(firstHalfErrorRate, secondHalfErrorRate, 1, true);
    const throughputTrend = this.calculateTrend(firstHalf.length, secondHalf.length, 5);

    return {
      responseTimeTrend,
      errorRateTrend,
      throughputTrend: throughputTrend as 'increasing' | 'decreasing' | 'stable'
    };
  }

  private groupMetricsByEndpoint(metrics: ApiPerformanceMetric[]): Record<string, ApiPerformanceMetric[]> {
    return metrics.reduce((groups, metric) => {
      const key = `${metric.endpoint}|${metric.method}`;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(metric);
      return groups;
    }, {} as Record<string, ApiPerformanceMetric[]>);
  }

  private calculateEndpointStats(endpoint: string, method: string, metrics: ApiPerformanceMetric[]): EndpointStats {
    const responseTimes = metrics.map(m => m.responseTime).sort((a, b) => a - b);
    const successfulRequests = metrics.filter(m => m.success).length;
    const totalRetries = metrics.reduce((sum, m) => sum + m.retryAttempts, 0);
    const recentErrors = metrics
      .filter(m => !m.success && m.error)
      .slice(-5)
      .map(m => m.error!);

    return {
      endpoint,
      method,
      totalRequests: metrics.length,
      successfulRequests,
      failedRequests: metrics.length - successfulRequests,
      successRate: (successfulRequests / metrics.length) * 100,
      avgResponseTime: responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length,
      minResponseTime: responseTimes[0] || 0,
      maxResponseTime: responseTimes[responseTimes.length - 1] || 0,
      p50ResponseTime: this.calculatePercentile(responseTimes, 50),
      p95ResponseTime: this.calculatePercentile(responseTimes, 95),
      p99ResponseTime: this.calculatePercentile(responseTimes, 99),
      totalRetries,
      avgRetries: totalRetries / metrics.length,
      errorRate: ((metrics.length - successfulRequests) / metrics.length) * 100,
      lastRequest: metrics[metrics.length - 1]?.timestamp || new Date(0),
      recentErrors
    };
  }

  private calculateOverviewStats(metrics: ApiPerformanceMetric[]) {
    const successfulRequests = metrics.filter(m => m.success).length;
    const totalRetries = metrics.reduce((sum, m) => sum + m.retryAttempts, 0);
    const avgResponseTime = metrics.reduce((sum, m) => sum + m.responseTime, 0) / metrics.length;

    return {
      totalRequests: metrics.length,
      successRate: metrics.length > 0 ? (successfulRequests / metrics.length) * 100 : 0,
      avgResponseTime: avgResponseTime || 0,
      errorRate: metrics.length > 0 ? ((metrics.length - successfulRequests) / metrics.length) * 100 : 0,
      totalRetries
    };
  }

  private generateTimeSeriesData(metrics: ApiPerformanceMetric[]) {
    const timeSlots = new Map<string, { responseTimes: number[]; successes: number; total: number }>();
    const slotDuration = 5 * 60 * 1000; // 5 minutes

    metrics.forEach(metric => {
      const slotTime = Math.floor(metric.timestamp.getTime() / slotDuration) * slotDuration;
      const slotKey = slotTime.toString();

      if (!timeSlots.has(slotKey)) {
        timeSlots.set(slotKey, { responseTimes: [], successes: 0, total: 0 });
      }

      const slot = timeSlots.get(slotKey)!;
      slot.responseTimes.push(metric.responseTime);
      slot.total++;
      if (metric.success) slot.successes++;
    });

    return Array.from(timeSlots.entries())
      .map(([timeStr, data]) => ({
        timestamp: new Date(parseInt(timeStr)),
        responseTime: data.responseTimes.reduce((sum, time) => sum + time, 0) / data.responseTimes.length,
        successRate: (data.successes / data.total) * 100,
        requestCount: data.total
      }))
      .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
  }

  private calculateRetryPatterns(metrics: ApiPerformanceMetric[]) {
    const retryData = new Map<string, { retries: number[]; successes: number; total: number }>();

    metrics.forEach(metric => {
      const key = `${metric.endpoint}|${metric.method}`;
      if (!retryData.has(key)) {
        retryData.set(key, { retries: [], successes: 0, total: 0 });
      }

      const data = retryData.get(key)!;
      data.retries.push(metric.retryAttempts);
      data.total++;
      if (metric.success) data.successes++;
    });

    return Array.from(retryData.entries()).map(([key, data]) => {
      const [endpoint] = key.split('|');
      return {
        endpoint,
        avgRetries: data.retries.reduce((sum, r) => sum + r, 0) / data.retries.length,
        maxRetries: Math.max(...data.retries),
        retrySuccessRate: (data.successes / data.total) * 100
      };
    });
  }

  private checkPerformanceAlerts(metric: ApiPerformanceMetric): void {
    const alerts: PerformanceAlert[] = [];

    // High response time alert
    if (metric.responseTime > this.thresholds.responseTime.critical) {
      alerts.push(this.createAlert(
        'high_response_time',
        'critical',
        metric.endpoint,
        `Response time ${metric.responseTime}ms exceeds critical threshold`,
        metric.responseTime,
        this.thresholds.responseTime.critical
      ));
    } else if (metric.responseTime > this.thresholds.responseTime.warning) {
      alerts.push(this.createAlert(
        'high_response_time',
        'medium',
        metric.endpoint,
        `Response time ${metric.responseTime}ms exceeds warning threshold`,
        metric.responseTime,
        this.thresholds.responseTime.warning
      ));
    }

    // High retry rate alert
    if (metric.retryAttempts > 0) {
      const recentMetrics = this.metrics
        .filter(m => m.endpoint === metric.endpoint)
        .slice(-10);

      const avgRetries = recentMetrics.reduce((sum, m) => sum + m.retryAttempts, 0) / recentMetrics.length;
      const retryRate = (recentMetrics.filter(m => m.retryAttempts > 0).length / recentMetrics.length) * 100;

      if (retryRate > this.thresholds.retryRate.critical) {
        alerts.push(this.createAlert(
          'high_retry_rate',
          'critical',
          metric.endpoint,
          `Retry rate ${retryRate.toFixed(1)}% exceeds critical threshold`,
          retryRate,
          this.thresholds.retryRate.critical
        ));
      }
    }

    // Add alerts and notify listeners
    alerts.forEach(alert => {
      this.alerts.push(alert);
      this.listeners.forEach(listener => listener(alert));
    });

    // Keep only recent alerts
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    this.alerts = this.alerts.filter(alert => alert.timestamp >= oneHourAgo);
  }

  private createAlert(
    type: PerformanceAlert['type'],
    severity: PerformanceAlert['severity'],
    endpoint: string,
    message: string,
    value: number,
    threshold: number
  ): PerformanceAlert {
    return {
      id: this.generateId(),
      timestamp: new Date(),
      type,
      severity,
      endpoint,
      message,
      value,
      threshold
    };
  }

  private calculatePercentile(sortedArray: number[], percentile: number): number {
    if (sortedArray.length === 0) return 0;

    const index = (percentile / 100) * (sortedArray.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);

    if (lower === upper) {
      return sortedArray[lower];
    }

    return sortedArray[lower] * (upper - index) + sortedArray[upper] * (index - lower);
  }

  private calculateTrend(first: number, second: number, threshold: number, inverse = false): 'improving' | 'degrading' | 'stable' {
    const diff = second - first;
    const percentChange = Math.abs(diff) / first * 100;

    if (percentChange < threshold) return 'stable';

    if (inverse) {
      return diff > 0 ? 'degrading' : 'improving';
    } else {
      return diff > 0 ? 'degrading' : 'improving';
    }
  }

  private convertToCSV(metrics: ApiPerformanceMetric[]): string {
    const headers = [
      'timestamp', 'endpoint', 'method', 'responseTime', 'statusCode',
      'success', 'retryAttempts', 'totalTime', 'error'
    ];

    const rows = metrics.map(metric => [
      metric.timestamp.toISOString(),
      metric.endpoint,
      metric.method,
      metric.responseTime.toString(),
      metric.statusCode.toString(),
      metric.success.toString(),
      metric.retryAttempts.toString(),
      metric.totalTime.toString(),
      metric.error || ''
    ]);

    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  private generateId(): string {
    return `perf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const apiPerformanceMonitor = new ApiPerformanceMonitor();