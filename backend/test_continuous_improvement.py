"""
Test suite for the continuous improvement system
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.improvement.improvement_engine import ContinuousImprovementEngine
from app.improvement.models import (
    UserFeedback, Improvement, FeatureRequest, 
    ImprovementPriority, ImprovementCategory, ImprovementStatus
)


class TestContinuousImprovementEngine:
    """Test the main improvement engine"""
    
    @pytest.fixture
    def engine(self):
        return ContinuousImprovementEngine(".")
    
    @pytest.mark.asyncio
    async def test_run_continuous_analysis(self, engine):
        """Test running continuous analysis"""
        # Mock the analysis methods to avoid actual file system operations
        with patch.object(engine, '_run_code_quality_analysis') as mock_code, \
             patch.object(engine, '_run_performance_analysis') as mock_perf, \
             patch.object(engine, '_run_feedback_analysis') as mock_feedback, \
             patch.object(engine, '_run_prioritization_update') as mock_priority, \
             patch.object(engine, '_run_impact_tracking') as mock_impact:
            
            # Set up mock returns
            mock_code.return_value = {'status': 'completed', 'improvements_generated': 5}
            mock_perf.return_value = {'status': 'completed', 'improvements_generated': 3}
            mock_feedback.return_value = {'status': 'completed', 'improvements_generated': 2}
            mock_priority.return_value = {'status': 'completed'}
            mock_impact.return_value = {'status': 'completed', 'improvements_tracked': 2}
            
            # Run analysis
            results = await engine.run_continuous_analysis()
            
            # Verify results
            assert 'timestamp' in results
            assert 'analysis_components' in results
            assert 'summary' in results
            
            # Check that all components were called
            mock_code.assert_called_once()
            mock_perf.assert_called_once()
            mock_feedback.assert_called_once()
            mock_priority.assert_called_once()
            mock_impact.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_user_feedback(self, engine):
        """Test submitting user feedback"""
        feedback = UserFeedback(
            feature="search",
            rating=2,
            comment="Search is very slow and often returns irrelevant results",
            category="performance",
            severity="high"
        )
        
        feedback_id = await engine.submit_user_feedback(feedback)
        
        assert feedback_id is not None
        assert len(feedback_id) > 0
    
    @pytest.mark.asyncio
    async def test_create_feature_request(self, engine):
        """Test creating feature request"""
        feature_request = await engine.create_feature_request(
            title="Dark mode support",
            description="Add dark mode theme for better user experience",
            requested_by="user123",
            user_votes=5
        )
        
        assert feature_request.title == "Dark mode support"
        assert feature_request.user_votes == 5
        assert feature_request.priority_score > 0
        assert feature_request in engine.feature_requests
    
    @pytest.mark.asyncio
    async def test_mark_improvement_completed(self, engine):
        """Test marking improvement as completed"""
        # Add a test improvement
        improvement = Improvement(
            title="Test improvement",
            description="Test description",
            priority=ImprovementPriority.MEDIUM,
            category=ImprovementCategory.PERFORMANCE,
            suggested_actions=["Test action"],
            estimated_effort=8,
            expected_impact=0.5,
            confidence=0.7,
            source_data={}
        )
        engine.improvements.append(improvement)
        
        # Mark as completed
        success = await engine.mark_improvement_completed(improvement.id)
        
        assert success is True
        assert improvement not in engine.improvements
        assert improvement in engine.improvement_history
        assert improvement.status == ImprovementStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_get_improvement_dashboard(self, engine):
        """Test getting dashboard data"""
        # Add some test data
        improvement = Improvement(
            title="Test improvement",
            description="Test description",
            priority=ImprovementPriority.HIGH,
            category=ImprovementCategory.CODE_QUALITY,
            suggested_actions=["Test action"],
            estimated_effort=16,
            expected_impact=0.8,
            confidence=0.9,
            source_data={}
        )
        engine.improvements.append(improvement)
        
        dashboard = await engine.get_improvement_dashboard()
        
        assert 'improvements' in dashboard
        assert 'feature_requests' in dashboard
        assert 'recent_activity' in dashboard
        assert dashboard['improvements']['total'] == 1
        assert 'high' in dashboard['improvements']['by_priority']


class TestCodeQualityAnalyzer:
    """Test code quality analysis"""
    
    @pytest.fixture
    def analyzer(self):
        from app.improvement.code_quality_analyzer import CodeQualityAnalyzer
        return CodeQualityAnalyzer(".")
    
    def test_should_analyze_file(self, analyzer):
        """Test file filtering logic"""
        from pathlib import Path
        
        # Should analyze
        assert analyzer._should_analyze_file(Path("src/main.py")) is True
        assert analyzer._should_analyze_file(Path("app/models.py")) is True
        
        # Should not analyze
        assert analyzer._should_analyze_file(Path("__pycache__/test.py")) is False
        assert analyzer._should_analyze_file(Path("node_modules/lib.js")) is False
        assert analyzer._should_analyze_file(Path("test_file.py")) is False
    
    def test_calculate_complexity(self, analyzer):
        """Test complexity calculation"""
        simple_code = """
