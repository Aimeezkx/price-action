export interface EventData {
  userId?: string;
  sessionId: string;
  platform: 'web' | 'ios';
  eventType: string;
  eventData?: any;
  ipAddress?: string;
  userAgent?: string;
}

export interface UserSession {
  sessionId: string;
  userId?: string;
  platform: 'web' | 'ios';
  deviceInfo?: {
    userAgent?: string;
    screenResolution?: string;
    deviceType?: string;
    osVersion?: string;
    appVersion?: string;
  };
}

export interface PlatformMetrics {
  platform: 'web' | 'ios';
  metricName: string;
  metricValue: number;
  metadata?: any;
}