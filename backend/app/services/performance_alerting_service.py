"""
Performance Trend Tracking and Alerting Service

Advanced alerting system for performance monitoring with trend analysis,
predictive alerting, and intelligent notification management.
"""

import asyncio
import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import statistics
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of performance alerts"""
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    TREND_DEGRADATION = "trend_degradation"
    ANOMALY_DETECTED = "anomaly_detected"
    REGRESSION_DETECTED = "regression_detected"
    PREDICTION_WARNING = "prediction_warning"
    SYSTEM_HEALTH = "system_health"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DASHBOARD = "dashboard"


@dataclass
class AlertRule:
    """Performance alert rule configuration"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    alert_type: AlertType
    severity: AlertSeverity
    threshold_value: Optional[float]
    comparison_operator: str  # >, <, >=, <=, ==, !=
    evaluation_window_minutes: int
    min_data_points: int
    notification_channels: List[NotificationChannel]
    suppression_duration_minutes: int
    enabled: bool
    conditions: Dict[str, Any]


@dataclass
class PerformanceAlert:
    """Performance alert instance"""
    alert_id: str
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold_value: Optional[float]
    trend_data: List[float]
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    acknowledged_by: Optional[str]
    context: Dict[str, Any]
    notification_history: List[Dict[str, Any]]


@dataclass
class TrendAnalysis:
    """Performance trend analysis result"""
    metric_name: str
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0-1
    slope: float
    r_squared: float
    prediction_24h: float
    confidence_interval: Tuple[float, float]
    anomalies_detected: int
    analysis_period_hours: int
    data_points: int


@dataclass
class AlertingConfiguration:
    """Global alerting configuration"""
    email_smtp_server: str
    email_smtp_port: int
    email_username: str
    email_password: str
    slack_webhook_url: str
    default_notification_channels: List[NotificationChannel]
    alert_aggregation_window_minutes: int
    max_alerts_per_hour: int
    enable_predictive_alerting: bool