def simple_function():
    return True
"""
        
        complex_code = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(10):
                    if i % 2 == 0:
                        return i
    return 0
"""
        
        simple_complexity = analyzer._calculate_complexity(simple_code)
        complex_complexity = analyzer._calculate_complexity(complex_code)
        
        assert simple_complexity < complex_complexity
        assert simple_complexity >= 1.0
    
    def test_count_code_smells(self, analyzer):
        """Test code smell detection"""
        import ast
        
        smelly_code = """
def bad_function(a, b, c, d, e, f, g):  # Too many parameters
    if True:
        if True:
            if True:
                if True:  # Deep nesting
                    for i in range(100):
                        for j in range(100):
                            print("This is a very long method that does too many things and should be refactored into smaller methods")
                            print("More lines to make it longer")
                            print("Even more lines")
                            print("And more")
                            print("Still more")
                            print("Way too long")
    return True
"""
        
        tree = ast.parse(smelly_code)
        smells = analyzer._count_code_smells(tree)
        
        assert smells > 0  # Should detect parameter and nesting issues


class TestPerformanceOptimizer:
    """Test performance optimization"""
    
    @pytest.fixture
    def optimizer(self):
        from app.improvement.performance_optimizer import PerformanceOptimizer
        return PerformanceOptimizer()
    
    @pytest.mark.asyncio
    async def test_collect_performance_metrics(self, optimizer):
        """Test performance metrics collection"""
        metric = await optimizer.collect_performance_metrics("test_operation")
        
        assert metric.operation == "test_operation"
        assert metric.response_time >= 0
        assert metric.memory_usage >= 0
        assert metric.cpu_usage >= 0
        assert metric.throughput >= 0
        assert metric.error_rate >= 0
    
    def test_percentile_calculation(self, optimizer):
        """Test percentile calculation"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        p50 = optimizer._percentile(data, 50)
        p95 = optimizer._percentile(data, 95)
        p99 = optimizer._percentile(data, 99)
        
        assert p50 == 5.5  # Median
        assert p95 > p50
        assert p99 > p95
    
    def test_calculate_trend(self, optimizer):
        """Test trend calculation"""
        increasing_values = [1, 2, 3, 4, 5]
        decreasing_values = [5, 4, 3, 2, 1]
        stable_values = [3, 3, 3, 3, 3]
        
        assert optimizer._calculate_trend(increasing_values) == "increasing"
        assert optimizer._calculate_trend(decreasing_values) == "decreasing"
        assert optimizer._calculate_trend(stable_values) == "stable"
    
    @pytest.mark.asyncio
    async def test_generate_performance_improvements(self, optimizer):
        """Test performance improvement generation"""
        analysis = {
            "operation": "document_processing",
            "response_time": {
                "avg": 5.0,  # Exceeds threshold
                "p95": 8.0,
                "trend": "increasing"
            },
            "memory_usage": {
                "avg": 400,
                "max": 600,  # Exceeds threshold
                "trend": "stable"
            },
            "cpu_usage": {
                "avg": 85,  # Exceeds threshold
                "max": 95,
                "trend": "stable"
            }
        }
        
        improvements = await optimizer.generate_performance_improvements(analysis)
        
        assert len(improvements) > 0
        
        # Check that improvements address the issues
        titles = [imp.title for imp in improvements]
        assert any("response time" in title.lower() for title in titles)
        assert any("memory" in title.lower() for title in titles)
        assert any("cpu" in title.lower() for title in titles)


class TestFeedbackAnalyzer:
    """Test feedback analysis"""
    
    @pytest.fixture
    def analyzer(self):
        from app.improvement.feedback_analyzer import FeedbackAnalyzer
        return FeedbackAnalyzer()
    
    @pytest.mark.asyncio
    async def test_collect_feedback(self, analyzer):
        """Test feedback collection"""
        feedback = UserFeedback(
            feature="search",
            rating=3,
            comment="Search works but could be faster and more accurate"
        )
        
        feedback_id = await analyzer.collect_feedback(feedback)
        
        assert feedback_id is not None
        assert feedback in analyzer.feedback_storage
    
    @pytest.mark.asyncio
    async def test_categorize_feedback(self, analyzer):
        """Test automatic feedback categorization"""
        search_comment = "The search function is slow and doesn't find what I need"
        upload_comment = "File upload keeps failing with large documents"
        ui_comment = "The interface is confusing and hard to navigate"
        
        search_category = await analyzer._categorize_feedback(search_comment)
        upload_category = await analyzer._categorize_feedback(upload_comment)
        ui_category = await analyzer._categorize_feedback(ui_comment)
        
        assert search_category == "search"
        assert upload_category == "upload"
        assert ui_category == "ui"
    
    @pytest.mark.asyncio
    async def test_determine_severity(self, analyzer):
        """Test severity determination"""
        critical_feedback = UserFeedback(
            feature="app",
            rating=1,
            comment="The app crashes every time I try to upload a document"
        )
        
        medium_feedback = UserFeedback(
            feature="search",
            rating=3,
            comment="Search is okay but could be improved"
        )
        
        critical_severity = await analyzer._determine_severity(critical_feedback)
        medium_severity = await analyzer._determine_severity(medium_feedback)
        
        assert critical_severity in ["critical", "high"]
        assert medium_severity == "medium"
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, analyzer):
        """Test sentiment analysis"""
        positive_comment = "I love this feature! It's amazing and very helpful"
        negative_comment = "This is terrible, slow, and frustrating to use"
        neutral_comment = "The feature works as expected"
        
        positive_sentiment = await analyzer._analyze_sentiment(positive_comment)
        negative_sentiment = await analyzer._analyze_sentiment(negative_comment)
        neutral_sentiment = await analyzer._analyze_sentiment(neutral_comment)
        
        assert positive_sentiment > 0
        assert negative_sentiment < 0
        assert abs(neutral_sentiment) < abs(positive_sentiment)


class TestPrioritizationEngine:
    """Test prioritization engine"""
    
    @pytest.fixture
    def engine(self):
        from app.improvement.prioritization_engine import PrioritizationEngine
        return PrioritizationEngine()
    
    def test_calculate_business_value_score(self, engine):
        """Test business value calculation"""
        high_impact_improvement = Improvement(
            title="Fix critical security vulnerability",
            description="Security issue",
            priority=ImprovementPriority.CRITICAL,
            category=ImprovementCategory.SECURITY,
            suggested_actions=["Fix vulnerability"],
            estimated_effort=8,
            expected_impact=0.9,
            confidence=0.8,
            source_data={}
        )
        
        low_impact_improvement = Improvement(
            title="Minor UI tweak",
            description="Small UI change",
            priority=ImprovementPriority.LOW,
            category=ImprovementCategory.USER_EXPERIENCE,
            suggested_actions=["Update UI"],
            estimated_effort=2,
            expected_impact=0.2,
            confidence=0.5,
            source_data={}
        )
        
        high_score = engine._calculate_business_value_score(high_impact_improvement)
        low_score = engine._calculate_business_value_score(low_impact_improvement)
        
        assert high_score > low_score
        assert high_score <= 100
        assert low_score >= 0
    
    def test_calculate_effort_efficiency_score(self, engine):
        """Test effort efficiency calculation"""
        efficient_improvement = Improvement(
            title="Quick fix",
            description="Easy fix with high impact",
            priority=ImprovementPriority.MEDIUM,
            category=ImprovementCategory.PERFORMANCE,
            suggested_actions=["Quick fix"],
            estimated_effort=2,  # Low effort
            expected_impact=0.8,  # High impact
            confidence=0.9,
            source_data={}
        )
        
        inefficient_improvement = Improvement(
            title="Complex refactor",
            description="Complex change with low impact",
            priority=ImprovementPriority.MEDIUM,
            category=ImprovementCategory.CODE_QUALITY,
            suggested_actions=["Refactor"],
            estimated_effort=40,  # High effort
            expected_impact=0.2,  # Low impact
            confidence=0.6,
            source_data={}
        )
        
        efficient_score = engine._calculate_effort_efficiency_score(efficient_improvement)
        inefficient_score = engine._calculate_effort_efficiency_score(inefficient_improvement)
        
        assert efficient_score > inefficient_score
    
    @pytest.mark.asyncio
    async def test_prioritize_improvements(self, engine):
        """Test improvement prioritization"""
        improvements = [
            Improvement(
                title="Critical security fix",
                description="Fix security vulnerability",
                priority=ImprovementPriority.CRITICAL,
                category=ImprovementCategory.SECURITY,
                suggested_actions=["Fix"],
                estimated_effort=8,
                expected_impact=0.9,
                confidence=0.9,
                source_data={}
            ),
            Improvement(
                title="Minor UI improvement",
                description="Small UI change",
                priority=ImprovementPriority.LOW,
                category=ImprovementCategory.USER_EXPERIENCE,
                suggested_actions=["Update"],
                estimated_effort=4,
                expected_impact=0.3,
                confidence=0.7,
                source_data={}
            ),
            Improvement(
                title="Performance optimization",
                description="Optimize slow operation",
                priority=ImprovementPriority.HIGH,
                category=ImprovementCategory.PERFORMANCE,
                suggested_actions=["Optimize"],
                estimated_effort=16,
                expected_impact=0.7,
                confidence=0.8,
                source_data={}
            )
        ]
        
        prioritized = await engine.prioritize_improvements(improvements)
        
        assert len(prioritized) == 3
        
        # Critical security fix should be first
        assert prioritized[0].category == ImprovementCategory.SECURITY
        
        # Verify scores are assigned
        for improvement in prioritized:
            assert 'priority_score' in improvement.source_data


class TestImpactTracker:
    """Test impact tracking"""
    
    @pytest.fixture
    def tracker(self):
        from app.improvement.impact_tracker import ImpactTracker
        return ImpactTracker()
    
    @pytest.mark.asyncio
    async def test_establish_baseline(self, tracker):
        """Test baseline establishment"""
        improvement_id = "test-improvement-1"
        metrics = {
            'response_time': 2.0,
            'memory_usage': 300,
            'cpu_usage': 60
        }
        
        baseline = await tracker.establish_baseline(improvement_id, metrics)
        
        assert baseline['improvement_id'] == improvement_id
        assert baseline['metrics'] == metrics
        assert improvement_id in tracker.baseline_metrics
    
    @pytest.mark.asyncio
    async def test_measure_impact(self, tracker):
        """Test impact measurement"""
        improvement_id = "test-improvement-1"
        
        # Establish baseline
        baseline_metrics = {
            'response_time': 2.0,
            'memory_usage': 300,
            'cpu_usage': 60
        }
        await tracker.establish_baseline(improvement_id, baseline_metrics)
        
        # Measure improved metrics
        improved_metrics = {
            'response_time': 1.0,  # 50% improvement
            'memory_usage': 200,   # 33% improvement
            'cpu_usage': 40        # 33% improvement
        }
        
        impacts = await tracker.measure_impact(improvement_id, improved_metrics)
        
        assert len(impacts) == 3
        
        # Check response time improvement
        response_impact = next(i for i in impacts if i.metric_name == 'response_time')
        assert response_impact.improvement_percentage == 50.0
        assert response_impact.before_value == 2.0
        assert response_impact.after_value == 1.0
    
    def test_categorize_metric(self, tracker):
        """Test metric categorization"""
        assert tracker._categorize_metric('response_time') == 'performance'
        assert tracker._categorize_metric('memory_usage') == 'resource_usage'
        assert tracker._categorize_metric('test_coverage') == 'quality'
        assert tracker._categorize_metric('error_rate') == 'reliability'
        assert tracker._categorize_metric('user_satisfaction') == 'user_experience'
        assert tracker._categorize_metric('unknown_metric') == 'other'


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])