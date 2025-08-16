"""
Comprehensive tests for the performance monitoring and optimization system.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from app.services.performance_monitoring_service import (
    PerformanceMonitoringService, PerformanceMetric, PerformanceMetricType,
    AlertSeverity, performance_monitor
)
from app.services.performance_regression_detector import (
    PerformanceRegressionDetector, RegressionType, regression_detector
)
from app.services.performance_optimization_engine import (
    PerformanceOptimizationEngine, SystemProfile, OptimizationCategory,
    ImpactLevel, EffortLevel, optimization_engine
)
from app.services.bottleneck_analyzer import (
    BottleneckAnalyzer, ComponentMetrics, BottleneckType, BottleneckSeverity,
    bottleneck_analyzer
)
from app.services.performance_alerting_service import (
    PerformanceAlertingService, AlertingConfiguration, AlertRule, AlertType,
    NotificationChannel, alerting_service
)


class TestPerformanceMonitoringService:
    """Test performance monitoring service"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create a fresh monitoring service instance"""
        service = PerformanceMonitoringService()
        yield service
        # Cleanup
        service.monitoring_active = False
        
    @pytest.mark.asyncio
    async def test_record_metric(self, monitoring_service):
        """Test recording performance metrics"""
        metric = PerformanceMetric(
            metric_type=PerformanceMetricType.CPU_USAGE,
            value=75.5,
            timestamp=datetime.now(),
            context={"component": "test"},
            tags={"source": "test"}
        )
        
        await monitoring_service.record_metric(metric)
        
        assert len(monitoring_service.metrics_storage) == 1
        assert monitoring_service.metrics_storage[0].value == 75.5
        
    @pytest.mark.asyncio
    async def test_performance_status(self, monitoring_service):
        """Test getting performance status"""
        # Add some test metrics
        for i in range(5):
            metric = PerformanceMetric(
                metric_type=PerformanceMetricType.RESPONSE_TIME,
                value=float(i),
                timestamp=datetime.now(),
                context={},
                tags={}
            )
            await monitoring_service.record_metric(metric)
            
        status = await monitoring_service.get_current_performance_status()
        
        assert "timestamp" in status
        assert "monitoring_active" in status
        assert "performance_summary" in status
        assert PerformanceMetricType.RESPONSE_TIME.value in status["performance_summary"]
        
    @pytest.mark.asyncio
    async def test_regression_detection(self, monitoring_service):
        """Test performance regression detection"""
        # Create baseline metrics (good performance)
        baseline_time = datetime.now() - timedelta(hours=2)
        for i in range(20):
            metric = PerformanceMetric(
                metric_type=PerformanceMetricType.RESPONSE_TIME,
                value=1.0 + np.random.normal(0, 0.1),  # Around 1 second
                timestamp=baseline_time + timedelta(minutes=i),
                context={},
                tags={}
            )
            monitoring_service.metrics_storage.append(metric)
            
        # Create recent metrics (degraded performance)
        recent_time = datetime.now() - timedelta(minutes=30)
        for i in range(10):
            metric = PerformanceMetric(
                metric_type=PerformanceMetricType.RESPONSE_TIME,
                value=3.0 + np.random.normal(0, 0.2),  # Around 3 seconds (degraded)
                timestamp=recent_time + timedelta(minutes=i),
                context={},
                tags={}
            )
            monitoring_service.metrics_storage.append(metric)
            
        # Test regression detection
        regression = await monitoring_service.detect_performance_regression(
            PerformanceMetricType.RESPONSE_TIME, lookback_hours=3
        )
        
        assert regression is not None
        assert regression["regression_detected"] is True
        assert regression["degradation_percentage"] > 50  # Should detect significant degradation
        
    @pytest.mark.asyncio
    async def test_alert_generation(self, monitoring_service):
        """Test alert generation for threshold violations"""
        # Record high CPU usage metric
        metric = PerformanceMetric(
            metric_type=PerformanceMetricType.CPU_USAGE,
            value=95.0,  # Above threshold
            timestamp=datetime.now(),
            context={"component": "test"},
            tags={}
        )
        
        await monitoring_service.record_metric(metric)
        
        # Check if alert was generated
        assert len(monitoring_service.alerts) > 0
        alert = monitoring_service.alerts[0]
        assert alert.metric_type == PerformanceMetricType.CPU_USAGE
        assert alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        
    @pytest.mark.asyncio
    async def test_baseline_updates(self, monitoring_service):
        """Test baseline calculation and updates"""
        # Add sufficient metrics for baseline calculation
        for i in range(100):
            metric = PerformanceMetric(
                metric_type=PerformanceMetricType.MEMORY_USAGE,
                value=50.0 + np.random.normal(0, 5),
                timestamp=datetime.now() - timedelta(minutes=i),
                context={},
                tags={}
            )
            monitoring_service.metrics_storage.append(metric)
            
        await monitoring_service._update_baselines()
        
        assert PerformanceMetricType.MEMORY_USAGE in monitoring_service.baselines
        baseline = monitoring_service.baselines[PerformanceMetricType.MEMORY_USAGE]
        assert 45 < baseline.mean < 55  # Should be around 50
        assert baseline.sample_count == 100


