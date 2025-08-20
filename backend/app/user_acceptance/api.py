"""
User Acceptance Testing API
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from .models import (
    UserScenario, TestScenarioType, UserTestSession, UserFeedback,
    FeedbackType, ABTest, ABTestVariant, UserSatisfactionSurvey,
    TestExecutionResult
)
from .scenario_manager import ScenarioManager
from .feedback_system import FeedbackCollector, FeedbackAnalyzer
from .ab_testing import ABTestManager, ABTestMetricsCollector
from .ux_metrics import UXMetricsCollector, UXMetricsAnalyzer
from .satisfaction_tracker import SatisfactionTracker

router = APIRouter(prefix="/api/user-acceptance", tags=["user-acceptance"])

# Initialize components
scenario_manager = ScenarioManager()
feedback_collector = FeedbackCollector()
feedback_analyzer = FeedbackAnalyzer(feedback_collector)
ab_test_manager = ABTestManager()
ab_metrics_collector = ABTestMetricsCollector(ab_test_manager)
ux_metrics_collector = UXMetricsCollector()
ux_metrics_analyzer = UXMetricsAnalyzer(ux_metrics_collector)
satisfaction_tracker = SatisfactionTracker()


# Request/Response Models
class StartTestSessionRequest(BaseModel):
    user_id: str
    scenario_id: str


class UpdateSessionProgressRequest(BaseModel):
    step_index: int
    completion_time: float
    success: bool = True


class CompleteSessionRequest(BaseModel):
    feedback: str = ""
    satisfaction: Optional[str] = None


class FeedbackRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    feedback_type: FeedbackType
    title: str
    description: str
    severity: str = "medium"
    satisfaction_rating: Optional[int] = None
    ease_of_use_rating: Optional[int] = None
    feature_usefulness_rating: Optional[int] = None


class SatisfactionSurveyRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    overall_satisfaction: int
    ease_of_use: int
    feature_completeness: int
    performance_satisfaction: int
    design_satisfaction: int
    likelihood_to_recommend: int
    most_valuable_feature: str = ""
    least_valuable_feature: str = ""
    improvement_suggestions: str = ""
    additional_comments: str = ""


class CreateABTestRequest(BaseModel):
    name: str
    description: str
    feature_name: str
    hypothesis: str
    success_metrics: List[str]
    variants: List[Dict[str, Any]]
    start_date: datetime
    end_date: datetime
    sample_size: int
    confidence_level: float = 0.95


class RecordABTestResultRequest(BaseModel):
    user_id: str
    session_id: str
    metrics: Dict[str, float]
    conversion_events: List[str] = []


class UXMetricRequest(BaseModel):
    user_id: str
    session_id: str
    metric_name: str
    metric_value: float
    metric_unit: str
    context: Dict[str, Any] = {}


# Scenario Management Endpoints
@router.get("/scenarios", response_model=List[UserScenario])
async def get_scenarios(scenario_type: Optional[TestScenarioType] = None):
    """Get all test scenarios, optionally filtered by type"""
    if scenario_type:
        return scenario_manager.get_scenarios_by_type(scenario_type)
    return scenario_manager.get_all_scenarios()


@router.get("/scenarios/{scenario_id}", response_model=UserScenario)
async def get_scenario(scenario_id: str):
    """Get a specific test scenario"""
    scenario = scenario_manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("/scenarios", response_model=UserScenario)
async def create_scenario(scenario_data: Dict[str, Any]):
    """Create a new test scenario"""
    try:
        return scenario_manager.create_scenario(scenario_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Test Session Management
@router.post("/sessions/start", response_model=UserTestSession)
async def start_test_session(request: StartTestSessionRequest):
    """Start a new test session"""
    try:
        return scenario_manager.start_test_session(request.user_id, request.scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sessions/{session_id}/progress")
async def update_session_progress(session_id: str, request: UpdateSessionProgressRequest):
    """Update test session progress"""
    try:
        scenario_manager.update_session_progress(
            session_id, request.step_index, request.completion_time, request.success
        )
        return {"status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/complete", response_model=TestExecutionResult)
async def complete_test_session(session_id: str, request: CompleteSessionRequest):
    """Complete a test session"""
    try:
        return scenario_manager.complete_session(
            session_id, request.feedback, request.satisfaction
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/metrics", response_model=List[Dict[str, Any]])
async def get_session_metrics(session_id: str):
    """Get UX metrics for a test session"""
    metrics = scenario_manager.get_session_metrics(session_id)
    return [metric.dict() for metric in metrics]


# Feedback Collection
@router.post("/feedback", response_model=UserFeedback)
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback"""
    feedback_data = request.dict()
    return feedback_collector.collect_feedback(feedback_data)


