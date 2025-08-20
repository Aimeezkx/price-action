#!/usr/bin/env python3
"""
User Acceptance Testing CLI Tool
"""
import asyncio
import click
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from app.user_acceptance.scenario_manager import ScenarioManager
from app.user_acceptance.feedback_system import FeedbackCollector, FeedbackAnalyzer
from app.user_acceptance.ab_testing import ABTestManager
from app.user_acceptance.ux_metrics import UXMetricsCollector, UXMetricsAnalyzer
from app.user_acceptance.satisfaction_tracker import SatisfactionTracker


@click.group()
def cli():
    """User Acceptance Testing CLI Tool"""
    pass


@cli.group()
def scenarios():
    """Manage test scenarios"""
    pass


@scenarios.command()
def list():
    """List all test scenarios"""
    manager = ScenarioManager()
    scenarios = manager.get_all_scenarios()
    
    if not scenarios:
        click.echo("No scenarios found.")
        return
    
    click.echo(f"\nFound {len(scenarios)} test scenarios:\n")
    
    for scenario in scenarios:
        click.echo(f"ID: {scenario.id}")
        click.echo(f"Name: {scenario.name}")
        click.echo(f"Type: {scenario.scenario_type}")
        click.echo(f"Duration: {scenario.estimated_duration} minutes")
        click.echo(f"Difficulty: {scenario.difficulty_level}")
        click.echo(f"Steps: {len(scenario.steps)}")
        click.echo("-" * 50)


@scenarios.command()
@click.argument('scenario_id')
def show(scenario_id: str):
    """Show detailed information about a scenario"""
    manager = ScenarioManager()
    scenario = manager.get_scenario(scenario_id)
    
    if not scenario:
        click.echo(f"Scenario {scenario_id} not found.")
        return
    
    click.echo(f"\nScenario: {scenario.name}")
    click.echo(f"ID: {scenario.id}")
    click.echo(f"Type: {scenario.scenario_type}")
    click.echo(f"Description: {scenario.description}")
    click.echo(f"Estimated Duration: {scenario.estimated_duration} minutes")
    click.echo(f"Difficulty: {scenario.difficulty_level}")
    
    click.echo(f"\nSteps ({len(scenario.steps)}):")
    for i, step in enumerate(scenario.steps, 1):
        click.echo(f"  {i}. {step}")
    
    click.echo(f"\nExpected Outcomes:")
    for i, outcome in enumerate(scenario.expected_outcomes, 1):
        click.echo(f"  {i}. {outcome}")
    
    click.echo(f"\nSuccess Criteria:")
    for i, criteria in enumerate(scenario.success_criteria, 1):
        click.echo(f"  {i}. {criteria}")


@scenarios.command()
@click.option('--file', '-f', help='JSON file with scenario data')
def create(file: str):
    """Create a new test scenario"""
    if file:
        with open(file, 'r') as f:
            scenario_data = json.load(f)
    else:
        # Interactive creation
        scenario_data = {}
        scenario_data['name'] = click.prompt('Scenario name')
        scenario_data['description'] = click.prompt('Description')
        scenario_data['scenario_type'] = click.prompt(
            'Type', 
            type=click.Choice(['document_upload', 'card_review', 'search_usage', 'chapter_browsing', 'export_functionality', 'mobile_usage', 'accessibility'])
        )
        scenario_data['estimated_duration'] = click.prompt('Estimated duration (minutes)', type=int)
        scenario_data['difficulty_level'] = click.prompt(
            'Difficulty level',
            type=click.Choice(['beginner', 'intermediate', 'advanced'])
        )
        
        # Steps
        steps = []
        click.echo("Enter test steps (empty line to finish):")
        while True:
            step = click.prompt(f'Step {len(steps) + 1}', default='', show_default=False)
            if not step:
                break
            steps.append(step)
        scenario_data['steps'] = steps
        
        # Expected outcomes
        outcomes = []
        click.echo("Enter expected outcomes (empty line to finish):")
        while True:
            outcome = click.prompt(f'Outcome {len(outcomes) + 1}', default='', show_default=False)
            if not outcome:
                break
            outcomes.append(outcome)
        scenario_data['expected_outcomes'] = outcomes
        
        # Success criteria
        criteria = []
        click.echo("Enter success criteria (empty line to finish):")
        while True:
            criterion = click.prompt(f'Criterion {len(criteria) + 1}', default='', show_default=False)
            if not criterion:
                break
            criteria.append(criterion)
        scenario_data['success_criteria'] = criteria
    
    manager = ScenarioManager()
    scenario = manager.create_scenario(scenario_data)
    
    click.echo(f"\nCreated scenario: {scenario.name} (ID: {scenario.id})")


