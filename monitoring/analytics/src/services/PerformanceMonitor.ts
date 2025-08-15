import { Pool } from 'pg';
import { createClient } from 'redis';
import { logger } from '../utils/logger';
import { PerformanceMetric, PerformanceAlert, PerformanceReport } from '../types/performance';

export class PerformanceMonitor {
  private db: Pool;
  private redis: any;
  private alertThresholds: Map<string, number>;

  constructor() {
    this.db = new Pool({
      connectionString: process.env.DATABASE_URL
    });
    
    this.redis = createClient({
      url: process.env.REDIS_URL
    });
    
    this.redis.connect();
    this.initializeDatabase();
    this.setupAlertThresholds();
  }

  private async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS performance_metrics (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          platform VARCHAR(20) NOT NULL,
          metric_type VARCHAR(100) NOT NULL,
          metric_name VARCHAR(200) NOT NULL,
          value NUMERIC NOT NULL,
          unit VARCHAR(20),
          metadata JSONB,
          user_id VARCHAR(255),
          session_id VARCHAR(255),
          timestamp TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS performance_alerts (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          platform VARCHAR(20) NOT NULL,
          metric_type VARCHAR(100) NOT NULL,
          metric_name VARCHAR(200) NOT NULL,
          threshold_value NUMERIC NOT NULL,
          actual_value NUMERIC NOT NULL,
          severity VARCHAR(20) NOT NULL,
          message TEXT,
          status VARCHAR(20) DEFAULT 'active',
          created_at TIMESTAMP DEFAULT NOW(),
          resolved_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS performance_baselines (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          platform VARCHAR(20) NOT NULL,
          metric_type VARCHAR(100) NOT NULL,
          metric_name VARCHAR(200) NOT NULL,
          baseline_value NUMERIC NOT NULL,
          p50_value NUMERIC,
          p95_value NUMERIC,
          p99_value NUMERIC,
          sample_count INTEGER,
          calculated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_perf_metrics_platform ON performance_metrics(platform);
        CREATE INDEX IF NOT EXISTS idx_perf_metrics_type ON performance_metrics(metric_type);
        CREATE INDEX IF NOT EXISTS idx_perf_metrics_timestamp ON performance_metrics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_perf_alerts_platform ON performance_alerts(platform);
        CREATE INDEX IF NOT EXISTS idx_perf_alerts_status ON performance_alerts(status);
      `);
      
      logger.info('Performance monitoring database initialized');
    } catch (error) {
      logger.error('Failed to initialize performance monitoring database:', error);
    }
  }

  private setupAlertThresholds() {
    this.alertThresholds = new Map([
      // Web platform thresholds
      ['web.page_load_time', 3000], // 3 seconds
      ['web.api_response_time', 1000], // 1 second
      ['web.first_contentful_paint', 2000], // 2 seconds
      ['web.largest_contentful_paint', 4000], // 4 seconds
      ['web.cumulative_layout_shift', 0.1], // 0.1 CLS score
      ['web.first_input_delay', 100], // 100ms
      ['web.memory_usage', 100 * 1024 * 1024], // 100MB
      ['web.bundle_size', 5 * 1024 * 1024], // 5MB
      
      // iOS platform thresholds
      ['ios.app_launch_time', 2000], // 2 seconds
      ['ios.screen_transition_time', 500], // 500ms
      ['ios.api_response_time', 1000], // 1 second
      ['ios.memory_usage', 200 * 1024 * 1024], // 200MB
      ['ios.battery_drain_rate', 5], // 5% per hour
      ['ios.crash_rate', 0.01], // 1% crash rate
      ['ios.frame_drop_rate', 0.05], // 5% frame drops
      
      // Backend thresholds
      ['backend.response_time', 500], // 500ms
      ['backend.error_rate', 0.01], // 1% error rate
      ['backend.cpu_usage', 80], // 80% CPU
      ['backend.memory_usage', 80], // 80% memory
      ['backend.disk_usage', 85], // 85% disk
      ['backend.queue_length', 1000], // 1000 jobs in queue
    ]);
  }

  async recordMetric(metric: PerformanceMetric): Promise<void> {
    try {
      // Store in database
      await this.db.query(`
        INSERT INTO performance_metrics (
          platform, metric_type, metric_name, value, unit, metadata, user_id, session_id
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      `, [
        metric.platform,
        metric.metricType,
        metric.metricName,
        metric.value,
        metric.unit,
        JSON.stringify(metric.metadata),
        metric.userId,
        metric.sessionId
      ]);

      // Update real-time metrics in Redis
      const key = `perf:${metric.platform}:${metric.metricType}:${metric.metricName}`;
      await this.redis.lpush(key, JSON.stringify({
        value: metric.value,
        timestamp: new Date().toISOString(),
        metadata: metric.metadata
      }));
      await this.redis.ltrim(key, 0, 999); // Keep last 1000 values
      await this.redis.expire(key, 86400); // 24 hours

      // Check for alerts
      await this.checkAlerts(metric);

      logger.debug(`Performance metric recorded: ${metric.platform}.${metric.metricName} = ${metric.value}`);
    } catch (error) {
      logger.error('Failed to record performance metric:', error);
      throw error;
    }
  }

  private async checkAlerts(metric: PerformanceMetric): Promise<void> {
    try {
      const thresholdKey = `${metric.platform}.${metric.metricName}`;
      const threshold = this.alertThresholds.get(thresholdKey);
      
      if (!threshold) {
        return;
      }

      let shouldAlert = false;
      let severity = 'info';

      // Determine if alert should be triggered
      if (metric.metricName.includes('time') || metric.metricName.includes('duration')) {
        // Higher is worse for time metrics
        if (metric.value > threshold * 2) {
          shouldAlert = true;
          severity = 'critical';
        } else if (metric.value > threshold * 1.5) {
          shouldAlert = true;
          severity = 'warning';
        }
      } else if (metric.metricName.includes('rate') || metric.metricName.includes('usage')) {
        // Higher is worse for rate/usage metrics
        if (metric.value > threshold) {
          shouldAlert = true;
          severity = metric.value > threshold * 1.5 ? 'critical' : 'warning';
        }
      }

      if (shouldAlert) {
        await this.createAlert({
          platform: metric.platform,
          metricType: metric.metricType,
          metricName: metric.metricName,
          thresholdValue: threshold,
          actualValue: metric.value,
          severity,
          message: `${metric.metricName} exceeded threshold: ${metric.value} > ${threshold}`
        });
      }
    } catch (error) {
      logger.error('Failed to check alerts:', error);
    }
  }

  private async createAlert(alert: Omit<PerformanceAlert, 'id' | 'status' | 'createdAt' | 'resolvedAt'>): Promise<void> {
    try {
      // Check if similar alert already exists
      const existingAlert = await this.db.query(`
        SELECT id FROM performance_alerts
        WHERE platform = $1 AND metric_name = $2 AND status = 'active'
        AND created_at > NOW() - INTERVAL '1 hour'
      `, [alert.platform, alert.metricName]);

      if (existingAlert.rows.length > 0) {
        return; // Don't create duplicate alerts
      }

      await this.db.query(`
        INSERT INTO performance_alerts (
          platform, metric_type, metric_name, threshold_value, 
          actual_value, severity, message
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [
        alert.platform,
        alert.metricType,
        alert.metricName,
        alert.thresholdValue,
        alert.actualValue,
        alert.severity,
        alert.message
      ]);

      // Send to real-time alert channel
      await this.redis.publish('performance_alerts', JSON.stringify(alert));

      logger.warn(`Performance alert created: ${alert.message}`);
    } catch (error) {
      logger.error('Failed to create performance alert:', error);
    }
  }

  async getPerformanceReport(platform?: string, startDate?: Date, endDate?: Date): Promise<PerformanceReport> {
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

      const [metrics, alerts, baselines] = await Promise.all([
        this.db.query(`
          SELECT 
            platform,
            metric_type,
            metric_name,
            COUNT(*) as sample_count,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as p50_value,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99_value
          FROM performance_metrics 
          ${whereString}
          GROUP BY platform, metric_type, metric_name
          ORDER BY platform, metric_type, metric_name
        `, params),

        this.db.query(`
          SELECT 
            platform,
            severity,
            COUNT(*) as alert_count
          FROM performance_alerts 
          ${whereString.replace('timestamp', 'created_at')}
          GROUP BY platform, severity
        `, params),

        this.db.query(`
          SELECT * FROM performance_baselines
          ${platform ? 'WHERE platform = $1' : ''}
          ORDER BY platform, metric_type, metric_name
        `, platform ? [platform] : [])
      ]);

      return {
        metrics: metrics.rows,
        alerts: alerts.rows,
        baselines: baselines.rows,
        generatedAt: new Date()
      };
    } catch (error) {
      logger.error('Failed to get performance report:', error);
      throw error;
    }
  }

  async getRealTimeMetrics(platform: string, metricType?: string): Promise<any> {
    try {
      const pattern = metricType 
        ? `perf:${platform}:${metricType}:*`
        : `perf:${platform}:*`;
      
      const keys = await this.redis.keys(pattern);
      const metrics: any = {};

      for (const key of keys) {
        const values = await this.redis.lrange(key, 0, 99);
        const parsedValues = values.map((v: string) => JSON.parse(v));
        
        const keyParts = key.split(':');
        const metricName = keyParts.slice(3).join(':');
        
        metrics[metricName] = {
          recent: parsedValues.slice(0, 10),
          count: parsedValues.length,
          latest: parsedValues[0]
        };
      }

      return metrics;
    } catch (error) {
      logger.error('Failed to get real-time metrics:', error);
      throw error;
    }
  }

  async updateBaselines(): Promise<void> {
    try {
      // Calculate baselines from last 7 days of data
      const result = await this.db.query(`
        SELECT 
          platform,
          metric_type,
          metric_name,
          COUNT(*) as sample_count,
          AVG(value) as baseline_value,
          PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as p50_value,
          PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value,
          PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY value) as p99_value
        FROM performance_metrics 
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY platform, metric_type, metric_name
        HAVING COUNT(*) >= 100
      `);

      for (const row of result.rows) {
        await this.db.query(`
          INSERT INTO performance_baselines (
            platform, metric_type, metric_name, baseline_value,
            p50_value, p95_value, p99_value, sample_count
          )
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
          ON CONFLICT (platform, metric_type, metric_name) 
          DO UPDATE SET
            baseline_value = $4,
            p50_value = $5,
            p95_value = $6,
            p99_value = $7,
            sample_count = $8,
            calculated_at = NOW()
        `, [
          row.platform,
          row.metric_type,
          row.metric_name,
          row.baseline_value,
          row.p50_value,
          row.p95_value,
          row.p99_value,
          row.sample_count
        ]);
      }

      logger.info(`Updated ${result.rows.length} performance baselines`);
    } catch (error) {
      logger.error('Failed to update baselines:', error);
      throw error;
    }
  }

  async getActiveAlerts(platform?: string): Promise<PerformanceAlert[]> {
    try {
      const whereClause = platform ? 'WHERE platform = $1 AND status = $2' : 'WHERE status = $1';
      const params = platform ? [platform, 'active'] : ['active'];

      const result = await this.db.query(`
        SELECT * FROM performance_alerts 
        ${whereClause}
        ORDER BY created_at DESC
      `, params);

      return result.rows;
    } catch (error) {
      logger.error('Failed to get active alerts:', error);
      throw error;
    }
  }

  async resolveAlert(alertId: string): Promise<void> {
    try {
      await this.db.query(`
        UPDATE performance_alerts 
        SET status = 'resolved', resolved_at = NOW()
        WHERE id = $1
      `, [alertId]);

      logger.info(`Performance alert resolved: ${alertId}`);
    } catch (error) {
      logger.error('Failed to resolve alert:', error);
      throw error;
    }
  }
}