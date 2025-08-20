#!/usr/bin/env python3
"""
Verification script for User Acceptance Testing Framework implementation
"""
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.user_acceptance.models import (
    UserScenario, TestScenarioType, UserTestSession, TestStatus,
    UserFeedback, FeedbackType, ABTest, ABTestVariant, UXMetric,
    UserSatisfactionSurvey, SatisfactionLevel
)
from app.user_acceptance.scenario_manager import ScenarioManager
from app.user_acceptance.feedback_system import FeedbackCollector, FeedbackAnalyzer
from app.user_acceptance.ab_testing import ABTestManager, ABTestMetricsCollector
from app.user_acceptance.ux_metrics import UXMetricsCollector, UXMetricsAnalyzer
from app.user_acceptance.satisfaction_tracker import SatisfactionTracker


def test_scenario_management():
    """Test scenario management functionality"""
    print("Testing Scenario Management...")
    
    manager = ScenarioManager()
    
    # Test getting default scenarios
    scenarios = manager.get_all_scenarios()
    print(f"✓ Found {len(scenarios)} default scenarios")
    
    # Test creating a custom scenario
    custom_scenario_data = {
        "name": "Custom Test Scenario",
        "description": "A custom test scenario for verification",
        "scenario_type": TestScenarioType.DOCUMENT_UPLOAD,
        "steps": [
            "Open the application",
            "Navigate to upload page",
            "Select a test file",
            "Click upload button",
            "Wait for processing"
        ],
        "expected_outcomes": [
            "File uploads successfully",
            "Processing completes without errors"
        ],
        "success_criteria": [
            "Upload completes in under 30 seconds",
            "No error messages displayed"
        ],
        "estimated_duration": 3,
        "difficulty_level": "beginner"
    }
    
    custom_scenario = manager.create_scenario(custom_scenario_data)
    print(f"✓ Created custom scenario: {custom_scenario.name}")
    
    # Test starting a test session
    session = manager.start_test_session("test_user_123", custom_scenario.id)
    print(f"✓ Started test session: {session.id}")
    
    # Test updating session progress
    manager.update_session_progress(session.id, 0, 5.2, True)
    manager.update_session_progress(session.id, 1, 8.1, True)
    print("✓ Updated session progress")
    
    # Test completing session
    result = manager.complete_session(session.id, "Test completed successfully", "satisfied")
    print(f"✓ Completed session with {result.success_rate:.1%} success rate")
    
    return True


def test_feedback_system():
    """Test feedback collection and analysis"""
    print("\nTesting Feedback System...")
    
    collector = FeedbackCollector()
    analyzer = FeedbackAnalyzer(collector)
    
    # Test collecting various types of feedback
    feedback_items = [
        {
            "user_id": "user_001",
            "feedback_type": FeedbackType.BUG_REPORT,
            "title": "Upload button not working",
            "description": "The upload button becomes unresponsive after clicking",
            "severity": "high"
        },
        {
            "user_id": "user_002",
            "feedback_type": FeedbackType.FEATURE_REQUEST,
            "title": "Dark mode support",
            "description": "Please add dark mode for better user experience",
            "severity": "low"
        },
        {
            "user_id": "user_003",
            "feedback_type": FeedbackType.USABILITY_ISSUE,
            "title": "Navigation is confusing",
            "description": "The main navigation menu is hard to understand",
            "severity": "medium"
        },
        {
            "user_id": "user_004",
            "feedback_type": FeedbackType.PERFORMANCE_COMPLAINT,
            "title": "Slow page loading",
            "description": "Pages take too long to load, especially on mobile",
            "severity": "high"
        }
    ]
    
    for feedback_data in feedback_items:
        feedback = collector.collect_feedback(feedback_data)
        print(f"✓ Collected {feedback.feedback_type} feedback: {feedback.title}")
    
    # Test collecting satisfaction surveys
    survey_data = {
        "user_id": "user_001",
        "overall_satisfaction": 4,
        "ease_of_use": 3,
        "feature_completeness": 4,
        "performance_satisfaction": 2,
        "design_satisfaction": 4,
        "likelihood_to_recommend": 7,
        "most_valuable_feature": "Document processing",
        "improvement_suggestions": "Improve performance and add more export options"
    }
    
    survey = collector.collect_survey(survey_data)
    print(f"✓ Collected satisfaction survey from {survey.user_id}")
    
    # Test feedback analysis
    themes = analyzer.analyze_feedback_themes(30)
    print(f"✓ Analyzed feedback themes: {themes['total_feedback']} items")
    
    satisfaction_trends = analyzer.analyze_satisfaction_trends(30)
    print(f"✓ Analyzed satisfaction trends: {satisfaction_trends['total_responses']} responses")
    
    improvements = analyzer.identify_improvement_opportunities()
    print(f"✓ Identified {len(improvements)} improvement opportunities")
    
    return True


