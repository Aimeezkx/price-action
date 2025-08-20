#!/usr/bin/env python3
"""
Test Analysis CLI Tool
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from test_analysis.analyzer import TestResultAnalyzer, ImprovementSuggestionEngine, ExecutiveSummaryGenerator
from test_analysis.collectors import TestResultAggregator
from test_analysis.dashboard import ReportGenerator


async def run_analysis(args):
    """Run comprehensive test analysis"""
    print("🔍 Starting test analysis...")
    
    # Initialize components
    aggregator = TestResultAggregator()
    analyzer = TestResultAnalyzer(args.data_dir)
    suggestion_engine = ImprovementSuggestionEngine()
    summary_generator = ExecutiveSummaryGenerator()
    report_generator = ReportGenerator(analyzer)
    
    try:
        # Collect test results
        print("📊 Collecting test results...")
        test_data = await aggregator.collect_all_results()
        
        if test_data.get("errors"):
            print("⚠️  Errors during collection:")
            for error in test_data["errors"]:
                print(f"   - {error['collector']}: {error['error']}")
        
        # Analyze results
        print("🔬 Analyzing test results...")
        report = await analyzer.analyze_test_results(test_data)
        
        # Update trends
        print("📈 Updating trend data...")
        await analyzer.update_trends(report)
        
        # Generate suggestions
        print("💡 Generating improvement suggestions...")
        suggestions = await suggestion_engine.generate_suggestions(report)
        
        # Generate executive summary
        print("📋 Creating executive summary...")
        executive_summary = await summary_generator.generate_summary(report)
        
        # Print summary to console
        print("\n" + "="*60)
        print("TEST ANALYSIS SUMMARY")
        print("="*60)
        print(f"Overall Status: {report.overall_status.value.upper()}")
        print(f"Health Score: {executive_summary.overall_health_score:.1f}/100")
        print(f"Pass Rate: {report.overall_pass_rate:.1f}%")
        print(f"Total Tests: {executive_summary.total_tests_executed}")
        print(f"Critical Issues: {executive_summary.critical_issues}")
        print(f"High Priority Issues: {executive_summary.high_priority_issues}")
        
        if executive_summary.coverage_percentage:
            print(f"Coverage: {executive_summary.coverage_percentage:.1f}%")
        
        print(f"Performance Status: {executive_summary.performance_status}")
        
        if executive_summary.key_achievements:
            print("\n🎉 Key Achievements:")
            for achievement in executive_summary.key_achievements:
                print(f"   ✓ {achievement}")
        
        if executive_summary.top_concerns:
            print("\n⚠️  Top Concerns:")
            for concern in executive_summary.top_concerns:
                print(f"   ⚠ {concern}")
        
        if executive_summary.recommended_actions:
            print("\n🔧 Recommended Actions:")
            for action in executive_summary.recommended_actions:
                print(f"   → {action}")
        
        if suggestions:
            print(f"\n💡 Improvement Suggestions ({len(suggestions)}):")
            for suggestion in suggestions[:5]:  # Show top 5
                print(f"   • {suggestion.title} ({suggestion.priority.value} priority)")
        
        print(f"\n📊 Trend Summary: {executive_summary.trend_summary}")
        
        # Generate reports if requested
        if args.generate_html:
            print("\n📄 Generating HTML report...")
            html_path = await report_generator.save_report(report, "html")
            print(f"   HTML report saved: {html_path}")
        
        if args.generate_json:
            print("\n📄 Generating JSON report...")
            json_path = await report_generator.save_report(report, "json")
            print(f"   JSON report saved: {json_path}")
        
        # Save raw data if requested
        if args.save_raw:
            raw_file = Path(args.data_dir) / f"raw_data_{report.report_date.strftime('%Y%m%d_%H%M%S')}.json"
            with open(raw_file, 'w') as f:
                json.dump(test_data, f, indent=2, default=str)
            print(f"   Raw data saved: {raw_file}")
        
        print("\n✅ Analysis complete!")
        
        # Exit with appropriate code
        if executive_summary.critical_issues > 0:
            print("❌ Exiting with error code due to critical issues")
            return 2
        elif report.overall_status.value == "failed":
            print("⚠️  Exiting with warning code due to test failures")
            return 1
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 3


async def show_dashboard(args):
    """Show dashboard data"""
    from test_analysis.dashboard import TestDashboard
    
    analyzer = TestResultAnalyzer(args.data_dir)
    dashboard = TestDashboard(analyzer)
    
    try:
        print("📊 Loading dashboard data...")
        dashboard_data = await dashboard.get_dashboard_data(args.days)
        
        if "error" in dashboard_data:
            print(f"❌ {dashboard_data['error']}")
            return 1
        
        # Print dashboard summary
        print("\n" + "="*60)
        print("TEST DASHBOARD")
        print("="*60)
        
        exec_summary = dashboard_data.get("executive_summary", {})
        print(f"Health Score: {exec_summary.get('overall_health_score', 0):.1f}/100")
        print(f"Pass Rate: {dashboard_data.get('overall_pass_rate', 0):.1f}%")
        print(f"Total Tests: {dashboard_data.get('total_tests', 0)}")
        print(f"Last Updated: {dashboard_data.get('last_updated', 'Unknown')}")
        
        # Show suite breakdown
        suite_breakdown = dashboard_data.get("suite_breakdown", {})
        if suite_breakdown.get("suite_details"):
            print("\n📋 Test Suites:")
            for suite in suite_breakdown["suite_details"]:
                status_icon = "✅" if suite["status"] == "passed" else "❌"
                print(f"   {status_icon} {suite['name']}: {suite['pass_rate']:.1f}% ({suite['total_tests']} tests)")
        
        # Show recent issues
        issue_summary = dashboard_data.get("issue_summary", {})
        if issue_summary.get("recent_issues"):
            print("\n🐛 Recent Issues:")
            for issue in issue_summary["recent_issues"][:5]:
                severity_icon = "🔴" if issue["severity"] == "critical" else "🟡"
                print(f"   {severity_icon} {issue['title']} ({issue['severity']})")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to load dashboard: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


async def generate_report(args):
    """Generate test report"""
    analyzer = TestResultAnalyzer(args.data_dir)
    report_generator = ReportGenerator(analyzer)
    
    try:
        # Load latest report
        from test_analysis.dashboard import TestDashboard
        dashboard = TestDashboard(analyzer)
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            print("❌ No test reports found. Run analysis first.")
            return 1
        
        print(f"📄 Generating {args.format} report...")
        report_path = await report_generator.save_report(latest_report, args.format)
        print(f"✅ Report saved: {report_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Test Analysis CLI Tool")
    parser.add_argument("--data-dir", default="test_results", help="Directory for test data")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run comprehensive test analysis")
    analyze_parser.add_argument("--generate-html", action="store_true", help="Generate HTML report")
    analyze_parser.add_argument("--generate-json", action="store_true", help="Generate JSON report")
    analyze_parser.add_argument("--save-raw", action="store_true", help="Save raw test data")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Show dashboard summary")
    dashboard_parser.add_argument("--days", type=int, default=7, help="Days for trend analysis")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate test report")
    report_parser.add_argument("--format", choices=["html", "json"], default="html", help="Report format")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run the appropriate command
    if args.command == "analyze":
        return asyncio.run(run_analysis(args))
    elif args.command == "dashboard":
        return asyncio.run(show_dashboard(args))
    elif args.command == "report":
        return asyncio.run(generate_report(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())