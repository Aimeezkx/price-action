#!/usr/bin/env python3
"""
Test the test analysis implementation
"""
import asyncio
import json
import tempfile
from pathlib import Path
import sys

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from test_analysis.analyzer import TestResultAnalyzer, ImprovementSuggestionEngine, ExecutiveSummaryGenerator
from test_analysis.models import TestCategory, TestStatus


async def test_analysis_system():
    """Test the test analysis system with sample data"""
    print("🧪 Testing Test Analysis System")
    print("=" * 50)
    
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        analyzer = TestResultAnalyzer(temp_dir)
        suggestion_engine = ImprovementSuggestionEngine()
        summary_generator = ExecutiveSummaryGenerator()
        
        # Create sample test data
        sample_data = {
            "test_suites": [
                {
                    "name": "Backend Unit Tests",
                    "category": "unit",
                    "status": "passed",
                    "total_tests": 150,
                    "passed_tests": 145,
                    "failed_tests": 3,
                    "skipped_tests": 2,
                    "error_tests": 0,
                    "duration": 45.2,
                    "coverage_percentage": 87.5,
                    "test_results": [
                        {
                            "name": "test_document_parser",
                            "status": "passed",
                            "duration": 0.5,
                            "metadata": {"file": "test_parser.py"}
                        },
                        {
                            "name": "test_invalid_input",
                            "status": "failed",
                            "duration": 0.3,
                            "error_message": "AssertionError: Expected validation error",
                            "metadata": {"file": "test_validation.py"}
                        }
                    ]
                },
                {
                    "name": "Frontend Unit Tests",
                    "category": "unit",
                    "status": "passed",
                    "total_tests": 85,
                    "passed_tests": 82,
                    "failed_tests": 1,
                    "skipped_tests": 2,
                    "error_tests": 0,
                    "duration": 23.1,
                    "coverage_percentage": 92.3
                },
                {
                    "name": "Integration Tests",
                    "category": "integration",
                    "status": "failed",
                    "total_tests": 45,
                    "passed_tests": 40,
                    "failed_tests": 5,
                    "skipped_tests": 0,
                    "error_tests": 0,
                    "duration": 120.5
                },
                {
                    "name": "E2E Tests",
                    "category": "e2e",
                    "status": "passed",
                    "total_tests": 25,
                    "passed_tests": 24,
                    "failed_tests": 1,
                    "skipped_tests": 0,
                    "error_tests": 0,
                    "duration": 180.3
                }
            ],
            "performance": {
                "document_processing": {
                    "metric": "processing_time",
                    "value": 28.5,
                    "unit": "seconds",
                    "threshold": 30,
                    "passed": True
                },
                "search_performance": {
                    "metric": "response_time",
                    "value": 650,
                    "unit": "ms",
                    "threshold": 500,
                    "passed": False
                },
                "api_response": {
                    "metric": "response_time",
                    "value": 120,
                    "unit": "ms",
                    "threshold": 200,
                    "passed": True
                }
            },
            "coverage": {
                "total_lines": 5000,
                "covered_lines": 4350,
                "coverage_percentage": 87.0,
                "uncovered_files": ["app/utils/legacy.py", "app/experimental/new_feature.py"],
                "coverage_by_file": {
                    "app/main.py": 95.2,
                    "app/models.py": 88.7,
                    "app/utils/legacy.py": 45.3,
                    "app/experimental/new_feature.py": 12.1
                }
            }
        }
        
        print("📊 Analyzing sample test data...")
        
        # Analyze the test data
        report = await analyzer.analyze_test_results(sample_data)
        
        print(f"✅ Analysis complete! Report ID: {report.id}")
        print(f"   Overall Status: {report.overall_status.value}")
        print(f"   Overall Pass Rate: {report.overall_pass_rate:.1f}%")
        print(f"   Total Issues: {len(report.issues)}")
        print(f"   Critical Issues: {report.critical_issues_count}")
        
        # Generate improvement suggestions
        print("\n💡 Generating improvement suggestions...")
        suggestions = await suggestion_engine.generate_suggestions(report)
        
        print(f"✅ Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion.title} ({suggestion.priority.value} priority)")
        
        # Generate executive summary
        print("\n📋 Generating executive summary...")
        summary = await summary_generator.generate_summary(report)
        
        print(f"✅ Executive Summary:")
        print(f"   Health Score: {summary.overall_health_score:.1f}/100")
        print(f"   Performance Status: {summary.performance_status}")
        print(f"   Key Achievements: {len(summary.key_achievements)}")
        print(f"   Top Concerns: {len(summary.top_concerns)}")
        print(f"   Recommended Actions: {len(summary.recommended_actions)}")
        
        # Test dashboard functionality
        print("\n📊 Testing dashboard functionality...")
        from test_analysis.dashboard import TestDashboard
        
        dashboard = TestDashboard(analyzer)
        dashboard_data = await dashboard.get_dashboard_data()
        
        if "error" not in dashboard_data:
            print("✅ Dashboard data generated successfully")
            print(f"   Total Tests: {dashboard_data.get('total_tests', 0)}")
            print(f"   Pass Rate: {dashboard_data.get('overall_pass_rate', 0):.1f}%")
        else:
            print(f"❌ Dashboard error: {dashboard_data['error']}")
        
        # Test report generation
        print("\n📄 Testing report generation...")
        from test_analysis.dashboard import ReportGenerator
        
        report_generator = ReportGenerator(analyzer)
        
        # Generate HTML report
        html_content = await report_generator.generate_html_report(report)
        print(f"✅ HTML report generated ({len(html_content)} characters)")
        
        # Generate JSON report
        json_content = await report_generator.generate_json_report(report)
        json_data = json.loads(json_content)
        print(f"✅ JSON report generated ({len(json_data)} sections)")
        
        print("\n🎉 All tests passed! Test analysis system is working correctly.")
        
        # Print sample executive summary
        print("\n" + "="*60)
        print("SAMPLE EXECUTIVE SUMMARY")
        print("="*60)
        print(f"Health Score: {summary.overall_health_score:.1f}/100")
        print(f"Pass Rate: {summary.overall_pass_rate:.1f}%")
        print(f"Total Tests: {summary.total_tests_executed}")
        print(f"Critical Issues: {summary.critical_issues}")
        print(f"Coverage: {summary.coverage_percentage:.1f}%")
        print(f"Performance: {summary.performance_status}")
        
        if summary.key_achievements:
            print("\n🎉 Key Achievements:")
            for achievement in summary.key_achievements:
                print(f"   ✓ {achievement}")
        
        if summary.top_concerns:
            print("\n⚠️  Top Concerns:")
            for concern in summary.top_concerns:
                print(f"   ⚠ {concern}")
        
        if summary.recommended_actions:
            print("\n🔧 Recommended Actions:")
            for action in summary.recommended_actions:
                print(f"   → {action}")
        
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_analysis_system())
        if success:
            print("\n✅ Test analysis implementation verified successfully!")
            sys.exit(0)
        else:
            print("\n❌ Test analysis implementation verification failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)