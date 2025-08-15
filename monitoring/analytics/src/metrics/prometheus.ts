import { register, collectDefaultMetrics, Counter, Histogram, Gauge } from 'prom-client';

// Collect default metrics
collectDefaultMetrics();

// Custom metrics
const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route'],
  buckets: [0.1, 0.5, 1, 2, 5]
});

const analyticsEventsTotal = new Counter({
  name: 'analytics_events_total',
  help: 'Total number of analytics events processed',
  labelNames: ['platform', 'event_type']
});

const abTestAssignmentsTotal = new Counter({
  name: 'ab_test_assignments_total',
  help: 'Total number of A/B test assignments',
  labelNames: ['test_name', 'variant_name', 'platform']
});

const feedbackSubmissionsTotal = new Counter({
  name: 'feedback_submissions_total',
  help: 'Total number of feedback submissions',
  labelNames: ['platform', 'feedback_type', 'sentiment']
});

const performanceAlertsTotal = new Counter({
  name: 'performance_alerts_total',
  help: 'Total number of performance alerts',
  labelNames: ['platform', 'severity']
});

const activeSessionsGauge = new Gauge({
  name: 'active_sessions_total',
  help: 'Number of active user sessions',
  labelNames: ['platform']
});

export function createPrometheusMetrics() {
  return {
    httpRequestsTotal,
    httpRequestDuration,
    analyticsEventsTotal,
    abTestAssignmentsTotal,
    feedbackSubmissionsTotal,
    performanceAlertsTotal,
    activeSessionsGauge,
    metricsHandler: (req: any, res: any) => {
      res.set('Content-Type', register.contentType);
      res.end(register.metrics());
    }
  };
}