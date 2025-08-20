"""
Test Result Dashboard and Visualization
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    TestAnalysisReport, TestSuiteResult, TestCategory, TestStatus,
    PerformanceBenchmark, CoverageReport, TestTrend, ExecutiveSummary
)
from .analyzer import TestResultAnalyzer, ExecutiveSummaryGenerator


class TestDashboard:
    """Test result dashboard with visualization data"""
    
    def __init__(self, analyzer: TestResultAnalyzer):
        self.analyzer = analyzer
        self.summary_generator = ExecutiveSummaryGenerator()
    
    async def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        # Load latest report
        latest_report = await self._get_latest_report()
        
        if not latest_report:
            return {"error": "No test reports available"}
        
        # Generate executive summary
        executive_summary = await self.summary_generator.generate_summary(latest_report)
        
        # Get trend data
        trend_data = await self._get_trend_data(days)
        
        # Get test suite breakdown
        suite_breakdown = self._get_suite_breakdown(latest_report)
        
        # Get performance metrics
        performance_metrics = self._get_performance_metrics(latest_report)
        
        # Get coverage analysis
        coverage_analysis = self._get_coverage_analysis(latest_report)
        
        # Get issue summary
        issue_summary = self._get_issue_summary(latest_report)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "executive_summary": executive_summary.dict(),
            "overall_status": latest_report.overall_status.value,
            "overall_pass_rate": latest_report.overall_pass_rate,
            "total_tests": sum(suite.total_tests for suite in latest_report.test_suites),
            "trend_data": trend_data,
            "suite_breakdown": suite_breakdown,
            "performance_metrics": performance_metrics,
            "coverage_analysis": coverage_analysis,
            "issue_summary": issue_summary,
            "last_updated": latest_report.report_date.isoformat()
        }
    
    async def _get_latest_report(self) -> Optional[TestAnalysisReport]:
        """Get the most recent test analysis report"""
        reports_dir = self.analyzer.data_dir
        
        if not reports_dir.exists():
            return None
        
        # Find the most recent report file
        report_files = list(reports_dir.glob("report_*.json"))
        
        if not report_files:
            return None
        
        latest_file = max(report_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                report_data = json.load(f)
                return TestAnalysisReport(**report_data)
        except Exception as e:
            print(f"Error loading report {latest_file}: {e}")
            return None
    
    async def _get_trend_data(self, days: int) -> Dict[str, Any]:
        """Get trend data for visualization"""
        trends_file = self.analyzer.data_dir / "trends.json"
        
        if not trends_file.exists():
            return {"pass_rate_trend": [], "coverage_trend": [], "duration_trend": []}
        
        try:
            with open(trends_file, 'r') as f:
                all_trends = json.load(f)
            
            # Filter to requested time period
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_trends = [
                trend for trend in all_trends
                if datetime.fromisoformat(trend["date"]) > cutoff_date
            ]
            
            # Group by date and aggregate
            daily_data = {}
            for trend in recent_trends:
                date = trend["date"][:10]  # Get date part only
                
                if date not in daily_data:
                    daily_data[date] = {
                        "total_tests": 0,
                        "passed_tests": 0,
                        "total_duration": 0.0,
                        "coverage_sum": 0.0,
                        "coverage_count": 0
                    }
                
                daily_data[date]["total_tests"] += trend["total_tests"]
                daily_data[date]["passed_tests"] += trend["passed_tests"]
                daily_data[date]["total_duration"] += trend["average_duration"] * trend["total_tests"]
                
                if trend.get("coverage_percentage"):
                    daily_data[date]["coverage_sum"] += trend["coverage_percentage"]
                    daily_data[date]["coverage_count"] += 1
            
            # Convert to chart data
            dates = sorted(daily_data.keys())
            
            pass_rate_trend = []
            coverage_trend = []
            duration_trend = []
            
            for date in dates:
                data = daily_data[date]
                
                # Pass rate
                pass_rate = (data["passed_tests"] / data["total_tests"] * 100) if data["total_tests"] > 0 else 0
                pass_rate_trend.append({"date": date, "value": pass_rate})
                
                # Coverage
                if data["coverage_count"] > 0:
                    avg_coverage = data["coverage_sum"] / data["coverage_count"]
                    coverage_trend.append({"date": date, "value": avg_coverage})
                
                # Duration
                avg_duration = data["total_duration"] / data["total_tests"] if data["total_tests"] > 0 else 0
                duration_trend.append({"date": date, "value": avg_duration})
            
            return {
                "pass_rate_trend": pass_rate_trend,
                "coverage_trend": coverage_trend,
                "duration_trend": duration_trend
            }
            
        except Exception as e:
            print(f"Error loading trend data: {e}")
            return {"pass_rate_trend": [], "coverage_trend": [], "duration_trend": []}
    
    def _get_suite_breakdown(self, report: TestAnalysisReport) -> Dict[str, Any]:
        """Get test suite breakdown for visualization"""
        breakdown = {
            "by_category": {},
            "by_status": {},
            "suite_details": []
        }
        
        # Breakdown by category
        for suite in report.test_suites:
            category = suite.category.value
            
            if category not in breakdown["by_category"]:
                breakdown["by_category"][category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "error": 0
                }
            
            breakdown["by_category"][category]["total"] += suite.total_tests
            breakdown["by_category"][category]["passed"] += suite.passed_tests
            breakdown["by_category"][category]["failed"] += suite.failed_tests
            breakdown["by_category"][category]["skipped"] += suite.skipped_tests
            breakdown["by_category"][category]["error"] += suite.error_tests
        
        # Breakdown by status
        total_tests = sum(suite.total_tests for suite in report.test_suites)
        total_passed = sum(suite.passed_tests for suite in report.test_suites)
        total_failed = sum(suite.failed_tests for suite in report.test_suites)
        total_skipped = sum(suite.skipped_tests for suite in report.test_suites)
        total_error = sum(suite.error_tests for suite in report.test_suites)
        
        breakdown["by_status"] = {
            "passed": {"count": total_passed, "percentage": (total_passed / total_tests * 100) if total_tests > 0 else 0},
            "failed": {"count": total_failed, "percentage": (total_failed / total_tests * 100) if total_tests > 0 else 0},
            "skipped": {"count": total_skipped, "percentage": (total_skipped / total_tests * 100) if total_tests > 0 else 0},
            "error": {"count": total_error, "percentage": (total_error / total_tests * 100) if total_tests > 0 else 0}
        }
        
        # Suite details
        for suite in report.test_suites:
            breakdown["suite_details"].append({
                "name": suite.name,
                "category": suite.category.value,
                "status": suite.status.value,
                "pass_rate": suite.pass_rate,
                "total_tests": suite.total_tests,
                "duration": suite.duration,
                "coverage": suite.coverage_percentage
            })
        
        return breakdown
    
    def _get_performance_metrics(self, report: TestAnalysisReport) -> Dict[str, Any]:
        """Get performance metrics for visualization"""
        metrics = {
            "benchmarks": [],
            "summary": {
                "total_benchmarks": len(report.performance_benchmarks),
                "passed_benchmarks": len([b for b in report.performance_benchmarks if b.passed]),
                "failed_benchmarks": len([b for b in report.performance_benchmarks if not b.passed])
            }
        }
        
        for benchmark in report.performance_benchmarks:
            metrics["benchmarks"].append({
                "name": benchmark.name,
                "metric": benchmark.metric,
                "value": benchmark.value,
                "unit": benchmark.unit,
                "threshold": benchmark.threshold,
                "passed": benchmark.passed,
                "status": "pass" if benchmark.passed else "fail"
            })
        
        return metrics
    
    def _get_coverage_analysis(self, report: TestAnalysisReport) -> Dict[str, Any]:
        """Get coverage analysis for visualization"""
        if not report.coverage_report:
            return {"error": "No coverage data available"}
        
        coverage = report.coverage_report
        
        analysis = {
            "overall": {
                "percentage": coverage.coverage_percentage,
                "total_lines": coverage.total_lines,
                "covered_lines": coverage.covered_lines,
                "uncovered_lines": coverage.total_lines - coverage.covered_lines
            },
            "by_file": [],
            "uncovered_files": coverage.uncovered_files,
            "status": self._get_coverage_status(coverage.coverage_percentage)
        }
        
        # File-level coverage
        for file_path, file_coverage in coverage.coverage_by_file.items():
            analysis["by_file"].append({
                "file": file_path,
                "coverage": file_coverage,
                "status": self._get_coverage_status(file_coverage)
            })
        
        # Sort by coverage percentage (lowest first)
        analysis["by_file"].sort(key=lambda x: x["coverage"])
        
        return analysis
    
    def _get_coverage_status(self, percentage: float) -> str:
        """Get coverage status based on percentage"""
        if percentage >= 90:
            return "excellent"
        elif percentage >= 80:
            return "good"
        elif percentage >= 70:
            return "fair"
        else:
            return "poor"
    
    def _get_issue_summary(self, report: TestAnalysisReport) -> Dict[str, Any]:
        """Get issue summary for visualization"""
        summary = {
            "total_issues": len(report.issues),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "by_category": {},
            "recent_issues": []
        }
        
        for issue in report.issues:
            # Count by severity
            summary["by_severity"][issue.severity.value] += 1
            
            # Count by category
            category = issue.category.value
            if category not in summary["by_category"]:
                summary["by_category"][category] = 0
            summary["by_category"][category] += 1
        
        # Get recent issues (sorted by creation date)
        sorted_issues = sorted(report.issues, key=lambda x: x.created_at, reverse=True)
        
        for issue in sorted_issues[:10]:  # Top 10 recent issues
            summary["recent_issues"].append({
                "id": issue.id,
                "title": issue.title,
                "severity": issue.severity.value,
                "category": issue.category.value,
                "test_case": issue.test_case,
                "created_at": issue.created_at.isoformat()
            })
        
        return summary


class ReportGenerator:
    """Generate various types of test reports"""
    
    def __init__(self, analyzer: TestResultAnalyzer):
        self.analyzer = analyzer
        self.summary_generator = ExecutiveSummaryGenerator()
    
    async def generate_html_report(self, report: TestAnalysisReport) -> str:
        """Generate HTML test report"""
        executive_summary = await self.summary_generator.generate_summary(report)
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Analysis Report - {report_date}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .warning {{ background-color: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .error {{ background-color: #f8d7da; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 3px; }}
                .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .pass {{ color: #28a745; }}
                .fail {{ color: #dc3545; }}
                .skip {{ color: #ffc107; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Analysis Report</h1>
                <p><strong>Generated:</strong> {report_date}</p>
                <p><strong>Overall Status:</strong> <span class="{overall_status_class}">{overall_status}</span></p>
                <p><strong>Health Score:</strong> {health_score:.1f}/100</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div class="metric">
                    <strong>Total Tests:</strong> {total_tests}
                </div>
                <div class="metric">
                    <strong>Pass Rate:</strong> {pass_rate:.1f}%
                </div>
                <div class="metric">
                    <strong>Coverage:</strong> {coverage}%
                </div>
                <div class="metric">
                    <strong>Critical Issues:</strong> {critical_issues}
                </div>
                
                <h3>Key Achievements</h3>
                <ul>
                    {achievements}
                </ul>
                
                <h3>Top Concerns</h3>
                <ul>
                    {concerns}
                </ul>
            </div>
            
            <h2>Test Suite Results</h2>
            {suite_results}
            
            <h2>Performance Benchmarks</h2>
            {performance_results}
            
            <h2>Coverage Report</h2>
            {coverage_report}
            
            <h2>Issues Found</h2>
            {issues_report}
        </body>
        </html>
        """
        
        # Format data for template
        overall_status_class = "pass" if report.overall_status == TestStatus.PASSED else "fail"
        
        achievements = "".join(f"<li>{achievement}</li>" for achievement in executive_summary.key_achievements)
        concerns = "".join(f"<li>{concern}</li>" for concern in executive_summary.top_concerns)
        
        # Generate suite results HTML
        suite_results = ""
        for suite in report.test_suites:
            status_class = "pass" if suite.status == TestStatus.PASSED else "fail"
            suite_results += f"""
            <div class="suite">
                <h3>{suite.name} <span class="{status_class}">({suite.status.value})</span></h3>
                <p>Category: {suite.category.value}</p>
                <p>Tests: {suite.total_tests} total, {suite.passed_tests} passed, {suite.failed_tests} failed</p>
                <p>Duration: {suite.duration:.2f}s</p>
                {f'<p>Coverage: {suite.coverage_percentage:.1f}%</p>' if suite.coverage_percentage else ''}
            </div>
            """
        
        # Generate performance results HTML
        performance_results = "<table><tr><th>Benchmark</th><th>Metric</th><th>Value</th><th>Threshold</th><th>Status</th></tr>"
        for benchmark in report.performance_benchmarks:
            status_class = "pass" if benchmark.passed else "fail"
            performance_results += f"""
            <tr>
                <td>{benchmark.name}</td>
                <td>{benchmark.metric}</td>
                <td>{benchmark.value} {benchmark.unit}</td>
                <td>{benchmark.threshold or 'N/A'}</td>
                <td class="{status_class}">{'PASS' if benchmark.passed else 'FAIL'}</td>
            </tr>
            """
        performance_results += "</table>"
        
        # Generate coverage report HTML
        coverage_report = ""
        if report.coverage_report:
            coverage_report = f"""
            <p><strong>Overall Coverage:</strong> {report.coverage_report.coverage_percentage:.1f}%</p>
            <p><strong>Lines:</strong> {report.coverage_report.covered_lines}/{report.coverage_report.total_lines}</p>
            """
        else:
            coverage_report = "<p>No coverage data available</p>"
        
        # Generate issues report HTML
        issues_report = "<table><tr><th>Title</th><th>Severity</th><th>Category</th><th>Test Case</th></tr>"
        for issue in report.issues:
            severity_class = "error" if issue.severity.value in ["critical", "high"] else "warning"
            issues_report += f"""
            <tr class="{severity_class}">
                <td>{issue.title}</td>
                <td>{issue.severity.value.upper()}</td>
                <td>{issue.category.value}</td>
                <td>{issue.test_case}</td>
            </tr>
            """
        issues_report += "</table>"
        
        # Fill template
        html_content = html_template.format(
            report_date=report.report_date.strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=report.overall_status.value.upper(),
            overall_status_class=overall_status_class,
            health_score=executive_summary.overall_health_score,
            total_tests=executive_summary.total_tests_executed,
            pass_rate=executive_summary.overall_pass_rate,
            coverage=executive_summary.coverage_percentage or 0,
            critical_issues=executive_summary.critical_issues,
            achievements=achievements,
            concerns=concerns,
            suite_results=suite_results,
            performance_results=performance_results,
            coverage_report=coverage_report,
            issues_report=issues_report
        )
        
        return html_content
    
    async def generate_json_report(self, report: TestAnalysisReport) -> str:
        """Generate JSON test report"""
        executive_summary = await self.summary_generator.generate_summary(report)
        
        json_report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_date": report.report_date.isoformat(),
                "report_id": report.id
            },
            "executive_summary": executive_summary.dict(),
            "test_results": report.dict(),
            "summary_statistics": {
                "total_test_suites": len(report.test_suites),
                "total_tests": sum(suite.total_tests for suite in report.test_suites),
                "overall_pass_rate": report.overall_pass_rate,
                "total_issues": len(report.issues),
                "critical_issues": len([i for i in report.issues if i.severity.value == "critical"]),
                "performance_benchmarks": len(report.performance_benchmarks),
                "failed_benchmarks": len([b for b in report.performance_benchmarks if not b.passed])
            }
        }
        
        return json.dumps(json_report, indent=2, default=str)
    
    async def save_report(self, report: TestAnalysisReport, format: str = "html") -> str:
        """Save report to file and return file path"""
        timestamp = report.report_date.strftime("%Y%m%d_%H%M%S")
        
        if format == "html":
            content = await self.generate_html_report(report)
            filename = f"test_report_{timestamp}.html"
        elif format == "json":
            content = await self.generate_json_report(report)
            filename = f"test_report_{timestamp}.json"
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        report_path = self.analyzer.data_dir / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write(content)
        
        return str(report_path)