#!/usr/bin/env python3
"""
Bug Tracking System Example

This script demonstrates the comprehensive bug tracking and issue management system.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.bug_tracking_service import (
    BugTrackingService, TestIssue, IssueSeverity, IssueCategory, 
    IssueStatus, ReproductionStep
)
from app.services.bug_reproduction_service import BugReproductionService
from app.services.bug_fix_verification_service import BugFixVerificationService

def demonstrate_bug_tracking():
    """Demonstrate the complete bug tracking workflow"""
    print("🐛 Bug Tracking System Demonstration")
    print("=" * 50)
    
    # Initialize services
    bug_service = BugTrackingService()
    repro_service = BugReproductionService()
    verification_service = BugFixVerificationService()
    
    # 1. Create a sample issue with reproduction steps
    print("\n1. Creating a new issue...")
    
    reproduction_steps = [
        ReproductionStep(
            step_number=1,
            action="Upload a large PDF document (>50MB)",
            expected_result="Document should be processed within 60 seconds",
            actual_result="Processing times out after 30 seconds",
            data_used={
                "filename": "large_document.pdf",
                "size_mb": 75,
                "pages": 200
            }
        ),
        ReproductionStep(
            step_number=2,
            action="Check processing status in the UI",
            expected_result="Status should show 'Processing Complete'",
            actual_result="Status shows 'Processing Failed - Timeout'",
            screenshot_path="/screenshots/timeout_error.png"
        )
    ]
    
    issue = bug_service.create_issue(
        title="Large PDF processing timeout",
        description="Documents larger than 50MB fail to process due to timeout limits. This affects user experience and prevents processing of academic papers and technical documents.",
        test_case="test_large_pdf_processing",
        expected_behavior="PDF documents up to 100MB should be processed successfully within 2 minutes",
        actual_behavior="Processing fails with timeout error after 30 seconds for documents >50MB",
        environment={
            "os": "Ubuntu 20.04",
            "python_version": "3.9.0",
            "memory": "8GB",
            "cpu": "Intel i7-8700K",
            "browser": "Chrome 96.0"
        },
        error_trace="""
