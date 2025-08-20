"""
Tests for User Acceptance Testing Framework
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

from app.user_acceptance.models import (
    UserScenario, TestScenarioType, UserTestSession, TestStatus,
    UserFeedback, FeedbackType, ABTest, ABTestVariant, UXMetric,
    UserSatisfactionSurvey
)
from app.user_acceptance.scenario_manager import ScenarioManager
from app.user_acceptance.feedback_system import FeedbackCollector, FeedbackAnalyzer
from app.user_acceptance.ab_testing import ABTestManager
from app.user_acceptance.ux_metrics import UXMetricsCollector, UXMetricsAnalyzer
from app.user_acceptance.satisfaction_tracker import SatisfactionTracker


class TestScenarioManager:
    """Test scenario management functionality"""
    
    def test_scenario_creation(self):
        """Test creating a new scenario"""
        manager = ScenarioManager()
        
        scenario_data = {
            "name": "Test Upload Scenario",
            "description": "Test document upload functionality",
            "scenario_type": TestScenarioType.DOCUMENT_UPLOAD,
            "steps": ["Navigate to upload", "Select file", "Click upload"],
            "expected_outcomes": ["File uploads successfully"],
            "success_criteria": ["Upload completes in under 30s"],
            "estimated_duration": 5,
            "difficulty_level": "beginner"
        }
        
        scenario = manager.create_scenario(scenario_data)
        
        assert scenario.name == "Test Upload Scenario"
        assert scenario.scenario_type == TestScenarioType.DOCUMENT_UPLOAD
        assert len(scenario.steps) == 3
        assert scenario.estimated_duration == 5
    
    def test_start_test_session(self):
        """Test starting a test session"""
        manager = ScenarioManager()
        
        # Create a scenario first
        scenario_data = {
            "name": "Test Scenario",
            "description": "Test scenario",
            "scenario_type": TestScenarioType.CARD_REVIEW,
            "steps": ["Step 1", "Step 2"],
            "expected_outcomes": ["Outcome 1"],
            "success_criteria": ["Criteria 1"],
            "estimated_duration": 3,
            "difficulty_level": "beginner"
        }
        scenario = manager.create_scenario(scenario_data)
        
        # Start session
        session = manager.start_test_session("user123", scenario.id)
        
        assert session.user_id == "user123"
        assert session.scenario_id == scenario.id
        assert session.status == TestStatus.RUNNING
        assert session.start_time is not None
    
    def test_update_session_progress(self):
        """Test updating session progress"""
        manager = ScenarioManager()
        
        # Create scenario and start session
        scenario_data = {
            "name": "Test Scenario",
            "description": "Test scenario",
            "scenario_type": TestScenarioType.SEARCH_USAGE,
            "steps": ["Step 1", "Step 2", "Step 3"],
            "expected_outcomes": ["Outcome 1"],
            "success_criteria": ["Criteria 1"],
            "estimated_duration": 5,
            "difficulty_level": "intermediate"
        }
        scenario = manager.create_scenario(scenario_data)
        session = manager.start_test_session("user123", scenario.id)
        
        # Update progress
        manager.update_session_progress(session.id, 0, 10.5, True)
        
        updated_session = manager.active_sessions[session.id]
        assert len(updated_session.time_per_step) >= 1
        assert updated_session.time_per_step[0] == 10.5
        assert updated_session.completion_rate > 0
    
    def test_complete_session(self):
        """Test completing a test session"""
        manager = ScenarioManager()
        
        # Create scenario and start session
        scenario_data = {
            "name": "Test Scenario",
            "description": "Test scenario",
            "scenario_type": TestScenarioType.CHAPTER_BROWSING,
            "steps": ["Step 1", "Step 2"],
            "expected_outcomes": ["Outcome 1"],
            "success_criteria": ["Criteria 1"],
            "estimated_duration": 3,
            "difficulty_level": "beginner"
        }
        scenario = manager.create_scenario(scenario_data)
        session = manager.start_test_session("user123", scenario.id)
        
        # Update progress for both steps
        manager.update_session_progress(session.id, 0, 5.0, True)
        manager.update_session_progress(session.id, 1, 7.0, True)
        
        # Complete session
        result = manager.complete_session(session.id, "Great test!", "satisfied")
        
        assert result.success == True
        assert result.completion_time == 12.0
        assert result.steps_completed == 2
        assert result.total_steps == 2
        assert session.id not in manager.active_sessions


class TestFeedbackSystem:
    """Test feedback collection and analysis"""
    
    def test_collect_feedback(self):
        """Test collecting user feedback"""
        collector = FeedbackCollector()
        
        feedback_data = {
            "user_id": "user123",
            "feedback_type": FeedbackType.BUG_REPORT,
            "title": "Upload fails",
            "description": "File upload fails with large PDFs",
            "severity": "high"
        }
        
        feedback = collector.collect_feedback(feedback_data)
        
        assert feedback.user_id == "user123"
        assert feedback.feedback_type == FeedbackType.BUG_REPORT
        assert feedback.title == "Upload fails"
        assert feedback.severity == "high"
        assert len(feedback.tags) > 0  # Auto-tagging should work
    
    def test_collect_survey(self):
        """Test collecting satisfaction survey"""
        collector = FeedbackCollector()
        
        survey_data = {
            "user_id": "user123",
            "overall_satisfaction": 4,
            "ease_of_use": 5,
            "feature_completeness": 3,
            "performance_satisfaction": 4,
            "design_satisfaction": 4,
            "likelihood_to_recommend": 8
        }
        
        survey = collector.collect_survey(survey_data)
        
        assert survey.user_id == "user123"
        assert survey.overall_satisfaction == 4
        assert survey.likelihood_to_recommend == 8
    
    def test_feedback_categorization(self):
        """Test automatic feedback categorization"""
        collector = FeedbackCollector()
        
        # Test UI categorization
        ui_feedback = collector.collect_feedback({
            "user_id": "user123",
            "feedback_type": FeedbackType.USABILITY_ISSUE,
            "title": "Button issue",
            "description": "The navigation button is hard to find",
            "severity": "medium"
        })
        
        assert ui_feedback.category == "ui_ux"
        
        # Test performance categorization
        perf_feedback = collector.collect_feedback({
            "user_id": "user123",
            "feedback_type": FeedbackType.PERFORMANCE_COMPLAINT,
            "title": "Slow loading",
            "description": "The page loading is very slow",
            "severity": "high"
        })
        
        assert perf_feedback.category == "performance"
    
    def test_feedback_analysis(self):
        """Test feedback analysis functionality"""
        collector = FeedbackCollector()
        analyzer = FeedbackAnalyzer(collector)
        
        # Add some test feedback
        for i in range(5):
            collector.collect_feedback({
                "user_id": f"user{i}",
                "feedback_type": FeedbackType.BUG_REPORT,
                "title": f"Bug {i}",
                "description": "Test bug description",
                "severity": "medium"
            })
        
        # Add surveys
        for i in range(3):
            collector.collect_survey({
                "user_id": f"user{i}",
                "overall_satisfaction": 4,
                "ease_of_use": 3,
                "feature_completeness": 4,
                "performance_satisfaction": 3,
                "design_satisfaction": 4,
                "likelihood_to_recommend": 7
            })
        
        # Test analysis
        satisfaction_trends = analyzer.analyze_satisfaction_trends(30)
        assert "total_responses" in satisfaction_trends
        assert satisfaction_trends["total_responses"] == 3
        
        feedback_themes = analyzer.analyze_feedback_themes(30)
        assert "total_feedback" in feedback_themes
        assert feedback_themes["total_feedback"] == 5


class TestABTesting:
    """Test A/B testing functionality"""
    
    def test_create_ab_test(self):
        """Test creating an A/B test"""
        manager = ABTestManager()
        
        test_data = {
            "name": "Upload Button Test",
            "description": "Test different upload button designs",
            "feature_name": "upload_button",
            "hypothesis": "Larger button will increase uploads",
            "success_metrics": ["upload_rate", "user_satisfaction"],
            "variants": [
                {
                    "name": "Control",
                    "description": "Current button",
                    "feature_flags": {"button_size": "normal"},
                    "traffic_percentage": 0.5,
                    "is_control": True
                },
                {
                    "name": "Large Button",
                    "description": "Larger upload button",
                    "feature_flags": {"button_size": "large"},
                    "traffic_percentage": 0.5,
                    "is_control": False
                }
            ],
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=14),
            "sample_size": 1000
        }
        
        test = manager.create_test(test_data)
        
        assert test.name == "Upload Button Test"
        assert len(test.variants) == 2
        assert test.feature_name == "upload_button"
    
    def test_variant_assignment(self):
        """Test user variant assignment"""
        manager = ABTestManager()
        
        # Create test
        test_data = {
            "name": "Test",
            "description": "Test",
            "feature_name": "test_feature",
            "hypothesis": "Test hypothesis",
            "success_metrics": ["metric1"],
            "variants": [
                {
                    "name": "Control",
                    "description": "Control",
                    "feature_flags": {"flag": "control"},
                    "traffic_percentage": 0.5,
                    "is_control": True
                },
                {
                    "name": "Variant",
                    "description": "Variant",
                    "feature_flags": {"flag": "variant"},
                    "traffic_percentage": 0.5,
                    "is_control": False
                }
            ],
            "start_date": datetime.now() - timedelta(days=1),
            "end_date": datetime.now() + timedelta(days=13),
            "sample_size": 1000
        }
        
        test = manager.create_test(test_data)
        manager.start_test(test.id)
        
        # Test consistent assignment
        variant1 = manager.assign_variant(test.id, "user123")
        variant2 = manager.assign_variant(test.id, "user123")
        
        assert variant1 is not None
        assert variant2 is not None
        assert variant1.id == variant2.id  # Should be consistent
    
    def test_record_ab_result(self):
        """Test recording A/B test results"""
        manager = ABTestManager()
        
        # Create and start test
        test_data = {
            "name": "Test",
            "description": "Test",
            "feature_name": "test_feature",
            "hypothesis": "Test hypothesis",
            "success_metrics": ["conversion_rate"],
            "variants": [
                {
                    "name": "Control",
                    "description": "Control",
                    "feature_flags": {"flag": "control"},
                    "traffic_percentage": 0.5,
                    "is_control": True
                },
                {
                    "name": "Variant",
                    "description": "Variant",
                    "feature_flags": {"flag": "variant"},
                    "traffic_percentage": 0.5,
                    "is_control": False
                }
            ],
            "start_date": datetime.now() - timedelta(days=1),
            "end_date": datetime.now() + timedelta(days=13),
            "sample_size": 1000
        }
        
        test = manager.create_test(test_data)
        manager.start_test(test.id)
        
        # Record result
        result = manager.record_result(
            test.id,
            "user123",
            "session456",
            {"conversion_rate": 0.15, "engagement": 0.8},
            ["completed_signup"]
        )
        
        assert result.test_id == test.id
        assert result.user_id == "user123"
        assert result.metrics["conversion_rate"] == 0.15
        assert "completed_signup" in result.conversion_events


class TestUXMetrics:
    """Test UX metrics collection and analysis"""
    
    def test_collect_metric(self):
        """Test collecting a UX metric"""
        collector = UXMetricsCollector()
        
        metric = collector.collect_metric(
            "user123",
            "session456",
            "page_load_time",
            1250.0,
            "milliseconds",
            {"page_name": "upload"}
        )
        
        assert metric.user_id == "user123"
        assert metric.session_id == "session456"
        assert metric.metric_name == "page_load_time"
        assert metric.metric_value == 1250.0
        assert metric.context["page_name"] == "upload"
    
    def test_collect_page_load_metrics(self):
        """Test collecting page load metrics"""
        collector = UXMetricsCollector()
        
        metrics = collector.collect_page_load_metrics(
            "user123",
            "session456",
            "dashboard",
            1500.0,
            {"dom_ready": 800.0, "first_paint": 600.0}
        )
        
        assert len(metrics) == 3  # load_time + 2 additional
        assert any(m.metric_name == "page_load_time" for m in metrics)
        assert any(m.metric_name == "dom_ready" for m in metrics)
    
    def test_collect_task_completion_metrics(self):
        """Test collecting task completion metrics"""
        collector = UXMetricsCollector()
        
        metrics = collector.collect_task_completion_metrics(
            "user123",
            "session456",
            "document_upload",
            45.0,  # 45 seconds
            5,     # 5 steps completed
            5,     # 5 total steps
            1      # 1 error
        )
        
        assert len(metrics) == 4  # completion_time, rate, error_rate, efficiency
        
        # Check completion rate
        completion_metric = next(m for m in metrics if m.metric_name == "task_completion_rate")
        assert completion_metric.metric_value == 1.0  # 100% completion
        
        # Check error rate
        error_metric = next(m for m in metrics if m.metric_name == "task_error_rate")
        assert error_metric.metric_value == 0.2  # 20% error rate (1/5)
    
    def test_ux_metrics_analysis(self):
        """Test UX metrics analysis"""
        collector = UXMetricsCollector()
        analyzer = UXMetricsAnalyzer(collector)
        
        # Add some test metrics
        for i in range(10):
            collector.collect_metric(
                f"user{i}",
                f"session{i}",
                "page_load_time",
                1000 + (i * 100),  # 1000-1900ms
                "milliseconds"
            )
        
        # Analyze performance
        analysis = analyzer.analyze_performance_metrics(30)
        
        assert "performance_metrics" in analysis
        assert "page_load_time" in analysis["performance_metrics"]
        
        load_time_stats = analysis["performance_metrics"]["page_load_time"]
        assert load_time_stats["count"] == 10
        assert load_time_stats["mean"] == 1450.0  # Average of 1000-1900


class TestSatisfactionTracker:
    """Test satisfaction tracking functionality"""
    
    def test_record_satisfaction_survey(self):
        """Test recording satisfaction survey"""
        tracker = SatisfactionTracker()
        
        survey_data = {
            "user_id": "user123",
            "overall_satisfaction": 4,
            "ease_of_use": 5,
            "feature_completeness": 3,
            "performance_satisfaction": 4,
            "design_satisfaction": 4,
            "likelihood_to_recommend": 8
        }
        
        survey = tracker.record_satisfaction_survey(survey_data)
        
        assert survey.user_id == "user123"
        assert survey.overall_satisfaction == 4
        assert len(tracker.satisfaction_history["user123"]) == 1
    
    def test_satisfaction_overview(self):
        """Test satisfaction overview calculation"""
        tracker = SatisfactionTracker()
        
        # Add multiple surveys
        for i in range(5):
            tracker.record_satisfaction_survey({
                "user_id": f"user{i}",
                "overall_satisfaction": 4,
                "ease_of_use": 4,
                "feature_completeness": 3,
                "performance_satisfaction": 4,
                "design_satisfaction": 4,
                "likelihood_to_recommend": 8
            })
        
        overview = tracker.get_satisfaction_overview(30)
        
        assert "total_responses" in overview
        assert overview["total_responses"] == 5
        assert "averages" in overview
        assert overview["averages"]["overall_satisfaction"]["mean"] == 4.0
        assert "nps" in overview
    
    def test_identify_satisfaction_issues(self):
        """Test identifying satisfaction issues"""
        tracker = SatisfactionTracker()
        
        # Add surveys with low scores
        for i in range(3):
            tracker.record_satisfaction_survey({
                "user_id": f"user{i}",
                "overall_satisfaction": 2,  # Low score
                "ease_of_use": 2,
                "feature_completeness": 2,
                "performance_satisfaction": 2,
                "design_satisfaction": 2,
                "likelihood_to_recommend": 4  # Low NPS
            })
        
        issues = tracker.identify_satisfaction_issues(30)
        
        assert len(issues) > 0
        assert any(issue["type"] == "low_satisfaction" for issue in issues)
        assert any(issue["severity"] == "high" for issue in issues)
    
    def test_user_satisfaction_trend(self):
        """Test user satisfaction trend analysis"""
        tracker = SatisfactionTracker()
        
        # Add multiple surveys for same user over time
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(3):
            survey_time = base_time + timedelta(days=i*10)
            survey = tracker.record_satisfaction_survey({
                "user_id": "user123",
                "overall_satisfaction": 2 + i,  # Improving trend
                "ease_of_use": 2 + i,
                "feature_completeness": 3,
                "performance_satisfaction": 3,
                "design_satisfaction": 3,
                "likelihood_to_recommend": 5 + i
            })
            # Manually set the created_at time
            survey.created_at = survey_time
            tracker.satisfaction_history["user123"][-1]["date"] = survey_time
        
        trend = tracker.get_user_satisfaction_trend("user123")
        
        assert "trends" in trend
        assert trend["trends"]["overall_satisfaction"]["trend_direction"] == "improving"
        assert trend["survey_count"] == 3


@pytest.fixture
def client():
    """Test client fixture"""
    from fastapi.testclient import TestClient
    from app.user_acceptance.api import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    return TestClient(app)


class TestUserAcceptanceAPI:
    """Test User Acceptance Testing API endpoints"""
    
    def test_get_scenarios(self, client):
        """Test getting scenarios endpoint"""
        response = client.get("/api/user-acceptance/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert isinstance(scenarios, list)
    
    def test_create_scenario(self, client):
        """Test creating scenario endpoint"""
        scenario_data = {
            "name": "API Test Scenario",
            "description": "Test scenario via API",
            "scenario_type": "document_upload",
            "steps": ["Step 1", "Step 2"],
            "expected_outcomes": ["Outcome 1"],
            "success_criteria": ["Criteria 1"],
            "estimated_duration": 5,
            "difficulty_level": "beginner"
        }
        
        response = client.post("/api/user-acceptance/scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["name"] == "API Test Scenario"
    
    def test_submit_feedback(self, client):
        """Test submitting feedback endpoint"""
        feedback_data = {
            "user_id": "test_user",
            "feedback_type": "bug_report",
            "title": "Test Bug",
            "description": "This is a test bug report",
            "severity": "medium"
        }
        
        response = client.post("/api/user-acceptance/feedback", json=feedback_data)
        assert response.status_code == 200
        feedback = response.json()
        assert feedback["title"] == "Test Bug"
    
    def test_dashboard_endpoint(self, client):
        """Test dashboard endpoint"""
        response = client.get("/api/user-acceptance/dashboard?days=7")
        assert response.status_code == 200
        dashboard = response.json()
        assert "summary" in dashboard
        assert "period_days" in dashboard
        assert dashboard["period_days"] == 7


if __name__ == "__main__":
    pytest.main([__file__])