class PerformanceAlertingService:
    """Main performance alerting service"""
    
    def __init__(self, config: AlertingConfiguration):
        self.config = config
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        self.metric_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.trend_cache: Dict[str, TrendAnalysis] = {}
        self.notification_rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        self.alerting_active = False
        
        # Initialize default alert rules (will be done synchronously)
        self._initialize_default_rules_sync()
        
    async def start_alerting(self):
        """Start the alerting service"""
        if self.alerting_active:
            return
            
        self.alerting_active = True
        logger.info("Starting performance alerting service")
        
        # Start alerting tasks
        asyncio.create_task(self._alert_evaluation_loop())
        asyncio.create_task(self._trend_analysis_loop())
        asyncio.create_task(self._alert_cleanup_loop())
        
    async def stop_alerting(self):
        """Stop the alerting service"""
        self.alerting_active = False
        logger.info("Stopping performance alerting service")
        
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")
        
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
            
    async def record_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """Record a metric value for alerting"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.metric_data[metric_name].append({
            'value': value,
            'timestamp': timestamp
        })
        
        # Trigger immediate evaluation for this metric
        await self._evaluate_metric_alerts(metric_name)
        
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            alert.updated_at = datetime.now()
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            
    async def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.updated_at = datetime.now()
            
            # Move to history
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved")
            
    async def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[PerformanceAlert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
            
        # Sort by severity and creation time
        severity_order = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.ERROR: 3,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 1
        }
        
        alerts.sort(key=lambda x: (severity_order[x.severity], x.created_at), reverse=True)
        return alerts
        
    async def get_trend_analysis(self, metric_name: str, hours: int = 24) -> Optional[TrendAnalysis]:
        """Get trend analysis for a metric"""
        if metric_name not in self.metric_data:
            return None
            
        data_points = list(self.metric_data[metric_name])
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter data to requested time window
        filtered_data = [dp for dp in data_points if dp['timestamp'] >= cutoff_time]
        
        if len(filtered_data) < 10:
            return None
            
        return await self._analyze_trend(metric_name, filtered_data, hours)
        
    def _initialize_default_rules_sync(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="cpu_usage_high",
                name="High CPU Usage",
                description="CPU usage exceeds 80%",
                metric_name="cpu_usage",
                alert_type=AlertType.THRESHOLD_EXCEEDED,
                severity=AlertSeverity.WARNING,
                threshold_value=80.0,
                comparison_operator=">",
                evaluation_window_minutes=5,
                min_data_points=3,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
                suppression_duration_minutes=30,
                enabled=True,
                conditions={}
            ),
            AlertRule(
                rule_id="memory_usage_critical",
                name="Critical Memory Usage",
                description="Memory usage exceeds 90%",
                metric_name="memory_usage",
                alert_type=AlertType.THRESHOLD_EXCEEDED,
                severity=AlertSeverity.CRITICAL,
                threshold_value=90.0,
                comparison_operator=">",
                evaluation_window_minutes=3,
                min_data_points=2,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                suppression_duration_minutes=15,
                enabled=True,
                conditions={}
            ),
            AlertRule(
                rule_id="response_time_degradation",
                name="Response Time Degradation",
                description="Response time trend is degrading",
                metric_name="response_time",
                alert_type=AlertType.TREND_DEGRADATION,
                severity=AlertSeverity.WARNING,
                threshold_value=None,
                comparison_operator="trend_increasing",
                evaluation_window_minutes=30,
                min_data_points=20,
                notification_channels=[NotificationChannel.EMAIL],
                suppression_duration_minutes=60,
                enabled=True,
                conditions={"trend_strength_threshold": 0.7}
            ),
            AlertRule(
                rule_id="error_rate_spike",
                name="Error Rate Spike",
                description="Error rate exceeds 5%",
                metric_name="error_rate",
                alert_type=AlertType.THRESHOLD_EXCEEDED,
                severity=AlertSeverity.ERROR,
                threshold_value=0.05,
                comparison_operator=">",
                evaluation_window_minutes=10,
                min_data_points=5,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                suppression_duration_minutes=20,
                enabled=True,
                conditions={}
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
            
    async def _alert_evaluation_loop(self):
        """Main alert evaluation loop"""
        while self.alerting_active:
            try:
                # Evaluate all metrics
                for metric_name in self.metric_data.keys():
                    await self._evaluate_metric_alerts(metric_name)
                    
                # Check for auto-resolution
                await self._check_alert_resolution()
                
                await asyncio.sleep(60)  # Evaluate every minute
                
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(60)
                
    async def _evaluate_metric_alerts(self, metric_name: str):
        """Evaluate alerts for a specific metric"""
        relevant_rules = [rule for rule in self.alert_rules.values() 
                         if rule.metric_name == metric_name and rule.enabled]
        
        for rule in relevant_rules:
            await self._evaluate_rule(rule)
            
    async def _evaluate_rule(self, rule: AlertRule):
        """Evaluate a specific alert rule"""
        try:
            data_points = list(self.metric_data[rule.metric_name])
            
            # Filter to evaluation window
            cutoff_time = datetime.now() - timedelta(minutes=rule.evaluation_window_minutes)
            recent_data = [dp for dp in data_points if dp['timestamp'] >= cutoff_time]
            
            if len(recent_data) < rule.min_data_points:
                return
                
            # Check if alert is already active and suppressed
            existing_alert_key = f"{rule.rule_id}_{rule.metric_name}"
            if existing_alert_key in self.active_alerts:
                existing_alert = self.active_alerts[existing_alert_key]
                if existing_alert.status == AlertStatus.SUPPRESSED:
                    suppression_end = (existing_alert.created_at + 
                                     timedelta(minutes=rule.suppression_duration_minutes))
                    if datetime.now() < suppression_end:
                        return
                        
            # Evaluate based on alert type
            should_alert = False
            current_value = recent_data[-1]['value']
            context = {}
            
            if rule.alert_type == AlertType.THRESHOLD_EXCEEDED:
                should_alert = await self._evaluate_threshold_rule(rule, recent_data)
                context['threshold_value'] = rule.threshold_value
                
            elif rule.alert_type == AlertType.TREND_DEGRADATION:
                should_alert, trend_context = await self._evaluate_trend_rule(rule, recent_data)
                context.update(trend_context)
                
            elif rule.alert_type == AlertType.ANOMALY_DETECTED:
                should_alert, anomaly_context = await self._evaluate_anomaly_rule(rule, recent_data)
                context.update(anomaly_context)
                
            if should_alert:
                await self._create_alert(rule, current_value, context)
                
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
            
    async def _evaluate_threshold_rule(self, rule: AlertRule, data_points: List[Dict]) -> bool:
        """Evaluate threshold-based rule"""
        values = [dp['value'] for dp in data_points]
        current_value = values[-1]
        
        if rule.comparison_operator == ">":
            return current_value > rule.threshold_value
        elif rule.comparison_operator == "<":
            return current_value < rule.threshold_value
        elif rule.comparison_operator == ">=":
            return current_value >= rule.threshold_value
        elif rule.comparison_operator == "<=":
            return current_value <= rule.threshold_value
        elif rule.comparison_operator == "==":
            return current_value == rule.threshold_value
        elif rule.comparison_operator == "!=":
            return current_value != rule.threshold_value
            
        return False
        
    async def _evaluate_trend_rule(self, rule: AlertRule, data_points: List[Dict]) -> Tuple[bool, Dict]:
        """Evaluate trend-based rule"""
        if len(data_points) < 10:
            return False, {}
            
        values = [dp['value'] for dp in data_points]
        timestamps = [dp['timestamp'] for dp in data_points]
        
        # Convert timestamps to numeric values for regression
        time_numeric = [(ts - timestamps[0]).total_seconds() for ts in timestamps]
        
        # Linear regression
        slope, intercept = np.polyfit(time_numeric, values, 1)
        
        # Calculate R-squared
        y_pred = [slope * t + intercept for t in time_numeric]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(len(values)))
        ss_tot = sum((values[i] - statistics.mean(values)) ** 2 for i in range(len(values)))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        trend_strength = abs(r_squared)
        trend_strength_threshold = rule.conditions.get('trend_strength_threshold', 0.5)
        
        context = {
            'slope': slope,
            'r_squared': r_squared,
            'trend_strength': trend_strength
        }
        
        if rule.comparison_operator == "trend_increasing":
            return slope > 0 and trend_strength > trend_strength_threshold, context
        elif rule.comparison_operator == "trend_decreasing":
            return slope < 0 and trend_strength > trend_strength_threshold, context
            
        return False, context
        
    async def _evaluate_anomaly_rule(self, rule: AlertRule, data_points: List[Dict]) -> Tuple[bool, Dict]:
        """Evaluate anomaly-based rule"""
        if len(data_points) < 20:
            return False, {}
            
        values = [dp['value'] for dp in data_points]
        
        # Simple anomaly detection using z-score
        mean_val = statistics.mean(values[:-5])  # Exclude recent values from baseline
        std_val = statistics.stdev(values[:-5]) if len(values) > 6 else 0
        
        if std_val == 0:
            return False, {}
            
        current_value = values[-1]
        z_score = abs((current_value - mean_val) / std_val)
        
        anomaly_threshold = rule.conditions.get('z_score_threshold', 3.0)
        
        context = {
            'z_score': z_score,
            'baseline_mean': mean_val,
            'baseline_std': std_val
        }
        
        return z_score > anomaly_threshold, context
        
    async def _create_alert(self, rule: AlertRule, current_value: float, context: Dict[str, Any]):
        """Create a new alert"""
        alert_id = f"{rule.rule_id}_{rule.metric_name}_{int(datetime.now().timestamp())}"
        
        # Check rate limiting
        if not await self._check_rate_limit(rule.rule_id):
            logger.warning(f"Rate limit exceeded for rule {rule.rule_id}")
            return
            
        alert = PerformanceAlert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=rule.name,
            description=rule.description,
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold_value=rule.threshold_value,
            trend_data=[dp['value'] for dp in list(self.metric_data[rule.metric_name])[-20:]],
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            acknowledged_at=None,
            resolved_at=None,
            acknowledged_by=None,
            context=context,
            notification_history=[]
        )
        
        # Store alert
        alert_key = f"{rule.rule_id}_{rule.metric_name}"
        self.active_alerts[alert_key] = alert
        
        # Send notifications
        await self._send_notifications(alert, rule.notification_channels)
        
        logger.warning(f"Created alert: {alert.title} - {alert.description}")
        
    async def _send_notifications(self, alert: PerformanceAlert, channels: List[NotificationChannel]):
        """Send alert notifications"""
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email_notification(alert)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack_notification(alert)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook_notification(alert)
                    
                # Record notification
                alert.notification_history.append({
                    'channel': channel.value,
                    'sent_at': datetime.now().isoformat(),
                    'status': 'sent'
                })
                
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
                alert.notification_history.append({
                    'channel': channel.value,
                    'sent_at': datetime.now().isoformat(),
                    'status': 'failed',
                    'error': str(e)
                })
                
    async def _send_email_notification(self, alert: PerformanceAlert):
        """Send email notification"""
        if not all([self.config.email_smtp_server, self.config.email_username]):
            return
            
        msg = MIMEMultipart()
        msg['From'] = self.config.email_username
        msg['To'] = self.config.email_username  # Could be configured per rule
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
Performance Alert: {alert.title}

Severity: {alert.severity.value.upper()}
Metric: {alert.metric_name}
Current Value: {alert.current_value}
Threshold: {alert.threshold_value}
Time: {alert.created_at}

Description: {alert.description}

Context: {json.dumps(alert.context, indent=2)}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
        server.starttls()
        server.login(self.config.email_username, self.config.email_password)
        server.send_message(msg)
        server.quit()
        
    async def _send_slack_notification(self, alert: PerformanceAlert):
        """Send Slack notification"""
        # Implementation would use Slack webhook
        pass
        
    async def _send_webhook_notification(self, alert: PerformanceAlert):
        """Send webhook notification"""
        # Implementation would send HTTP POST to configured webhook
        pass
        
    async def _check_rate_limit(self, rule_id: str) -> bool:
        """Check if alert is rate limited"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old timestamps
        self.notification_rate_limits[rule_id] = [
            ts for ts in self.notification_rate_limits[rule_id] if ts > hour_ago
        ]
        
        # Check limit
        if len(self.notification_rate_limits[rule_id]) >= self.config.max_alerts_per_hour:
            return False
            
        # Add current timestamp
        self.notification_rate_limits[rule_id].append(now)
        return True
        
    async def _check_alert_resolution(self):
        """Check if active alerts should be auto-resolved"""
        for alert_key, alert in list(self.active_alerts.items()):
            rule = self.alert_rules.get(alert.rule_id)
            if not rule:
                continue
                
            # Check if conditions are no longer met
            data_points = list(self.metric_data[alert.metric_name])
            cutoff_time = datetime.now() - timedelta(minutes=rule.evaluation_window_minutes)
            recent_data = [dp for dp in data_points if dp['timestamp'] >= cutoff_time]
            
            if len(recent_data) >= rule.min_data_points:
                should_alert = False
                
                if rule.alert_type == AlertType.THRESHOLD_EXCEEDED:
                    should_alert = await self._evaluate_threshold_rule(rule, recent_data)
                    
                if not should_alert:
                    await self.resolve_alert(alert.alert_id)
                    
    async def _trend_analysis_loop(self):
        """Periodic trend analysis"""
        while self.alerting_active:
            try:
                for metric_name in self.metric_data.keys():
                    trend = await self.get_trend_analysis(metric_name, 24)
                    if trend:
                        self.trend_cache[metric_name] = trend
                        
                await asyncio.sleep(3600)  # Update trends every hour
                
            except Exception as e:
                logger.error(f"Error in trend analysis loop: {e}")
                await asyncio.sleep(3600)
                
    async def _analyze_trend(self, metric_name: str, data_points: List[Dict], hours: int) -> TrendAnalysis:
        """Analyze trend for a metric"""
        values = [dp['value'] for dp in data_points]
        timestamps = [dp['timestamp'] for dp in data_points]
        
        # Linear regression
        time_numeric = [(ts - timestamps[0]).total_seconds() for ts in timestamps]
        slope, intercept = np.polyfit(time_numeric, values, 1)
        
        # Calculate R-squared
        y_pred = [slope * t + intercept for t in time_numeric]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(len(values)))
        ss_tot = sum((values[i] - statistics.mean(values)) ** 2 for i in range(len(values)))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.001:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
            
        # Predict 24h ahead
        future_seconds = 24 * 3600
        prediction_24h = slope * (time_numeric[-1] + future_seconds) + intercept
        
        # Simple confidence interval (could be improved)
        std_error = np.std([values[i] - y_pred[i] for i in range(len(values))])
        confidence_interval = (prediction_24h - 2 * std_error, prediction_24h + 2 * std_error)
        
        # Count anomalies (simple z-score method)
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        anomalies = 0
        if std_val > 0:
            anomalies = sum(1 for v in values if abs((v - mean_val) / std_val) > 2)
            
        return TrendAnalysis(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=abs(r_squared),
            slope=slope,
            r_squared=r_squared,
            prediction_24h=prediction_24h,
            confidence_interval=confidence_interval,
            anomalies_detected=anomalies,
            analysis_period_hours=hours,
            data_points=len(data_points)
        )
        
    async def _alert_cleanup_loop(self):
        """Clean up old resolved alerts"""
        while self.alerting_active:
            try:
                # Clean up alerts older than 30 days
                cutoff_time = datetime.now() - timedelta(days=30)
                
                self.alert_history = [
                    alert for alert in self.alert_history 
                    if alert.resolved_at and alert.resolved_at > cutoff_time
                ]
                
                await asyncio.sleep(86400)  # Clean up daily
                
            except Exception as e:
                logger.error(f"Error in alert cleanup loop: {e}")
                await asyncio.sleep(86400)


# Example configuration
default_config = AlertingConfiguration(
    email_smtp_server="smtp.gmail.com",
    email_smtp_port=587,
    email_username="alerts@example.com",
    email_password="password",
    slack_webhook_url="https://hooks.slack.com/services/...",
    default_notification_channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
    alert_aggregation_window_minutes=5,
    max_alerts_per_hour=10,
    enable_predictive_alerting=True
)

# Global instance
alerting_service = PerformanceAlertingService(default_config)