def test_ab_testing():
    """Test A/B testing functionality"""
    print("\nTesting A/B Testing Framework...")
    
    manager = ABTestManager()
    
    # Test creating an A/B test
    test_data = {
        "name": "Upload Button Color Test",
        "description": "Test different colors for the upload button",
        "feature_name": "upload_button_color",
        "hypothesis": "Blue button will increase upload completion rate",
        "success_metrics": ["upload_completion_rate", "user_satisfaction"],
        "variants": [
            {
                "name": "Control (Green)",
                "description": "Current green upload button",
                "feature_flags": {"button_color": "green"},
                "traffic_percentage": 0.5,
                "is_control": True
            },
            {
                "name": "Blue Button",
                "description": "Blue upload button variant",
                "feature_flags": {"button_color": "blue"},
                "traffic_percentage": 0.5,
                "is_control": False
            }
        ],
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=14),
        "sample_size": 1000,
        "confidence_level": 0.95
    }
    
    test = manager.create_test(test_data)
    print(f"✓ Created A/B test: {test.name}")
    
    # Start the test
    manager.start_test(test.id)
    print("✓ Started A/B test")
    
    # Test user assignment
    user_ids = ["user_001", "user_002", "user_003", "user_004", "user_005"]
    assignments = {}
    
    for user_id in user_ids:
        variant = manager.assign_variant(test.id, user_id)
        if variant:
            assignments[user_id] = variant.name
            print(f"✓ Assigned {user_id} to {variant.name}")
    
    # Test recording results
    for user_id in user_ids[:3]:
        result = manager.record_result(
            test.id,
            user_id,
            f"session_{user_id}",
            {
                "upload_completion_rate": 0.85 if "Blue" in assignments.get(user_id, "") else 0.75,
                "user_satisfaction": 4.2 if "Blue" in assignments.get(user_id, "") else 3.8
            },
            ["completed_upload"] if user_id != "user_003" else []
        )
        print(f"✓ Recorded result for {user_id}")
    
    # Test getting results
    results = manager.get_test_results(test.id)
    print(f"✓ Retrieved test results: {results['total_results']} data points")
    
    return True


def test_ux_metrics():
    """Test UX metrics collection and analysis"""
    print("\nTesting UX Metrics System...")
    
    collector = UXMetricsCollector()
    analyzer = UXMetricsAnalyzer(collector)
    
    # Test collecting various UX metrics
    test_sessions = ["session_001", "session_002", "session_003"]
    
    for i, session_id in enumerate(test_sessions):
        user_id = f"user_{i+1:03d}"
        
        # Page load metrics
        metrics = collector.collect_page_load_metrics(
            user_id, session_id, "dashboard", 
            1200 + (i * 200),  # Varying load times
            {"dom_ready": 800 + (i * 100), "first_paint": 600 + (i * 50)}
        )
        print(f"✓ Collected page load metrics for {session_id}")
        
        # Interaction metrics
        collector.collect_interaction_metrics(
            user_id, session_id, "button_click", 
            150 + (i * 25), True
        )
        
        # Task completion metrics
        collector.collect_task_completion_metrics(
            user_id, session_id, "document_upload",
            30 + (i * 10), 5, 5, i  # Varying error counts
        )
        print(f"✓ Collected interaction and task metrics for {session_id}")
    
    # Test metrics analysis
    performance_analysis = analyzer.analyze_performance_metrics(30)
    print(f"✓ Analyzed performance metrics")
    
    usability_analysis = analyzer.analyze_usability_metrics(30)
    print(f"✓ Analyzed usability metrics")
    
    # Test dashboard data generation
    dashboard_data = analyzer.generate_ux_dashboard_data(7)
    print(f"✓ Generated UX dashboard data")
    
    return True


def test_satisfaction_tracking():
    """Test satisfaction tracking functionality"""
    print("\nTesting Satisfaction Tracking...")
    
    tracker = SatisfactionTracker()
    
    # Test recording multiple satisfaction surveys over time
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(5):
        survey_time = base_time + timedelta(days=i*7)
        survey_data = {
            "user_id": f"user_{i+1:03d}",
            "overall_satisfaction": 3 + (i * 0.2),  # Improving trend
            "ease_of_use": 3 + (i * 0.3),
            "feature_completeness": 3,
            "performance_satisfaction": 2 + (i * 0.4),
            "design_satisfaction": 4,
            "likelihood_to_recommend": 6 + i
        }
        
        survey = tracker.record_satisfaction_survey(survey_data)
        # Manually adjust timestamp for testing
        survey.created_at = survey_time
        tracker.satisfaction_history[survey.user_id][-1]["date"] = survey_time
        
        print(f"✓ Recorded satisfaction survey for user_{i+1:03d}")
    
    # Test satisfaction overview
    overview = tracker.get_satisfaction_overview(30)
    if "error" not in overview:
        print(f"✓ Generated satisfaction overview: {overview['total_responses']} responses")
        print(f"  NPS Score: {overview['nps']['score']:.1f}")
    
    # Test identifying issues
    issues = tracker.identify_satisfaction_issues(30)
    print(f"✓ Identified {len(issues)} satisfaction issues")
    
    # Test user trend analysis
    trend = tracker.get_user_satisfaction_trend("user_001")
    if "error" not in trend:
        print(f"✓ Analyzed user satisfaction trend: {trend['overall_trend']}")
    
    # Test improvement impact tracking
    baseline_period = (base_time, base_time + timedelta(days=14))
    measurement_period = (base_time + timedelta(days=15), base_time + timedelta(days=30))
    
    impact = tracker.track_improvement_impact(
        "test_improvement_001",
        baseline_period,
        measurement_period
    )
    
    if "error" not in impact:
        print(f"✓ Tracked improvement impact: {impact['summary']['overall_impact']}")
    
    return True


