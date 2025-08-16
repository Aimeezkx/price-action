"""
Bottleneck Identification and Analysis System

Advanced system for identifying performance bottlenecks across
different system components and providing detailed analysis.
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class BottleneckType(Enum):
    """Types of performance bottlenecks"""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    NETWORK_BOUND = "network_bound"
    DATABASE_BOUND = "database_bound"
    LOCK_CONTENTION = "lock_contention"
    QUEUE_BACKLOG = "queue_backlog"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class BottleneckSeverity(Enum):
    """Severity levels for bottlenecks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComponentMetrics:
    """Metrics for a system component"""
    component_name: str
    response_times: List[float]
    throughput: float
    error_rate: float
    resource_usage: Dict[str, float]
    queue_depth: int
    active_connections: int
    timestamp: datetime


@dataclass
class BottleneckAnalysis:
    """Detailed bottleneck analysis"""
    bottleneck_id: str
    component: str
    bottleneck_type: BottleneckType
    severity: BottleneckSeverity
    confidence_score: float
    impact_score: float
    description: str
    root_cause: str
    affected_operations: List[str]
    performance_impact: Dict[str, float]
    suggested_fixes: List[str]
    monitoring_recommendations: List[str]
    detected_at: datetime
    metrics_snapshot: Dict[str, Any]


@dataclass
class SystemBottleneckReport:
    """Comprehensive system bottleneck report"""
    report_id: str
    generated_at: datetime
    analysis_period: timedelta
    bottlenecks: List[BottleneckAnalysis]
    system_health_score: float
    performance_trends: Dict[str, str]
    recommendations: List[str]
    next_analysis_time: datetime


