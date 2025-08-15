import { Pool } from 'pg';
import { createClient } from 'redis';
import { logger } from '../utils/logger';
import { EventData, UserSession, PlatformMetrics } from '../types/analytics';

export class AnalyticsService {
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
        CREATE TABLE IF NOT EXISTS events (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id VARCHAR(255),
          session_id VARCHAR(255) NOT NULL,
          platform VARCHAR(20) NOT NULL,
          event_type VARCHAR(100) NOT NULL,
          event_data JSONB,
          timestamp TIMESTAMP DEFAULT NOW(),
          ip_address INET,
          user_agent TEXT
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          session_id VARCHAR(255) UNIQUE NOT NULL,
          user_id VARCHAR(255),
          platform VARCHAR(20) NOT NULL,
          device_info JSONB,
          start_time TIMESTAMP DEFAULT NOW(),
          end_time TIMESTAMP,
          duration_seconds INTEGER,
          page_views INTEGER DEFAULT 0,
          actions_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS platform_metrics (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          platform VARCHAR(20) NOT NULL,
          metric_name VARCHAR(100) NOT NULL,
          metric_value NUMERIC,
          metadata JSONB,
          timestamp TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_platform ON events(platform);
        CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_sessions_platform ON user_sessions(platform);
        CREATE INDEX IF NOT EXISTS idx_metrics_platform ON platform_metrics(platform);
      `);
      
      logger.info('Analytics database initialized');
    } catch (error) {
      logger.error('Failed to initialize analytics database:', error);
    }
  }

  async trackEvent(eventData: EventData): Promise<void> {
    try {
      await this.db.query(`
        INSERT INTO events (user_id, session_id, platform, event_type, event_data, ip_address, user_agent)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [
        eventData.userId,
        eventData.sessionId,
        eventData.platform,
        eventData.eventType,
        JSON.stringify(eventData.eventData),
        eventData.ipAddress,
        eventData.userAgent
      ]);

      // Update session activity
      await this.updateSessionActivity(eventData.sessionId);

      // Cache recent events for real-time analytics
      await this.redis.lpush(
        `recent_events:${eventData.platform}`,
        JSON.stringify(eventData)
      );
      await this.redis.ltrim(`recent_events:${eventData.platform}`, 0, 999);

      logger.debug(`Event tracked: ${eventData.eventType} for platform ${eventData.platform}`);
    } catch (error) {
      logger.error('Failed to track event:', error);
      throw error;
    }
  }

  async startSession(sessionData: UserSession): Promise<void> {
    try {
      await this.db.query(`
        INSERT INTO user_sessions (session_id, user_id, platform, device_info)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (session_id) DO UPDATE SET
          start_time = NOW(),
          device_info = $4
      `, [
        sessionData.sessionId,
        sessionData.userId,
        sessionData.platform,
        JSON.stringify(sessionData.deviceInfo)
      ]);

      logger.debug(`Session started: ${sessionData.sessionId} on ${sessionData.platform}`);
    } catch (error) {
      logger.error('Failed to start session:', error);
      throw error;
    }
  }

  async endSession(sessionId: string): Promise<void> {
    try {
      await this.db.query(`
        UPDATE user_sessions 
        SET end_time = NOW(),
            duration_seconds = EXTRACT(EPOCH FROM (NOW() - start_time))
        WHERE session_id = $1
      `, [sessionId]);

      logger.debug(`Session ended: ${sessionId}`);
    } catch (error) {
      logger.error('Failed to end session:', error);
      throw error;
    }
  }

  private async updateSessionActivity(sessionId: string): Promise<void> {
    try {
      await this.db.query(`
        UPDATE user_sessions 
        SET actions_count = actions_count + 1
        WHERE session_id = $1
      `, [sessionId]);
    } catch (error) {
      logger.error('Failed to update session activity:', error);
    }
  }

  async recordPlatformMetric(metric: PlatformMetrics): Promise<void> {
    try {
      await this.db.query(`
        INSERT INTO platform_metrics (platform, metric_name, metric_value, metadata)
        VALUES ($1, $2, $3, $4)
      `, [
        metric.platform,
        metric.metricName,
        metric.metricValue,
        JSON.stringify(metric.metadata)
      ]);

      // Update real-time metrics cache
      await this.redis.hset(
        `metrics:${metric.platform}`,
        metric.metricName,
        metric.metricValue
      );

      logger.debug(`Metric recorded: ${metric.metricName} = ${metric.metricValue} for ${metric.platform}`);
    } catch (error) {
      logger.error('Failed to record platform metric:', error);
      throw error;
    }
  }

  async getAnalytics(platform?: string, startDate?: Date, endDate?: Date): Promise<any> {
    try {
      const whereClause = [];
      const params = [];
      let paramIndex = 1;

      if (platform) {
        whereClause.push(`platform = $${paramIndex++}`);
        params.push(platform);
      }

      if (startDate) {
        whereClause.push(`timestamp >= $${paramIndex++}`);
        params.push(startDate);
      }

      if (endDate) {
        whereClause.push(`timestamp <= $${paramIndex++}`);
        params.push(endDate);
      }

      const whereString = whereClause.length > 0 ? `WHERE ${whereClause.join(' AND ')}` : '';

      const [events, sessions, metrics] = await Promise.all([
        this.db.query(`
          SELECT 
            platform,
            event_type,
            COUNT(*) as count,
            DATE_TRUNC('hour', timestamp) as hour
          FROM events 
          ${whereString}
          GROUP BY platform, event_type, hour
          ORDER BY hour DESC
        `, params),

        this.db.query(`
          SELECT 
            platform,
            COUNT(*) as session_count,
            AVG(duration_seconds) as avg_duration,
            AVG(actions_count) as avg_actions
          FROM user_sessions 
          ${whereString.replace('timestamp', 'start_time')}
          GROUP BY platform
        `, params),

        this.db.query(`
          SELECT 
            platform,
            metric_name,
            AVG(metric_value) as avg_value,
            MAX(metric_value) as max_value,
            MIN(metric_value) as min_value
          FROM platform_metrics 
          ${whereString}
          GROUP BY platform, metric_name
        `, params)
      ]);

      return {
        events: events.rows,
        sessions: sessions.rows,
        metrics: metrics.rows
      };
    } catch (error) {
      logger.error('Failed to get analytics:', error);
      throw error;
    }
  }

  async getRealTimeMetrics(platform: string): Promise<any> {
    try {
      const [recentEvents, currentMetrics] = await Promise.all([
        this.redis.lrange(`recent_events:${platform}`, 0, 99),
        this.redis.hgetall(`metrics:${platform}`)
      ]);

      return {
        recentEvents: recentEvents.map((event: string) => JSON.parse(event)),
        currentMetrics
      };
    } catch (error) {
      logger.error('Failed to get real-time metrics:', error);
      throw error;
    }
  }
}