@cli.group()
def feedback():
    """Manage user feedback"""
    pass


@feedback.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
def analyze(days: int):
    """Analyze user feedback"""
    collector = FeedbackCollector()
    analyzer = FeedbackAnalyzer(collector)
    
    click.echo(f"Analyzing feedback from the last {days} days...\n")
    
    # Get feedback themes
    themes = analyzer.analyze_feedback_themes(days)
    
    if 'error' in themes:
        click.echo(f"Error: {themes['error']}")
        return
    
    click.echo(f"Total feedback items: {themes['total_feedback']}")
    
    if themes['total_feedback'] > 0:
        click.echo(f"\nFeedback by type:")
        for feedback_type, count in themes['by_type'].items():
            click.echo(f"  {feedback_type}: {count}")
        
        click.echo(f"\nFeedback by category:")
        for category, count in themes['by_category'].items():
            click.echo(f"  {category}: {count}")
        
        click.echo(f"\nFeedback by severity:")
        for severity, count in themes['by_severity'].items():
            click.echo(f"  {severity}: {count}")
        
        if themes['top_tags']:
            click.echo(f"\nTop tags:")
            for tag, count in list(themes['top_tags'].items())[:5]:
                click.echo(f"  {tag}: {count}")
        
        click.echo(f"\nCritical issues: {themes['critical_issues']}")
        click.echo(f"Bug reports: {themes['bug_reports']}")
        click.echo(f"Usability issues: {themes['usability_issues']}")


@feedback.command()
def improvements():
    """Show improvement opportunities"""
    collector = FeedbackCollector()
    analyzer = FeedbackAnalyzer(collector)
    
    opportunities = analyzer.identify_improvement_opportunities()
    
    if not opportunities:
        click.echo("No improvement opportunities identified.")
        return
    
    click.echo(f"Found {len(opportunities)} improvement opportunities:\n")
    
    for i, opp in enumerate(opportunities, 1):
        click.echo(f"{i}. {opp['description']}")
        click.echo(f"   Type: {opp['type']}")
        click.echo(f"   Priority: {opp['priority']}")
        if 'frequency' in opp:
            click.echo(f"   Frequency: {opp['frequency']}")
        click.echo()


@cli.group()
def satisfaction():
    """Manage satisfaction tracking"""
    pass


@satisfaction.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
def overview(days: int):
    """Show satisfaction overview"""
    tracker = SatisfactionTracker()
    overview = tracker.get_satisfaction_overview(days)
    
    if 'error' in overview:
        click.echo(f"Error: {overview['error']}")
        return
    
    click.echo(f"Satisfaction Overview (Last {days} days)\n")
    click.echo(f"Total responses: {overview['total_responses']}")
    
    if overview['total_responses'] > 0:
        click.echo(f"\nAverage Scores (out of 5):")
        for metric, stats in overview['averages'].items():
            if metric != 'nps_score':
                click.echo(f"  {metric.replace('_', ' ').title()}: {stats['mean']:.1f}")
        
        click.echo(f"\nNet Promoter Score: {overview['nps']['score']:.1f}")
        click.echo(f"  Promoters: {overview['nps']['promoters']}")
        click.echo(f"  Passives: {overview['nps']['passives']}")
        click.echo(f"  Detractors: {overview['nps']['detractors']}")
        
        if 'insights' in overview:
            click.echo(f"\nInsights:")
            for insight in overview['insights']:
                click.echo(f"  • {insight}")


