"""
Performance optimization suggestion engine
"""
import asyncio
import time
import psutil
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .models import (
    PerformanceMetric, Improvement, ImprovementPriority, 
    ImprovementCategory, ImprovementImpact
)


class PerformanceOptimizer:
    """Analyzes performance metrics and suggests optimizations"""
    
    def __init__(self):
        self.performance_thresholds = {
            'response_time': 1.0,  # seconds
            'memory_usage': 512,   # MB
            'cpu_usage': 80,       # percentage
            'throughput': 100,     # requests/second
            'error_rate': 0.05     # 5%
        }
        self.metrics_history = []
        self.baseline_metrics = {}
    
    async def collect_performance_metrics(self, operation: str) -> PerformanceMetric:
        """Collect performance metrics for an operation"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        # Simulate operation monitoring
        await asyncio.sleep(0.1)  # Allow time for measurement
        
        end_time = time.time()
        end_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        end_cpu = psutil.cpu_percent()
        
        metric = PerformanceMetric(
            operation=operation,
            response_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            cpu_usage=(start_cpu + end_cpu) / 2,
            throughput=1.0 / (end_time - start_time) if end_time > start_time else 0,
            error_rate=0.0  # Would be calculated from actual error tracking
        )
        
        self.metrics_history.append(metric)
        return metric
    
    async def analyze_performance_trends(self, 
                                       operation: str, 
                                       days: int = 7) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.operation == operation and m.timestamp >= cutoff_date
        ]
        
        if not recent_metrics:
            return {"error": "No recent metrics found"}
        
        # Calculate trends
        response_times = [m.response_time for m in recent_metrics]
        memory_usage = [m.memory_usage for m in recent_metrics]
        cpu_usage = [m.cpu_usage for m in recent_metrics]
        
        analysis = {
            "operation": operation,
            "sample_count": len(recent_metrics),
            "response_time": {
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": self._percentile(response_times, 95),
                "p99": self._percentile(response_times, 99),
                "trend": self._calculate_trend(response_times)
            },
            "memory_usage": {
                "avg": statistics.mean(memory_usage),
                "max": max(memory_usage),
                "trend": self._calculate_trend(memory_usage)
            },
            "cpu_usage": {
                "avg": statistics.mean(cpu_usage),
                "max": max(cpu_usage),
                "trend": self._calculate_trend(cpu_usage)
            }
        }
        
        return analysis
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression slope
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    async def generate_performance_improvements(self, 
                                             analysis: Dict[str, Any]) -> List[Improvement]:
        """Generate performance improvement suggestions"""
        improvements = []
        operation = analysis.get("operation", "unknown")
        
        # Response time improvements
        response_time_data = analysis.get("response_time", {})
        avg_response_time = response_time_data.get("avg", 0)
        p95_response_time = response_time_data.get("p95", 0)
        
        if avg_response_time > self.performance_thresholds['response_time']:
            priority = (ImprovementPriority.CRITICAL if avg_response_time > 5.0 
                       else ImprovementPriority.HIGH)
            
            improvements.append(Improvement(
                title=f"Optimize response time for {operation}",
                description=f"Average response time is {avg_response_time:.2f}s, exceeding threshold of {self.performance_thresholds['response_time']}s",
                priority=priority,
                category=ImprovementCategory.PERFORMANCE,
                suggested_actions=self._get_response_time_optimizations(operation, avg_response_time),
                estimated_effort=self._estimate_optimization_effort(avg_response_time, "response_time"),
                expected_impact=0.8,
                confidence=0.7,
                source_data={"analysis": analysis}
            ))
        
        # Memory usage improvements
        memory_data = analysis.get("memory_usage", {})
        avg_memory = memory_data.get("avg", 0)
        max_memory = memory_data.get("max", 0)
        
        if max_memory > self.performance_thresholds['memory_usage']:
            improvements.append(Improvement(
                title=f"Optimize memory usage for {operation}",
                description=f"Peak memory usage is {max_memory:.1f}MB, exceeding threshold of {self.performance_thresholds['memory_usage']}MB",
                priority=ImprovementPriority.HIGH,
                category=ImprovementCategory.PERFORMANCE,
                suggested_actions=self._get_memory_optimizations(operation, max_memory),
                estimated_effort=self._estimate_optimization_effort(max_memory, "memory"),
                expected_impact=0.6,
                confidence=0.8,
                source_data={"analysis": analysis}
            ))
        
        # CPU usage improvements
        cpu_data = analysis.get("cpu_usage", {})
        avg_cpu = cpu_data.get("avg", 0)
        max_cpu = cpu_data.get("max", 0)
        
        if avg_cpu > self.performance_thresholds['cpu_usage']:
            improvements.append(Improvement(
                title=f"Optimize CPU usage for {operation}",
                description=f"Average CPU usage is {avg_cpu:.1f}%, exceeding threshold of {self.performance_thresholds['cpu_usage']}%",
                priority=ImprovementPriority.MEDIUM,
                category=ImprovementCategory.PERFORMANCE,
                suggested_actions=self._get_cpu_optimizations(operation, avg_cpu),
                estimated_effort=self._estimate_optimization_effort(avg_cpu, "cpu"),
                expected_impact=0.5,
                confidence=0.6,
                source_data={"analysis": analysis}
            ))
        
        # Trend-based improvements
        if response_time_data.get("trend") == "increasing":
            improvements.append(Improvement(
                title=f"Address performance degradation in {operation}",
                description=f"Response time trend is increasing, indicating performance degradation",
                priority=ImprovementPriority.HIGH,
                category=ImprovementCategory.PERFORMANCE,
                suggested_actions=[
                    "Profile recent code changes for performance impact",
                    "Check for resource leaks or memory growth",
                    "Review database query performance",
                    "Monitor for increased load or data volume"
                ],
                estimated_effort=16,
                expected_impact=0.7,
                confidence=0.6,
                source_data={"analysis": analysis}
            ))
        
        return improvements
    
    def _get_response_time_optimizations(self, operation: str, response_time: float) -> List[str]:
        """Get response time optimization suggestions"""
        base_suggestions = [
            "Profile code to identify bottlenecks",
            "Optimize database queries and add indexes",
            "Implement caching for frequently accessed data",
            "Use async/await for I/O operations"
        ]
        
        if "document" in operation.lower():
            base_suggestions.extend([
                "Implement streaming for large document processing",
                "Use background tasks for heavy processing",
                "Optimize PDF parsing algorithms",
                "Cache processed document metadata"
            ])
        
        if "search" in operation.lower():
            base_suggestions.extend([
                "Optimize search index structure",
                "Implement search result caching",
                "Use pagination for large result sets",
                "Pre-compute popular search results"
            ])
        
        if response_time > 10.0:
            base_suggestions.extend([
                "Consider breaking operation into smaller chunks",
                "Implement progress tracking for long operations",
                "Use worker queues for background processing"
            ])
        
        return base_suggestions
    
    def _get_memory_optimizations(self, operation: str, memory_usage: float) -> List[str]:
        """Get memory optimization suggestions"""
        suggestions = [
            "Profile memory usage to identify leaks",
            "Implement object pooling for frequently created objects",
            "Use generators instead of lists for large datasets",
            "Clear unused references and implement proper cleanup"
        ]
        
        if "document" in operation.lower():
            suggestions.extend([
                "Process documents in chunks instead of loading entirely",
                "Use streaming for large file operations",
                "Implement lazy loading for document content",
                "Cache only essential document metadata"
            ])
        
        if memory_usage > 1000:  # > 1GB
            suggestions.extend([
                "Consider using external storage for large objects",
                "Implement memory-mapped files for large datasets",
                "Use compression for stored data"
            ])
        
        return suggestions
    
    def _get_cpu_optimizations(self, operation: str, cpu_usage: float) -> List[str]:
        """Get CPU optimization suggestions"""
        suggestions = [
            "Profile CPU usage to identify hot spots",
            "Optimize algorithms and data structures",
            "Use multiprocessing for CPU-intensive tasks",
            "Implement efficient caching to reduce computation"
        ]
        
        if "nlp" in operation.lower() or "extraction" in operation.lower():
            suggestions.extend([
                "Optimize NLP model inference",
                "Use batch processing for multiple documents",
                "Consider using lighter NLP models",
                "Implement model result caching"
            ])
        
        if cpu_usage > 90:
            suggestions.extend([
                "Consider horizontal scaling",
                "Implement rate limiting to prevent overload",
                "Use background processing for non-critical tasks"
            ])
        
        return suggestions
    
    def _estimate_optimization_effort(self, value: float, metric_type: str) -> int:
        """Estimate effort required for optimization"""
        if metric_type == "response_time":
            if value > 10:
                return 40  # Major refactoring needed
            elif value > 5:
                return 24  # Significant optimization
            else:
                return 8   # Minor optimization
        
        elif metric_type == "memory":
            if value > 1000:
                return 32  # Major memory optimization
            elif value > 500:
                return 16  # Moderate optimization
            else:
                return 8   # Minor optimization
        
        elif metric_type == "cpu":
            if value > 90:
                return 24  # Significant CPU optimization
            else:
                return 12  # Moderate optimization
        
        return 8  # Default
    
    async def measure_improvement_impact(self, 
                                       improvement_id: str,
                                       operation: str,
                                       before_metrics: PerformanceMetric,
                                       after_metrics: PerformanceMetric) -> List[ImprovementImpact]:
        """Measure the impact of implemented improvements"""
        impacts = []
        
        # Response time impact
        if before_metrics.response_time > 0:
            response_improvement = (
                (before_metrics.response_time - after_metrics.response_time) / 
                before_metrics.response_time * 100
            )
            impacts.append(ImprovementImpact(
                improvement_id=improvement_id,
                metric_name="response_time",
                before_value=before_metrics.response_time,
                after_value=after_metrics.response_time,
                improvement_percentage=response_improvement,
                validation_method="performance_monitoring"
            ))
        
        # Memory usage impact
        memory_improvement = (
            (before_metrics.memory_usage - after_metrics.memory_usage) / 
            max(before_metrics.memory_usage, 1) * 100
        )
        impacts.append(ImprovementImpact(
            improvement_id=improvement_id,
            metric_name="memory_usage",
            before_value=before_metrics.memory_usage,
            after_value=after_metrics.memory_usage,
            improvement_percentage=memory_improvement,
            validation_method="memory_profiling"
        ))
        
        # CPU usage impact
        cpu_improvement = (
            (before_metrics.cpu_usage - after_metrics.cpu_usage) / 
            max(before_metrics.cpu_usage, 1) * 100
        )
        impacts.append(ImprovementImpact(
            improvement_id=improvement_id,
            metric_name="cpu_usage",
            before_value=before_metrics.cpu_usage,
            after_value=after_metrics.cpu_usage,
            improvement_percentage=cpu_improvement,
            validation_method="cpu_profiling"
        ))
        
        # Throughput impact
        if before_metrics.throughput > 0:
            throughput_improvement = (
                (after_metrics.throughput - before_metrics.throughput) / 
                before_metrics.throughput * 100
            )
            impacts.append(ImprovementImpact(
                improvement_id=improvement_id,
                metric_name="throughput",
                before_value=before_metrics.throughput,
                after_value=after_metrics.throughput,
                improvement_percentage=throughput_improvement,
                validation_method="load_testing"
            ))
        
        return impacts
    
    async def set_performance_baseline(self, operation: str) -> Dict[str, float]:
        """Set performance baseline for an operation"""
        recent_metrics = [
            m for m in self.metrics_history[-100:]  # Last 100 measurements
            if m.operation == operation
        ]
        
        if not recent_metrics:
            return {}
        
        baseline = {
            "response_time": statistics.median([m.response_time for m in recent_metrics]),
            "memory_usage": statistics.median([m.memory_usage for m in recent_metrics]),
            "cpu_usage": statistics.median([m.cpu_usage for m in recent_metrics]),
            "throughput": statistics.median([m.throughput for m in recent_metrics]),
            "error_rate": statistics.median([m.error_rate for m in recent_metrics])
        }
        
        self.baseline_metrics[operation] = baseline
        return baseline
    
    async def detect_performance_regressions(self, 
                                           operation: str,
                                           current_metric: PerformanceMetric) -> List[str]:
        """Detect performance regressions compared to baseline"""
        if operation not in self.baseline_metrics:
            return []
        
        baseline = self.baseline_metrics[operation]
        regressions = []
        
        # Check for significant regressions (>20% worse)
        if current_metric.response_time > baseline["response_time"] * 1.2:
            regressions.append(
                f"Response time regression: {current_metric.response_time:.2f}s vs baseline {baseline['response_time']:.2f}s"
            )
        
        if current_metric.memory_usage > baseline["memory_usage"] * 1.2:
            regressions.append(
                f"Memory usage regression: {current_metric.memory_usage:.1f}MB vs baseline {baseline['memory_usage']:.1f}MB"
            )
        
        if current_metric.cpu_usage > baseline["cpu_usage"] * 1.2:
            regressions.append(
                f"CPU usage regression: {current_metric.cpu_usage:.1f}% vs baseline {baseline['cpu_usage']:.1f}%"
            )
        
        if current_metric.throughput < baseline["throughput"] * 0.8:
            regressions.append(
                f"Throughput regression: {current_metric.throughput:.1f} vs baseline {baseline['throughput']:.1f}"
            )
        
        return regressions