class BottleneckAnalyzer:
    """Main bottleneck analysis engine"""
    
    def __init__(self):
        self.component_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.analysis_history: List[BottleneckAnalysis] = []
        self.monitoring_active = False
        self.analysis_interval = 300  # 5 minutes
        
        # Thresholds for bottleneck detection
        self.thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "response_time_p95": 2.0,
            "error_rate": 0.05,
            "queue_depth": 100,
            "io_wait_percentage": 20.0
        }
        
    async def start_analysis(self):
        """Start continuous bottleneck analysis"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        logger.info("Starting bottleneck analysis")
        
        # Start analysis tasks
        asyncio.create_task(self._continuous_analysis())
        asyncio.create_task(self._collect_system_metrics())
        
    async def stop_analysis(self):
        """Stop bottleneck analysis"""
        self.monitoring_active = False
        logger.info("Stopping bottleneck analysis")
        
    async def analyze_component(self, component_name: str) -> List[BottleneckAnalysis]:
        """Analyze bottlenecks for a specific component"""
        if component_name not in self.component_metrics:
            return []
            
        metrics = list(self.component_metrics[component_name])
        if len(metrics) < 10:
            return []
            
        bottlenecks = []
        
        # Analyze different types of bottlenecks
        bottlenecks.extend(await self._analyze_cpu_bottlenecks(component_name, metrics))
        bottlenecks.extend(await self._analyze_memory_bottlenecks(component_name, metrics))
        bottlenecks.extend(await self._analyze_io_bottlenecks(component_name, metrics))
        bottlenecks.extend(await self._analyze_database_bottlenecks(component_name, metrics))
        bottlenecks.extend(await self._analyze_queue_bottlenecks(component_name, metrics))
        
        return bottlenecks
        
    async def generate_system_report(self) -> SystemBottleneckReport:
        """Generate comprehensive system bottleneck report"""
        all_bottlenecks = []
        
        # Analyze all components
        for component_name in self.component_metrics.keys():
            component_bottlenecks = await self.analyze_component(component_name)
            all_bottlenecks.extend(component_bottlenecks)
            
        # Sort by impact score
        all_bottlenecks.sort(key=lambda x: x.impact_score, reverse=True)
        
        # Calculate system health score
        health_score = await self._calculate_system_health_score(all_bottlenecks)
        
        # Generate performance trends
        trends = await self._analyze_performance_trends()
        
        # Generate recommendations
        recommendations = await self._generate_system_recommendations(all_bottlenecks)
        
        return SystemBottleneckReport(
            report_id=f"bottleneck_report_{int(time.time())}",
            generated_at=datetime.now(),
            analysis_period=timedelta(hours=1),
            bottlenecks=all_bottlenecks,
            system_health_score=health_score,
            performance_trends=trends,
            recommendations=recommendations,
            next_analysis_time=datetime.now() + timedelta(minutes=self.analysis_interval)
        )
        
    async def record_component_metrics(self, metrics: ComponentMetrics):
        """Record metrics for a component"""
        self.component_metrics[metrics.component_name].append(metrics)
        
    async def _continuous_analysis(self):
        """Continuous bottleneck analysis loop"""
        while self.monitoring_active:
            try:
                # Generate system report
                report = await self.generate_system_report()
                
                # Log critical bottlenecks
                critical_bottlenecks = [b for b in report.bottlenecks 
                                      if b.severity == BottleneckSeverity.CRITICAL]
                
                if critical_bottlenecks:
                    logger.warning(f"Found {len(critical_bottlenecks)} critical bottlenecks")
                    for bottleneck in critical_bottlenecks:
                        logger.warning(f"Critical bottleneck in {bottleneck.component}: {bottleneck.description}")
                        
                await asyncio.sleep(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
                await asyncio.sleep(60)
                
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()
                
                # Create system component metrics
                system_metrics = ComponentMetrics(
                    component_name="system",
                    response_times=[],
                    throughput=0.0,
                    error_rate=0.0,
                    resource_usage={
                        "cpu_usage": cpu_percent,
                        "memory_usage": memory.percent,
                        "disk_read_bytes": disk_io.read_bytes if disk_io else 0,
                        "disk_write_bytes": disk_io.write_bytes if disk_io else 0,
                        "network_bytes_sent": network_io.bytes_sent if network_io else 0,
                        "network_bytes_recv": network_io.bytes_recv if network_io else 0
                    },
                    queue_depth=0,
                    active_connections=len(psutil.net_connections()),
                    timestamp=datetime.now()
                )
                
                await self.record_component_metrics(system_metrics)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)
                
    async def _analyze_cpu_bottlenecks(self, 
                                     component: str, 
                                     metrics: List[ComponentMetrics]) -> List[BottleneckAnalysis]:
        """Analyze CPU-related bottlenecks"""
        bottlenecks = []
        
        # Get recent CPU usage data
        cpu_usage_values = []
        for metric in metrics[-50:]:  # Last 50 measurements
            if "cpu_usage" in metric.resource_usage:
                cpu_usage_values.append(metric.resource_usage["cpu_usage"])
                
        if not cpu_usage_values:
            return bottlenecks
            
        avg_cpu = statistics.mean(cpu_usage_values)
        max_cpu = max(cpu_usage_values)
        
        if avg_cpu > self.thresholds["cpu_usage"]:
            severity = self._calculate_severity(avg_cpu, self.thresholds["cpu_usage"], 100)
            
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_id=f"cpu_{component}_{int(time.time())}",
                component=component,
                bottleneck_type=BottleneckType.CPU_BOUND,
                severity=severity,
                confidence_score=0.9 if avg_cpu > 90 else 0.7,
                impact_score=avg_cpu / 100.0,
                description=f"High CPU usage in {component} (avg: {avg_cpu:.1f}%, max: {max_cpu:.1f}%)",
                root_cause="CPU-intensive operations or inefficient algorithms",
                affected_operations=["All operations in component"],
                performance_impact={
                    "response_time_increase": f"{(avg_cpu - 50) * 2:.1f}%",
                    "throughput_decrease": f"{(avg_cpu - 50) * 1.5:.1f}%"
                },
                suggested_fixes=[
                    "Profile CPU usage to identify hotspots",
                    "Optimize algorithms and data structures",
                    "Implement asynchronous processing",
                    "Add CPU-intensive task queuing",
                    "Consider horizontal scaling"
                ],
                monitoring_recommendations=[
                    "Monitor CPU usage per process",
                    "Track CPU wait times",
                    "Monitor thread pool utilization"
                ],
                detected_at=datetime.now(),
                metrics_snapshot={
                    "avg_cpu_usage": avg_cpu,
                    "max_cpu_usage": max_cpu,
                    "sample_count": len(cpu_usage_values)
                }
            ))
            
        return bottlenecks
        
    async def _analyze_memory_bottlenecks(self, 
                                        component: str, 
                                        metrics: List[ComponentMetrics]) -> List[BottleneckAnalysis]:
        """Analyze memory-related bottlenecks"""
        bottlenecks = []
        
        memory_usage_values = []
        for metric in metrics[-50:]:
            if "memory_usage" in metric.resource_usage:
                memory_usage_values.append(metric.resource_usage["memory_usage"])
                
        if not memory_usage_values:
            return bottlenecks
            
        avg_memory = statistics.mean(memory_usage_values)
        max_memory = max(memory_usage_values)
        
        if avg_memory > self.thresholds["memory_usage"]:
            severity = self._calculate_severity(avg_memory, self.thresholds["memory_usage"], 100)
            
            bottlenecks.append(BottleneckAnalysis(
                bottleneck_id=f"memory_{component}_{int(time.time())}",
                component=component,
                bottleneck_type=BottleneckType.MEMORY_BOUND,
                severity=severity,
                confidence_score=0.8,
                impact_score=avg_memory / 100.0,
                description=f"High memory usage in {component} (avg: {avg_memory:.1f}%, max: {max_memory:.1f}%)",
                root_cause="Memory leaks, inefficient data structures, or insufficient memory allocation",
                affected_operations=["Memory-intensive operations"],
                performance_impact={
                    "gc_frequency_increase": f"{(avg_memory - 70) * 3:.1f}%",
                    "response_time_increase": f"{(avg_memory - 70) * 1.5:.1f}%"
                },
                suggested_fixes=[
                    "Profile memory usage to identify leaks",
                    "Implement object pooling",
                    "Optimize data structures",
                    "Add memory-efficient caching",
                    "Configure garbage collection"
                ],
                monitoring_recommendations=[
                    "Monitor memory allocation patterns",
                    "Track garbage collection frequency",
                    "Monitor heap usage"
                ],
                detected_at=datetime.now(),
                metrics_snapshot={
                    "avg_memory_usage": avg_memory,
                    "max_memory_usage": max_memory,
                    "sample_count": len(memory_usage_values)
                }
            ))
            
        return bottlenecks
        
    async def _analyze_io_bottlenecks(self, 
                                    component: str, 
                                    metrics: List[ComponentMetrics]) -> List[BottleneckAnalysis]:
        """Analyze I/O-related bottlenecks"""
        bottlenecks = []
        
        # Analyze disk I/O patterns
        disk_read_values = []
        disk_write_values = []
        
        for i, metric in enumerate(metrics[-50:]):
            if i > 0:  # Need previous value for rate calculation
                prev_metric = metrics[i-1]
                
                if ("disk_read_bytes" in metric.resource_usage and 
                    "disk_read_bytes" in prev_metric.resource_usage):
                    
                    time_diff = (metric.timestamp - prev_metric.timestamp).total_seconds()
                    if time_diff > 0:
                        read_rate = (metric.resource_usage["disk_read_bytes"] - 
                                   prev_metric.resource_usage["disk_read_bytes"]) / time_diff
                        disk_read_values.append(read_rate)
                        
                if ("disk_write_bytes" in metric.resource_usage and 
                    "disk_write_bytes" in prev_metric.resource_usage):
                    
                    time_diff = (metric.timestamp - prev_metric.timestamp).total_seconds()
                    if time_diff > 0:
                        write_rate = (metric.resource_usage["disk_write_bytes"] - 
                                    prev_metric.resource_usage["disk_write_bytes"]) / time_diff
                        disk_write_values.append(write_rate)
                        
        if disk_read_values or disk_write_values:
            total_io_rate = 0
            if disk_read_values:
                total_io_rate += statistics.mean(disk_read_values)
            if disk_write_values:
                total_io_rate += statistics.mean(disk_write_values)
                
            # Check if I/O rate is high (>100MB/s)
            if total_io_rate > 100 * 1024 * 1024:
                bottlenecks.append(BottleneckAnalysis(
                    bottleneck_id=f"io_{component}_{int(time.time())}",
                    component=component,
                    bottleneck_type=BottleneckType.IO_BOUND,
                    severity=BottleneckSeverity.MEDIUM,
                    confidence_score=0.7,
                    impact_score=min(total_io_rate / (500 * 1024 * 1024), 1.0),
                    description=f"High I/O activity in {component} ({total_io_rate / (1024*1024):.1f} MB/s)",
                    root_cause="Inefficient file operations or excessive disk access",
                    affected_operations=["File operations", "Database operations"],
                    performance_impact={
                        "io_wait_time_increase": "20-40%",
                        "response_time_increase": "15-30%"
                    },
                    suggested_fixes=[
                        "Implement asynchronous I/O",
                        "Add file system caching",
                        "Optimize file access patterns",
                        "Consider SSD storage",
                        "Implement data compression"
                    ],
                    monitoring_recommendations=[
                        "Monitor I/O wait times",
                        "Track file descriptor usage",
                        "Monitor disk queue depth"
                    ],
                    detected_at=datetime.now(),
                    metrics_snapshot={
                        "total_io_rate_mb_s": total_io_rate / (1024*1024),
                        "avg_read_rate": statistics.mean(disk_read_values) if disk_read_values else 0,
                        "avg_write_rate": statistics.mean(disk_write_values) if disk_write_values else 0
                    }
                ))
                
        return bottlenecks
        
    async def _analyze_database_bottlenecks(self, 
                                          component: str, 
                                          metrics: List[ComponentMetrics]) -> List[BottleneckAnalysis]:
        """Analyze database-related bottlenecks"""
        bottlenecks = []
        
        # Look for database-related components
        if "database" not in component.lower() and "db" not in component.lower():
            return bottlenecks
            
        response_times = []
        for metric in metrics[-50:]:
            if metric.response_times:
                response_times.extend(metric.response_times)
                
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = np.percentile(response_times, 95)
            
            if avg_response_time > 1.0:  # 1 second threshold
                severity = self._calculate_severity(avg_response_time, 1.0, 10.0)
                
                bottlenecks.append(BottleneckAnalysis(
                    bottleneck_id=f"db_{component}_{int(time.time())}",
                    component=component,
                    bottleneck_type=BottleneckType.DATABASE_BOUND,
                    severity=severity,
                    confidence_score=0.85,
                    impact_score=min(avg_response_time / 5.0, 1.0),
                    description=f"Slow database operations in {component} (avg: {avg_response_time:.2f}s, P95: {p95_response_time:.2f}s)",
                    root_cause="Slow queries, missing indexes, or database contention",
                    affected_operations=["Database queries", "Data retrieval", "Data updates"],
                    performance_impact={
                        "query_response_time": f"{avg_response_time:.2f}s",
                        "user_experience_impact": "High" if avg_response_time > 3 else "Medium"
                    },
                    suggested_fixes=[
                        "Identify and optimize slow queries",
                        "Add appropriate database indexes",
                        "Implement query result caching",
                        "Optimize database schema",
                        "Consider read replicas"
                    ],
                    monitoring_recommendations=[
                        "Monitor query execution times",
                        "Track database connection pool usage",
                        "Monitor index usage statistics"
                    ],
                    detected_at=datetime.now(),
                    metrics_snapshot={
                        "avg_response_time": avg_response_time,
                        "p95_response_time": p95_response_time,
                        "sample_count": len(response_times)
                    }
                ))
                
        return bottlenecks
        
    async def _analyze_queue_bottlenecks(self, 
                                       component: str, 
                                       metrics: List[ComponentMetrics]) -> List[BottleneckAnalysis]:
        """Analyze queue-related bottlenecks"""
        bottlenecks = []
        
        queue_depths = [metric.queue_depth for metric in metrics[-50:] if metric.queue_depth > 0]
        
        if queue_depths:
            avg_queue_depth = statistics.mean(queue_depths)
            max_queue_depth = max(queue_depths)
            
            if avg_queue_depth > self.thresholds["queue_depth"]:
                severity = self._calculate_severity(avg_queue_depth, self.thresholds["queue_depth"], 1000)
                
                bottlenecks.append(BottleneckAnalysis(
                    bottleneck_id=f"queue_{component}_{int(time.time())}",
                    component=component,
                    bottleneck_type=BottleneckType.QUEUE_BACKLOG,
                    severity=severity,
                    confidence_score=0.8,
                    impact_score=min(avg_queue_depth / 500.0, 1.0),
                    description=f"Queue backlog in {component} (avg: {avg_queue_depth:.0f}, max: {max_queue_depth:.0f})",
                    root_cause="Processing capacity insufficient for incoming load",
                    affected_operations=["Queued operations", "Background tasks"],
                    performance_impact={
                        "processing_delay": f"{avg_queue_depth * 0.1:.1f}s estimated",
                        "throughput_impact": "Reduced"
                    },
                    suggested_fixes=[
                        "Increase worker capacity",
                        "Optimize task processing time",
                        "Implement priority queuing",
                        "Add queue monitoring and alerting",
                        "Consider horizontal scaling"
                    ],
                    monitoring_recommendations=[
                        "Monitor queue depth trends",
                        "Track processing rates",
                        "Monitor worker utilization"
                    ],
                    detected_at=datetime.now(),
                    metrics_snapshot={
                        "avg_queue_depth": avg_queue_depth,
                        "max_queue_depth": max_queue_depth,
                        "sample_count": len(queue_depths)
                    }
                ))
                
        return bottlenecks
        
    def _calculate_severity(self, value: float, threshold: float, max_value: float) -> BottleneckSeverity:
        """Calculate bottleneck severity based on threshold exceedance"""
        if value <= threshold:
            return BottleneckSeverity.LOW
            
        exceedance_ratio = (value - threshold) / (max_value - threshold)
        
        if exceedance_ratio >= 0.8:
            return BottleneckSeverity.CRITICAL
        elif exceedance_ratio >= 0.6:
            return BottleneckSeverity.HIGH
        elif exceedance_ratio >= 0.3:
            return BottleneckSeverity.MEDIUM
        else:
            return BottleneckSeverity.LOW
            
    async def _calculate_system_health_score(self, bottlenecks: List[BottleneckAnalysis]) -> float:
        """Calculate overall system health score"""
        if not bottlenecks:
            return 100.0
            
        # Weight bottlenecks by severity
        severity_weights = {
            BottleneckSeverity.LOW: 1,
            BottleneckSeverity.MEDIUM: 3,
            BottleneckSeverity.HIGH: 7,
            BottleneckSeverity.CRITICAL: 15
        }
        
        total_impact = sum(severity_weights[b.severity] * b.impact_score for b in bottlenecks)
        max_possible_impact = len(bottlenecks) * 15  # All critical with max impact
        
        health_score = max(0, 100 - (total_impact / max_possible_impact * 100))
        return health_score
        
    async def _analyze_performance_trends(self) -> Dict[str, str]:
        """Analyze performance trends across components"""
        trends = {}
        
        for component_name, metrics_deque in self.component_metrics.items():
            metrics = list(metrics_deque)
            if len(metrics) < 20:
                continue
                
            # Analyze response time trend
            recent_response_times = []
            older_response_times = []
            
            for i, metric in enumerate(metrics):
                if metric.response_times:
                    avg_response = statistics.mean(metric.response_times)
                    if i >= len(metrics) // 2:
                        recent_response_times.append(avg_response)
                    else:
                        older_response_times.append(avg_response)
                        
            if recent_response_times and older_response_times:
                recent_avg = statistics.mean(recent_response_times)
                older_avg = statistics.mean(older_response_times)
                
                if recent_avg > older_avg * 1.2:
                    trends[component_name] = "degrading"
                elif recent_avg < older_avg * 0.8:
                    trends[component_name] = "improving"
                else:
                    trends[component_name] = "stable"
                    
        return trends
        
    async def _generate_system_recommendations(self, bottlenecks: List[BottleneckAnalysis]) -> List[str]:
        """Generate system-wide recommendations"""
        recommendations = []
        
        if not bottlenecks:
            recommendations.append("System performance is healthy - continue monitoring")
            return recommendations
            
        # Count bottlenecks by type
        bottleneck_counts = defaultdict(int)
        for bottleneck in bottlenecks:
            bottleneck_counts[bottleneck.bottleneck_type] += 1
            
        # Generate recommendations based on patterns
        if bottleneck_counts[BottleneckType.CPU_BOUND] > 2:
            recommendations.append("Multiple CPU bottlenecks detected - consider CPU optimization or scaling")
            
        if bottleneck_counts[BottleneckType.MEMORY_BOUND] > 1:
            recommendations.append("Memory bottlenecks detected - review memory usage patterns")
            
        if bottleneck_counts[BottleneckType.DATABASE_BOUND] > 0:
            recommendations.append("Database performance issues - prioritize database optimization")
            
        # Critical bottlenecks
        critical_bottlenecks = [b for b in bottlenecks if b.severity == BottleneckSeverity.CRITICAL]
        if critical_bottlenecks:
            recommendations.append(f"URGENT: {len(critical_bottlenecks)} critical bottlenecks require immediate attention")
            
        return recommendations


# Global instance
bottleneck_analyzer = BottleneckAnalyzer()