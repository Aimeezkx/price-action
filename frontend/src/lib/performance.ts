import React from 'react';

/**
 * Frontend Performance Monitoring Service
 * Tracks page load times, component render times, and user interactions
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

interface NavigationTiming {
  pageLoadTime: number;
  domContentLoadedTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
    this.trackNavigationTiming();
  }

  private initializeObservers() {
    // Track Core Web Vitals
    if ('PerformanceObserver' in window) {
      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.recordMetric('LCP', lastEntry.startTime, {
          element: lastEntry.element?.tagName
        });
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(lcpObserver);

      // First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.recordMetric('FID', entry.processingStart - entry.startTime, {
            eventType: entry.name
          });
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
      this.observers.push(fidObserver);

      // Cumulative Layout Shift
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
        this.recordMetric('CLS', clsValue);
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(clsObserver);
    }
  }

  private trackNavigationTiming() {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        if (navigation) {
          const timing: NavigationTiming = {
            pageLoadTime: navigation.loadEventEnd - navigation.navigationStart,
            domContentLoadedTime: navigation.domContentLoadedEventEnd - navigation.navigationStart,
            firstContentfulPaint: 0,
            largestContentfulPaint: 0,
            cumulativeLayoutShift: 0
          };

          // Get paint timings
          const paintEntries = performance.getEntriesByType('paint');
          paintEntries.forEach((entry) => {
            if (entry.name === 'first-contentful-paint') {
              timing.firstContentfulPaint = entry.startTime;
            }
          });

          this.recordMetric('PageLoad', timing.pageLoadTime, timing);
        }
      }, 0);
    });
  }

  recordMetric(name: string, value: number, metadata?: Record<string, any>) {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata
    };

    this.metrics.push(metric);

    // Log performance issues
    if (this.isPerformanceIssue(name, value)) {
      console.warn(`Performance issue detected: ${name} = ${value}ms`, metadata);
    }

    // Keep only last 100 metrics to prevent memory leaks
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-100);
    }
  }

  private isPerformanceIssue(name: string, value: number): boolean {
    const thresholds: Record<string, number> = {
      'PageLoad': 2000, // 2 seconds
      'LCP': 2500, // 2.5 seconds
      'FID': 100, // 100ms
      'CLS': 0.1, // 0.1 score
      'ComponentRender': 16, // 16ms (60fps)
      'APICall': 1000 // 1 second
    };

    return value > (thresholds[name] || Infinity);
  }

  // Track component render times
  trackComponentRender(componentName: string, renderTime: number) {
    this.recordMetric('ComponentRender', renderTime, { component: componentName });
  }

  // Track API call performance
  trackAPICall(endpoint: string, duration: number, status: number) {
    this.recordMetric('APICall', duration, { 
      endpoint, 
      status,
      success: status >= 200 && status < 300
    });
  }

  // Track user interactions
  trackUserInteraction(action: string, duration?: number) {
    this.recordMetric('UserInteraction', duration || 0, { action });
  }

  // Get performance summary
  getPerformanceSummary() {
    const summary: Record<string, any> = {};
    
    this.metrics.forEach(metric => {
      if (!summary[metric.name]) {
        summary[metric.name] = {
          count: 0,
          total: 0,
          min: Infinity,
          max: -Infinity,
          avg: 0
        };
      }

      const stat = summary[metric.name];
      stat.count++;
      stat.total += metric.value;
      stat.min = Math.min(stat.min, metric.value);
      stat.max = Math.max(stat.max, metric.value);
      stat.avg = stat.total / stat.count;
    });

    return summary;
  }

  // Export metrics for analysis
  exportMetrics() {
    return {
      metrics: this.metrics,
      summary: this.getPerformanceSummary(),
      timestamp: Date.now()
    };
  }

  // Clean up observers
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.metrics = [];
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// React hook for component performance tracking
export function usePerformanceTracking(componentName: string) {
  const trackRender = (renderTime: number) => {
    performanceMonitor.trackComponentRender(componentName, renderTime);
  };

  const trackInteraction = (action: string, duration?: number) => {
    performanceMonitor.trackUserInteraction(`${componentName}:${action}`, duration);
  };

  return { trackRender, trackInteraction };
}

// Higher-order component for automatic performance tracking
export function withPerformanceTracking<T extends object>(
  WrappedComponent: React.ComponentType<T>,
  componentName: string
) {
  return function PerformanceTrackedComponent(props: T) {
    const renderStart = performance.now();
    
    React.useEffect(() => {
      const renderEnd = performance.now();
      performanceMonitor.trackComponentRender(componentName, renderEnd - renderStart);
    });

    return React.createElement(WrappedComponent, props);
  };
}