class TestPerformanceRegressionDetector:
    """Test performance regression detection"""
    
    @pytest.fixture
    def detector(self):
        return PerformanceRegressionDetector()
        
    @pytest.mark.asyncio
    async def test_statistical_significance_test(self, detector):
        """Test statistical significance testing"""
        # Create baseline and degraded data
        baseline = np.random.normal(1.0, 0.1, 50)  # Mean ~1.0
        current = np.random.normal(2.0, 0.1, 50)   # Mean ~2.0 (degraded)
        
        result = await detector._statistical_significance_test(baseline, current)
        
        assert result["significant_degradation"] is True
        assert result["p_value"] < 0.05
        assert result["current_mean"] > result["baseline_mean"]
        
    @pytest.mark.asyncio
    async def test_change_point_detection(self, detector):
        """Test change point detection"""
        # Create data with a clear change point
        values = np.concatenate([
            np.random.normal(1.0, 0.1, 50),  # Stable period
            np.random.normal(3.0, 0.1, 50)   # Changed period
        ])
        
        result = await detector._change_point_detection(values)
        
        assert result["change_points_detected"] is True
        assert len(result["change_point_indices"]) > 0
        
    @pytest.mark.asyncio
    async def test_anomaly_detection(self, detector):
        """Test anomaly detection"""
        # Create mostly normal data with some outliers
        normal_data = np.random.normal(1.0, 0.1, 90)
        outliers = np.array([5.0, -2.0, 6.0, -3.0])  # Clear outliers
        values = np.concatenate([normal_data, outliers])
        
        result = await detector._anomaly_detection(values)
        
        assert result["anomalies_detected"] is True
        assert len(result["anomaly_indices"]) > 0
        
    @pytest.mark.asyncio
    async def test_full_regression_detection(self, detector):
        """Test complete regression detection workflow"""
        # Create time series data with regression
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(48, 0, -1)]
        
        # Baseline period (first 24 hours) - good performance
        baseline_values = [1.0 + np.random.normal(0, 0.1) for _ in range(24)]
        
        # Recent period (last 24 hours) - degraded performance
        recent_values = [2.5 + np.random.normal(0, 0.2) for _ in range(24)]
        
        metric_data = []
        for i, (ts, val) in enumerate(zip(timestamps, baseline_values + recent_values)):
            metric_data.append({
                'timestamp': ts.isoformat(),
                'value': val
            })
            
        result = await detector.detect_regression(metric_data, "test_metric")
        
        assert result.regression_detected is True
        assert result.degradation_percentage > 50
        assert result.confidence_score > 0.5
        assert len(result.recommendations) > 0


