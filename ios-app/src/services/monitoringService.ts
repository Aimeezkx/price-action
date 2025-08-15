import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import DeviceInfo from 'react-native-device-info';

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
  private metricsBuffer: PerformanceMetric[] = [];
  private eventsBuffer: AnalyticsEvent[] = [];
  private flushInterval: number = 30000; // 30 seconds
  private isOnline: boolean = true;

  constructor() {
    this.analyticsUrl = __DEV__ 
      ? 'http://localhost:8080/api' 
      : 'https://analytics.documentlearning.app/api';
    this.sessionId = this.generateSessionId();
    this.initializeSession();
    this.setupPeriodicFlush();
    this.setupNetworkListener();
  }

  private generateSessionId(): string {
    return `ios_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async initializeSession(): Promise<void> {
    try {
      const deviceInfo = await this.getDeviceInfo();
      
      await this.startSession({
        sessionId: this.sessionId,
        userId: this.userId,
        platform: 'ios',
        deviceInfo
      });
    } catch (error) {
      console.error('Failed to initialize monitoring session:', error);
    }
  }

  private async getDeviceInfo(): Promise<any> {
    try {
      const [
        deviceId,
        deviceName,
        systemVersion,
        appVersion,
        buildNumber,
        deviceType,
        isTablet
      ] = await Promise.all([
        DeviceInfo.getUniqueId(),
        DeviceInfo.getDeviceName(),
        DeviceInfo.getSystemVersion(),
        DeviceInfo.getVersion(),
        DeviceInfo.getBuildNumber(),
        DeviceInfo.getDeviceType(),
        DeviceInfo.isTablet()
      ]);

      return {
        deviceId,
        deviceName,
        systemVersion,
        appVersion,
        buildNumber,
        deviceType: isTablet ? 'tablet' : deviceType,
        platform: Platform.OS,
        platformVersion: Platform.Version
      };
    } catch (error) {
      console.error('Failed to get device info:', error);
      return {
        platform: Platform.OS,
        platformVersion: Platform.Version
      };
    }
  }

  private async startSession(sessionData: any): Promise<void> {
    try {
      if (!this.isOnline) {
        await this.storeOfflineData('session', sessionData);
        return;
      }

      const response = await fetch(`${this.analyticsUrl}/analytics/sessions/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to start analytics session:', error);
      await this.storeOfflineData('session', sessionData);
    }
  }

  private setupPeriodicFlush(): void {
    setInterval(() => {
      this.flushData();
    }, this.flushInterval);
  }

  private setupNetworkListener(): void {
    // In a real implementation, you'd use @react-native-netinfo/netinfo
    // For now, we'll assume online status
    this.isOnline = true;
  }

  private async storeOfflineData(type: string, data: any): Promise<void> {
    try {
      const key = `monitoring_${type}_${Date.now()}`;
      await AsyncStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.error('Failed to store offline data:', error);
    }
  }

  private async syncOfflineData(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const monitoringKeys = keys.filter(key => key.startsWith('monitoring_'));

      for (const key of monitoringKeys) {
        try {
          const data = await AsyncStorage.getItem(key);
          if (data) {
            const parsedData = JSON.parse(data);
            
            if (key.includes('_event_')) {
              await this.sendEvent(parsedData);
            } else if (key.includes('_metric_')) {
              await this.sendMetric(parsedData);
            } else if (key.includes('_session_')) {
              await this.startSession(parsedData);
            }
            
            await AsyncStorage.removeItem(key);
          }
        } catch (error) {
          console.error(`Failed to sync offline data for key ${key}:`, error);
        }
      }
    } catch (error) {
      console.error('Failed to sync offline data:', error);
    }
  }

  setUserId(userId: string): void {
    this.userId = userId;
  }

  async trackEvent(eventType: string, eventData?: any): Promise<void> {
    const event: AnalyticsEvent = {
      sessionId: this.sessionId,
      userId: this.userId,
      eventType,
      eventData
    };

    if (this.isOnline) {
      this.eventsBuffer.push(event);
      
      if (this.eventsBuffer.length >= 10) {
        await this.flushEvents();
      }
    } else {
      await this.storeOfflineData('event', event);
    }
  }

  private async sendEvent(event: AnalyticsEvent): Promise<void> {
    try {
      const response = await fetch(`${this.analyticsUrl}/analytics/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...event,
          platform: 'ios'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to send event:', error);
      throw error;
    }
  }

  recordMetric(metric: PerformanceMetric): void {
    const enhancedMetric = {
      ...metric,
      metadata: {
        ...metric.metadata,
        sessionId: this.sessionId,
        userId: this.userId
      }
    };

    if (this.isOnline) {
      this.metricsBuffer.push(enhancedMetric);
      
      if (this.metricsBuffer.length >= 20) {
        this.flushMetrics();
      }
    } else {
      this.storeOfflineData('metric', enhancedMetric);
    }
  }

  private async sendMetric(metric: PerformanceMetric): Promise<void> {
    try {
      const response = await fetch(`${this.analyticsUrl}/performance/metrics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: 'ios',
          sessionId: this.sessionId,
          userId: this.userId,
          ...metric
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to send metric:', error);
      throw error;
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
          platform: 'ios',
          ...feedback
        })
      });

      if (response.ok) {
        const result = await response.json();
        return result.feedbackId || null;
      }
      return null;
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      return null;
    }
  }

  async getABTestAssignment(testName: string): Promise<any> {
    try {
      const params = new URLSearchParams({
        sessionId: this.sessionId,
        platform: 'ios'
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

  private async flushData(): Promise<void> {
    if (this.isOnline) {
      await Promise.all([
        this.flushEvents(),
        this.flushMetrics(),
        this.syncOfflineData()
      ]);
    }
  }

  private async flushEvents(): Promise<void> {
    if (this.eventsBuffer.length === 0) return;

    const events = this.eventsBuffer.splice(0);
    
    try {
      for (const event of events) {
        await this.sendEvent(event);
      }
    } catch (error) {
      console.error('Failed to flush events:', error);
      // Put events back in buffer for retry
      this.eventsBuffer.unshift(...events);
    }
  }

  private async flushMetrics(): Promise<void> {
    if (this.metricsBuffer.length === 0) return;

    const metrics = this.metricsBuffer.splice(0);
    
    try {
      const response = await fetch(`${this.analyticsUrl}/performance/metrics/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metrics: metrics.map(metric => ({
            platform: 'ios',
            sessionId: this.sessionId,
            userId: this.userId,
            ...metric
          }))
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to flush metrics:', error);
      // Put metrics back in buffer for retry
      this.metricsBuffer.unshift(...metrics);
    }
  }

  // iOS-specific performance tracking
  trackScreenTransition(fromScreen: string, toScreen: string, duration: number): void {
    this.recordMetric({
      metricType: 'timing',
      metricName: 'screen_transition_time',
      value: duration,
      unit: 'ms',
      metadata: {
        fromScreen,
        toScreen
      }
    });
  }

  trackAppLaunch(duration: number): void {
    this.recordMetric({
      metricType: 'timing',
      metricName: 'app_launch_time',
      value: duration,
      unit: 'ms'
    });
  }

  trackMemoryUsage(usage: number): void {
    this.recordMetric({
      metricType: 'resource',
      metricName: 'memory_usage',
      value: usage,
      unit: 'bytes'
    });
  }

  trackBatteryDrain(drainRate: number): void {
    this.recordMetric({
      metricType: 'resource',
      metricName: 'battery_drain_rate',
      value: drainRate,
      unit: 'percent_per_hour'
    });
  }

  trackCrash(error: Error, context?: any): void {
    this.trackEvent('app_crash', {
      error: error.message,
      stack: error.stack,
      context
    });
  }

  async endSession(): Promise<void> {
    try {
      await this.flushData();
      
      if (this.isOnline) {
        await fetch(`${this.analyticsUrl}/analytics/sessions/${this.sessionId}/end`, {
          method: 'POST'
        });
      }
    } catch (error) {
      console.error('Failed to end session:', error);
    }
  }
}

// Create singleton instance
export const monitoring = new MonitoringService();

// Export types for use in components
export type { AnalyticsEvent, PerformanceMetric, FeedbackData };