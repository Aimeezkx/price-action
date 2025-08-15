import { Pool } from 'pg';
import { createClient } from 'redis';
import { logger } from '../utils/logger';
import { ABTest, ABTestVariant, ABTestAssignment } from '../types/abTesting';

export class ABTestingService {
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
        CREATE TABLE IF NOT EXISTS ab_tests (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name VARCHAR(255) UNIQUE NOT NULL,
          description TEXT,
          platform VARCHAR(20) NOT NULL,
          status VARCHAR(20) DEFAULT 'draft',
          traffic_allocation NUMERIC DEFAULT 1.0,
          start_date TIMESTAMP,
          end_date TIMESTAMP,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS ab_test_variants (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
          name VARCHAR(255) NOT NULL,
          description TEXT,
          traffic_weight NUMERIC NOT NULL,
          config JSONB,
          is_control BOOLEAN DEFAULT false,
          created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS ab_test_assignments (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
          variant_id UUID REFERENCES ab_test_variants(id) ON DELETE CASCADE,
          user_id VARCHAR(255),
          session_id VARCHAR(255),
          platform VARCHAR(20) NOT NULL,
          assigned_at TIMESTAMP DEFAULT NOW(),
          UNIQUE(test_id, user_id, session_id)
        );

        CREATE TABLE IF NOT EXISTS ab_test_events (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          test_id UUID REFERENCES ab_tests(id) ON DELETE CASCADE,
          variant_id UUID REFERENCES ab_test_variants(id) ON DELETE CASCADE,
          user_id VARCHAR(255),
          session_id VARCHAR(255),
          event_type VARCHAR(100) NOT NULL,
          event_data JSONB,
          timestamp TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ab_assignments_test ON ab_test_assignments(test_id);
        CREATE INDEX IF NOT EXISTS idx_ab_assignments_user ON ab_test_assignments(user_id);
        CREATE INDEX IF NOT EXISTS idx_ab_events_test ON ab_test_events(test_id);
        CREATE INDEX IF NOT EXISTS idx_ab_events_variant ON ab_test_events(variant_id);
      `);
      
      logger.info('A/B testing database initialized');
    } catch (error) {
      logger.error('Failed to initialize A/B testing database:', error);
    }
  }

  async createTest(testData: ABTest): Promise<string> {
    try {
      const result = await this.db.query(`
        INSERT INTO ab_tests (name, description, platform, traffic_allocation, start_date, end_date)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
      `, [
        testData.name,
        testData.description,
        testData.platform,
        testData.trafficAllocation,
        testData.startDate,
        testData.endDate
      ]);

      const testId = result.rows[0].id;

      // Create variants
      for (const variant of testData.variants) {
        await this.db.query(`
          INSERT INTO ab_test_variants (test_id, name, description, traffic_weight, config, is_control)
          VALUES ($1, $2, $3, $4, $5, $6)
        `, [
          testId,
          variant.name,
          variant.description,
          variant.trafficWeight,
          JSON.stringify(variant.config),
          variant.isControl
        ]);
      }

      logger.info(`A/B test created: ${testData.name} (${testId})`);
      return testId;
    } catch (error) {
      logger.error('Failed to create A/B test:', error);
      throw error;
    }
  }

  async getAssignment(testName: string, userId?: string, sessionId?: string, platform?: string): Promise<ABTestAssignment | null> {
    try {
      // Check if user/session already has an assignment
      let existingAssignment = null;
      if (userId || sessionId) {
        const result = await this.db.query(`
          SELECT a.*, v.name as variant_name, v.config as variant_config
          FROM ab_test_assignments a
          JOIN ab_test_variants v ON a.variant_id = v.id
          JOIN ab_tests t ON a.test_id = t.id
          WHERE t.name = $1 AND (a.user_id = $2 OR a.session_id = $3)
          AND t.status = 'active'
          AND (t.end_date IS NULL OR t.end_date > NOW())
        `, [testName, userId, sessionId]);

        if (result.rows.length > 0) {
          existingAssignment = result.rows[0];
        }
      }

      if (existingAssignment) {
        return {
          testId: existingAssignment.test_id,
          variantId: existingAssignment.variant_id,
          variantName: existingAssignment.variant_name,
          config: existingAssignment.variant_config,
          assignedAt: existingAssignment.assigned_at
        };
      }

      // Get active test
      const testResult = await this.db.query(`
        SELECT * FROM ab_tests 
        WHERE name = $1 AND status = 'active'
        AND (start_date IS NULL OR start_date <= NOW())
        AND (end_date IS NULL OR end_date > NOW())
      `, [testName]);

      if (testResult.rows.length === 0) {
        return null;
      }

      const test = testResult.rows[0];

      // Check traffic allocation
      if (Math.random() > test.traffic_allocation) {
        return null;
      }

      // Get variants
      const variantsResult = await this.db.query(`
        SELECT * FROM ab_test_variants 
        WHERE test_id = $1 
        ORDER BY traffic_weight DESC
      `, [test.id]);

      if (variantsResult.rows.length === 0) {
        return null;
      }

      // Select variant based on traffic weights
      const variants = variantsResult.rows;
      const totalWeight = variants.reduce((sum, v) => sum + parseFloat(v.traffic_weight), 0);
      const random = Math.random() * totalWeight;
      
      let cumulativeWeight = 0;
      let selectedVariant = variants[0];
      
      for (const variant of variants) {
        cumulativeWeight += parseFloat(variant.traffic_weight);
        if (random <= cumulativeWeight) {
          selectedVariant = variant;
          break;
        }
      }

      // Create assignment
      await this.db.query(`
        INSERT INTO ab_test_assignments (test_id, variant_id, user_id, session_id, platform)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (test_id, user_id, session_id) DO NOTHING
      `, [test.id, selectedVariant.id, userId, sessionId, platform]);

      // Cache assignment
      const cacheKey = `ab_assignment:${testName}:${userId || sessionId}`;
      await this.redis.setex(cacheKey, 3600, JSON.stringify({
        testId: test.id,
        variantId: selectedVariant.id,
        variantName: selectedVariant.name,
        config: selectedVariant.config
      }));

      return {
        testId: test.id,
        variantId: selectedVariant.id,
        variantName: selectedVariant.name,
        config: selectedVariant.config,
        assignedAt: new Date()
      };
    } catch (error) {
      logger.error('Failed to get A/B test assignment:', error);
      throw error;
    }
  }

  async trackEvent(testName: string, eventType: string, userId?: string, sessionId?: string, eventData?: any): Promise<void> {
    try {
      // Get assignment
      const assignment = await this.getAssignment(testName, userId, sessionId);
      if (!assignment) {
        return;
      }

      // Track event
      await this.db.query(`
        INSERT INTO ab_test_events (test_id, variant_id, user_id, session_id, event_type, event_data)
        VALUES ($1, $2, $3, $4, $5, $6)
      `, [
        assignment.testId,
        assignment.variantId,
        userId,
        sessionId,
        eventType,
        JSON.stringify(eventData)
      ]);

      logger.debug(`A/B test event tracked: ${testName} - ${eventType}`);
    } catch (error) {
      logger.error('Failed to track A/B test event:', error);
      throw error;
    }
  }

  async getTestResults(testName: string): Promise<any> {
    try {
      const result = await this.db.query(`
        SELECT 
          t.name as test_name,
          v.name as variant_name,
          v.is_control,
          COUNT(DISTINCT a.user_id, a.session_id) as participants,
          COUNT(e.id) as total_events,
          COUNT(DISTINCT CASE WHEN e.event_type = 'conversion' THEN e.user_id END) as conversions,
          CASE 
            WHEN COUNT(DISTINCT a.user_id, a.session_id) > 0 
            THEN COUNT(DISTINCT CASE WHEN e.event_type = 'conversion' THEN e.user_id END)::FLOAT / COUNT(DISTINCT a.user_id, a.session_id)
            ELSE 0 
          END as conversion_rate
        FROM ab_tests t
        JOIN ab_test_variants v ON t.id = v.test_id
        LEFT JOIN ab_test_assignments a ON v.id = a.variant_id
        LEFT JOIN ab_test_events e ON v.id = e.variant_id
        WHERE t.name = $1
        GROUP BY t.name, v.name, v.is_control
        ORDER BY v.is_control DESC, v.name
      `, [testName]);

      return result.rows;
    } catch (error) {
      logger.error('Failed to get A/B test results:', error);
      throw error;
    }
  }

  async updateTestStatus(testName: string, status: string): Promise<void> {
    try {
      await this.db.query(`
        UPDATE ab_tests 
        SET status = $1, updated_at = NOW()
        WHERE name = $2
      `, [status, testName]);

      // Clear cache for this test
      const keys = await this.redis.keys(`ab_assignment:${testName}:*`);
      if (keys.length > 0) {
        await this.redis.del(keys);
      }

      logger.info(`A/B test status updated: ${testName} -> ${status}`);
    } catch (error) {
      logger.error('Failed to update A/B test status:', error);
      throw error;
    }
  }

  async getActiveTests(platform?: string): Promise<any[]> {
    try {
      const whereClause = platform ? 'AND platform = $2' : '';
      const params = platform ? ['active', platform] : ['active'];

      const result = await this.db.query(`
        SELECT 
          t.*,
          COUNT(v.id) as variant_count,
          COUNT(a.id) as participant_count
        FROM ab_tests t
        LEFT JOIN ab_test_variants v ON t.id = v.test_id
        LEFT JOIN ab_test_assignments a ON t.id = a.test_id
        WHERE t.status = $1 ${whereClause}
        GROUP BY t.id
        ORDER BY t.created_at DESC
      `, params);

      return result.rows;
    } catch (error) {
      logger.error('Failed to get active tests:', error);
      throw error;
    }
  }
}