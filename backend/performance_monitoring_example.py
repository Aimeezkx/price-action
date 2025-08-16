"""
Performance Monitoring System Example

Demonstrates the complete performance monitoring and optimization system
including real-time monitoring, regression detection, optimization suggestions,
bottleneck analysis, and alerting.
"""

import asyncio
import time
import random
import logging
from datetime import datetime, timedelta
import numpy as np

from app.services.performance_monitoring_service import (
    performance_monitor, PerformanceMetric, PerformanceMetricType
)
from app.services.performance_regression_detector import regression_detector
from app.services.performance_optimization_engine import (
    optimization_engine, SystemProfile
)
from app.services.bottleneck_analyzer import (
    bottleneck_analyzer, ComponentMetrics
)
from app.services.performance_alerting_service import (
    alerting_service, AlertingConfiguration, NotificationChannel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitoringDemo:
    """Demonstration of the performance monitoring system"""
    
    def __init__(self):
        self.demo_running = False
        self.components = ["web_server", "database", "cache", "queue_processor", "api_gateway"]
        
    async def run_demo(self):
        """Run the complete performance monitoring demonstration"""
        logger.info("Starting Performance Monitoring System Demo")
        
        try:
            # 1. Start monitoring services
            await self.start_monitoring_services()
            
            # 2. Simulate system load and performance data
            await self.simulate_system_performance()
            
            # 3. Demonstrate regression detection
            await self.demonstrate_regression_detection()
            
            # 4. Generate optimization suggestions
            await self.demonstrate_optimization_suggestions()
            
            # 5. Analyze bottlenecks
            await self.demonstrate_bottleneck_analysis()
            
            # 6. Show alerting functionality
            await self.demonstrate_alerting()
            
            # 7. Generate comprehensive report
            await self.generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
        finally:
            await self.stop_monitoring_services()
            
        logger.info("Performance Monitoring System Demo completed")
        
    async def start_monitoring_services(self):
        """Start all monitoring services"""
        logger.info("Starting monitoring services...")
        
        # Start performance monitoring
        await performance_monitor.start_monitoring()
        
        # Start bottleneck analysis
        await bottleneck_analyzer.start_analysis()
        
        # Start alerting service
        await alerting_service.start_alerting()
        
        logger.info("All monitoring services started")
        
    async def stop_monitoring_services(self):
        """Stop all monitoring services"""
        logger.info("Stopping monitoring services...")
        
        await performance_monitor.stop_monitoring()
        await bottleneck_analyzer.stop_analysis()
        await alerting_service.stop_alerting()
        
        logger.info("All monitoring services stopped")
        
    async def simulate_system_performance(self):
        """Simulate realistic system performance data"""
        logger.info("Simulating system performance data...")
        
        # Simulate 2 hours of performance data
        start_time = datetime.now() - timedelta(hours=2)
        
        for minute in range(120):  # 2 hours
            current_time = start_time + timedelta(minutes=minute)
            
            # Simulate gradual performance degradation
            degradation_factor = 1.0 + (minute / 120.0) * 0.5  # Up to 50% degradation
            
            # CPU Usage (gradually increasing)
            cpu_base = 40.0
            cpu_value = cpu_base * degradation_factor + random.gauss(0, 5)
            cpu_value = max(0, min(100, cpu_value))
            
            await self.record_metric(
                PerformanceMetricType.CPU_USAGE,
                cpu_value,
                current_time,
                {"component": "system"}
            )
            
            # Memory Usage (with some spikes)
            memory_base = 60.0
            if minute % 30 == 0:  # Memory spike every 30 minutes
                memory_value = memory_base + 20 + random.gauss(0, 3)
            else:
                memory_value = memory_base * degradation_factor + random.gauss(0, 3)
            memory_value = max(0, min(100, memory_value))
            
            await self.record_metric(
                PerformanceMetricType.MEMORY_USAGE,
                memory_value,
                current_time,
                {"component": "system"}
            )
            
            # Response Time (increasing with load)
            response_base = 0.5
            response_value = response_base * (degradation_factor ** 2) + random.gauss(0, 0.1)
            response_value = max(0.1, response_value)
            
            await self.record_metric(
                PerformanceMetricType.RESPONSE_TIME,
                response_value,
                current_time,
                {"component": "web_server"}
            )
            
            # Database Query Time (with occasional slow queries)
            db_base = 0.2
            if random.random() < 0.05:  # 5% chance of slow query
                db_value = db_base * 10 + random.gauss(0, 0.5)
            else:
                db_value = db_base * degradation_factor + random.gauss(0, 0.05)
            db_value = max(0.01, db_value)
            
            await self.record_metric(
                PerformanceMetricType.DATABASE_QUERY_TIME,
                db_value,
                current_time,
                {"component": "database"}
            )
            
            # Search Response Time
            search_base = 0.3
            search_value = search_base * degradation_factor + random.gauss(0, 0.08)
            search_value = max(0.05, search_value)
            
            await self.record_metric(
                PerformanceMetricType.SEARCH_RESPONSE_TIME,
                search_value,
                current_time,
                {"component": "search_service"}
            )
            
            # Document Processing Time (varies by document size)
            doc_base = 15.0
            doc_size_factor = random.uniform(0.5, 2.0)  # Simulate different document sizes
            doc_value = doc_base * doc_size_factor * degradation_factor + random.gauss(0, 2)
            doc_value = max(1.0, doc_value)
            
            await self.record_metric(
                PerformanceMetricType.DOCUMENT_PROCESSING_TIME,
                doc_value,
                current_time,
                {"component": "document_processor"}
            )
            
            # Record component metrics for bottleneck analysis
            for component in self.components:
                await self.record_component_metrics(component, current_time, degradation_factor)
                
        logger.info("Completed simulating 2 hours of performance data")
        
    async def record_metric(self, metric_type: PerformanceMetricType, value: float, 
                          timestamp: datetime, context: dict):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=timestamp,
            context=context,
            tags={"source": "demo"}
        )
        
        await performance_monitor.record_metric(metric)
        
        # Also record for alerting service
        await alerting_service.record_metric(metric_type.value, value, timestamp)
        
    async def record_component_metrics(self, component: str, timestamp: datetime, 
                                     degradation_factor: float):
        """Record component-specific metrics"""
        # Generate component-specific response times
        base_response = {"web_server": 0.5, "database": 0.2, "cache": 0.05, 
                        "queue_processor": 1.0, "api_gateway": 0.3}.get(component, 0.5)
        
        response_times = []
        for _ in range(random.randint(1, 5)):
            response_time = base_response * degradation_factor + random.gauss(0, base_response * 0.2)
            response_times.append(max(0.01, response_time))
            
        # Generate other metrics
        throughput = random.uniform(50, 200) / degradation_factor
        error_rate = min(0.1, 0.001 * degradation_factor + random.gauss(0, 0.005))
        error_rate = max(0, error_rate)
        
        resource_usage = {
            "cpu_usage": 40 * degradation_factor + random.gauss(0, 5),
            "memory_usage": 50 * degradation_factor + random.gauss(0, 8)
        }
        
        queue_depth = int(10 * degradation_factor + random.gauss(0, 5))
        queue_depth = max(0, queue_depth)
        
        active_connections = int(50 * degradation_factor + random.gauss(0, 10))
        active_connections = max(0, active_connections)
        
        metrics = ComponentMetrics(
            component_name=component,
            response_times=response_times,
            throughput=throughput,
            error_rate=error_rate,
            resource_usage=resource_usage,
            queue_depth=queue_depth,
            active_connections=active_connections,
            timestamp=timestamp
        )
        
        await bottleneck_analyzer.record_component_metrics(metrics)
        
    async def demonstrate_regression_detection(self):
        """Demonstrate performance regression detection"""
        logger.info("Demonstrating regression detection...")
        
        # Test regression detection for different metrics
        metrics_to_test = [
            PerformanceMetricType.CPU_USAGE,
            PerformanceMetricType.RESPONSE_TIME,
            PerformanceMetricType.DATABASE_QUERY_TIME
        ]
        
        for metric_type in metrics_to_test:
            regression = await performance_monitor.detect_performance_regression(
                metric_type, lookback_hours=2
            )
            
            if regression and regression.get("regression_detected"):
                logger.warning(f"REGRESSION DETECTED for {metric_type.value}:")
                logger.warning(f"  - Degradation: {regression['degradation_percentage']:.1f}%")
                logger.warning(f"  - Baseline mean: {regression['baseline_mean']:.3f}")
                logger.warning(f"  - Current mean: {regression['recent_mean']:.3f}")
            else:
                logger.info(f"No regression detected for {metric_type.value}")
                
    async def demonstrate_optimization_suggestions(self):
        """Demonstrate optimization suggestion generation"""
        logger.info("Generating optimization suggestions...")
        
        # Get current performance status
        status = await performance_monitor.get_current_performance_status()
        
        # Create system profile from current metrics
        cpu_avg = 75.0  # Simulated high CPU usage
        memory_avg = 80.0  # Simulated high memory usage
        
        profile = SystemProfile(
            cpu_usage_avg=cpu_avg,
            memory_usage_avg=memory_avg,
            disk_io_rate=50 * 1024 * 1024,  # 50 MB/s
            network_io_rate=20 * 1024 * 1024,  # 20 MB/s
            database_query_time_avg=1.5,  # Slow queries
            cache_hit_rate=0.7,  # Low cache hit rate
            error_rate=0.03,  # 3% error rate
            response_time_p95=2.5,  # Slow response times
            throughput=80,  # Moderate throughput
            active_connections=150,
            queue_depth=50
        )
        
        suggestions = await optimization_engine.generate_suggestions(profile)
        
        logger.info(f"Generated {len(suggestions)} optimization suggestions:")
        
        for i, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
            logger.info(f"\n{i}. {suggestion.title}")
            logger.info(f"   Category: {suggestion.category.value}")
            logger.info(f"   Impact: {suggestion.impact_level.value}, Effort: {suggestion.effort_level.value}")
            logger.info(f"   Priority Score: {suggestion.priority_score:.2f}")
            logger.info(f"   Expected Improvement: {suggestion.expected_improvement}")
            logger.info(f"   Implementation Steps:")
            for step in suggestion.implementation_steps[:3]:  # Show first 3 steps
                logger.info(f"     - {step}")
                
    async def demonstrate_bottleneck_analysis(self):
        """Demonstrate bottleneck analysis"""
        logger.info("Analyzing system bottlenecks...")
        
        # Analyze bottlenecks for each component
        all_bottlenecks = []
        
        for component in self.components:
            bottlenecks = await bottleneck_analyzer.analyze_component(component)
            all_bottlenecks.extend(bottlenecks)
            
            if bottlenecks:
                logger.warning(f"Bottlenecks found in {component}:")
                for bottleneck in bottlenecks:
                    logger.warning(f"  - {bottleneck.bottleneck_type.value}: {bottleneck.description}")
                    logger.warning(f"    Severity: {bottleneck.severity.value}")
                    logger.warning(f"    Impact Score: {bottleneck.impact_score:.2f}")
            else:
                logger.info(f"No bottlenecks detected in {component}")
                
        # Generate system report
        report = await bottleneck_analyzer.generate_system_report()
        
        logger.info(f"\nSystem Bottleneck Report:")
        logger.info(f"  - System Health Score: {report.system_health_score:.1f}/100")
        logger.info(f"  - Total Bottlenecks: {len(report.bottlenecks)}")
        logger.info(f"  - Performance Trends: {report.performance_trends}")
        logger.info(f"  - Recommendations:")
        for rec in report.recommendations:
            logger.info(f"    • {rec}")
            
    async def demonstrate_alerting(self):
        """Demonstrate alerting functionality"""
        logger.info("Demonstrating alerting system...")
        
        # Record some metrics that should trigger alerts
        await alerting_service.record_metric("cpu_usage", 95.0)  # Critical CPU
        await alerting_service.record_metric("memory_usage", 92.0)  # Critical memory
        await alerting_service.record_metric("error_rate", 0.08)  # High error rate
        
        # Wait for alert processing
        await asyncio.sleep(1)
        
        # Get active alerts
        active_alerts = await alerting_service.get_active_alerts()
        
        logger.info(f"Active alerts: {len(active_alerts)}")
        
        for alert in active_alerts:
            logger.warning(f"ALERT: {alert.title}")
            logger.warning(f"  - Severity: {alert.severity.value}")
            logger.warning(f"  - Metric: {alert.metric_name} = {alert.current_value}")
            logger.warning(f"  - Threshold: {alert.threshold_value}")
            logger.warning(f"  - Created: {alert.created_at}")
            
        # Demonstrate alert acknowledgment
        if active_alerts:
            alert = active_alerts[0]
            await alerting_service.acknowledge_alert(alert.alert_id, "demo_user")
            logger.info(f"Acknowledged alert: {alert.alert_id}")
            
        # Show trend analysis
        trend = await alerting_service.get_trend_analysis("cpu_usage", 2)
        if trend:
            logger.info(f"\nCPU Usage Trend Analysis:")
            logger.info(f"  - Direction: {trend.trend_direction}")
            logger.info(f"  - Strength: {trend.trend_strength:.2f}")
            logger.info(f"  - 24h Prediction: {trend.prediction_24h:.1f}%")
            logger.info(f"  - Anomalies: {trend.anomalies_detected}")
            
    async def generate_comprehensive_report(self):
        """Generate a comprehensive performance report"""
        logger.info("Generating comprehensive performance report...")
        
        # Get performance status
        status = await performance_monitor.get_current_performance_status()
        
        # Get optimization suggestions
        profile = SystemProfile(
            cpu_usage_avg=75.0,
            memory_usage_avg=80.0,
            disk_io_rate=50 * 1024 * 1024,
            network_io_rate=20 * 1024 * 1024,
            database_query_time_avg=1.5,
            cache_hit_rate=0.7,
            error_rate=0.03,
            response_time_p95=2.5,
            throughput=80,
            active_connections=150,
            queue_depth=50
        )
        suggestions = await optimization_engine.generate_suggestions(profile)
        
        # Get bottleneck report
        bottleneck_report = await bottleneck_analyzer.generate_system_report()
        
        # Get active alerts
        active_alerts = await alerting_service.get_active_alerts()
        
        # Generate summary report
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE PERFORMANCE MONITORING REPORT")
        logger.info("="*80)
        
        logger.info(f"\n📊 SYSTEM OVERVIEW:")
        logger.info(f"  • Monitoring Active: {status['monitoring_active']}")
        logger.info(f"  • Total Metrics Collected: {status['metrics_count']}")
        logger.info(f"  • System Health Score: {bottleneck_report.system_health_score:.1f}/100")
        logger.info(f"  • Active Alerts: {len(active_alerts)}")
        
        logger.info(f"\n⚡ PERFORMANCE METRICS:")
        for metric_name, metric_data in status.get('performance_summary', {}).items():
            if metric_data:
                logger.info(f"  • {metric_name}:")
                logger.info(f"    - Current: {metric_data.get('current', 'N/A')}")
                logger.info(f"    - Average: {metric_data.get('average', 'N/A'):.2f}")
                logger.info(f"    - Range: {metric_data.get('min', 'N/A'):.2f} - {metric_data.get('max', 'N/A'):.2f}")
                
        logger.info(f"\n🚨 CRITICAL ISSUES:")
        critical_alerts = [a for a in active_alerts if a.severity.value == "critical"]
        if critical_alerts:
            for alert in critical_alerts:
                logger.info(f"  • {alert.title}: {alert.current_value} (threshold: {alert.threshold_value})")
        else:
            logger.info("  • No critical issues detected")
            
        logger.info(f"\n🔍 BOTTLENECKS IDENTIFIED:")
        critical_bottlenecks = [b for b in bottleneck_report.bottlenecks 
                              if b.severity.value in ["high", "critical"]]
        if critical_bottlenecks:
            for bottleneck in critical_bottlenecks[:5]:
                logger.info(f"  • {bottleneck.component}: {bottleneck.description}")
        else:
            logger.info("  • No critical bottlenecks detected")
            
        logger.info(f"\n💡 TOP OPTIMIZATION RECOMMENDATIONS:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            logger.info(f"  {i}. {suggestion.title}")
            logger.info(f"     Impact: {suggestion.impact_level.value}, "
                       f"Effort: {suggestion.effort_level.value}, "
                       f"Priority: {suggestion.priority_score:.2f}")
            
        logger.info(f"\n📈 PERFORMANCE TRENDS:")
        for component, trend in bottleneck_report.performance_trends.items():
            logger.info(f"  • {component}: {trend}")
            
        logger.info(f"\n🎯 NEXT ACTIONS:")
        for rec in bottleneck_report.recommendations[:5]:
            logger.info(f"  • {rec}")
            
        logger.info("\n" + "="*80)
        logger.info("END OF REPORT")
        logger.info("="*80)


async def main():
    """Main demo function"""
    demo = PerformanceMonitoringDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())