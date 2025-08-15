interface AnalyticsEvent {
  eventType: string;
  eventData?: any;
  userId?: string;
  sessionId: string;
}

interface PerformanceMetric {
  metricType: string;
  metricName: string;
  value: number;
  unit?: string;
  metadata?: any;
}

interface FeedbackData {
  feedbackType: 'bug' | 'feature-request' | 'general' | 'rating';
  category?: string;
  rating?: number;
  title?: string;
  description?: string;
  metadata?: any;
}

class MonitoringService {
  private analyticsUrl: string;
  private sessionId: string;
  private userId?: string;
  private performanceObserver?: PerformanceObserver;
  private metricsBuffer: PerformanceMetric[] = [];
  private flushInterval: number = 30000; // 30 seconds

  constructor() {
    this.analyticsUrl = import.meta.env.VITE_ANALYTICS_URL || 'http://localhost:8080/api';
    this.sessionId = this.generateSessionId();
    this.initializePerformanceMonitoring();
    this.startSession();
    this.setupPeriodicFlush();
  }

  private generateSessionId(): string {
    return `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async startSession(): Promise<void> {
    try {
      await fetch(`${this.analyticsUrl}/analytics/sessions/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: this.sessionId,
          userId: this.userId,
          platform: 'web',
          deviceInfo: {
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`,
            deviceType: this.getDeviceType(),
            appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0'
          }
        })
      });
    } catch (error) {
      console.error('Failed to start analytics session:', error);
    }
  }

  private getDeviceType(): string {
    const userAgent = navigator.userAgent.toLowerCase();
    if (/mobile|android|iphone|ipad|phone/i.test(userAgent)) {
      return 'mobile';
    } else if (/tablet|ipad/i.test(userAgent)) {
      return 'tablet';
    }
    return 'desktop';
  }

  private initializePerformanceMonitoring(): void {
    // Web Vitals monitoring
    if ('PerformanceObserver' in window) {
      // Largest Contentful Paint
      this.observePerformanceEntry('largest-contentful-paint', (entries) => {
        const lcp = entries[entries.length - 1];
        this.recordMetric({
          metricType: 'user-experience',
          metricName: 'largest_contentful_paint',
          value: lcp.startTime,
          unit: 'ms'
        });
      });

      // First Input Delay
      this.observePerformanceEntry('first-input', (entries) => {
        const fid = entries[0];
        this.recordMetric({
          metricType: 'user-experience',
          metricName: 'first_input_delay',
          value: fid.processingStart - fid.startTime,
          unit: 'ms'
        });
      });

      // Cumulative Layout Shift
      this.observePerformanceEntry('layout-shift', (entries) => {
        let clsValue = 0;
        for (const entry of entries) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        }
        this.recordMetric({
          metricType: 'user-experience',
          metricName: 'cumulative_layout_shift',
          value: clsValue,
          unit: 'score'
        });
      });
    }

    // Navigation timing
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          this.recordMetric({
            metricType: 'timing',
            metricName: 'page_load_time',
            value: navigation.loadEventEnd - navigation.fetchStart,
            unit: 'ms'
          });

          this.recordMetric({
            metricType: 'timing',
            metricName: 'first_contentful_paint',
            value: navigation.domContentLoadedEventEnd - navigation.fetchStart,
            unit: 'ms'
          });
        }
      }, 0);
    });

    // Memory usage monitoring
    if ('memory' in performance) {
      setInterval(() => {
        const memory = (performance as any).memory;
        this.recordMetric({
          metricType: 'resource',
          metricName: 'memory_usage',
          value: memory.usedJSHeapSize,
          unit: 'bytes',
          metadata: {
            total: memory.totalJSHeapSize,
            limit: memory.jsHeapSizeLimit
          }
        });
      }, 60000); // Every minute
    }
  }

  private observePerformanceEntry(type: string, callback: (entries: any[]) => void): void {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });
      observer.observe({ type, buffered: true });
    } catch (error) {
      console.warn(`Failed to observe ${type}:`, error);
    }
  }

  private setupPeriodicFlush(): void {
    setInterval(() => {
      this.flushMetrics();
    }, this.flushInterval);

    // Flush on page unload
    window.addEventListener('beforeunload', () => {
      this.flushMetrics();
      this.endSession();
    });
  }

  setUserId(userId: string): void {
    this.userId = userId;
  }

  async trackEvent(eventType: string, eventData?: any): Promise<void> {
    try {
      await fetch(`${this.analyticsUrl}/analytics/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: this.sessionId,
          userId: this.userId,
          platform: 'web',
          eventType,
          eventData
        })
      });
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  recordMetric(metric: PerformanceMetric): void {
    this.metricsBuffer.push({
      ...metric,
      metadata: {
        ...metric.metadata,
        sessionId: this.sessionId,
        userId: this.userId
      }
    });

    // Flush if buffer is getting large
    if (this.metricsBuffer.length >= 50) {
      this.flushMetrics();
    }
  }

  private async flushMetrics(): Promise<void> {
    if (this.metricsBuffer.length === 0) return;

    const metrics = this.metricsBuffer.splice(0);
    
    try {
      await fetch(`${this.analyticsUrl}/performance/metrics/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metrics: metrics.map(metric => ({
            platform: 'web',
            sessionId: this.sessionId,
            userId: this.userId,
            ...metric
          }))
        })
      });
    } catch (error) {
      console.error('Failed to flush metrics:', error);
      // Put metrics back in buffer for retry
      this.metricsBuffer.unshift(...metrics);
    }
  }

  async submitFeedback(feedback: FeedbackData): Promise<string | null> {
    try {
      const response = await fetch(`${this.analyticsUrl}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: this.sessionId,
          userId: this.userId,
          platform: 'web',
          ...feedback
        })
      });

      const result = await response.json();
      return result.feedbackId || null;
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      return null;
    }
  }

  async getABTestAssignment(testName: string): Promise<any> {
    try {
      const params = new URLSearchParams({
        sessionId: this.sessionId,
        platform: 'web'
      });
      
      if (this.userId) {
        params.append('userId', this.userId);
      }

      const response = await fetch(
        `${this.analyticsUrl}/ab-testing/assignment/${testName}?${params}`
      );

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Failed to get A/B test assignment:', error);
      return null;
    }
  }

  async trackABTestEvent(testName: string, eventType: string, eventData?: any): Promise<void> {
    try {
      await fetch(`${this.analyticsUrl}/ab-testing/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          testName,
          eventType,
          sessionId: this.sessionId,
          userId: this.userId,
          eventData
        })
      });
    } catch (error) {
      console.error('Failed to track A/B test event:', error);
    }
  }

  private async endSession(): Promise<void> {
    try {
      await fetch(`${this.analyticsUrl}/analytics/sessions/${this.sessionId}/end`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Failed to end session:', error);
    }
  }

  // API response time tracking
  trackAPICall(url: string, method: string, duration: number, status: number): void {
    this.recordMetric({
      metricType: 'timing',
      metricName: 'api_response_time',
      value: duration,
      unit: 'ms',
      metadata: {
        url,
        method,
        status
      }
    });
  }
}

// Create singleton instance
export const monitoring = new MonitoringService();

// Export types for use in components
export type { AnalyticsEvent, PerformanceMetric, FeedbackData };