class TestPerformanceOptimizationEngine:
    """Test performance optimization engine"""
    
    @pytest.fixture
    def engine(self):
        return PerformanceOptimizationEngine()
        
    @pytest.mark.asyncio
    async def test_cpu_optimization_suggestion(self, engine):
        """Test CPU optimization suggestion generation"""
        profile = SystemProfile(
            cpu_usage_avg=85.0,  # High CPU usage
            memory_usage_avg=60.0,
            disk_io_rate=1000000,
            network_io_rate=1000000,
            database_query_time_avg=0.5,
            cache_hit_rate=0.9,
            error_rate=0.01,
            response_time_p95=1.5,
            throughput=100,
            active_connections=50,
            queue_depth=10
        )
        
        suggestions = await engine.generate_suggestions(profile)
        
        # Should generate CPU optimization suggestion
        cpu_suggestions = [s for s in suggestions if s.category == OptimizationCategory.CPU_OPTIMIZATION]
        assert len(cpu_suggestions) > 0
        
        cpu_suggestion = cpu_suggestions[0]
        assert cpu_suggestion.impact_level in [ImpactLevel.HIGH, ImpactLevel.MEDIUM]
        assert len(cpu_suggestion.implementation_steps) > 0
        assert len(cpu_suggestion.code_examples) > 0
        
    @pytest.mark.asyncio
    async def test_memory_optimization_suggestion(self, engine):
        """Test memory optimization suggestion generation"""
        profile = SystemProfile(
            cpu_usage_avg=50.0,
            memory_usage_avg=90.0,  # High memory usage
            disk_io_rate=1000000,
            network_io_rate=1000000,
            database_query_time_avg=0.5,
            cache_hit_rate=0.9,
            error_rate=0.01,
            response_time_p95=1.5,
            throughput=100,
            active_connections=50,
            queue_depth=10
        )
        
        suggestions = await engine.generate_suggestions(profile)
        
        # Should generate memory optimization suggestion
        memory_suggestions = [s for s in suggestions if s.category == OptimizationCategory.MEMORY_MANAGEMENT]
        assert len(memory_suggestions) > 0
        
        memory_suggestion = memory_suggestions[0]
        assert memory_suggestion.impact_level == ImpactLevel.HIGH
        assert "memory" in memory_suggestion.title.lower()
        
    @pytest.mark.asyncio
    async def test_database_optimization_suggestion(self, engine):
        """Test database optimization suggestion generation"""
        profile = SystemProfile(
            cpu_usage_avg=50.0,
            memory_usage_avg=60.0,
            disk_io_rate=1000000,
            network_io_rate=1000000,
            database_query_time_avg=5.0,  # Slow database queries
            cache_hit_rate=0.9,
            error_rate=0.01,
            response_time_p95=1.5,
            throughput=100,
            active_connections=50,
            queue_depth=10
        )
        
        suggestions = await engine.generate_suggestions(profile)
        
        # Should generate database optimization suggestion
        db_suggestions = [s for s in suggestions if s.category == OptimizationCategory.DATABASE]
        assert len(db_suggestions) > 0
        
    @pytest.mark.asyncio
    async def test_suggestion_prioritization(self, engine):
        """Test suggestion prioritization by impact/effort ratio"""
        profile = SystemProfile(
            cpu_usage_avg=85.0,
            memory_usage_avg=85.0,
            disk_io_rate=1000000,
            network_io_rate=1000000,
            database_query_time_avg=3.0,
            cache_hit_rate=0.5,  # Low cache hit rate
            error_rate=0.01,
            response_time_p95=1.5,
            throughput=50,  # Low throughput
            active_connections=50,
            queue_depth=10
        )
        
        suggestions = await engine.generate_suggestions(profile)
        
        # Should have multiple suggestions
        assert len(suggestions) > 1
        
        # Should be sorted by priority score
        for i in range(len(suggestions) - 1):
            assert suggestions[i].priority_score >= suggestions[i + 1].priority_score
            
    @pytest.mark.asyncio
    async def test_implementation_tracking(self, engine):
        """Test tracking of implemented suggestions"""
        suggestion_id = "test_suggestion_123"
        
        # Mark as implemented
        await engine.mark_suggestion_implemented(suggestion_id)
        
        assert suggestion_id in engine.implemented_suggestions
        
        # Check implementation status
        status = await engine.get_implementation_status()
        assert status["implemented_count"] == 1


