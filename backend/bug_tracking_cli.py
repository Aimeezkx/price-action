#!/usr/bin/env python3
"""
Bug Tracking CLI Tool

Command-line interface for managing bug tracking and issue management.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.bug_tracking_service import (
    BugTrackingService, TestIssue, IssueSeverity, IssueCategory, 
    IssueStatus, ReproductionStep
)
from app.services.bug_reproduction_service import BugReproductionService
from app.services.bug_fix_verification_service import BugFixVerificationService

class BugTrackingCLI:
    """Command-line interface for bug tracking"""
    
    def __init__(self):
        self.bug_service = BugTrackingService()
        self.repro_service = BugReproductionService()
        self.verification_service = BugFixVerificationService()
    
    def create_issue(self, args):
        """Create a new issue"""
        try:
            # Parse reproduction steps if provided
            reproduction_steps = []
            if args.reproduction_steps:
                steps_data = json.loads(args.reproduction_steps)
                for step_data in steps_data:
                    step = ReproductionStep(**step_data)
                    reproduction_steps.append(step)
            
            # Parse environment
            environment = json.loads(args.environment) if args.environment else {}
            
            issue = self.bug_service.create_issue(
                title=args.title,
                description=args.description,
                test_case=args.test_case,
                expected_behavior=args.expected_behavior,
                actual_behavior=args.actual_behavior,
                environment=environment,
                error_trace=args.error_trace,
                reproduction_steps=reproduction_steps
            )
            
            print(f"✅ Created issue: {issue.id}")
            print(f"   Title: {issue.title}")
            print(f"   Severity: {issue.severity.value}")
            print(f"   Category: {issue.category.value}")
            print(f"   Status: {issue.status.value}")
            
        except Exception as e:
            print(f"❌ Error creating issue: {e}")
            sys.exit(1)
    
    def list_issues(self, args):
        """List issues"""
        try:
            # Parse filters
            status = IssueStatus(args.status) if args.status else None
            category = IssueCategory(args.category) if args.category else None
            severity = IssueSeverity(args.severity) if args.severity else None
            
            issues = self.bug_service.list_issues(
                status=status,
                category=category,
                severity=severity,
                limit=args.limit
            )
            
            if not issues:
                print("No issues found.")
                return
            
            print(f"Found {len(issues)} issues:")
            print()
            
            for issue in issues:
                status_icon = self._get_status_icon(issue.status)
                severity_icon = self._get_severity_icon(issue.severity)
                
                print(f"{status_icon} {severity_icon} {issue.id[:8]} - {issue.title}")
                print(f"   Category: {issue.category.value}")
                print(f"   Created: {issue.created_at.strftime('%Y-%m-%d %H:%M')}")
                if issue.assigned_to:
                    print(f"   Assigned: {issue.assigned_to}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing issues: {e}")
            sys.exit(1)
    
    def show_issue(self, args):
        """Show detailed issue information"""
        try:
            issue = self.bug_service.get_issue(args.issue_id)
            if not issue:
                print(f"❌ Issue {args.issue_id} not found")
                sys.exit(1)
            
            print(f"Issue: {issue.id}")
            print(f"Title: {issue.title}")
            print(f"Status: {issue.status.value}")
            print(f"Severity: {issue.severity.value}")
            print(f"Category: {issue.category.value}")
            print(f"Created: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Updated: {issue.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if issue.assigned_to:
                print(f"Assigned to: {issue.assigned_to}")
            
            if issue.tags:
                print(f"Tags: {', '.join(issue.tags)}")
            
            print(f"\nDescription:")
            print(issue.description)
            
            print(f"\nTest Case: {issue.test_case}")
            print(f"Expected Behavior: {issue.expected_behavior}")
            print(f"Actual Behavior: {issue.actual_behavior}")
            
            if issue.environment:
                print(f"\nEnvironment:")
                for key, value in issue.environment.items():
                    print(f"  {key}: {value}")
            
            if issue.reproduction_steps:
                print(f"\nReproduction Steps:")
                for step in issue.reproduction_steps:
                    print(f"  {step.step_number}. {step.action}")
                    print(f"     Expected: {step.expected_result}")
                    print(f"     Actual: {step.actual_result}")
            
            if issue.error_trace:
                print(f"\nError Trace:")
                print(issue.error_trace)
            
            if issue.fix_commit:
                print(f"\nFix Commit: {issue.fix_commit}")
            
            if issue.verification_test:
                print(f"Verification Test: {issue.verification_test}")
                
        except Exception as e:
            print(f"❌ Error showing issue: {e}")
            sys.exit(1)
    
    def update_issue(self, args):
        """Update an issue"""
        try:
            updates = {}
            
            if args.status:
                updates['status'] = IssueStatus(args.status)
            if args.severity:
                updates['severity'] = IssueSeverity(args.severity)
            if args.category:
                updates['category'] = IssueCategory(args.category)
            if args.assigned_to:
                updates['assigned_to'] = args.assigned_to
            if args.tags:
                updates['tags'] = args.tags.split(',')
            
            issue = self.bug_service.update_issue(args.issue_id, **updates)
            if not issue:
                print(f"❌ Issue {args.issue_id} not found")
                sys.exit(1)
            
            print(f"✅ Updated issue: {issue.id}")
            print(f"   Status: {issue.status.value}")
            print(f"   Severity: {issue.severity.value}")
            print(f"   Category: {issue.category.value}")
            
        except Exception as e:
            print(f"❌ Error updating issue: {e}")
            sys.exit(1)
    
    def mark_fixed(self, args):
        """Mark issue as fixed"""
        try:
            issue = self.bug_service.mark_issue_fixed(args.issue_id, args.fix_commit)
            if not issue:
                print(f"❌ Issue {args.issue_id} not found")
                sys.exit(1)
            
            print(f"✅ Marked issue {issue.id} as fixed")
            print(f"   Fix commit: {args.fix_commit}")
            print(f"   Regression test: {issue.verification_test}")
            
        except Exception as e:
            print(f"❌ Error marking issue as fixed: {e}")
            sys.exit(1)
    
    def detect_from_logs(self, args):
        """Detect issues from log file"""
        try:
            log_file = Path(args.log_file)
            if not log_file.exists():
                print(f"❌ Log file {args.log_file} not found")
                sys.exit(1)
            
            with open(log_file, 'r') as f:
                log_entries = f.readlines()
            
            issues = self.bug_service.detect_issues_from_logs(log_entries)
            
            print(f"✅ Detected {len(issues)} potential issues from logs")
            
            for issue in issues:
                print(f"   {issue.id[:8]} - {issue.title}")
                print(f"   Severity: {issue.severity.value}")
                print(f"   Category: {issue.category.value}")
                print()
                
        except Exception as e:
            print(f"❌ Error detecting issues from logs: {e}")
            sys.exit(1)
    
    def create_reproduction_script(self, args):
        """Create reproduction script"""
        try:
            issue = self.bug_service.get_issue(args.issue_id)
            if not issue:
                print(f"❌ Issue {args.issue_id} not found")
                sys.exit(1)
            
            script = self.repro_service.create_reproduction_script(issue, args.script_type)
            
            print(f"✅ Created reproduction script: {script.script_id}")
            print(f"   Type: {script.script_type}")
            print(f"   Expected outcome: {script.expected_outcome}")
            
            if args.show_content:
                print(f"\nScript content:")
                print(script.script_content)
                
        except Exception as e:
            print(f"❌ Error creating reproduction script: {e}")
            sys.exit(1)
    
    def run_reproduction_script(self, args):
        """Run reproduction script"""
        try:
            result = self.repro_service.run_reproduction_script(args.script_id)
            
            if 'error' in result:
                print(f"❌ Error running script: {result['error']}")
                sys.exit(1)
            
            success = result.get('overall_success', False)
            print(f"{'✅' if success else '❌'} Script execution {'succeeded' if success else 'failed'}")
            
            if args.verbose:
                print(f"\nSetup results:")
                for setup_result in result.get('setup_results', []):
                    status = '✅' if setup_result['success'] else '❌'
                    print(f"  {status} {setup_result['command']}")
                
                print(f"\nScript result:")
                script_result = result.get('script_result', {})
                if script_result:
                    print(f"  Return code: {script_result.get('return_code', 'N/A')}")
                    if script_result.get('output'):
                        print(f"  Output: {script_result['output'][:200]}...")
                    if script_result.get('error'):
                        print(f"  Error: {script_result['error'][:200]}...")
                
        except Exception as e:
            print(f"❌ Error running reproduction script: {e}")
            sys.exit(1)
    
    def verify_fix(self, args):
        """Verify fix comprehensively"""
        try:
            issue = self.bug_service.get_issue(args.issue_id)
            if not issue:
                print(f"❌ Issue {args.issue_id} not found")
                sys.exit(1)
            
            print(f"🔍 Verifying fix for issue {args.issue_id}...")
            result = self.verification_service.verify_fix(issue, args.fix_commit)
            
            status_icon = '✅' if result.verification_status == 'passed' else '⚠️' if result.verification_status == 'partial' else '❌'
            print(f"{status_icon} Verification {result.verification_status.upper()}")
            
            print(f"\nVerification Summary:")
            print(f"  Tests Passed: {'✅' if result.tests_passed else '❌'}")
            print(f"  Reproduction Scripts Passed: {'✅' if result.reproduction_scripts_passed else '❌'}")
            print(f"  Regression Tests Passed: {'✅' if result.regression_tests_passed else '❌'}")
            
            if result.performance_impact:
                print(f"\nPerformance Impact:")
                for metric, value in result.performance_impact.items():
                    print(f"  {metric.replace('_', ' ').title()}: {value}")
            
            if result.code_quality_score:
                print(f"\nCode Quality Score: {result.code_quality_score:.1f}")
            
            if result.recommendations:
                print(f"\nRecommendations:")
                for i, rec in enumerate(result.recommendations, 1):
                    print(f"  {i}. {rec}")
                    
        except Exception as e:
            print(f"❌ Error verifying fix: {e}")
            sys.exit(1)
    
    def show_statistics(self, args):
        """Show issue statistics"""
        try:
            stats = self.bug_service.get_issue_statistics()
            
            print(f"Issue Statistics:")
            print(f"  Total Issues: {stats['total_issues']}")
            print(f"  Open Critical Issues: {stats['open_critical_issues']}")
            
            print(f"\nStatus Distribution:")
            for status, count in stats['status_distribution'].items():
                print(f"  {status.title()}: {count}")
            
            print(f"\nSeverity Distribution:")
            for severity, count in stats['severity_distribution'].items():
                print(f"  {severity.title()}: {count}")
            
            print(f"\nCategory Distribution:")
            for category, count in stats['category_distribution'].items():
                print(f"  {category.replace('_', ' ').title()}: {count}")
                
        except Exception as e:
            print(f"❌ Error showing statistics: {e}")
            sys.exit(1)
    
    def _get_status_icon(self, status: IssueStatus) -> str:
        """Get icon for issue status"""
        icons = {
            IssueStatus.OPEN: "🔴",
            IssueStatus.IN_PROGRESS: "🟡",
            IssueStatus.RESOLVED: "🟢",
            IssueStatus.CLOSED: "⚫",
            IssueStatus.DUPLICATE: "🔵",
            IssueStatus.WONT_FIX: "⚪"
        }
        return icons.get(status, "❓")
    
    def _get_severity_icon(self, severity: IssueSeverity) -> str:
        """Get icon for issue severity"""
        icons = {
            IssueSeverity.CRITICAL: "🚨",
            IssueSeverity.HIGH: "⚠️",
            IssueSeverity.MEDIUM: "📋",
            IssueSeverity.LOW: "📝"
        }
        return icons.get(severity, "❓")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Bug Tracking CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create issue command
    create_parser = subparsers.add_parser('create', help='Create a new issue')
    create_parser.add_argument('--title', required=True, help='Issue title')
    create_parser.add_argument('--description', required=True, help='Issue description')
    create_parser.add_argument('--test-case', required=True, help='Test case that found the issue')
    create_parser.add_argument('--expected-behavior', required=True, help='Expected behavior')
    create_parser.add_argument('--actual-behavior', required=True, help='Actual behavior')
    create_parser.add_argument('--environment', help='Environment info as JSON')
    create_parser.add_argument('--error-trace', help='Error trace/stack trace')
    create_parser.add_argument('--reproduction-steps', help='Reproduction steps as JSON')
    
    # List issues command
    list_parser = subparsers.add_parser('list', help='List issues')
    list_parser.add_argument('--status', choices=[s.value for s in IssueStatus], help='Filter by status')
    list_parser.add_argument('--category', choices=[c.value for c in IssueCategory], help='Filter by category')
    list_parser.add_argument('--severity', choices=[s.value for s in IssueSeverity], help='Filter by severity')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Show issue command
    show_parser = subparsers.add_parser('show', help='Show detailed issue information')
    show_parser.add_argument('issue_id', help='Issue ID')
    
    # Update issue command
    update_parser = subparsers.add_parser('update', help='Update an issue')
    update_parser.add_argument('issue_id', help='Issue ID')
    update_parser.add_argument('--status', choices=[s.value for s in IssueStatus], help='New status')
    update_parser.add_argument('--severity', choices=[s.value for s in IssueSeverity], help='New severity')
    update_parser.add_argument('--category', choices=[c.value for c in IssueCategory], help='New category')
    update_parser.add_argument('--assigned-to', help='Assign to user')
    update_parser.add_argument('--tags', help='Comma-separated tags')
    
    # Mark fixed command
    fixed_parser = subparsers.add_parser('mark-fixed', help='Mark issue as fixed')
    fixed_parser.add_argument('issue_id', help='Issue ID')
    fixed_parser.add_argument('fix_commit', help='Fix commit hash')
    
    # Detect from logs command
    detect_parser = subparsers.add_parser('detect-logs', help='Detect issues from log file')
    detect_parser.add_argument('log_file', help='Path to log file')
    
    # Create reproduction script command
    repro_parser = subparsers.add_parser('create-repro', help='Create reproduction script')
    repro_parser.add_argument('issue_id', help='Issue ID')
    repro_parser.add_argument('--script-type', choices=['pytest', 'playwright', 'api', 'manual'], 
                             default='pytest', help='Script type')
    repro_parser.add_argument('--show-content', action='store_true', help='Show script content')
    
    # Run reproduction script command
    run_repro_parser = subparsers.add_parser('run-repro', help='Run reproduction script')
    run_repro_parser.add_argument('script_id', help='Script ID')
    run_repro_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # Verify fix command
    verify_parser = subparsers.add_parser('verify-fix', help='Verify fix comprehensively')
    verify_parser.add_argument('issue_id', help='Issue ID')
    verify_parser.add_argument('fix_commit', help='Fix commit hash')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show issue statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = BugTrackingCLI()
    
    # Route to appropriate command handler
    if args.command == 'create':
        cli.create_issue(args)
    elif args.command == 'list':
        cli.list_issues(args)
    elif args.command == 'show':
        cli.show_issue(args)
    elif args.command == 'update':
        cli.update_issue(args)
    elif args.command == 'mark-fixed':
        cli.mark_fixed(args)
    elif args.command == 'detect-logs':
        cli.detect_from_logs(args)
    elif args.command == 'create-repro':
        cli.create_reproduction_script(args)
    elif args.command == 'run-repro':
        cli.run_reproduction_script(args)
    elif args.command == 'verify-fix':
        cli.verify_fix(args)
    elif args.command == 'stats':
        cli.show_statistics(args)

if __name__ == '__main__':
    main()