@satisfaction.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
def issues(days: int):
    """Show satisfaction issues"""
    tracker = SatisfactionTracker()
    issues = tracker.identify_satisfaction_issues(days)
    
    if not issues:
        click.echo("No satisfaction issues identified.")
        return
    
    click.echo(f"Found {len(issues)} satisfaction issues:\n")
    
    for i, issue in enumerate(issues, 1):
        click.echo(f"{i}. {issue['description']}")
        click.echo(f"   Severity: {issue['severity']}")
        click.echo(f"   Current Score: {issue['current_score']}")
        click.echo(f"   Sample Size: {issue['sample_size']}")
        click.echo()


@cli.group()
def ab_tests():
    """Manage A/B tests"""
    pass


@ab_tests.command()
def list():
    """List all A/B tests"""
    manager = ABTestManager()
    tests = list(manager.tests.values())
    
    if not tests:
        click.echo("No A/B tests found.")
        return
    
    click.echo(f"\nFound {len(tests)} A/B tests:\n")
    
    for test in tests:
        click.echo(f"ID: {test.id}")
        click.echo(f"Name: {test.name}")
        click.echo(f"Feature: {test.feature_name}")
        click.echo(f"Status: {test.status}")
        click.echo(f"Variants: {len(test.variants)}")
        click.echo(f"Start: {test.start_date.strftime('%Y-%m-%d')}")
        click.echo(f"End: {test.end_date.strftime('%Y-%m-%d')}")
        click.echo("-" * 50)


@ab_tests.command()
@click.argument('test_id')
def results(test_id: str):
    """Show A/B test results"""
    manager = ABTestManager()
    
    try:
        results = manager.get_test_results(test_id)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return
    
    if 'error' in results:
        click.echo(f"Error: {results['error']}")
        return
    
    click.echo(f"\nA/B Test Results: {results['test_name']}")
    click.echo(f"Status: {results['status']}")
    click.echo(f"Total Results: {results['total_results']}")
    
    click.echo(f"\nVariant Statistics:")
    for variant_id, stats in results['variant_statistics'].items():
        click.echo(f"\n  {stats['name']} {'(Control)' if stats['is_control'] else ''}")
        click.echo(f"    Sample Size: {stats['sample_size']}")
        click.echo(f"    Unique Users: {stats['unique_users']}")
        click.echo(f"    Conversion Rate: {stats['conversion_rate']:.2%}")
    
    if 'significance_tests' in results and results['significance_tests']:
        click.echo(f"\nStatistical Significance:")
        for variant_id, sig in results['significance_tests'].items():
            if 'error' not in sig:
                click.echo(f"\n  {sig['variant_name']}")
                click.echo(f"    Relative Improvement: {sig['relative_improvement']:.2%}")
                click.echo(f"    Significant: {'Yes' if sig['is_significant'] else 'No'}")
    
    if 'summary' in results:
        summary = results['summary']
        click.echo(f"\nSummary:")
        click.echo(f"  Total Participants: {summary['total_participants']}")
        click.echo(f"  Best Conversion Rate: {summary['best_conversion_rate']:.2%}")
        click.echo(f"  Winner is Significant: {'Yes' if summary['winner_is_significant'] else 'No'}")
        click.echo(f"\nRecommendation: {summary['recommendation']}")


@cli.group()
def ux_metrics():
    """Manage UX metrics"""
    pass


