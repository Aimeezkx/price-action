import { Router } from 'express';
import { FeedbackService } from '../services/FeedbackService';
import { logger } from '../utils/logger';
import Joi from 'joi';

const feedbackSchema = Joi.object({
  userId: Joi.string().optional(),
  sessionId: Joi.string().optional(),
  platform: Joi.string().valid('web', 'ios').required(),
  feedbackType: Joi.string().valid('bug', 'feature-request', 'general', 'rating').required(),
  category: Joi.string().optional(),
  rating: Joi.number().integer().min(1).max(5).optional(),
  title: Joi.string().max(500).optional(),
  description: Joi.string().max(5000).optional(),
  metadata: Joi.object().optional()
});

const responseSchema = Joi.object({
  responseText: Joi.string().required(),
  responseType: Joi.string().valid('reply', 'resolution', 'escalation').default('reply')
});

export function feedbackRoutes(feedbackService: FeedbackService): Router {
  const router = Router();

  // Submit feedback
  router.post('/', async (req, res) => {
    try {
      const { error, value } = feedbackSchema.validate(req.body);
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      const feedbackId = await feedbackService.submitFeedback(value);
      res.status(201).json({ success: true, feedbackId });
    } catch (error) {
      logger.error('Failed to submit feedback:', error);
      res.status(500).json({ error: 'Failed to submit feedback' });
    }
  });

  // Get feedback list
  router.get('/', async (req, res) => {
    try {
      const filters = {
        platform: req.query.platform as string,
        feedbackType: req.query.feedbackType as string,
        status: req.query.status as string,
        sentiment: req.query.sentiment as string,
        minRating: req.query.minRating ? parseInt(req.query.minRating as string) : undefined,
        maxRating: req.query.maxRating ? parseInt(req.query.maxRating as string) : undefined,
        limit: req.query.limit ? parseInt(req.query.limit as string) : 50,
        offset: req.query.offset ? parseInt(req.query.offset as string) : 0
      };

      const feedback = await feedbackService.getFeedbackList(filters);
      res.json(feedback);
    } catch (error) {
      logger.error('Failed to get feedback list:', error);
      res.status(500).json({ error: 'Failed to get feedback list' });
    }
  });

  // Get feedback analysis
  router.get('/analysis', async (req, res) => {
    try {
      const { platform, startDate, endDate } = req.query;
      
      const start = startDate ? new Date(startDate as string) : undefined;
      const end = endDate ? new Date(endDate as string) : undefined;

      const analysis = await feedbackService.getFeedbackAnalysis(
        platform as string,
        start,
        end
      );

      res.json(analysis);
    } catch (error) {
      logger.error('Failed to get feedback analysis:', error);
      res.status(500).json({ error: 'Failed to get feedback analysis' });
    }
  });

  // Update feedback status
  router.patch('/:feedbackId/status', async (req, res) => {
    try {
      const { feedbackId } = req.params;
      const { status } = req.body;

      if (!['new', 'in-progress', 'responded', 'resolved', 'closed'].includes(status)) {
        return res.status(400).json({ error: 'Invalid status' });
      }

      await feedbackService.updateFeedbackStatus(feedbackId, status);
      res.json({ success: true });
    } catch (error) {
      logger.error('Failed to update feedback status:', error);
      res.status(500).json({ error: 'Failed to update feedback status' });
    }
  });

  // Add response to feedback
  router.post('/:feedbackId/responses', async (req, res) => {
    try {
      const { feedbackId } = req.params;
      const { error, value } = responseSchema.validate(req.body);
      
      if (error) {
        return res.status(400).json({ error: error.details[0].message });
      }

      const responderId = req.headers['x-responder-id'] as string || 'system';
      
      await feedbackService.addFeedbackResponse(
        feedbackId,
        value.responseText,
        responderId,
        value.responseType
      );

      res.status(201).json({ success: true });
    } catch (error) {
      logger.error('Failed to add feedback response:', error);
      res.status(500).json({ error: 'Failed to add response' });
    }
  });

  return router;
}