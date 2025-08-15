import { Pool } from 'pg';
import { createClient } from 'redis';
import { logger } from '../utils/logger';
import { FeedbackData, FeedbackAnalysis, SentimentScore } from '../types/feedback';

export class FeedbackService {
  private db: Pool;
  private redis: any;

  constructor() {
    this.db = new Pool({
      connectionString: process.env.DATABASE_URL
    });
    
    this.redis = createClient({
      url: process.env.REDIS_URL
    });
    
    this.redis.connect();
    this.initializeDatabase();
  }

  private async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS feedback (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id VARCHAR(255),
          session_id VARCHAR(255),
          platform VARCHAR(20) NOT NULL,
          feedback_type VARCHAR(50) NOT NULL,
          category VARCHAR(100),
          rating INTEGER,
          title VARCHAR(500),
          description TEXT,
          metadata JSONB,
          sentiment_score NUMERIC,
          sentiment_label VARCHAR(20),
          status VARCHAR(20) DEFAULT 'new',
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS feedback_responses (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          feedback_id UUID REFERENCES feedback(id) ON DELETE CASCADE,
          responder_id VARCHAR(255),
          response_text TEXT NOT NULL,
          response_type VARCHAR(50) DEFAULT 'reply',
          created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS feedback_tags (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          feedback_id UUID REFERENCES feedback(id) ON DELETE CASCADE,
          tag VARCHAR(100) NOT NULL,
          confidence NUMERIC DEFAULT 1.0,
          created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_feedback_platform ON feedback(platform);
        CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
        CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);
        CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);
        CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
      `);
      
      logger.info('Feedback database initialized');
    } catch (error) {
      logger.error('Failed to initialize feedback database:', error);
    }
  }

  async submitFeedback(feedbackData: FeedbackData): Promise<string> {
    try {
      // Analyze sentiment
      const sentiment = await this.analyzeSentiment(feedbackData.description || feedbackData.title || '');
      
      // Extract tags
      const tags = await this.extractTags(feedbackData);

      const result = await this.db.query(`
        INSERT INTO feedback (
          user_id, session_id, platform, feedback_type, category, 
          rating, title, description, metadata, sentiment_score, sentiment_label
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
      `, [
        feedbackData.userId,
        feedbackData.sessionId,
        feedbackData.platform,
        feedbackData.feedbackType,
        feedbackData.category,
        feedbackData.rating,
        feedbackData.title,
        feedbackData.description,
        JSON.stringify(feedbackData.metadata),
        sentiment.score,
        sentiment.label
      ]);

      const feedbackId = result.rows[0].id;

      // Add tags
      for (const tag of tags) {
        await this.db.query(`
          INSERT INTO feedback_tags (feedback_id, tag, confidence)
          VALUES ($1, $2, $3)
        `, [feedbackId, tag.tag, tag.confidence]);
      }

      // Update real-time feedback metrics
      await this.updateFeedbackMetrics(feedbackData.platform, feedbackData.feedbackType, sentiment.label);

      logger.info(`Feedback submitted: ${feedbackId} from ${feedbackData.platform}`);
      return feedbackId;
    } catch (error) {
      logger.error('Failed to submit feedback:', error);
      throw error;
    }
  }

  private async analyzeSentiment(text: string): Promise<SentimentScore> {
    try {
      // Simple rule-based sentiment analysis
      // In production, you might use a more sophisticated NLP service
      const positiveWords = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'awesome', 'fantastic'];
      const negativeWords = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'worst', 'broken', 'useless'];
      
      const words = text.toLowerCase().split(/\s+/);
      let positiveCount = 0;
      let negativeCount = 0;

      for (const word of words) {
        if (positiveWords.includes(word)) positiveCount++;
        if (negativeWords.includes(word)) negativeCount++;
      }

      const totalSentimentWords = positiveCount + negativeCount;
      if (totalSentimentWords === 0) {
        return { score: 0, label: 'neutral' };
      }

      const score = (positiveCount - negativeCount) / totalSentimentWords;
      let label = 'neutral';
      
      if (score > 0.2) label = 'positive';
      else if (score < -0.2) label = 'negative';

      return { score, label };
    } catch (error) {
      logger.error('Failed to analyze sentiment:', error);
      return { score: 0, label: 'neutral' };
    }
  }

  private async extractTags(feedbackData: FeedbackData): Promise<Array<{tag: string, confidence: number}>> {
    try {
      const tags: Array<{tag: string, confidence: number}> = [];
      const text = `${feedbackData.title || ''} ${feedbackData.description || ''}`.toLowerCase();

      // Feature-based tags
      const featureTags = {
        'upload': ['upload', 'file', 'document'],
        'flashcard': ['card', 'flashcard', 'study', 'review'],
        'search': ['search', 'find', 'query'],
        'performance': ['slow', 'fast', 'speed', 'performance', 'lag'],
        'ui': ['interface', 'design', 'layout', 'button', 'menu'],
        'mobile': ['mobile', 'phone', 'ios', 'android', 'touch'],
        'bug': ['bug', 'error', 'crash', 'broken', 'issue'],
        'feature-request': ['feature', 'request', 'suggestion', 'would like', 'could you']
      };

      for (const [tag, keywords] of Object.entries(featureTags)) {
        const matches = keywords.filter(keyword => text.includes(keyword));
        if (matches.length > 0) {
          tags.push({
            tag,
            confidence: Math.min(matches.length / keywords.length, 1.0)
          });
        }
      }

      // Rating-based tags
      if (feedbackData.rating !== undefined) {
        if (feedbackData.rating >= 4) {
          tags.push({ tag: 'high-satisfaction', confidence: 1.0 });
        } else if (feedbackData.rating <= 2) {
          tags.push({ tag: 'low-satisfaction', confidence: 1.0 });
        }
      }

      return tags;
    } catch (error) {
      logger.error('Failed to extract tags:', error);
      return [];
    }
  }

  private async updateFeedbackMetrics(platform: string, feedbackType: string, sentiment: string): Promise<void> {
    try {
      const key = `feedback_metrics:${platform}`;
      await this.redis.hincrby(key, `${feedbackType}_count`, 1);
      await this.redis.hincrby(key, `${sentiment}_count`, 1);
      await this.redis.expire(key, 86400); // 24 hours
    } catch (error) {
      logger.error('Failed to update feedback metrics:', error);
    }
  }

  async getFeedbackAnalysis(platform?: string, startDate?: Date, endDate?: Date): Promise<FeedbackAnalysis> {
    try {
      const whereClause = [];
      const params = [];
      let paramIndex = 1;

      if (platform) {
        whereClause.push(`platform = $${paramIndex++}`);
        params.push(platform);
      }

      if (startDate) {
        whereClause.push(`created_at >= $${paramIndex++}`);
        params.push(startDate);
      }

      if (endDate) {
        whereClause.push(`created_at <= $${paramIndex++}`);
        params.push(endDate);
      }

      const whereString = whereClause.length > 0 ? `WHERE ${whereClause.join(' AND ')}` : '';

      const [overallStats, sentimentStats, categoryStats, ratingStats, tagStats] = await Promise.all([
        this.db.query(`
          SELECT 
            platform,
            COUNT(*) as total_feedback,
            AVG(rating) as avg_rating,
            COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_count
          FROM feedback 
          ${whereString}
          GROUP BY platform
        `, params),

        this.db.query(`
          SELECT 
            platform,
            sentiment_label,
            COUNT(*) as count,
            AVG(sentiment_score) as avg_score
          FROM feedback 
          ${whereString}
          GROUP BY platform, sentiment_label
        `, params),

        this.db.query(`
          SELECT 
            platform,
            category,
            COUNT(*) as count,
            AVG(rating) as avg_rating
          FROM feedback 
          ${whereString}
          GROUP BY platform, category
          ORDER BY count DESC
        `, params),

        this.db.query(`
          SELECT 
            platform,
            rating,
            COUNT(*) as count
          FROM feedback 
          ${whereString}
          GROUP BY platform, rating
          ORDER BY rating
        `, params),

        this.db.query(`
          SELECT 
            f.platform,
            ft.tag,
            COUNT(*) as count,
            AVG(ft.confidence) as avg_confidence
          FROM feedback f
          JOIN feedback_tags ft ON f.id = ft.feedback_id
          ${whereString}
          GROUP BY f.platform, ft.tag
          ORDER BY count DESC
          LIMIT 20
        `, params)
      ]);

      return {
        overall: overallStats.rows,
        sentiment: sentimentStats.rows,
        categories: categoryStats.rows,
        ratings: ratingStats.rows,
        tags: tagStats.rows
      };
    } catch (error) {
      logger.error('Failed to get feedback analysis:', error);
      throw error;
    }
  }

  async getFeedbackList(filters: any = {}): Promise<any[]> {
    try {
      const whereClause = [];
      const params = [];
      let paramIndex = 1;

      if (filters.platform) {
        whereClause.push(`platform = $${paramIndex++}`);
        params.push(filters.platform);
      }

      if (filters.feedbackType) {
        whereClause.push(`feedback_type = $${paramIndex++}`);
        params.push(filters.feedbackType);
      }

      if (filters.status) {
        whereClause.push(`status = $${paramIndex++}`);
        params.push(filters.status);
      }

      if (filters.sentiment) {
        whereClause.push(`sentiment_label = $${paramIndex++}`);
        params.push(filters.sentiment);
      }

      if (filters.minRating) {
        whereClause.push(`rating >= $${paramIndex++}`);
        params.push(filters.minRating);
      }

      if (filters.maxRating) {
        whereClause.push(`rating <= $${paramIndex++}`);
        params.push(filters.maxRating);
      }

      const whereString = whereClause.length > 0 ? `WHERE ${whereClause.join(' AND ')}` : '';
      const limit = filters.limit || 50;
      const offset = filters.offset || 0;

      const result = await this.db.query(`
        SELECT 
          f.*,
          ARRAY_AGG(ft.tag) as tags
        FROM feedback f
        LEFT JOIN feedback_tags ft ON f.id = ft.feedback_id
        ${whereString}
        GROUP BY f.id
        ORDER BY f.created_at DESC
        LIMIT $${paramIndex++} OFFSET $${paramIndex++}
      `, [...params, limit, offset]);

      return result.rows;
    } catch (error) {
      logger.error('Failed to get feedback list:', error);
      throw error;
    }
  }

  async updateFeedbackStatus(feedbackId: string, status: string, responderId?: string): Promise<void> {
    try {
      await this.db.query(`
        UPDATE feedback 
        SET status = $1, updated_at = NOW()
        WHERE id = $2
      `, [status, feedbackId]);

      logger.info(`Feedback status updated: ${feedbackId} -> ${status}`);
    } catch (error) {
      logger.error('Failed to update feedback status:', error);
      throw error;
    }
  }

  async addFeedbackResponse(feedbackId: string, responseText: string, responderId: string, responseType: string = 'reply'): Promise<void> {
    try {
      await this.db.query(`
        INSERT INTO feedback_responses (feedback_id, responder_id, response_text, response_type)
        VALUES ($1, $2, $3, $4)
      `, [feedbackId, responderId, responseText, responseType]);

      // Update feedback status to 'responded' if it was 'new'
      await this.db.query(`
        UPDATE feedback 
        SET status = CASE WHEN status = 'new' THEN 'responded' ELSE status END,
            updated_at = NOW()
        WHERE id = $1
      `, [feedbackId]);

      logger.info(`Response added to feedback: ${feedbackId}`);
    } catch (error) {
      logger.error('Failed to add feedback response:', error);
      throw error;
    }
  }
}