"""
Performance Monitoring API Endpoints

REST API endpoints for performance monitoring, optimization suggestions,
bottleneck analysis, and alerting management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from ..services.performance_monitoring_service import (
    performance_monitor, PerformanceMetric, PerformanceMetricType
)
from ..services.performance_regression_detector import (
    regression_detector, RegressionDetectionResult
)
from ..services.performance_optimization_engine import (
    optimization_engine, OptimizationSuggestion, SystemProfile
)
from ..services.bottleneck_analyzer import (
    bottleneck_analyzer, BottleneckAnalysis, ComponentMetrics
)
from ..services.performance_alerting_service import (
    alerting_service, PerformanceAlert, AlertRule, TrendAnalysis
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])


# Pydantic models for API
class MetricRecordRequest(BaseModel):
    metric_type: str
    value: float
    context: Dict[str, Any] = {}
    tags: Dict[str, str] = {}


class SystemProfileRequest(BaseModel):
    cpu_usage_avg: float = Field(..., ge=0, le=100)
    memory_usage_avg: float = Field(..., ge=0, le=100)
    disk_io_rate: float = Field(..., ge=0)
    network_io_rate: float = Field(..., ge=0)
    database_query_time_avg: float = Field(..., ge=0)
    cache_hit_rate: float = Field(..., ge=0, le=1)
    error_rate: float = Field(..., ge=0, le=1)
    response_time_p95: float = Field(..., ge=0)
    throughput: float = Field(..., ge=0)
    active_connections: int = Field(..., ge=0)
    queue_depth: int = Field(..., ge=0)


class ComponentMetricsRequest(BaseModel):
    component_name: str
    response_times: List[float] = []
    throughput: float = 0.0
    error_rate: float = 0.0
    resource_usage: Dict[str, float] = {}
    queue_depth: int = 0
    active_connections: int = 0


class AlertRuleRequest(BaseModel):
    name: str
    description: str
    metric_name: str
    alert_type: str
    severity: str
    threshold_value: Optional[float] = None
    comparison_operator: str
    evaluation_window_minutes: int = Field(..., gt=0)
    min_data_points: int = Field(..., gt=0)
    notification_channels: List[str] = []
    suppression_duration_minutes: int = Field(..., gt=0)
    enabled: bool = True
    conditions: Dict[str, Any] = {}


class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: str


# Performance Monitoring Endpoints
@router.post("/metrics/record")
async def record_performance_metric(request: MetricRecordRequest):
    """Record a performance metric"""
    try:
        # Validate metric type
        try:
            metric_type = PerformanceMetricType(request.metric_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid metric type: {request.metric_type}")
        
        # Create metric
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=request.value,
            timestamp=datetime.now(),
            context=request.context,
            tags=request.tags
        )
        
        # Record metric
        await performance_monitor.record_metric(metric)
        
        return {"status": "success", "message": "Metric recorded"}
        
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_performance_status():
    """Get current performance monitoring status"""
    try:
        status = await performance_monitor.get_current_performance_status()
        return status
    except Exception as e:
        logger.error(f"Error getting performance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{metric_type}")
async def get_performance_trends(
    metric_type: str,
    hours: int = Query(24, ge=1, le=168)  # 1 hour to 1 week
):
    """Get performance trends for a specific metric type"""
    try:
        # Validate metric type
        try:
            metric_type_enum = PerformanceMetricType(metric_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")
        
        trends = await performance_monitor.get_performance_trends(metric_type_enum, hours)
        return trends
        
    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Regression Detection Endpoints
@router.post("/regression/detect/{metric_name}")
async def detect_performance_regression(
    metric_name: str,
    lookback_hours: int = Query(24, ge=1, le=168)
):
    """Detect performance regression for a metric"""
    try:
        # Get metric data (this would typically come from a database)
        # For now, we'll use the in-memory data from the monitoring service
        recent_metrics = performance_monitor._get_recent_metrics(hours=lookback_hours)
        
        # Convert to format expected by regression detector
        metric_data = []
        for metric in recent_metrics:
            if metric.metric_type.value == metric_name:
                metric_data.append({
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.value
                })
        
        if not metric_data:
            raise HTTPException(status_code=404, detail=f"No data found for metric: {metric_name}")
        
        result = await regression_detector.detect_regression(metric_data, metric_name)
        
        return {
            "metric_name": metric_name,
            "regression_detected": result.regression_detected,
            "regression_type": result.regression_type.value if result.regression_type else None,
            "confidence_score": result.confidence_score,
            "severity_score": result.severity_score,
            "baseline_mean": result.baseline_mean,
            "current_mean": result.current_mean,
            "degradation_percentage": result.degradation_percentage,
            "statistical_significance": result.statistical_significance,
            "detection_timestamp": result.detection_timestamp.isoformat(),
            "recommendations": result.recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting regression: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Optimization Suggestions Endpoints
@router.post("/optimization/suggestions")
async def generate_optimization_suggestions(profile: SystemProfileRequest):
    """Generate optimization suggestions based on system profile"""
    try:
        system_profile = SystemProfile(
            cpu_usage_avg=profile.cpu_usage_avg,
            memory_usage_avg=profile.memory_usage_avg,
            disk_io_rate=profile.disk_io_rate,
            network_io_rate=profile.network_io_rate,
            database_query_time_avg=profile.database_query_time_avg,
            cache_hit_rate=profile.cache_hit_rate,
            error_rate=profile.error_rate,
            response_time_p95=profile.response_time_p95,
            throughput=profile.throughput,
            active_connections=profile.active_connections,
            queue_depth=profile.queue_depth
        )
        
        suggestions = await optimization_engine.generate_suggestions(system_profile)
        
        return {
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "title": s.title,
                    "description": s.description,
                    "category": s.category.value,
                    "impact_level": s.impact_level.value,
                    "effort_level": s.effort_level.value,
                    "priority_score": s.priority_score,
                    "confidence_score": s.confidence_score,
                    "implementation_steps": s.implementation_steps,
                    "expected_improvement": s.expected_improvement,
                    "code_examples": s.code_examples,
                    "monitoring_metrics": s.monitoring_metrics,
                    "estimated_time_hours": s.estimated_time_hours,
                    "prerequisites": s.prerequisites,
                    "risks": s.risks,
                    "created_at": s.created_at.isoformat()
                }
                for s in suggestions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating optimization suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/implemented/{suggestion_id}")
async def mark_suggestion_implemented(suggestion_id: str):
    """Mark an optimization suggestion as implemented"""
    try:
        await optimization_engine.mark_suggestion_implemented(suggestion_id)
        return {"status": "success", "message": "Suggestion marked as implemented"}
    except Exception as e:
        logger.error(f"Error marking suggestion as implemented: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization/status")
async def get_optimization_status():
    """Get optimization implementation status"""
    try:
        status = await optimization_engine.get_implementation_status()
        return status
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Bottleneck Analysis Endpoints
@router.post("/bottlenecks/record")
async def record_component_metrics(request: ComponentMetricsRequest):
    """Record metrics for a component"""
    try:
        metrics = ComponentMetrics(
            component_name=request.component_name,
            response_times=request.response_times,
            throughput=request.throughput,
            error_rate=request.error_rate,
            resource_usage=request.resource_usage,
            queue_depth=request.queue_depth,
            active_connections=request.active_connections,
            timestamp=datetime.now()
        )
        
        await bottleneck_analyzer.record_component_metrics(metrics)
        
        return {"status": "success", "message": "Component metrics recorded"}
        
    except Exception as e:
        logger.error(f"Error recording component metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bottlenecks/analyze/{component_name}")
async def analyze_component_bottlenecks(component_name: str):
    """Analyze bottlenecks for a specific component"""
    try:
        bottlenecks = await bottleneck_analyzer.analyze_component(component_name)
        
        return {
            "component": component_name,
            "bottlenecks": [
                {
                    "bottleneck_id": b.bottleneck_id,
                    "component": b.component,
                    "bottleneck_type": b.bottleneck_type.value,
                    "severity": b.severity.value,
                    "confidence_score": b.confidence_score,
                    "impact_score": b.impact_score,
                    "description": b.description,
                    "root_cause": b.root_cause,
                    "affected_operations": b.affected_operations,
                    "performance_impact": b.performance_impact,
                    "suggested_fixes": b.suggested_fixes,
                    "monitoring_recommendations": b.monitoring_recommendations,
                    "detected_at": b.detected_at.isoformat()
                }
                for b in bottlenecks
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing component bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bottlenecks/report")
async def generate_system_bottleneck_report():
    """Generate comprehensive system bottleneck report"""
    try:
        report = await bottleneck_analyzer.generate_system_report()
        
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "analysis_period_hours": report.analysis_period.total_seconds() / 3600,
            "system_health_score": report.system_health_score,
            "performance_trends": report.performance_trends,
            "recommendations": report.recommendations,
            "next_analysis_time": report.next_analysis_time.isoformat(),
            "bottlenecks": [
                {
                    "bottleneck_id": b.bottleneck_id,
                    "component": b.component,
                    "bottleneck_type": b.bottleneck_type.value,
                    "severity": b.severity.value,
                    "confidence_score": b.confidence_score,
                    "impact_score": b.impact_score,
                    "description": b.description,
                    "root_cause": b.root_cause,
                    "suggested_fixes": b.suggested_fixes,
                    "detected_at": b.detected_at.isoformat()
                }
                for b in report.bottlenecks
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating bottleneck report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Alerting Endpoints
@router.get("/alerts/active")
async def get_active_alerts(severity: Optional[str] = None):
    """Get active performance alerts"""
    try:
        from ..services.performance_alerting_service import AlertSeverity
        
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        alerts = await alerting_service.get_active_alerts(severity_filter)
        
        return {
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "rule_id": a.rule_id,
                    "alert_type": a.alert_type.value,
                    "severity": a.severity.value,
                    "title": a.title,
                    "description": a.description,
                    "metric_name": a.metric_name,
                    "current_value": a.current_value,
                    "threshold_value": a.threshold_value,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat(),
                    "updated_at": a.updated_at.isoformat(),
                    "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                    "acknowledged_by": a.acknowledged_by,
                    "context": a.context
                }
                for a in alerts
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: AlertAcknowledgeRequest):
    """Acknowledge an active alert"""
    try:
        await alerting_service.acknowledge_alert(alert_id, request.acknowledged_by)
        return {"status": "success", "message": "Alert acknowledged"}
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an active alert"""
    try:
        await alerting_service.resolve_alert(alert_id)
        return {"status": "success", "message": "Alert resolved"}
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/trends/{metric_name}")
async def get_alert_trends(
    metric_name: str,
    hours: int = Query(24, ge=1, le=168)
):
    """Get trend analysis for a metric"""
    try:
        trend = await alerting_service.get_trend_analysis(metric_name, hours)
        
        if not trend:
            raise HTTPException(status_code=404, detail=f"No trend data found for metric: {metric_name}")
        
        return {
            "metric_name": trend.metric_name,
            "trend_direction": trend.trend_direction,
            "trend_strength": trend.trend_strength,
            "slope": trend.slope,
            "r_squared": trend.r_squared,
            "prediction_24h": trend.prediction_24h,
            "confidence_interval": trend.confidence_interval,
            "anomalies_detected": trend.anomalies_detected,
            "analysis_period_hours": trend.analysis_period_hours,
            "data_points": trend.data_points
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task endpoints
@router.post("/monitoring/start")
async def start_performance_monitoring(background_tasks: BackgroundTasks):
    """Start performance monitoring services"""
    try:
        background_tasks.add_task(performance_monitor.start_monitoring)
        background_tasks.add_task(bottleneck_analyzer.start_analysis)
        background_tasks.add_task(alerting_service.start_alerting)
        
        return {"status": "success", "message": "Performance monitoring started"}
        
    except Exception as e:
        logger.error(f"Error starting performance monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_performance_monitoring():
    """Stop performance monitoring services"""
    try:
        await performance_monitor.stop_monitoring()
        await bottleneck_analyzer.stop_analysis()
        await alerting_service.stop_alerting()
        
        return {"status": "success", "message": "Performance monitoring stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping performance monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def performance_monitoring_health():
    """Health check for performance monitoring system"""
    try:
        status = {
            "monitoring_active": performance_monitor.monitoring_active,
            "analysis_active": bottleneck_analyzer.monitoring_active,
            "alerting_active": alerting_service.alerting_active,
            "metrics_count": len(performance_monitor.metrics_storage),
            "active_alerts_count": len(alerting_service.active_alerts),
            "timestamp": datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))