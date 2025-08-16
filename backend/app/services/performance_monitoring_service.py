"""
Performance Monitoring Service

Provides real-time performance monitoring, regression detection,
optimization suggestions, and bottleneck analysis.
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceMetricType(Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    DATABASE_QUERY_TIME = "database_query_time"
    DOCUMENT_PROCESSING_TIME = "document_processing_time"
    SEARCH_RESPONSE_TIME = "search_response_time"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: PerformanceMetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any]
    tags: Dict[str, str]


@dataclass
class PerformanceBaseline:
    """Performance baseline for comparison"""
    metric_type: PerformanceMetricType
    mean: float
    std_dev: float
    percentile_95: float
    percentile_99: float
    sample_count: int
    last_updated: datetime


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    metric_type: PerformanceMetricType
    severity: AlertSeverity
    message: str
    current_value: float
    baseline_value: float
    threshold_exceeded: float
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class OptimizationSuggestion:
    """Performance optimization suggestion"""
    suggestion_id: str
    title: str
    description: str
    impact_level: str  # low, medium, high
    effort_level: str  # low, medium, high
    category: str
    implementation_steps: List[str]
    expected_improvement: str
    confidence_score: float


@dataclass
class BottleneckAnalysis:
    """Bottleneck analysis result"""
    component: str
    bottleneck_type: str
    severity: float
    description: str
    affected_operations: List[str]
    suggested_fixes: List[str]
    performance_impact: float


class PerformanceMonitoringService:
    """Main performance monitoring service"""
    
    def __init__(self):
        self.metrics_storage: List[PerformanceMetric] = []
        self.baselines: Dict[PerformanceMetricType, PerformanceBaseline] = {}
        self.alerts: List[PerformanceAlert] = []
        self.monitoring_active = False
        self.monitoring_interval = 5  # seconds
        self.data_retention_days = 30
        
        # Performance thresholds
        self.thresholds = {
            PerformanceMetricType.RESPONSE_TIME: 2.0,  # seconds
            PerformanceMetricType.CPU_USAGE: 80.0,  # percentage
            PerformanceMetricType.MEMORY_USAGE: 85.0,  # percentage
            PerformanceMetricType.DOCUMENT_PROCESSING_TIME: 30.0,  # seconds
            PerformanceMetricType.SEARCH_RESPONSE_TIME: 0.5,  # seconds
        }
        
    async def start_monitoring(self):
        """Start real-time performance monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        logger.info("Starting performance monitoring")
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_system_metrics())
        asyncio.create_task(self._analyze_performance_trends())
        asyncio.create_task(self._cleanup_old_data())
        
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        logger.info("Stopping performance monitoring")
        
    async def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        self.metrics_storage.append(metric)
        
        # Check for alerts
        await self._check_performance_alerts(metric)
        
        # Update baselines periodically
        if len(self.metrics_storage) % 100 == 0:
            await self._update_baselines()
            
    async def get_current_performance_status(self) -> Dict[str, Any]:
        """Get current performance status"""
        recent_metrics = self._get_recent_metrics(minutes=5)
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.monitoring_active,
            "metrics_count": len(recent_metrics),
            "active_alerts": len([a for a in self.alerts if 
                                (datetime.now() - a.timestamp).seconds < 3600]),
            "performance_summary": {}
        }
        
        # Calculate summary statistics for each metric type
        for metric_type in PerformanceMetricType:
            type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
            if type_metrics:
                values = [m.value for m in type_metrics]
                status["performance_summary"][metric_type.value] = {
                    "current": values[-1] if values else None,
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
                
        return status
        
    async def detect_performance_regression(self, 
                                          metric_type: PerformanceMetricType,
                                          lookback_hours: int = 24) -> Optional[Dict[str, Any]]:
        """Detect performance regression for a specific metric"""
        if metric_type not in self.baselines:
            return None
            
        baseline = self.baselines[metric_type]
        recent_metrics = self._get_recent_metrics(hours=lookback_hours)
        type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
        
        if len(type_metrics) < 10:  # Need sufficient data
            return None
            
        recent_values = [m.value for m in type_metrics]
        recent_mean = statistics.mean(recent_values)
        
        # Calculate regression score
        regression_threshold = 1.5  # 50% worse than baseline
        regression_score = recent_mean / baseline.mean
        
        if regression_score > regression_threshold:
            return {
                "metric_type": metric_type.value,
                "regression_detected": True,
                "regression_score": regression_score,
                "baseline_mean": baseline.mean,
                "recent_mean": recent_mean,
                "degradation_percentage": ((regression_score - 1) * 100),
                "sample_size": len(recent_values),
                "detection_timestamp": datetime.now().isoformat()
            }
            
        return None
        
    async def generate_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        """Generate automated optimization suggestions"""
        suggestions = []
        recent_metrics = self._get_recent_metrics(hours=1)
        
        # Analyze CPU usage patterns
        cpu_metrics = [m for m in recent_metrics 
                      if m.metric_type == PerformanceMetricType.CPU_USAGE]
        if cpu_metrics:
            avg_cpu = statistics.mean([m.value for m in cpu_metrics])
            if avg_cpu > 70:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"cpu_opt_{int(time.time())}",
                    title="High CPU Usage Optimization",
                    description=f"CPU usage averaging {avg_cpu:.1f}% over the last hour",
                    impact_level="high",
                    effort_level="medium",
                    category="system_resources",
                    implementation_steps=[
                        "Profile CPU-intensive operations",
                        "Implement caching for repeated calculations",
                        "Consider async processing for heavy tasks",
                        "Optimize database queries"
                    ],
                    expected_improvement="20-30% CPU usage reduction",
                    confidence_score=0.8
                ))
                
        # Analyze memory usage
        memory_metrics = [m for m in recent_metrics 
                         if m.metric_type == PerformanceMetricType.MEMORY_USAGE]
        if memory_metrics:
            avg_memory = statistics.mean([m.value for m in memory_metrics])
            if avg_memory > 80:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"mem_opt_{int(time.time())}",
                    title="Memory Usage Optimization",
                    description=f"Memory usage averaging {avg_memory:.1f}% over the last hour",
                    impact_level="high",
                    effort_level="medium",
                    category="memory_management",
                    implementation_steps=[
                        "Implement memory profiling",
                        "Add object pooling for frequently created objects",
                        "Optimize data structures",
                        "Implement garbage collection tuning"
                    ],
                    expected_improvement="15-25% memory usage reduction",
                    confidence_score=0.75
                ))
                
        # Analyze document processing times
        doc_metrics = [m for m in recent_metrics 
                      if m.metric_type == PerformanceMetricType.DOCUMENT_PROCESSING_TIME]
        if doc_metrics:
            avg_processing = statistics.mean([m.value for m in doc_metrics])
            if avg_processing > 20:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"doc_opt_{int(time.time())}",
                    title="Document Processing Optimization",
                    description=f"Document processing averaging {avg_processing:.1f}s",
                    impact_level="high",
                    effort_level="high",
                    category="document_processing",
                    implementation_steps=[
                        "Implement parallel processing for document chunks",
                        "Add preprocessing to skip unnecessary operations",
                        "Optimize NLP pipeline efficiency",
                        "Implement incremental processing"
                    ],
                    expected_improvement="40-60% processing time reduction",
                    confidence_score=0.85
                ))
                
        return suggestions
        
    async def identify_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Identify system bottlenecks"""
        bottlenecks = []
        recent_metrics = self._get_recent_metrics(hours=2)
        
        # Group metrics by component/operation
        component_metrics = {}
        for metric in recent_metrics:
            component = metric.context.get('component', 'unknown')
            if component not in component_metrics:
                component_metrics[component] = []
            component_metrics[component].append(metric)
            
        # Analyze each component
        for component, metrics in component_metrics.items():
            bottleneck = await self._analyze_component_bottleneck(component, metrics)
            if bottleneck:
                bottlenecks.append(bottleneck)
                
        return bottlenecks
        
    async def get_performance_trends(self, 
                                   metric_type: PerformanceMetricType,
                                   hours: int = 24) -> Dict[str, Any]:
        """Get performance trends for a metric type"""
        metrics = self._get_recent_metrics(hours=hours)
        type_metrics = [m for m in metrics if m.metric_type == metric_type]
        
        if not type_metrics:
            return {"error": "No data available"}
            
        # Sort by timestamp
        type_metrics.sort(key=lambda x: x.timestamp)
        
        # Calculate hourly averages
        hourly_data = {}
        for metric in type_metrics:
            hour_key = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
            hourly_data[hour_key].append(metric.value)
            
        trend_data = []
        for hour, values in sorted(hourly_data.items()):
            trend_data.append({
                "timestamp": hour.isoformat(),
                "average": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            })
            
        # Calculate trend direction
        if len(trend_data) >= 2:
            recent_avg = statistics.mean([d["average"] for d in trend_data[-3:]])
            earlier_avg = statistics.mean([d["average"] for d in trend_data[:3]])
            trend_direction = "improving" if recent_avg < earlier_avg else "degrading"
        else:
            trend_direction = "insufficient_data"
            
        return {
            "metric_type": metric_type.value,
            "trend_direction": trend_direction,
            "data_points": trend_data,
            "summary": {
                "total_samples": len(type_metrics),
                "time_range_hours": hours,
                "overall_average": statistics.mean([m.value for m in type_metrics])
            }
        }
        
    async def _monitor_system_metrics(self):
        """Monitor system-level metrics"""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                await self.record_metric(PerformanceMetric(
                    metric_type=PerformanceMetricType.CPU_USAGE,
                    value=cpu_percent,
                    timestamp=datetime.now(),
                    context={"component": "system"},
                    tags={"source": "psutil"}
                ))
                
                # Memory usage
                memory = psutil.virtual_memory()
                await self.record_metric(PerformanceMetric(
                    metric_type=PerformanceMetricType.MEMORY_USAGE,
                    value=memory.percent,
                    timestamp=datetime.now(),
                    context={"component": "system", "total_gb": memory.total / (1024**3)},
                    tags={"source": "psutil"}
                ))
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    await self.record_metric(PerformanceMetric(
                        metric_type=PerformanceMetricType.DISK_IO,
                        value=disk_io.read_bytes + disk_io.write_bytes,
                        timestamp=datetime.now(),
                        context={"component": "system", "read_bytes": disk_io.read_bytes,
                                "write_bytes": disk_io.write_bytes},
                        tags={"source": "psutil"}
                    ))
                    
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(self.monitoring_interval)
                
    async def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers any alerts"""
        threshold = self.thresholds.get(metric.metric_type)
        if not threshold:
            return
            
        if metric.value > threshold:
            # Check if we already have a recent alert for this metric
            recent_alerts = [a for a in self.alerts 
                           if a.metric_type == metric.metric_type and
                           (datetime.now() - a.timestamp).seconds < 300]  # 5 minutes
            
            if not recent_alerts:
                severity = self._calculate_alert_severity(metric.value, threshold)
                alert = PerformanceAlert(
                    alert_id=f"alert_{metric.metric_type.value}_{int(time.time())}",
                    metric_type=metric.metric_type,
                    severity=severity,
                    message=f"{metric.metric_type.value} exceeded threshold: {metric.value:.2f} > {threshold}",
                    current_value=metric.value,
                    baseline_value=threshold,
                    threshold_exceeded=(metric.value - threshold) / threshold * 100,
                    timestamp=datetime.now(),
                    context=metric.context
                )
                
                self.alerts.append(alert)
                logger.warning(f"Performance alert: {alert.message}")
                
    def _calculate_alert_severity(self, value: float, threshold: float) -> AlertSeverity:
        """Calculate alert severity based on threshold exceedance"""
        exceedance = (value - threshold) / threshold
        
        if exceedance > 1.0:  # 100% over threshold
            return AlertSeverity.CRITICAL
        elif exceedance > 0.5:  # 50% over threshold
            return AlertSeverity.HIGH
        elif exceedance > 0.2:  # 20% over threshold
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
            
    def _get_recent_metrics(self, minutes: int = None, hours: int = None) -> List[PerformanceMetric]:
        """Get recent metrics within specified time window"""
        if minutes:
            cutoff = datetime.now() - timedelta(minutes=minutes)
        elif hours:
            cutoff = datetime.now() - timedelta(hours=hours)
        else:
            cutoff = datetime.now() - timedelta(hours=1)
            
        return [m for m in self.metrics_storage if m.timestamp >= cutoff]
        
    async def _update_baselines(self):
        """Update performance baselines"""
        # Use last 7 days of data for baselines
        baseline_metrics = self._get_recent_metrics(hours=24*7)
        
        for metric_type in PerformanceMetricType:
            type_metrics = [m for m in baseline_metrics if m.metric_type == metric_type]
            
            if len(type_metrics) >= 50:  # Need sufficient data
                values = [m.value for m in type_metrics]
                
                self.baselines[metric_type] = PerformanceBaseline(
                    metric_type=metric_type,
                    mean=statistics.mean(values),
                    std_dev=statistics.stdev(values) if len(values) > 1 else 0,
                    percentile_95=self._percentile(values, 95),
                    percentile_99=self._percentile(values, 99),
                    sample_count=len(values),
                    last_updated=datetime.now()
                )
                
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
        
    async def _analyze_component_bottleneck(self, 
                                          component: str, 
                                          metrics: List[PerformanceMetric]) -> Optional[BottleneckAnalysis]:
        """Analyze bottlenecks for a specific component"""
        if len(metrics) < 10:
            return None
            
        # Calculate performance statistics
        response_times = [m.value for m in metrics 
                         if m.metric_type == PerformanceMetricType.RESPONSE_TIME]
        
        if not response_times:
            return None
            
        avg_response = statistics.mean(response_times)
        max_response = max(response_times)
        
        # Determine if this is a bottleneck
        if avg_response > 2.0 or max_response > 10.0:
            severity = min(avg_response / 2.0, 1.0)  # Normalize to 0-1
            
            return BottleneckAnalysis(
                component=component,
                bottleneck_type="response_time",
                severity=severity,
                description=f"Component {component} showing slow response times (avg: {avg_response:.2f}s)",
                affected_operations=[m.context.get('operation', 'unknown') for m in metrics],
                suggested_fixes=[
                    "Profile component performance",
                    "Optimize database queries",
                    "Implement caching",
                    "Consider load balancing"
                ],
                performance_impact=severity * 100
            )
            
        return None
        
    async def _analyze_performance_trends(self):
        """Analyze performance trends and generate insights"""
        while self.monitoring_active:
            try:
                # Run trend analysis every hour
                await asyncio.sleep(3600)
                
                for metric_type in PerformanceMetricType:
                    regression = await self.detect_performance_regression(metric_type)
                    if regression and regression.get("regression_detected"):
                        logger.warning(f"Performance regression detected for {metric_type.value}: "
                                     f"{regression['degradation_percentage']:.1f}% degradation")
                        
            except Exception as e:
                logger.error(f"Error analyzing performance trends: {e}")
                
    async def _cleanup_old_data(self):
        """Clean up old performance data"""
        while self.monitoring_active:
            try:
                # Clean up every 6 hours
                await asyncio.sleep(21600)
                
                cutoff = datetime.now() - timedelta(days=self.data_retention_days)
                
                # Remove old metrics
                self.metrics_storage = [m for m in self.metrics_storage 
                                      if m.timestamp >= cutoff]
                
                # Remove old alerts
                alert_cutoff = datetime.now() - timedelta(days=7)
                self.alerts = [a for a in self.alerts if a.timestamp >= alert_cutoff]
                
                logger.info(f"Cleaned up old performance data. "
                          f"Metrics: {len(self.metrics_storage)}, Alerts: {len(self.alerts)}")
                          
            except Exception as e:
                logger.error(f"Error cleaning up performance data: {e}")


# Global instance
performance_monitor = PerformanceMonitoringService()