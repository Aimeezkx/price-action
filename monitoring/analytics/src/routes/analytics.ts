import { Router } from 'express';
import { AnalyticsService } from '../services/AnalyticsService';
import { logger } from '../utils/logger';
import Joi from 'joi';

const eventSchema = Joi.object({
  userId: Joi.string().optional(),
  sessionId: Joi.string().required(),
  platform: Joi.string().valid('web', 'ios').required(),
  eventType: Joi.string().required(),
  eventData: Joi.object().optional(),
  ipAddress: Joi.string().ip().optional(),
  userAgent: Joi.string().optional()
});

const sessionSchema = Joi.object({
  sessionId: Joi.string().required(),
  userId: Joi.string().optional(),
  platform: Joi.string().valid('web', 'ios').required(),
  deviceInfo: Joi.object().optional()
});

const metricSchema = Joi.object({
  platform: Joi.string().valid('web', 'ios').required(),
  metricName: Joi.string().required(),
  metricValue: Joi.number().required(),
  metadata: Joi.object().optional()
});

export function analyticsRoutes(analyticsService: AnalyticsService): Router {
  const router = Router();

  // Track event
  router.post('/events', async (req, res) => {
    try {
      const { error, value } = eventSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      // Add IP address from request if not provided
      if (!value.ipAddress) {
        value.ipAddress = req.ip || req.connection.remoteAddress;
      }

      // Add user agent if not provided
      if (!value.userAgent) {
        value.userAgent = req.get('User-Agent');
      }

      await analyticsService.trackEvent(value);
      res.status(201).json({ success: true });
    } catch (error) {
      logger.error('Failed to track event:', error);
      res.status(500).json({ error: 'Failed to track event' });
    }
  });

  // Start session
  router.post('/sessions/start', async (req, res) => {
    try {
      const { error, value } = sessionSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      await analyticsService.startSession(value);
      res.status(201).json({ success: true });
    } catch (error) {
      logger.error('Failed to start session:', error);
      res.status(500).json({ error: 'Failed to start session' });
    }
  });

  // End session
  router.post('/sessions/:sessionId/end', async (req, res) => {
    try {
      const { sessionId } = req.params;
      await analyticsService.endSession(sessionId);
      res.json({ success: true });
    } catch (error) {
      logger.error('Failed to end session:', error);
      res.status(500).json({ error: 'Failed to end session' });
    }
  });

  // Record platform metric
  router.post('/metrics', async (req, res) => {
    try {
      const { error, value } = metricSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      await analyticsService.recordPlatformMetric(value);
      res.status(201).json({ success: true });
    } catch (error) {
      logger.error('Failed to record metric:', error);
      res.status(500).json({ error: 'Failed to record metric' });
    }
  });

  // Get analytics data
  router.get('/data', async (req, res) => {
    try {
      const { platform, startDate, endDate } = req.query;
      
      const start = startDate ? new Date(startDate as string) : undefined;
      const end = endDate ? new Date(endDate as string) : undefined;

      const analytics = await analyticsService.getAnalytics(
        platform as string,
        start,
        end
      );

      res.json(analytics);
    } catch (error) {
      logger.error('Failed to get analytics:', error);
      res.status(500).json({ error: 'Failed to get analytics' });
    }
  });

  // Get real-time metrics
  router.get('/realtime/:platform', async (req, res) => {
    try {
      const { platform } = req.params;
      const metrics = await analyticsService.getRealTimeMetrics(platform);
      res.json(metrics);
    } catch (error) {
      logger.error('Failed to get real-time metrics:', error);
      res.status(500).json({ error: 'Failed to get real-time metrics' });
    }
  });

  return router;
}