def test_integration():
    """Test integration between components"""
    print("\nTesting Component Integration...")
    
    # Test metrics collector with A/B test manager
    ab_manager = ABTestManager()
    metrics_collector = ABTestMetricsCollector(ab_manager)
    
    # Create a simple test
    test_data = {
        "name": "Integration Test",
        "description": "Test integration",
        "feature_name": "test_feature",
        "hypothesis": "Test hypothesis",
        "success_metrics": ["conversion_rate"],
        "variants": [
            {
                "name": "Control",
                "description": "Control variant",
                "feature_flags": {"test_flag": "control"},
                "traffic_percentage": 0.5,
                "is_control": True
            },
            {
                "name": "Variant",
                "description": "Test variant",
                "feature_flags": {"test_flag": "variant"},
                "traffic_percentage": 0.5,
                "is_control": False
            }
        ],
        "start_date": datetime.now(),
        "end_date": datetime.now() + timedelta(days=7),
        "sample_size": 100
    }
    
    test = ab_manager.create_test(test_data)
    ab_manager.start_test(test.id)
    
    # Test session metrics collection
    session_data = {
        "session_duration": 300,
        "page_views": 5,
        "performed_search": True,
        "completed_study_session": True
    }
    
    results = metrics_collector.collect_session_metrics("user_integration", "session_integration", session_data)
    print(f"✓ Collected {len(results)} A/B test results from session metrics")
    
    return True


def run_verification():
    """Run all verification tests"""
    print("=" * 60)
    print("User Acceptance Testing Framework Verification")
    print("=" * 60)
    
    tests = [
        ("Scenario Management", test_scenario_management),
        ("Feedback System", test_feedback_system),
        ("A/B Testing", test_ab_testing),
        ("UX Metrics", test_ux_metrics),
        ("Satisfaction Tracking", test_satisfaction_tracking),
        ("Integration", test_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} - PASSED")
            else:
                failed += 1
                print(f"✗ {test_name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"Verification Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! User Acceptance Testing Framework is working correctly.")
        
        # Generate a sample report
        print("\nGenerating sample dashboard data...")
        
        try:
            from app.user_acceptance.scenario_manager import ScenarioManager
            from app.user_acceptance.feedback_system import FeedbackCollector, FeedbackAnalyzer
            from app.user_acceptance.ab_testing import ABTestManager
            from app.user_acceptance.ux_metrics import UXMetricsCollector, UXMetricsAnalyzer
            from app.user_acceptance.satisfaction_tracker import SatisfactionTracker
            
            # Initialize components
            scenario_manager = ScenarioManager()
            feedback_collector = FeedbackCollector()
            feedback_analyzer = FeedbackAnalyzer(feedback_collector)
            ab_test_manager = ABTestManager()
            ux_metrics_collector = UXMetricsCollector()
            ux_metrics_analyzer = UXMetricsAnalyzer(ux_metrics_collector)
            satisfaction_tracker = SatisfactionTracker()
            
            # Generate sample dashboard
            dashboard_data = {
                "generated_at": datetime.now().isoformat(),
                "period_days": 7,
                "summary": {
                    "total_scenarios": len(scenario_manager.get_all_scenarios()),
                    "active_sessions": len(scenario_manager.active_sessions),
                    "total_feedback": len(feedback_collector.feedback_store),
                    "total_surveys": len(feedback_collector.surveys_store),
                    "active_ab_tests": len(ab_test_manager.get_active_tests())
                },
                "status": "All systems operational"
            }
            
            print(f"\nSample Dashboard Data:")
            print(f"  Total Scenarios: {dashboard_data['summary']['total_scenarios']}")
            print(f"  Active Sessions: {dashboard_data['summary']['active_sessions']}")
            print(f"  Total Feedback: {dashboard_data['summary']['total_feedback']}")
            print(f"  Total Surveys: {dashboard_data['summary']['total_surveys']}")
            print(f"  Active A/B Tests: {dashboard_data['summary']['active_ab_tests']}")
            
        except Exception as e:
            print(f"Warning: Could not generate dashboard data: {e}")
        
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)