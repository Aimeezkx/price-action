import { Router } from 'express';
import { ABTestingService } from '../services/ABTestingService';
import { logger } from '../utils/logger';
import Joi from 'joi';

const testSchema = Joi.object({
  name: Joi.string().required(),
  description: Joi.string().optional(),
  platform: Joi.string().valid('web', 'ios', 'both').required(),
  trafficAllocation: Joi.number().min(0).max(1).default(1.0),
  startDate: Joi.date().optional(),
  endDate: Joi.date().optional(),
  variants: Joi.array().items(
    Joi.object({
      name: Joi.string().required(),
      description: Joi.string().optional(),
      trafficWeight: Joi.number().min(0).max(1).required(),
      config: Joi.object().required(),
      isControl: Joi.boolean().default(false)
    })
  ).min(2).required()
});

const eventSchema = Joi.object({
  testName: Joi.string().required(),
  eventType: Joi.string().required(),
  userId: Joi.string().optional(),
  sessionId: Joi.string().optional(),
  eventData: Joi.object().optional()
});

export function abTestingRoutes(abTestingService: ABTestingService): Router {
  const router = Router();

  // Create A/B test
  router.post('/tests', async (req, res) => {
    try {
      const { error, value } = testSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      // Validate traffic weights sum to 1.0
      const totalWeight = value.variants.reduce((sum: number, v: any) => sum + v.trafficWeight, 0);
      if (Math.abs(totalWeight - 1.0) > 0.001) {
        return res.status(400).json({ error: 'Variant traffic weights must sum to 1.0' });
      }

      const testId = await abTestingService.createTest(value);
      res.status(201).json({ success: true, testId });
    } catch (error) {
      logger.error('Failed to create A/B test:', error);
      res.status(500).json({ error: 'Failed to create A/B test' });
    }
  });

  // Get A/B test assignment
  router.get('/assignment/:testName', async (req, res) => {
    try {
      const { testName } = req.params;
      const { userId, sessionId, platform } = req.query;

      const assignment = await abTestingService.getAssignment(
        testName,
        userId as string,
        sessionId as string,
        platform as string
      );

      if (assignment) {
        res.json(assignment);
      } else {
        res.status(404).json({ error: 'No assignment available' });
      }
    } catch (error) {
      logger.error('Failed to get A/B test assignment:', error);
      res.status(500).json({ error: 'Failed to get assignment' });
    }
  });

  // Track A/B test event
  router.post('/events', async (req, res) => {
    try {
      const { error, value } = eventSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      await abTestingService.trackEvent(
        value.testName,
        value.eventType,
        value.userId,
        value.sessionId,
        value.eventData
      );

      res.status(201).json({ success: true });
    } catch (error) {
      logger.error('Failed to track A/B test event:', error);
      res.status(500).json({ error: 'Failed to track event' });
    }
  });

  // Get A/B test results
  router.get('/tests/:testName/results', async (req, res) => {
    try {
      const { testName } = req.params;
      const results = await abTestingService.getTestResults(testName);
      res.json(results);
    } catch (error) {
      logger.error('Failed to get A/B test results:', error);
      res.status(500).json({ error: 'Failed to get test results' });
    }
  });

  // Update test status
  router.patch('/tests/:testName/status', async (req, res) => {
    try {
      const { testName } = req.params;
      const { status } = req.body;

      if (!['draft', 'active', 'paused', 'completed'].includes(status)) {
        return res.status(400).json({ error: 'Invalid status' });
      }

      await abTestingService.updateTestStatus(testName, status);
      res.json({ success: true });
    } catch (error) {
      logger.error('Failed to update test status:', error);
      res.status(500).json({ error: 'Failed to update test status' });
    }
  });

  // Get active tests
  router.get('/tests/active', async (req, res) => {
    try {
      const { platform } = req.query;
      const tests = await abTestingService.getActiveTests(platform as string);
      res.json(tests);
    } catch (error) {
      logger.error('Failed to get active tests:', error);
      res.status(500).json({ error: 'Failed to get active tests' });
    }
  });

  return router;
}