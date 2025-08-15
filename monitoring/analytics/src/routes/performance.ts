import { Router } from 'express';
import { PerformanceMonitor } from '../services/PerformanceMonitor';
import { logger } from '../utils/logger';
import Joi from 'joi';

const metricSchema = Joi.object({
  platform: Joi.string().valid('web', 'ios', 'backend').required(),
  metricType: Joi.string().required(),
  metricName: Joi.string().required(),
  value: Joi.number().required(),
  unit: Joi.string().optional(),
  metadata: Joi.object().optional(),
  userId: Joi.string().optional(),
  sessionId: Joi.string().optional()
});

const batchMetricsSchema = Joi.object({
  metrics: Joi.array().items(metricSchema).required()
});

export function performanceRoutes(performanceMonitor: PerformanceMonitor): Router {
  const router = Router();

  // Record single performance metric
  router.post('/metrics', async (req, res) => {
    try {
      const { error, value } = metricSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      await performanceMonitor.recordMetric(value);
      res.status(201).json({ success: true });
    } catch (error) {
      logger.error('Failed to record performance metric:', error);
      res.status(500).json({ error: 'Failed to record metric' });
    }
  });

  // Record batch of performance metrics
  router.post('/metrics/batch', async (req, res) => {
    try {
      const { error, value } = batchMetricsSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      const promises = value.metrics.map((metric: any) => 
        performanceMonitor.recordMetric(metric)
      );
      
      await Promise.all(promises);
      res.status(201).json({ success: true, count: value.metrics.length });
    } catch (error) {
      logger.error('Failed to record performance metrics batch:', error);
      res.status(500).json({ error: 'Failed to record metrics' });
    }
  });

  // Get performance report
  router.get('/report', async (req, res) => {
    try {
      const { platform, startDate, endDate } = req.query;
      
      const start = startDate ? new Date(startDate as string) : undefined;
      const end = endDate ? new Date(endDate as string) : undefined;

      const report = await performanceMonitor.getPerformanceReport(
        platform as string,
        start,
        end
      );

      res.json(report);
    } catch (error) {
      logger.error('Failed to get performance report:', error);
      res.status(500).json({ error: 'Failed to get performance report' });
    }
  });

  // Get real-time metrics
  router.get('/realtime/:platform', async (req, res) => {
    try {
      const { platform } = req.params;
      const { metricType } = req.query;
      
      const metrics = await performanceMonitor.getRealTimeMetrics(
        platform,
        metricType as string
      );
      
      res.json(metrics);
    } catch (error) {
      logger.error('Failed to get real-time metrics:', error);
      res.status(500).json({ error: 'Failed to get real-time metrics' });
    }
  });

  // Get active alerts
  router.get('/alerts', async (req, res) => {
    try {
      const { platform } = req.query;
      const alerts = await performanceMonitor.getActiveAlerts(platform as string);
      res.json(alerts);
    } catch (error) {
      logger.error('Failed to get active alerts:', error);
      res.status(500).json({ error: 'Failed to get alerts' });
    }
  });

  // Resolve alert
  router.post('/alerts/:alertId/resolve', async (req, res) => {
    try {
      const { alertId } = req.params;
      await performanceMonitor.resolveAlert(alertId);
      res.json({ success: true });
    } catch (error) {
      logger.error('Failed to resolve alert:', error);
      res.status(500).json({ error: 'Failed to resolve alert' });
    }
  });

  // Update baselines
  router.post('/baselines/update', async (req, res) => {
    try {
      await performanceMonitor.updateBaselines();
      res.json({ success: true });
    } catch (error) {
      logger.error('Failed to update baselines:', error);
      res.status(500).json({ error: 'Failed to update baselines' });
    }
  });

  return router;
}