TimeoutError: Document processing exceeded maximum time limit
  at DocumentProcessor.process_pdf (document_processor.py:145)
  at ProcessingQueue.handle_job (queue_service.py:89)
  at Worker.run (worker.py:34)
        """,
        reproduction_steps=reproduction_steps
    )
    
    print(f"✅ Created issue: {issue.id}")
    print(f"   Title: {issue.title}")
    print(f"   Severity: {issue.severity.value}")
    print(f"   Category: {issue.category.value}")
    print(f"   Status: {issue.status.value}")
    
    # 2. Generate reproduction documentation
    print("\n2. Generating reproduction documentation...")
    
    documentation = repro_service.document_reproduction_steps(issue)
    print(f"✅ Generated reproduction documentation ({len(documentation)} characters)")
    print("   Documentation includes:")
    print("   - Detailed reproduction steps")
    print("   - Environment information")
    print("   - Expected vs actual behavior")
    print("   - Error traces and screenshots")
    
    # 3. Create automated reproduction scripts
    print("\n3. Creating reproduction scripts...")
    
    # Create different types of reproduction scripts
    pytest_script = repro_service.create_reproduction_script(issue, "pytest")
    playwright_script = repro_service.create_reproduction_script(issue, "playwright")
    
    print(f"✅ Created pytest reproduction script: {pytest_script.script_id}")
    print(f"✅ Created playwright reproduction script: {playwright_script.script_id}")
    
    # 4. Simulate automated issue detection
    print("\n4. Demonstrating automated issue detection...")
    
    # Simulate log entries with various issues
    sample_logs = [
        "2023-12-01 10:15:23 INFO Document processing started for user_123",
        "2023-12-01 10:15:45 ERROR Memory leak detected in PDF parser - heap usage: 2.1GB",
        "2023-12-01 10:16:12 WARNING Search response time: 3.2 seconds (threshold: 1.0s)",
        "2023-12-01 10:16:30 ERROR Unauthorized access attempt from IP 192.168.1.100",
        "2023-12-01 10:17:01 INFO Document processing completed successfully",
        "2023-12-01 10:17:15 ERROR Database connection timeout after 30 seconds"
    ]
    
    detected_issues = bug_service.detect_issues_from_logs(sample_logs)
    print(f"✅ Detected {len(detected_issues)} issues from log analysis:")
    
    for detected_issue in detected_issues:
        print(f"   - {detected_issue.title} ({detected_issue.severity.value})")
    
    # 5. Simulate test failure detection
    print("\n5. Detecting issues from test failures...")
    
    test_failure_data = {
        "failures": [
            {
                "test_name": "test_document_chapter_extraction",
                "error": "AssertionError: Expected 8 chapters, got 5",
                "traceback": "Traceback (most recent call last):\n  File 'test_chapter.py', line 45, in test_extraction\n    assert len(chapters) == 8\nAssertionError: Expected 8 chapters, got 5"
            },
            {
                "test_name": "test_search_performance",
                "error": "TimeoutError: Search took 5.2 seconds, expected < 1.0s",
                "traceback": "Traceback (most recent call last):\n  File 'test_search.py', line 23, in test_performance\n    assert response_time < 1.0\nTimeoutError: Search took 5.2 seconds"
            }
        ]
    }
    
    test_failure_issues = bug_service.detect_issues_from_test_failures(test_failure_data)
    print(f"✅ Detected {len(test_failure_issues)} issues from test failures:")
    
    for test_issue in test_failure_issues:
        print(f"   - {test_issue.title} ({test_issue.category.value})")
    
    # 6. Update issue status and assign
    print("\n6. Updating issue status...")
    
    updated_issue = bug_service.update_issue(
        issue.id,
        status=IssueStatus.IN_PROGRESS,
        assigned_to="developer@example.com",
        tags=["performance", "pdf-processing", "timeout"]
    )
    
    print(f"✅ Updated issue status to: {updated_issue.status.value}")
    print(f"   Assigned to: {updated_issue.assigned_to}")
    print(f"   Tags: {', '.join(updated_issue.tags)}")
    
    # 7. Mark issue as fixed and generate regression test
    print("\n7. Marking issue as fixed...")
    
    fix_commit = "a1b2c3d4e5f6789"  # Simulated commit hash
    fixed_issue = bug_service.mark_issue_fixed(issue.id, fix_commit)
    
    print(f"✅ Marked issue as fixed with commit: {fix_commit}")
    print(f"   Status: {fixed_issue.status.value}")
    print(f"   Regression test generated: {fixed_issue.verification_test}")
    
    # 8. Demonstrate fix verification (mocked for demo)
    print("\n8. Performing comprehensive fix verification...")
    
    # In a real scenario, this would run actual tests
    print("   🔍 Running reproduction scripts...")
    print("   🔍 Verifying regression tests...")
    print("   🔍 Checking unit test coverage...")
    print("   🔍 Running integration tests...")
    print("   🔍 Assessing performance impact...")
    print("   🔍 Scanning for security vulnerabilities...")
    
    # Simulate verification result
    print("   ✅ All verification checks passed!")
    print("   📊 Code coverage: 87%")
    print("   ⚡ Performance impact: Minimal")
    print("   🔒 Security scan: No issues found")
    
    # 9. Show issue statistics
    print("\n9. Issue Statistics:")
    
    stats = bug_service.get_issue_statistics()
    print(f"   Total Issues: {stats['total_issues']}")
    print(f"   Open Critical Issues: {stats['open_critical_issues']}")
    
    print("   Status Distribution:")
    for status, count in stats['status_distribution'].items():
        print(f"     {status.title()}: {count}")
    
    print("   Severity Distribution:")
    for severity, count in stats['severity_distribution'].items():
        print(f"     {severity.title()}: {count}")
    
    print("   Category Distribution:")
    for category, count in stats['category_distribution'].items():
        print(f"     {category.replace('_', ' ').title()}: {count}")
    
    # 10. List all issues
    print("\n10. Current Issues:")
    
    all_issues = bug_service.list_issues(limit=10)
    for issue_item in all_issues:
        status_icon = get_status_icon(issue_item.status)
        severity_icon = get_severity_icon(issue_item.severity)
        print(f"   {status_icon} {severity_icon} {issue_item.id[:8]} - {issue_item.title}")
        print(f"      Category: {issue_item.category.value}, Created: {issue_item.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n" + "=" * 50)
    print("🎉 Bug Tracking System Demonstration Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Manual issue creation with detailed reproduction steps")
    print("✅ Automated issue detection from logs and test failures")
    print("✅ Issue categorization and prioritization")
    print("✅ Reproduction script generation (pytest, playwright)")
    print("✅ Comprehensive fix verification workflow")
    print("✅ Regression test generation")
    print("✅ Issue statistics and reporting")
    print("✅ Complete issue lifecycle management")

def get_status_icon(status: IssueStatus) -> str:
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

def get_severity_icon(severity: IssueSeverity) -> str:
    """Get icon for issue severity"""
    icons = {
        IssueSeverity.CRITICAL: "🚨",
        IssueSeverity.HIGH: "⚠️",
        IssueSeverity.MEDIUM: "📋",
        IssueSeverity.LOW: "📝"
    }
    return icons.get(severity, "❓")

def demonstrate_cli_usage():
    """Demonstrate CLI usage examples"""
    print("\n" + "=" * 50)
    print("📋 CLI Usage Examples")
    print("=" * 50)
    
    print("\n1. Create a new issue:")
    print('python bug_tracking_cli.py create \\')
    print('  --title "Search API returns 500 error" \\')
    print('  --description "Search endpoint fails with internal server error" \\')
    print('  --test-case "test_search_api" \\')
    print('  --expected-behavior "Should return search results" \\')
    print('  --actual-behavior "Returns 500 internal server error" \\')
    print('  --environment \'{"os": "Ubuntu", "python": "3.9"}\'')
    
    print("\n2. List issues with filters:")
    print("python bug_tracking_cli.py list --status open --severity high")
    print("python bug_tracking_cli.py list --category security --limit 5")
    
    print("\n3. Show detailed issue information:")
    print("python bug_tracking_cli.py show <issue-id>")
    
    print("\n4. Update issue status:")
    print("python bug_tracking_cli.py update <issue-id> --status in_progress --assigned-to dev@example.com")
    
    print("\n5. Mark issue as fixed:")
    print("python bug_tracking_cli.py mark-fixed <issue-id> <commit-hash>")
    
    print("\n6. Detect issues from logs:")
    print("python bug_tracking_cli.py detect-logs /path/to/application.log")
    
    print("\n7. Create reproduction script:")
    print("python bug_tracking_cli.py create-repro <issue-id> --script-type playwright")
    
    print("\n8. Run reproduction script:")
    print("python bug_tracking_cli.py run-repro <script-id> --verbose")
    
    print("\n9. Verify fix comprehensively:")
    print("python bug_tracking_cli.py verify-fix <issue-id> <commit-hash>")
    
    print("\n10. Show statistics:")
    print("python bug_tracking_cli.py stats")

def demonstrate_api_usage():
    """Demonstrate API usage examples"""
    print("\n" + "=" * 50)
    print("🌐 API Usage Examples")
    print("=" * 50)
    
    print("\n1. Create issue via API:")
    print("POST /api/bug-tracking/issues")
    print(json.dumps({
        "title": "Document upload fails",
        "description": "Large documents fail to upload",
        "test_case": "test_document_upload",
        "expected_behavior": "Document should upload successfully",
        "actual_behavior": "Upload fails with timeout",
        "environment": {"browser": "Chrome", "os": "Windows"},
        "reproduction_steps": [
            {
                "step_number": 1,
                "action": "Select large PDF file",
                "expected_result": "File should be selected",
                "actual_result": "File selected successfully"
            },
            {
                "step_number": 2,
                "action": "Click upload button",
                "expected_result": "Upload should complete",
                "actual_result": "Upload times out after 30 seconds"
            }
        ]
    }, indent=2))
    
    print("\n2. List issues with filters:")
    print("GET /api/bug-tracking/issues?status=open&severity=high&limit=10")
    
    print("\n3. Get specific issue:")
    print("GET /api/bug-tracking/issues/{issue_id}")
    
    print("\n4. Update issue:")
    print("PUT /api/bug-tracking/issues/{issue_id}")
    print(json.dumps({
        "status": "in_progress",
        "assigned_to": "developer@example.com",
        "tags": ["urgent", "backend"]
    }, indent=2))
    
    print("\n5. Mark issue as fixed:")
    print("POST /api/bug-tracking/issues/{issue_id}/mark-fixed")
    print(json.dumps({"fix_commit": "abc123def456"}, indent=2))
    
    print("\n6. Detect issues from logs:")
    print("POST /api/bug-tracking/detect-from-logs")
    print(json.dumps([
        "ERROR: Database connection failed",
        "WARNING: Memory usage high: 85%",
        "ERROR: Authentication failed for user"
    ], indent=2))
    
    print("\n7. Create reproduction script:")
    print("POST /api/bug-tracking/issues/{issue_id}/reproduction-script?script_type=pytest")
    
    print("\n8. Verify fix comprehensively:")
    print("POST /api/bug-tracking/issues/{issue_id}/verify-fix-comprehensive")
    print(json.dumps({"fix_commit": "abc123def456"}, indent=2))
    
    print("\n9. Get issue statistics:")
    print("GET /api/bug-tracking/statistics")

if __name__ == "__main__":
    try:
        demonstrate_bug_tracking()
        demonstrate_cli_usage()
        demonstrate_api_usage()
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)