"""
User Experience Metrics Tracking System
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics

from .models import UXMetric, UserTestSession

logger = logging.getLogger(__name__)


class UXMetricsCollector:
    """Collects and manages user experience metrics"""
    
    def __init__(self, storage_path: str = "backend/app/user_acceptance/ux_metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metrics: Dict[str, List[UXMetric]] = defaultdict(list)
        self._load_existing_metrics()
    
    def _load_existing_metrics(self):
        """Load existing metrics from storage"""
        metric_files = self.storage_path.glob("metrics_*.json")
        for file_path in metric_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for metric_data in data:
                        metric = UXMetric(**metric_data)
                        self.metrics[metric.session_id].append(metric)
            except Exception as e:
                logger.error(f"Error loading UX metrics from {file_path}: {e}")
    
    def collect_metric(self, user_id: str, session_id: str, metric_name: str, 
                      metric_value: float, metric_unit: str, context: Dict[str, Any] = None) -> UXMetric:
        """Collect a single UX metric"""
        metric = UXMetric(
            user_id=user_id,
            session_id=session_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            context=context or {}
        )
        
        self.metrics[session_id].append(metric)
        self._save_session_metrics(session_id)
        
        logger.debug(f"Collected UX metric: {metric_name} = {metric_value} {metric_unit}")
        return metric
    
    def collect_page_load_metrics(self, user_id: str, session_id: str, 
                                 page_name: str, load_time: float, 
                                 additional_metrics: Dict[str, float] = None) -> List[UXMetric]:
        """Collect page load performance metrics"""
        metrics = []
        
        # Main load time metric
        metrics.append(self.collect_metric(
            user_id=user_id,
            session_id=session_id,
            metric_name="page_load_time",
            metric_value=load_time,
            metric_unit="milliseconds",
            context={"page_name": page_name}
        ))
        
        # Additional metrics if provided
        if additional_metrics:
            for metric_name, value in additional_metrics.items():
                metrics.append(self.collect_metric(
                    user_id=user_id,
                    session_id=session_id,
                    metric_name=metric_name,
                    metric_value=value,
                    metric_unit="milliseconds",
                    context={"page_name": page_name}
                ))
        
        return metrics
    
    def collect_interaction_metrics(self, user_id: str, session_id: str, 
                                   interaction_type: str, response_time: float,
                                   success: bool = True, context: Dict[str, Any] = None) -> List[UXMetric]:
        """Collect user interaction metrics"""
        metrics = []
        
        # Response time metric
        metrics.append(self.collect_metric(
            user_id=user_id,
            session_id=session_id,
            metric_name=f"{interaction_type}_response_time",
            metric_value=response_time,
            metric_unit="milliseconds",
            context=context or {}
        ))
        
        # Success rate metric
        metrics.append(self.collect_metric(
            user_id=user_id,
            session_id=session_id,
            metric_name=f"{interaction_type}_success",
            metric_value=1.0 if success else 0.0,
            metric_unit="boolean",
            context=context or {}
        ))
        
        return metrics
    
    def collect_task_completion_metrics(self, user_id: str, session_id: str,
                                      task_name: str, completion_time: float,
                                      steps_completed: int, total_steps: int,
                                      errors_encountered: int = 0) -> List[UXMetric]:
        """Collect task completion metrics"""
        metrics = []
        
        # Task completion time
        metrics.append(self.collect_metric(
            user_id=user_id,
            session_id=session_id,
            metric_name="task_completion_time",
            metric_value=completion_time,
            metric_unit="seconds",
            context={"task_name": task_name}
        ))
        
        # Task completion rate
        completion_rate = steps_completed / total_steps if total_steps > 0 else 0
        metrics.append(self.collect_metric(
            user_id=user_id,
            session_id=session_id,
            metric_name="task_completion_rate",
            metric_value=completion_rate,
            metric_unit="percentage",
            context={"task_name": task_name}
        ))
        
        # Error rate
        error_rate = errors_encountered / total_steps if total_steps > 0 else 0
        metrics.append(self.collect_metric(
            user_id=user_id,
            session_id=session_id,
            metric_name="task_error_rate",
            metric_value=error_rate,
            metric_unit="percentage",
            context={"task_name": task_name}
        ))
        
        # Task efficiency (steps per minute)
        if completion_time > 0:
            efficiency = (steps_completed * 60) / completion_time
            metrics.append(self.collect_metric(
                user_id=user_id,
                session_id=session_id,
                metric_name="task_efficiency",
                metric_value=efficiency,
                metric_unit="steps_per_minute",
                context={"task_name": task_name}
            ))
        
        return metrics
    
    def collect_usability_metrics(self, user_id: str, session_id: str,
                                 feature_name: str, usability_data: Dict[str, Any]) -> List[UXMetric]:
        """Collect usability-specific metrics"""
        metrics = []
        
        # Time to first success
        if "time_to_first_success" in usability_data:
            metrics.append(self.collect_metric(
                user_id=user_id,
                session_id=session_id,
                metric_name="time_to_first_success",
                metric_value=usability_data["time_to_first_success"],
                metric_unit="seconds",
                context={"feature_name": feature_name}
            ))
        
        # Number of attempts before success
        if "attempts_before_success" in usability_data:
            metrics.append(self.collect_metric(
                user_id=user_id,
                session_id=session_id,
                metric_name="attempts_before_success",
                metric_value=usability_data["attempts_before_success"],
                metric_unit="count",
                context={"feature_name": feature_name}
            ))
        
        # User confusion indicators
        if "help_requests" in usability_data:
            metrics.append(self.collect_metric(
                user_id=user_id,
                session_id=session_id,
                metric_name="help_requests",
                metric_value=usability_data["help_requests"],
                metric_unit="count",
                context={"feature_name": feature_name}
            ))
        
        # Navigation efficiency
        if "navigation_steps" in usability_data and "optimal_steps" in usability_data:
            efficiency = usability_data["optimal_steps"] / usability_data["navigation_steps"]
            metrics.append(self.collect_metric(
                user_id=user_id,
                session_id=session_id,
                metric_name="navigation_efficiency",
                metric_value=efficiency,
                metric_unit="ratio",
                context={"feature_name": feature_name}
            ))
        
        return metrics
    
    def _save_session_metrics(self, session_id: str):
        """Save metrics for a session to storage"""
        if session_id not in self.metrics:
            return
        
        file_path = self.storage_path / f"metrics_{session_id}.json"
        metrics_data = [m.dict() for m in self.metrics[session_id]]
        
        with open(file_path, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)
    
    def get_session_metrics(self, session_id: str) -> List[UXMetric]:
        """Get all metrics for a session"""
        return self.metrics.get(session_id, [])
    
    def get_user_metrics(self, user_id: str, days: int = 30) -> List[UXMetric]:
        """Get all metrics for a user within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        user_metrics = []
        
        for session_metrics in self.metrics.values():
            for metric in session_metrics:
                if metric.user_id == user_id and metric.timestamp >= cutoff_date:
                    user_metrics.append(metric)
        
        return user_metrics
    
    def get_metrics_by_name(self, metric_name: str, days: int = 30) -> List[UXMetric]:
        """Get all metrics with a specific name within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        matching_metrics = []
        
        for session_metrics in self.metrics.values():
            for metric in session_metrics:
                if metric.metric_name == metric_name and metric.timestamp >= cutoff_date:
                    matching_metrics.append(metric)
        
        return matching_metrics


class UXMetricsAnalyzer:
    """Analyzes UX metrics and generates insights"""
    
    def __init__(self, metrics_collector: UXMetricsCollector):
        self.collector = metrics_collector
    
    def analyze_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Analyze performance-related UX metrics"""
        performance_metrics = [
            "page_load_time",
            "search_response_time",
            "upload_response_time",
            "card_flip_response_time"
        ]
        
        analysis = {}
        
        for metric_name in performance_metrics:
            metrics = self.collector.get_metrics_by_name(metric_name, days)
            if metrics:
                values = [m.metric_value for m in metrics]
                analysis[metric_name] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0
                }
        
        return {
            "period_days": days,
            "performance_metrics": analysis,
            "performance_summary": self._generate_performance_summary(analysis)
        }
    
    def analyze_usability_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Analyze usability-related UX metrics"""
        usability_metrics = [
            "task_completion_rate",
            "task_completion_time",
            "task_error_rate",
            "time_to_first_success",
            "attempts_before_success",
            "navigation_efficiency"
        ]
        
        analysis = {}
        
        for metric_name in usability_metrics:
            metrics = self.collector.get_metrics_by_name(metric_name, days)
            if metrics:
                values = [m.metric_value for m in metrics]
                
                # Group by context (e.g., task_name, feature_name)
                context_groups = defaultdict(list)
                for metric in metrics:
                    context_key = metric.context.get("task_name") or metric.context.get("feature_name") or "general"
                    context_groups[context_key].append(metric.metric_value)
                
                analysis[metric_name] = {
                    "overall": {
                        "count": len(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values)
                    },
                    "by_context": {
                        context: {
                            "count": len(context_values),
                            "mean": statistics.mean(context_values),
                            "median": statistics.median(context_values)
                        }
                        for context, context_values in context_groups.items()
                    }
                }
        
        return {
            "period_days": days,
            "usability_metrics": analysis,
            "usability_insights": self._generate_usability_insights(analysis)
        }
    
    def analyze_user_journey_metrics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze metrics for a specific user's journey"""
        user_metrics = self.collector.get_user_metrics(user_id, days)
        
        if not user_metrics:
            return {"error": "No metrics found for user"}
        
        # Group metrics by session
        session_groups = defaultdict(list)
        for metric in user_metrics:
            session_groups[metric.session_id].append(metric)
        
        # Analyze each session
        session_analysis = {}
        for session_id, session_metrics in session_groups.items():
            session_analysis[session_id] = self._analyze_session_metrics(session_metrics)
        
        # Overall user analysis
        overall_analysis = {
            "total_sessions": len(session_groups),
            "total_metrics": len(user_metrics),
            "date_range": {
                "start": min(m.timestamp for m in user_metrics).isoformat(),
                "end": max(m.timestamp for m in user_metrics).isoformat()
            },
            "metric_types": list(set(m.metric_name for m in user_metrics)),
            "average_session_duration": self._calculate_average_session_duration(session_groups)
        }
        
        return {
            "user_id": user_id,
            "period_days": days,
            "overall_analysis": overall_analysis,
            "session_analysis": session_analysis,
            "user_insights": self._generate_user_insights(user_metrics, session_analysis)
        }
    
    def _analyze_session_metrics(self, session_metrics: List[UXMetric]) -> Dict[str, Any]:
        """Analyze metrics for a single session"""
        if not session_metrics:
            return {}
        
        # Group by metric type
        metric_groups = defaultdict(list)
        for metric in session_metrics:
            metric_groups[metric.metric_name].append(metric.metric_value)
        
        analysis = {}
        for metric_name, values in metric_groups.items():
            analysis[metric_name] = {
                "count": len(values),
                "total": sum(values),
                "average": statistics.mean(values),
                "min": min(values),
                "max": max(values)
            }
        
        # Session timeline
        timeline = sorted(session_metrics, key=lambda m: m.timestamp)
        session_duration = (timeline[-1].timestamp - timeline[0].timestamp).total_seconds()
        
        return {
            "session_start": timeline[0].timestamp.isoformat(),
            "session_end": timeline[-1].timestamp.isoformat(),
            "session_duration": session_duration,
            "metric_summary": analysis,
            "total_interactions": len(session_metrics)
        }
    
    def _calculate_average_session_duration(self, session_groups: Dict[str, List[UXMetric]]) -> float:
        """Calculate average session duration"""
        durations = []
        
        for session_metrics in session_groups.values():
            if len(session_metrics) >= 2:
                timeline = sorted(session_metrics, key=lambda m: m.timestamp)
                duration = (timeline[-1].timestamp - timeline[0].timestamp).total_seconds()
                durations.append(duration)
        
        return statistics.mean(durations) if durations else 0
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _generate_performance_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary insights"""
        insights = []
        
        for metric_name, stats in analysis.items():
            if "load_time" in metric_name or "response_time" in metric_name:
                if stats["p95"] > 2000:  # 2 seconds
                    insights.append(f"{metric_name} P95 is {stats['p95']:.0f}ms (concerning)")
                elif stats["p95"] > 1000:  # 1 second
                    insights.append(f"{metric_name} P95 is {stats['p95']:.0f}ms (needs attention)")
                else:
                    insights.append(f"{metric_name} P95 is {stats['p95']:.0f}ms (good)")
        
        return {
            "insights": insights,
            "overall_performance": "good" if len([i for i in insights if "concerning" in i]) == 0 else "needs_improvement"
        }
    
    def _generate_usability_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate usability insights"""
        insights = []
        
        # Task completion rate insights
        if "task_completion_rate" in analysis:
            completion_stats = analysis["task_completion_rate"]["overall"]
            if completion_stats["mean"] < 0.8:
                insights.append(f"Low task completion rate: {completion_stats['mean']:.1%}")
            else:
                insights.append(f"Good task completion rate: {completion_stats['mean']:.1%}")
        
        # Error rate insights
        if "task_error_rate" in analysis:
            error_stats = analysis["task_error_rate"]["overall"]
            if error_stats["mean"] > 0.2:
                insights.append(f"High error rate: {error_stats['mean']:.1%}")
        
        # Time to first success insights
        if "time_to_first_success" in analysis:
            success_stats = analysis["time_to_first_success"]["overall"]
            if success_stats["mean"] > 60:  # More than 1 minute
                insights.append(f"Users take {success_stats['mean']:.0f}s to first success (consider UX improvements)")
        
        return insights
    
    def _generate_user_insights(self, user_metrics: List[UXMetric], 
                               session_analysis: Dict[str, Any]) -> List[str]:
        """Generate insights for a specific user"""
        insights = []
        
        # Session frequency
        session_count = len(session_analysis)
        if session_count == 1:
            insights.append("New user - single session")
        elif session_count < 5:
            insights.append(f"Occasional user - {session_count} sessions")
        else:
            insights.append(f"Regular user - {session_count} sessions")
        
        # Performance patterns
        load_time_metrics = [m for m in user_metrics if "load_time" in m.metric_name]
        if load_time_metrics:
            avg_load_time = statistics.mean(m.metric_value for m in load_time_metrics)
            if avg_load_time > 3000:
                insights.append("Experiencing slow load times")
        
        # Task completion patterns
        completion_metrics = [m for m in user_metrics if "completion_rate" in m.metric_name]
        if completion_metrics:
            avg_completion = statistics.mean(m.metric_value for m in completion_metrics)
            if avg_completion < 0.7:
                insights.append("Struggling with task completion")
            elif avg_completion > 0.9:
                insights.append("Highly successful with tasks")
        
        return insights
    
    def generate_ux_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Generate data for UX metrics dashboard"""
        performance_analysis = self.analyze_performance_metrics(days)
        usability_analysis = self.analyze_usability_metrics(days)
        
        # Key metrics summary
        key_metrics = {}
        
        # Average page load time
        if "page_load_time" in performance_analysis["performance_metrics"]:
            key_metrics["avg_page_load_time"] = performance_analysis["performance_metrics"]["page_load_time"]["mean"]
        
        # Task completion rate
        if "task_completion_rate" in usability_analysis["usability_metrics"]:
            key_metrics["avg_completion_rate"] = usability_analysis["usability_metrics"]["task_completion_rate"]["overall"]["mean"]
        
        # Error rate
        if "task_error_rate" in usability_analysis["usability_metrics"]:
            key_metrics["avg_error_rate"] = usability_analysis["usability_metrics"]["task_error_rate"]["overall"]["mean"]
        
        return {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "key_metrics": key_metrics,
            "performance_analysis": performance_analysis,
            "usability_analysis": usability_analysis,
            "alerts": self._generate_ux_alerts(performance_analysis, usability_analysis)
        }
    
    def _generate_ux_alerts(self, performance_analysis: Dict[str, Any], 
                           usability_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate UX alerts based on analysis"""
        alerts = []
        
        # Performance alerts
        perf_metrics = performance_analysis.get("performance_metrics", {})
        for metric_name, stats in perf_metrics.items():
            if "load_time" in metric_name and stats["p95"] > 3000:
                alerts.append({
                    "type": "performance",
                    "severity": "high",
                    "message": f"{metric_name} P95 exceeds 3 seconds",
                    "value": stats["p95"],
                    "threshold": 3000
                })
        
        # Usability alerts
        usability_metrics = usability_analysis.get("usability_metrics", {})
        if "task_completion_rate" in usability_metrics:
            completion_rate = usability_metrics["task_completion_rate"]["overall"]["mean"]
            if completion_rate < 0.7:
                alerts.append({
                    "type": "usability",
                    "severity": "high",
                    "message": "Task completion rate below 70%",
                    "value": completion_rate,
                    "threshold": 0.7
                })
        
        return alerts