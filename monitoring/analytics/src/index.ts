import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { createPrometheusMetrics } from './metrics/prometheus';
import { initializeTracing } from './tracing/jaeger';
import { AnalyticsService } from './services/AnalyticsService';
import { ABTestingService } from './services/ABTestingService';
import { FeedbackService } from './services/FeedbackService';
import { PerformanceMonitor } from './services/PerformanceMonitor';
import { logger } from './utils/logger';
import { analyticsRoutes } from './routes/analytics';
import { abTestingRoutes } from './routes/abTesting';
import { feedbackRoutes } from './routes/feedback';
import { performanceRoutes } from './routes/performance';

const app = express();
const PORT = process.env.PORT || 8080;

// Initialize tracing
initializeTracing();

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Prometheus metrics
const metrics = createPrometheusMetrics();
app.use('/metrics', metrics.metricsHandler);

// Initialize services
const analyticsService = new AnalyticsService();
const abTestingService = new ABTestingService();
const feedbackService = new FeedbackService();
const performanceMonitor = new PerformanceMonitor();

// Routes
app.use('/api/analytics', analyticsRoutes(analyticsService));
app.use('/api/ab-testing', abTestingRoutes(abTestingService));
app.use('/api/feedback', feedbackRoutes(feedbackService));
app.use('/api/performance', performanceRoutes(performanceMonitor));

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

// Error handling
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// Start server
app.listen(PORT, () => {
  logger.info(`Analytics service started on port ${PORT}`);
});

export default app;