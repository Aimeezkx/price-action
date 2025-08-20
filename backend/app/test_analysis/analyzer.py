"""
Test Result Analysis Engine
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

from .models import (
    TestAnalysisReport, TestSuiteResult, TestResult, TestCategory, TestStatus,
    PerformanceBenchmark, CoverageReport, TestIssue, TestTrend,
    ImprovementSuggestion, ExecutiveSummary, IssueSeverity, IssueCategory
)


class TestResultAnalyzer:
    """Analyze test results and generate insights"""
    
    def __init__(self, data_dir: str = "test_results"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    async def analyze_test_results(self, test_data: Dict[str, Any]) -> TestAnalysisReport:
        """Analyze comprehensive test results"""
        report = TestAnalysisReport()
        
        # Parse test suite results
        if "test_suites" in test_data:
            report.test_suites = self._parse_test_suites(test_data["test_suites"])
        
        # Parse performance benchmarks
        if "performance" in test_data:
            report.performance_benchmarks = self._parse_performance_data(test_data["performance"])
        
        # Parse coverage report
        if "coverage" in test_data:
            report.coverage_report = self._parse_coverage_data(test_data["coverage"])
        
        # Identify issues
        report.issues = await self._identify_issues(report)
        
        # Load historical trends
        report.trends = await self._load_trends()
        
        # Save report
        await self._save_report(report)
        
        return report
    
    def _parse_test_suites(self, suites_data: List[Dict]) -> List[TestSuiteResult]:
        """Parse test suite results from raw data"""
        suites = []
        
        for suite_data in suites_data:
            suite = TestSuiteResult(
                name=suite_data.get("name", "Unknown"),
                category=TestCategory(suite_data.get("category", "unit")),
                status=TestStatus(suite_data.get("status", "pending")),
                total_tests=suite_data.get("total_tests", 0),
                passed_tests=suite_data.get("passed_tests", 0),
                failed_tests=suite_data.get("failed_tests", 0),
                skipped_tests=suite_data.get("skipped_tests", 0),
                error_tests=suite_data.get("error_tests", 0),
                duration=suite_data.get("duration", 0.0),
                coverage_percentage=suite_data.get("coverage_percentage")
            )
            
            # Parse individual test results
            if "test_results" in suite_data:
                for test_data in suite_data["test_results"]:
                    test_result = TestResult(
                        name=test_data.get("name", "Unknown"),
                        category=suite.category,
                        status=TestStatus(test_data.get("status", "pending")),
                        duration=test_data.get("duration", 0.0),
                        error_message=test_data.get("error_message"),
                        stack_trace=test_data.get("stack_trace"),
                        metadata=test_data.get("metadata", {})
                    )
                    suite.test_results.append(test_result)
            
            suites.append(suite)
        
        return suites
    
    def _parse_performance_data(self, perf_data: Dict) -> List[PerformanceBenchmark]:
        """Parse performance benchmark data"""
        benchmarks = []
        
        for benchmark_name, data in perf_data.items():
            if isinstance(data, dict):
                benchmark = PerformanceBenchmark(
                    name=benchmark_name,
                    metric=data.get("metric", "response_time"),
                    value=data.get("value", 0.0),
                    unit=data.get("unit", "ms"),
                    threshold=data.get("threshold"),
                    passed=data.get("passed", True)
                )
                benchmarks.append(benchmark)
        
        return benchmarks
    
    def _parse_coverage_data(self, coverage_data: Dict) -> CoverageReport:
        """Parse code coverage data"""
        return CoverageReport(
            total_lines=coverage_data.get("total_lines", 0),
            covered_lines=coverage_data.get("covered_lines", 0),
            coverage_percentage=coverage_data.get("coverage_percentage", 0.0),
            uncovered_files=coverage_data.get("uncovered_files", []),
            coverage_by_file=coverage_data.get("coverage_by_file", {})
        )
    
    async def _identify_issues(self, report: TestAnalysisReport) -> List[TestIssue]:
        """Identify issues from test results"""
        issues = []
        
        # Check for failed tests
        for suite in report.test_suites:
            for test in suite.test_results:
                if test.status == TestStatus.FAILED:
                    issue = TestIssue(
                        title=f"Test Failure: {test.name}",
                        description=test.error_message or "Test failed without error message",
                        severity=self._determine_issue_severity(test, suite),
                        category=self._map_test_category_to_issue_category(test.category),
                        test_case=test.name,
                        reproduction_steps=[
                            f"Run test: {test.name}",
                            "Check test output for details"
                        ],
                        expected_behavior="Test should pass",
                        actual_behavior=f"Test failed: {test.error_message}",
                        environment={"category": test.category.value}
                    )
                    issues.append(issue)
        
        # Check for performance issues
        for benchmark in report.performance_benchmarks:
            if not benchmark.passed:
                issue = TestIssue(
                    title=f"Performance Issue: {benchmark.name}",
                    description=f"{benchmark.metric} exceeded threshold",
                    severity=IssueSeverity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    test_case=benchmark.name,
                    reproduction_steps=[
                        f"Run performance test: {benchmark.name}",
                        f"Check {benchmark.metric} value"
                    ],
                    expected_behavior=f"{benchmark.metric} should be <= {benchmark.threshold} {benchmark.unit}",
                    actual_behavior=f"{benchmark.metric} was {benchmark.value} {benchmark.unit}",
                    environment={"benchmark": benchmark.name}
                )
                issues.append(issue)
        
        # Check for low coverage
        if report.coverage_report and report.coverage_report.coverage_percentage < 90:
            issue = TestIssue(
                title="Low Code Coverage",
                description=f"Code coverage is {report.coverage_report.coverage_percentage:.1f}%, below 90% target",
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.BUG,
                test_case="coverage_check",
                reproduction_steps=[
                    "Run test suite with coverage",
                    "Check coverage report"
                ],
                expected_behavior="Code coverage should be >= 90%",
                actual_behavior=f"Code coverage is {report.coverage_report.coverage_percentage:.1f}%",
                environment={"coverage": str(report.coverage_report.coverage_percentage)}
            )
            issues.append(issue)
        
        return issues
    
    def _determine_issue_severity(self, test: TestResult, suite: TestSuiteResult) -> IssueSeverity:
        """Determine issue severity based on test and suite context"""
        # Critical tests that should never fail
        critical_patterns = ["security", "data_integrity", "core_functionality"]
        
        if any(pattern in test.name.lower() for pattern in critical_patterns):
            return IssueSeverity.CRITICAL
        
        # High priority for integration and API tests
        if suite.category in [TestCategory.INTEGRATION, TestCategory.API, TestCategory.E2E]:
            return IssueSeverity.HIGH
        
        # Performance tests are high priority
        if suite.category == TestCategory.PERFORMANCE:
            return IssueSeverity.HIGH
        
        return IssueSeverity.MEDIUM
    
    def _map_test_category_to_issue_category(self, test_category: TestCategory) -> IssueCategory:
        """Map test category to issue category"""
        mapping = {
            TestCategory.PERFORMANCE: IssueCategory.PERFORMANCE,
            TestCategory.SECURITY: IssueCategory.SECURITY,
            TestCategory.ACCESSIBILITY: IssueCategory.ACCESSIBILITY,
        }
        return mapping.get(test_category, IssueCategory.BUG)
    
    async def _load_trends(self) -> List[TestTrend]:
        """Load historical test trends"""
        trends = []
        trends_file = self.data_dir / "trends.json"
        
        if trends_file.exists():
            try:
                with open(trends_file, 'r') as f:
                    trends_data = json.load(f)
                    
                for trend_data in trends_data:
                    trend = TestTrend(
                        date=datetime.fromisoformat(trend_data["date"]),
                        category=TestCategory(trend_data["category"]),
                        total_tests=trend_data["total_tests"],
                        passed_tests=trend_data["passed_tests"],
                        failed_tests=trend_data["failed_tests"],
                        pass_rate=trend_data["pass_rate"],
                        coverage_percentage=trend_data.get("coverage_percentage"),
                        average_duration=trend_data["average_duration"]
                    )
                    trends.append(trend)
            except Exception as e:
                print(f"Error loading trends: {e}")
        
        return trends
    
    async def _save_report(self, report: TestAnalysisReport):
        """Save test analysis report"""
        report_file = self.data_dir / f"report_{report.report_date.strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report.dict(), f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving report: {e}")
    
    async def update_trends(self, report: TestAnalysisReport):
        """Update trend data with new report"""
        trends_file = self.data_dir / "trends.json"
        
        # Load existing trends
        existing_trends = []
        if trends_file.exists():
            try:
                with open(trends_file, 'r') as f:
                    existing_trends = json.load(f)
            except Exception as e:
                print(f"Error loading existing trends: {e}")
        
        # Add new trend data points
        for suite in report.test_suites:
            trend_data = {
                "date": report.report_date.isoformat(),
                "category": suite.category.value,
                "total_tests": suite.total_tests,
                "passed_tests": suite.passed_tests,
                "failed_tests": suite.failed_tests,
                "pass_rate": suite.pass_rate,
                "coverage_percentage": suite.coverage_percentage,
                "average_duration": suite.duration / max(suite.total_tests, 1)
            }
            existing_trends.append(trend_data)
        
        # Keep only last 30 days of data
        cutoff_date = datetime.now() - timedelta(days=30)
        filtered_trends = [
            trend for trend in existing_trends
            if datetime.fromisoformat(trend["date"]) > cutoff_date
        ]
        
        # Save updated trends
        try:
            with open(trends_file, 'w') as f:
                json.dump(filtered_trends, f, indent=2)
        except Exception as e:
            print(f"Error saving trends: {e}")


class ImprovementSuggestionEngine:
    """Generate improvement suggestions based on test results"""
    
    async def generate_suggestions(self, report: TestAnalysisReport) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Coverage improvement suggestions
        if report.coverage_report and report.coverage_report.coverage_percentage < 90:
            suggestions.append(ImprovementSuggestion(
                title="Improve Code Coverage",
                description=f"Current coverage is {report.coverage_report.coverage_percentage:.1f}%, target is 90%+",
                priority=IssueSeverity.MEDIUM,
                category=IssueCategory.BUG,
                suggested_actions=[
                    "Add unit tests for uncovered functions",
                    "Review and test edge cases",
                    "Add integration tests for complex workflows",
                    "Consider property-based testing for data validation"
                ],
                impact_estimate="medium",
                effort_estimate="medium"
            ))
        
        # Performance improvement suggestions
        failed_benchmarks = [b for b in report.performance_benchmarks if not b.passed]
        if failed_benchmarks:
            suggestions.append(ImprovementSuggestion(
                title="Optimize Performance",
                description=f"{len(failed_benchmarks)} performance benchmarks failed",
                priority=IssueSeverity.HIGH,
                category=IssueCategory.PERFORMANCE,
                suggested_actions=[
                    "Profile slow operations to identify bottlenecks",
                    "Implement caching for frequently accessed data",
                    "Optimize database queries and indexes",
                    "Consider async processing for heavy operations"
                ],
                impact_estimate="high",
                effort_estimate="high"
            ))
        
        # Test stability suggestions
        flaky_tests = self._identify_flaky_tests(report)
        if flaky_tests:
            suggestions.append(ImprovementSuggestion(
                title="Fix Flaky Tests",
                description=f"Found {len(flaky_tests)} potentially flaky tests",
                priority=IssueSeverity.MEDIUM,
                category=IssueCategory.BUG,
                suggested_actions=[
                    "Add proper wait conditions for async operations",
                    "Use deterministic test data",
                    "Improve test isolation and cleanup",
                    "Add retry mechanisms for network-dependent tests"
                ],
                impact_estimate="medium",
                effort_estimate="low"
            ))
        
        # Security suggestions
        security_issues = [i for i in report.issues if i.category == IssueCategory.SECURITY]
        if security_issues:
            suggestions.append(ImprovementSuggestion(
                title="Address Security Issues",
                description=f"Found {len(security_issues)} security-related issues",
                priority=IssueSeverity.CRITICAL,
                category=IssueCategory.SECURITY,
                suggested_actions=[
                    "Review and fix security test failures",
                    "Update security testing coverage",
                    "Implement additional security controls",
                    "Schedule security audit"
                ],
                impact_estimate="high",
                effort_estimate="medium"
            ))
        
        return suggestions
    
    def _identify_flaky_tests(self, report: TestAnalysisReport) -> List[str]:
        """Identify potentially flaky tests based on patterns"""
        flaky_tests = []
        
        for suite in report.test_suites:
            for test in suite.test_results:
                # Look for tests with timing-related failures
                if test.status == TestStatus.FAILED and test.error_message:
                    flaky_patterns = ["timeout", "timing", "race condition", "intermittent"]
                    if any(pattern in test.error_message.lower() for pattern in flaky_patterns):
                        flaky_tests.append(test.name)
        
        return flaky_tests


class ExecutiveSummaryGenerator:
    """Generate executive summaries for stakeholders"""
    
    async def generate_summary(self, report: TestAnalysisReport) -> ExecutiveSummary:
        """Generate executive summary"""
        summary = ExecutiveSummary(
            overall_health_score=self._calculate_health_score(report),
            total_tests_executed=sum(suite.total_tests for suite in report.test_suites),
            overall_pass_rate=report.overall_pass_rate,
            critical_issues=len([i for i in report.issues if i.severity == IssueSeverity.CRITICAL]),
            high_priority_issues=len([i for i in report.issues if i.severity == IssueSeverity.HIGH]),
            coverage_percentage=report.coverage_report.coverage_percentage if report.coverage_report else None,
            performance_status=self._assess_performance_status(report),
            key_achievements=self._identify_achievements(report),
            top_concerns=self._identify_concerns(report),
            recommended_actions=self._generate_recommendations(report),
            trend_summary=self._generate_trend_summary(report)
        )
        
        return summary
    
    def _calculate_health_score(self, report: TestAnalysisReport) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0
        
        # Deduct for failed tests
        if report.overall_pass_rate < 100:
            score -= (100 - report.overall_pass_rate) * 0.5
        
        # Deduct for critical issues
        critical_issues = len([i for i in report.issues if i.severity == IssueSeverity.CRITICAL])
        score -= critical_issues * 20
        
        # Deduct for high priority issues
        high_issues = len([i for i in report.issues if i.severity == IssueSeverity.HIGH])
        score -= high_issues * 10
        
        # Deduct for low coverage
        if report.coverage_report and report.coverage_report.coverage_percentage < 90:
            score -= (90 - report.coverage_report.coverage_percentage) * 0.5
        
        # Deduct for performance issues
        failed_benchmarks = len([b for b in report.performance_benchmarks if not b.passed])
        score -= failed_benchmarks * 5
        
        return max(0.0, min(100.0, score))
    
    def _assess_performance_status(self, report: TestAnalysisReport) -> str:
        """Assess overall performance status"""
        failed_benchmarks = [b for b in report.performance_benchmarks if not b.passed]
        
        if not report.performance_benchmarks:
            return "unknown"
        
        failure_rate = len(failed_benchmarks) / len(report.performance_benchmarks)
        
        if failure_rate == 0:
            return "excellent"
        elif failure_rate < 0.1:
            return "good"
        elif failure_rate < 0.3:
            return "needs_attention"
        else:
            return "critical"
    
    def _identify_achievements(self, report: TestAnalysisReport) -> List[str]:
        """Identify key achievements"""
        achievements = []
        
        if report.overall_pass_rate >= 95:
            achievements.append(f"Excellent test pass rate: {report.overall_pass_rate:.1f}%")
        
        if report.coverage_report and report.coverage_report.coverage_percentage >= 90:
            achievements.append(f"Strong code coverage: {report.coverage_report.coverage_percentage:.1f}%")
        
        passed_benchmarks = [b for b in report.performance_benchmarks if b.passed]
        if len(passed_benchmarks) == len(report.performance_benchmarks) and report.performance_benchmarks:
            achievements.append("All performance benchmarks passed")
        
        security_suites = [s for s in report.test_suites if s.category == TestCategory.SECURITY]
        if security_suites and all(s.status == TestStatus.PASSED for s in security_suites):
            achievements.append("All security tests passed")
        
        return achievements
    
    def _identify_concerns(self, report: TestAnalysisReport) -> List[str]:
        """Identify top concerns"""
        concerns = []
        
        critical_issues = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            concerns.append(f"{len(critical_issues)} critical issues require immediate attention")
        
        if report.overall_pass_rate < 90:
            concerns.append(f"Low test pass rate: {report.overall_pass_rate:.1f}%")
        
        if report.coverage_report and report.coverage_report.coverage_percentage < 80:
            concerns.append(f"Low code coverage: {report.coverage_report.coverage_percentage:.1f}%")
        
        failed_benchmarks = [b for b in report.performance_benchmarks if not b.passed]
        if failed_benchmarks:
            concerns.append(f"{len(failed_benchmarks)} performance benchmarks failed")
        
        return concerns
    
    def _generate_recommendations(self, report: TestAnalysisReport) -> List[str]:
        """Generate recommended actions"""
        recommendations = []
        
        critical_issues = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append("Address critical issues immediately before release")
        
        if report.overall_pass_rate < 95:
            recommendations.append("Investigate and fix failing tests")
        
        if report.coverage_report and report.coverage_report.coverage_percentage < 90:
            recommendations.append("Increase test coverage to meet 90% target")
        
        failed_benchmarks = [b for b in report.performance_benchmarks if not b.passed]
        if failed_benchmarks:
            recommendations.append("Optimize performance to meet benchmark targets")
        
        return recommendations
    
    def _generate_trend_summary(self, report: TestAnalysisReport) -> str:
        """Generate trend summary"""
        if not report.trends:
            return "No historical data available for trend analysis"
        
        # Simple trend analysis - compare with previous week
        recent_trends = sorted(report.trends, key=lambda x: x.date, reverse=True)[:7]
        
        if len(recent_trends) < 2:
            return "Insufficient data for trend analysis"
        
        current_pass_rate = recent_trends[0].pass_rate
        previous_pass_rate = recent_trends[-1].pass_rate
        
        if current_pass_rate > previous_pass_rate:
            return f"Test quality improving: pass rate increased from {previous_pass_rate:.1f}% to {current_pass_rate:.1f}%"
        elif current_pass_rate < previous_pass_rate:
            return f"Test quality declining: pass rate decreased from {previous_pass_rate:.1f}% to {current_pass_rate:.1f}%"
        else:
            return f"Test quality stable: pass rate maintained at {current_pass_rate:.1f}%"