class TestBottleneckAnalyzer:
    """Test bottleneck analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        return BottleneckAnalyzer()
        
    @pytest.mark.asyncio
    async def test_cpu_bottleneck_detection(self, analyzer):
        """Test CPU bottleneck detection"""
        # Create metrics with high CPU usage
        for i in range(20):
            metrics = ComponentMetrics(
                component_name="test_component",
                response_times=[],
                throughput=0.0,
                error_rate=0.0,
                resource_usage={"cpu_usage": 90.0 + np.random.normal(0, 2)},
                queue_depth=0,
                active_connections=0,
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            await analyzer.record_component_metrics(metrics)
            
        bottlenecks = await analyzer.analyze_component("test_component")
        
        # Should detect CPU bottleneck
        cpu_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.CPU_BOUND]
        assert len(cpu_bottlenecks) > 0
        
        cpu_bottleneck = cpu_bottlenecks[0]
        assert cpu_bottleneck.severity in [BottleneckSeverity.HIGH, BottleneckSeverity.CRITICAL]
        assert "cpu" in cpu_bottleneck.description.lower()
        
    @pytest.mark.asyncio
    async def test_database_bottleneck_detection(self, analyzer):
        """Test database bottleneck detection"""
        # Create metrics for database component with slow response times
        for i in range(20):
            metrics = ComponentMetrics(
                component_name="database_service",
                response_times=[3.0 + np.random.normal(0, 0.5) for _ in range(5)],  # Slow responses
                throughput=10.0,
                error_rate=0.02,
                resource_usage={},
                queue_depth=0,
                active_connections=50,
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            await analyzer.record_component_metrics(metrics)
            
        bottlenecks = await analyzer.analyze_component("database_service")
        
        # Should detect database bottleneck
        db_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.DATABASE_BOUND]
        assert len(db_bottlenecks) > 0
        
        db_bottleneck = db_bottlenecks[0]
        assert "database" in db_bottleneck.description.lower() or "slow" in db_bottleneck.description.lower()
        
    @pytest.mark.asyncio
    async def test_queue_bottleneck_detection(self, analyzer):
        """Test queue bottleneck detection"""
        # Create metrics with high queue depth
        for i in range(20):
            metrics = ComponentMetrics(
                component_name="queue_processor",
                response_times=[],
                throughput=0.0,
                error_rate=0.0,
                resource_usage={},
                queue_depth=200 + int(np.random.normal(0, 20)),  # High queue depth
                active_connections=0,
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            await analyzer.record_component_metrics(metrics)
            
        bottlenecks = await analyzer.analyze_component("queue_processor")
        
        # Should detect queue bottleneck
        queue_bottlenecks = [b for b in bottlenecks if b.bottleneck_type == BottleneckType.QUEUE_BACKLOG]
        assert len(queue_bottlenecks) > 0
        
        queue_bottleneck = queue_bottlenecks[0]
        assert "queue" in queue_bottleneck.description.lower()
        
    @pytest.mark.asyncio
    async def test_system_report_generation(self, analyzer):
        """Test system bottleneck report generation"""
        # Add metrics for multiple components
        components = ["web_server", "database", "cache", "queue_processor"]
        
        for component in components:
            for i in range(10):
                metrics = ComponentMetrics(
                    component_name=component,
                    response_times=[1.0 + np.random.normal(0, 0.2) for _ in range(3)],
                    throughput=50.0,
                    error_rate=0.01,
                    resource_usage={"cpu_usage": 60.0 + np.random.normal(0, 10)},
                    queue_depth=20,
                    active_connections=30,
                    timestamp=datetime.now() - timedelta(minutes=i)
                )
                await analyzer.record_component_metrics(metrics)
                
        report = await analyzer.generate_system_report()
        
        assert report.report_id is not None
        assert 0 <= report.system_health_score <= 100
        assert len(report.performance_trends) > 0
        assert len(report.recommendations) > 0


class TestPerformanceAlertingService:
    """Test performance alerting service"""
    
    @pytest.fixture
    def alerting_config(self):
        return AlertingConfiguration(
            email_smtp_server="smtp.test.com",
            email_smtp_port=587,
            email_username="test@test.com",
            email_password="password",
            slack_webhook_url="https://hooks.slack.com/test",
            default_notification_channels=[NotificationChannel.EMAIL],
            alert_aggregation_window_minutes=5,
            max_alerts_per_hour=10,
            enable_predictive_alerting=True
        )
        
    @pytest.fixture
    def alerting_service_instance(self, alerting_config):
        service = PerformanceAlertingService(alerting_config)
        yield service
        service.alerting_active = False
        
    @pytest.mark.asyncio
    async def test_threshold_alert_generation(self, alerting_service_instance):
        """Test threshold-based alert generation"""
        # Record metrics that exceed threshold
        for i in range(5):
            await alerting_service_instance.record_metric("cpu_usage", 85.0 + i)
            
        # Wait a moment for alert evaluation
        await asyncio.sleep(0.1)
        
        # Should have generated an alert
        active_alerts = await alerting_service_instance.get_active_alerts()
        cpu_alerts = [a for a in active_alerts if a.metric_name == "cpu_usage"]
        assert len(cpu_alerts) > 0
        
    @pytest.mark.asyncio
    async def test_alert_acknowledgment(self, alerting_service_instance):
        """Test alert acknowledgment"""
        # Generate an alert
        await alerting_service_instance.record_metric("memory_usage", 95.0)
        await asyncio.sleep(0.1)
        
        active_alerts = await alerting_service_instance.get_active_alerts()
        assert len(active_alerts) > 0
        
        alert = active_alerts[0]
        
        # Acknowledge the alert
        await alerting_service_instance.acknowledge_alert(alert.alert_id, "test_user")
        
        # Check acknowledgment
        updated_alerts = await alerting_service_instance.get_active_alerts()
        acknowledged_alert = next(a for a in updated_alerts if a.alert_id == alert.alert_id)
        assert acknowledged_alert.acknowledged_by == "test_user"
        assert acknowledged_alert.acknowledged_at is not None
        
    @pytest.mark.asyncio
    async def test_alert_resolution(self, alerting_service_instance):
        """Test alert resolution"""
        # Generate an alert
        await alerting_service_instance.record_metric("error_rate", 0.1)
        await asyncio.sleep(0.1)
        
        active_alerts = await alerting_service_instance.get_active_alerts()
        assert len(active_alerts) > 0
        
        alert = active_alerts[0]
        
        # Resolve the alert
        await alerting_service_instance.resolve_alert(alert.alert_id)
        
        # Check resolution
        updated_alerts = await alerting_service_instance.get_active_alerts()
        assert alert.alert_id not in [a.alert_id for a in updated_alerts]
        
    @pytest.mark.asyncio
    async def test_trend_analysis(self, alerting_service_instance):
        """Test trend analysis functionality"""
        # Record trending data
        base_time = datetime.now() - timedelta(hours=2)
        for i in range(50):
            # Create increasing trend
            value = 1.0 + (i * 0.1) + np.random.normal(0, 0.05)
            timestamp = base_time + timedelta(minutes=i * 2)
            
            await alerting_service_instance.record_metric("response_time", value)
            
        trend = await alerting_service_instance.get_trend_analysis("response_time", 2)
        
        assert trend is not None
        assert trend.trend_direction == "increasing"
        assert trend.trend_strength > 0.5  # Should detect strong trend
        
    @pytest.mark.asyncio
    async def test_rate_limiting(self, alerting_service_instance):
        """Test alert rate limiting"""
        # Try to generate many alerts quickly
        for i in range(15):  # More than max_alerts_per_hour (10)
            await alerting_service_instance.record_metric("cpu_usage", 90.0)
            await asyncio.sleep(0.01)
            
        # Should be rate limited
        active_alerts = await alerting_service_instance.get_active_alerts()
        cpu_alerts = [a for a in active_alerts if a.metric_name == "cpu_usage"]
        assert len(cpu_alerts) <= alerting_service_instance.config.max_alerts_per_hour


class TestIntegration:
    """Integration tests for the complete performance monitoring system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_workflow(self):
        """Test complete monitoring workflow from metric recording to optimization"""
        # 1. Record performance metrics
        monitoring_service = PerformanceMonitoringService()
        
        # Simulate degrading performance over time
        base_time = datetime.now() - timedelta(hours=2)
        for i in range(60):
            # CPU usage gradually increasing
            cpu_value = 50.0 + (i * 0.5) + np.random.normal(0, 2)
            cpu_metric = PerformanceMetric(
                metric_type=PerformanceMetricType.CPU_USAGE,
                value=min(cpu_value, 100.0),
                timestamp=base_time + timedelta(minutes=i),
                context={"component": "web_server"},
                tags={"source": "integration_test"}
            )
            await monitoring_service.record_metric(cpu_metric)
            
            # Response time also increasing
            response_value = 0.5 + (i * 0.02) + np.random.normal(0, 0.05)
            response_metric = PerformanceMetric(
                metric_type=PerformanceMetricType.RESPONSE_TIME,
                value=max(response_value, 0.1),
                timestamp=base_time + timedelta(minutes=i),
                context={"component": "web_server"},
                tags={"source": "integration_test"}
            )
            await monitoring_service.record_metric(response_metric)
            
        # 2. Check performance status
        status = await monitoring_service.get_current_performance_status()
        assert status["monitoring_active"] is False  # Not started yet
        assert len(status["performance_summary"]) > 0
        
        # 3. Detect regression
        regression = await monitoring_service.detect_performance_regression(
            PerformanceMetricType.CPU_USAGE, lookback_hours=2
        )
        assert regression is not None
        
        # 4. Generate optimization suggestions
        engine = PerformanceOptimizationEngine()
        profile = SystemProfile(
            cpu_usage_avg=80.0,  # High from our test data
            memory_usage_avg=60.0,
            disk_io_rate=1000000,
            network_io_rate=1000000,
            database_query_time_avg=1.0,
            cache_hit_rate=0.8,
            error_rate=0.02,
            response_time_p95=2.0,  # High from our test data
            throughput=50,
            active_connections=100,
            queue_depth=20
        )
        
        suggestions = await engine.generate_suggestions(profile)
        assert len(suggestions) > 0
        
        # Should have CPU optimization suggestion
        cpu_suggestions = [s for s in suggestions if s.category == OptimizationCategory.CPU_OPTIMIZATION]
        assert len(cpu_suggestions) > 0
        
        # 5. Analyze bottlenecks
        analyzer = BottleneckAnalyzer()
        
        # Record component metrics
        for i in range(20):
            metrics = ComponentMetrics(
                component_name="web_server",
                response_times=[1.5 + np.random.normal(0, 0.2) for _ in range(3)],
                throughput=50.0,
                error_rate=0.02,
                resource_usage={"cpu_usage": 80.0 + np.random.normal(0, 5)},
                queue_depth=25,
                active_connections=100,
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            await analyzer.record_component_metrics(metrics)
            
        bottlenecks = await analyzer.analyze_component("web_server")
        assert len(bottlenecks) > 0
        
        # 6. Generate system report
        report = await analyzer.generate_system_report()
        assert report.system_health_score < 100  # Should detect issues
        assert len(report.recommendations) > 0
        
        print(f"Integration test completed successfully:")
        print(f"- Recorded {len(monitoring_service.metrics_storage)} metrics")
        print(f"- Detected regression: {regression['regression_detected'] if regression else 'None'}")
        print(f"- Generated {len(suggestions)} optimization suggestions")
        print(f"- Found {len(bottlenecks)} bottlenecks")
        print(f"- System health score: {report.system_health_score:.1f}")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__ + "::TestIntegration::test_end_to_end_monitoring_workflow", "-v"])