@ux_metrics.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
def performance(days: int):
    """Analyze performance metrics"""
    collector = UXMetricsCollector()
    analyzer = UXMetricsAnalyzer(collector)
    
    analysis = analyzer.analyze_performance_metrics(days)
    
    click.echo(f"Performance Analysis (Last {days} days)\n")
    
    if not analysis['performance_metrics']:
        click.echo("No performance metrics found.")
        return
    
    for metric_name, stats in analysis['performance_metrics'].items():
        click.echo(f"{metric_name.replace('_', ' ').title()}:")
        click.echo(f"  Count: {stats['count']}")
        click.echo(f"  Mean: {stats['mean']:.1f}ms")
        click.echo(f"  Median: {stats['median']:.1f}ms")
        click.echo(f"  P95: {stats['p95']:.1f}ms")
        click.echo(f"  P99: {stats['p99']:.1f}ms")
        click.echo()
    
    if 'performance_summary' in analysis:
        summary = analysis['performance_summary']
        click.echo("Performance Summary:")
        click.echo(f"  Overall Performance: {summary['overall_performance']}")
        if summary['insights']:
            click.echo("  Insights:")
            for insight in summary['insights']:
                click.echo(f"    • {insight}")


@ux_metrics.command()
@click.option('--days', '-d', default=30, help='Number of days to analyze')
def usability(days: int):
    """Analyze usability metrics"""
    collector = UXMetricsCollector()
    analyzer = UXMetricsAnalyzer(collector)
    
    analysis = analyzer.analyze_usability_metrics(days)
    
    click.echo(f"Usability Analysis (Last {days} days)\n")
    
    if not analysis['usability_metrics']:
        click.echo("No usability metrics found.")
        return
    
    for metric_name, data in analysis['usability_metrics'].items():
        click.echo(f"{metric_name.replace('_', ' ').title()}:")
        overall = data['overall']
        click.echo(f"  Overall Mean: {overall['mean']:.3f}")
        click.echo(f"  Overall Median: {overall['median']:.3f}")
        click.echo(f"  Count: {overall['count']}")
        
        if data['by_context']:
            click.echo("  By Context:")
            for context, context_stats in data['by_context'].items():
                click.echo(f"    {context}: {context_stats['mean']:.3f} (n={context_stats['count']})")
        click.echo()
    
    if 'usability_insights' in analysis and analysis['usability_insights']:
        click.echo("Usability Insights:")
        for insight in analysis['usability_insights']:
            click.echo(f"  • {insight}")


@cli.command()
@click.option('--days', '-d', default=7, help='Number of days for dashboard data')
@click.option('--output', '-o', help='Output file for JSON data')
def dashboard(days: int, output: str):
    """Generate dashboard data"""
    # Initialize all components
    scenario_manager = ScenarioManager()
    feedback_collector = FeedbackCollector()
    feedback_analyzer = FeedbackAnalyzer(feedback_collector)
    ab_test_manager = ABTestManager()
    ux_metrics_collector = UXMetricsCollector()
    ux_metrics_analyzer = UXMetricsAnalyzer(ux_metrics_collector)
    satisfaction_tracker = SatisfactionTracker()
    
    # Collect data
    feedback_analysis = feedback_analyzer.analyze_feedback_themes(days)
    satisfaction_overview = satisfaction_tracker.get_satisfaction_overview(days)
    ux_dashboard = ux_metrics_analyzer.generate_ux_dashboard_data(days)
    active_ab_tests = ab_test_manager.get_active_tests()
    
    dashboard_data = {
        "period_days": days,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "active_test_sessions": len(scenario_manager.active_sessions),
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
        }
    }
    
    if output:
        with open(output, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        click.echo(f"Dashboard data saved to {output}")
    else:
        click.echo("User Acceptance Testing Dashboard\n")
        click.echo(f"Period: Last {days} days")
        click.echo(f"Generated: {dashboard_data['generated_at']}")
        click.echo(f"\nSummary:")
        click.echo(f"  Active Test Sessions: {dashboard_data['summary']['active_test_sessions']}")
        click.echo(f"  Active A/B Tests: {dashboard_data['summary']['active_ab_tests']}")
        click.echo(f"  Total Feedback Items: {dashboard_data['summary']['total_feedback_items']}")
        click.echo(f"  Satisfaction Responses: {dashboard_data['summary']['satisfaction_responses']}")


if __name__ == '__main__':
    cli()