@router.post("/surveys", response_model=UserSatisfactionSurvey)
async def submit_satisfaction_survey(request: SatisfactionSurveyRequest):
    """Submit user satisfaction survey"""
    survey_data = request.dict()
    return feedback_collector.collect_survey(survey_data)


@router.get("/feedback/analysis")
async def get_feedback_analysis(days: int = Query(30, ge=1, le=365)):
    """Get feedback analysis for specified period"""
    return feedback_analyzer.generate_feedback_report(days)


@router.get("/feedback/themes")
async def get_feedback_themes(days: int = Query(30, ge=1, le=365)):
    """Get feedback themes analysis"""
    return feedback_analyzer.analyze_feedback_themes(days)


@router.get("/feedback/improvements")
async def get_improvement_opportunities():
    """Get identified improvement opportunities"""
    return feedback_analyzer.identify_improvement_opportunities()


# A/B Testing
@router.post("/ab-tests", response_model=ABTest)
async def create_ab_test(request: CreateABTestRequest):
    """Create a new A/B test"""
    try:
        test_data = request.dict()
        return ab_test_manager.create_test(test_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-tests", response_model=List[ABTest])
async def get_ab_tests():
    """Get all A/B tests"""
    return list(ab_test_manager.tests.values())


@router.get("/ab-tests/active", response_model=List[ABTest])
async def get_active_ab_tests():
    """Get active A/B tests"""
    return ab_test_manager.get_active_tests()


@router.get("/ab-tests/{test_id}")
async def get_ab_test_results(test_id: str):
    """Get A/B test results"""
    try:
        return ab_test_manager.get_test_results(test_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/ab-tests/{test_id}/start")
async def start_ab_test(test_id: str):
    """Start an A/B test"""
    success = ab_test_manager.start_test(test_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"status": "started"}


@router.post("/ab-tests/{test_id}/stop")
async def stop_ab_test(test_id: str):
    """Stop an A/B test"""
    success = ab_test_manager.stop_test(test_id)
    if not success:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"status": "stopped"}


@router.get("/ab-tests/user/{user_id}")
async def get_user_ab_tests(user_id: str):
    """Get active A/B tests for a user"""
    return ab_test_manager.get_user_tests(user_id)


@router.post("/ab-tests/{test_id}/results")
async def record_ab_test_result(test_id: str, request: RecordABTestResultRequest):
    """Record A/B test result"""
    try:
        return ab_test_manager.record_result(
            test_id, request.user_id, request.session_id,
            request.metrics, request.conversion_events
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# UX Metrics
@router.post("/ux-metrics")
async def record_ux_metric(request: UXMetricRequest):
    """Record a UX metric"""
    return ux_metrics_collector.collect_metric(
        request.user_id, request.session_id, request.metric_name,
        request.metric_value, request.metric_unit, request.context
    )


@router.post("/ux-metrics/page-load")
async def record_page_load_metrics(
    user_id: str,
    session_id: str,
    page_name: str,
    load_time: float,
    additional_metrics: Optional[Dict[str, float]] = None
):
    """Record page load metrics"""
    return ux_metrics_collector.collect_page_load_metrics(
        user_id, session_id, page_name, load_time, additional_metrics
    )


@router.post("/ux-metrics/interaction")
async def record_interaction_metrics(
    user_id: str,
    session_id: str,
    interaction_type: str,
    response_time: float,
    success: bool = True,
    context: Optional[Dict[str, Any]] = None
):
    """Record interaction metrics"""
    return ux_metrics_collector.collect_interaction_metrics(
        user_id, session_id, interaction_type, response_time, success, context
    )


@router.post("/ux-metrics/task-completion")
async def record_task_completion_metrics(
    user_id: str,
    session_id: str,
    task_name: str,
    completion_time: float,
    steps_completed: int,
    total_steps: int,
    errors_encountered: int = 0
):
    """Record task completion metrics"""
    return ux_metrics_collector.collect_task_completion_metrics(
        user_id, session_id, task_name, completion_time,
        steps_completed, total_steps, errors_encountered
    )


@router.get("/ux-metrics/analysis/performance")
async def get_performance_analysis(days: int = Query(30, ge=1, le=365)):
    """Get performance metrics analysis"""
    return ux_metrics_analyzer.analyze_performance_metrics(days)


@router.get("/ux-metrics/analysis/usability")
async def get_usability_analysis(days: int = Query(30, ge=1, le=365)):
    """Get usability metrics analysis"""
    return ux_metrics_analyzer.analyze_usability_metrics(days)


@router.get("/ux-metrics/analysis/user/{user_id}")
async def get_user_journey_analysis(user_id: str, days: int = Query(30, ge=1, le=365)):
    """Get user journey analysis"""
    return ux_metrics_analyzer.analyze_user_journey_metrics(user_id, days)


@router.get("/ux-metrics/dashboard")
async def get_ux_dashboard(days: int = Query(7, ge=1, le=30)):
    """Get UX metrics dashboard data"""
    return ux_metrics_analyzer.generate_ux_dashboard_data(days)


# Satisfaction Tracking
@router.post("/satisfaction/survey")
async def record_satisfaction_survey(request: SatisfactionSurveyRequest):
    """Record satisfaction survey"""
    survey_data = request.dict()
    return satisfaction_tracker.record_satisfaction_survey(survey_data)


@router.get("/satisfaction/overview")
async def get_satisfaction_overview(days: int = Query(30, ge=1, le=365)):
    """Get satisfaction overview"""
    return satisfaction_tracker.get_satisfaction_overview(days)


@router.get("/satisfaction/user/{user_id}/trend")
async def get_user_satisfaction_trend(user_id: str):
    """Get satisfaction trend for a user"""
    return satisfaction_tracker.get_user_satisfaction_trend(user_id)


@router.get("/satisfaction/issues")
async def get_satisfaction_issues(days: int = Query(30, ge=1, le=365)):
    """Get identified satisfaction issues"""
    return satisfaction_tracker.identify_satisfaction_issues(days)


@router.get("/satisfaction/report")
async def get_satisfaction_report(days: int = Query(30, ge=1, le=365)):
    """Get comprehensive satisfaction report"""
    return satisfaction_tracker.generate_satisfaction_report(days)


@router.post("/satisfaction/track-improvement")
async def track_improvement_impact(
    improvement_id: str,
    baseline_start: datetime,
    baseline_end: datetime,
    measurement_start: datetime,
    measurement_end: datetime
):
    """Track improvement impact on satisfaction"""
    return satisfaction_tracker.track_improvement_impact(
        improvement_id,
        (baseline_start, baseline_end),
        (measurement_start, measurement_end)
    )


# Dashboard and Reporting
@router.get("/dashboard")
async def get_user_acceptance_dashboard(days: int = Query(7, ge=1, le=30)):
    """Get comprehensive user acceptance testing dashboard"""
    # Collect data from all components
    feedback_analysis = feedback_analyzer.analyze_feedback_themes(days)
    satisfaction_overview = satisfaction_tracker.get_satisfaction_overview(days)
    ux_dashboard = ux_metrics_analyzer.generate_ux_dashboard_data(days)
    active_ab_tests = ab_test_manager.get_active_tests()
    
    # Get recent test sessions
    recent_sessions = len(scenario_manager.active_sessions)
    
    return {
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "active_test_sessions": recent_sessions,
            "active_ab_tests": len(active_ab_tests),
            "total_feedback_items": feedback_analysis.get("total_feedback", 0),
            "satisfaction_responses": satisfaction_overview.get("total_responses", 0) if "error" not in satisfaction_overview else 0
        },
        "feedback_analysis": feedback_analysis,
        "satisfaction_overview": satisfaction_overview,
        "ux_metrics": ux_dashboard,
        "ab_tests": {
            "active_count": len(active_ab_tests),
            "active_tests": [{"id": test.id, "name": test.name, "feature": test.feature_name} for test in active_ab_tests]
        },
        "alerts": _generate_dashboard_alerts(feedback_analysis, satisfaction_overview, ux_dashboard)
    }


def _generate_dashboard_alerts(feedback_analysis: Dict[str, Any], 
                              satisfaction_overview: Dict[str, Any],
                              ux_dashboard: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate alerts for the dashboard"""
    alerts = []
    
    # Critical issues from feedback
    if "critical_issues" in feedback_analysis and feedback_analysis["critical_issues"] > 0:
        alerts.append({
            "type": "critical",
            "message": f"{feedback_analysis['critical_issues']} critical issues reported",
            "source": "feedback"
        })
    
    # Low satisfaction alerts
    if "error" not in satisfaction_overview and "nps" in satisfaction_overview:
        nps_score = satisfaction_overview["nps"]["score"]
        if nps_score < 0:
            alerts.append({
                "type": "critical",
                "message": f"Negative NPS score: {nps_score}",
                "source": "satisfaction"
            })
    
    # UX performance alerts
    if "alerts" in ux_dashboard:
        for ux_alert in ux_dashboard["alerts"]:
            alerts.append({
                "type": ux_alert["severity"],
                "message": ux_alert["message"],
                "source": "ux_metrics"
            })
    
    return alerts