export interface PerformanceMetric {
  platform: 'web' | 'ios' | 'backend';
  metricType: string; // 'timing', 'resource', 'user-experience', 'system'
  metricName: string;
  value: number;
  unit?: string;
  metadata?: any;
  userId?: string;
  sessionId?: string;
}

export interface PerformanceAlert {
  id: string;
  platform: string;
  metricType: string;
  metricName: string;
  thresholdValue: number;
  actualValue: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  status: 'active' | 'resolved';
  createdAt: Date;
  resolvedAt?: Date;
}

export interface PerformanceReport {
  metrics: any[];
  alerts: any[];
  baselines: any[];
  generatedAt: Date;
}