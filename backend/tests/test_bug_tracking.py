"""
Tests for Bug Tracking System

Comprehensive tests for bug tracking, reproduction, and fix verification services.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.services.bug_tracking_service import (
    BugTrackingService, TestIssue, IssueSeverity, IssueCategory, 
    IssueStatus, ReproductionStep, BugDetector, IssuePrioritizer
)
from app.services.bug_reproduction_service import (
    BugReproductionService, ReproductionScript, ReproductionEnvironment
)
from app.services.bug_fix_verification_service import (
    BugFixVerificationService, FixVerificationResult
)

class TestBugTrackingService:
    """Test bug tracking service functionality"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def bug_service(self, temp_storage):
        """Create bug tracking service with temporary storage"""
        return BugTrackingService(storage_path=temp_storage)
    
    def test_create_issue(self, bug_service):
        """Test creating a new issue"""
        reproduction_steps = [
            ReproductionStep(
                step_number=1,
                action="Upload a PDF document",
                expected_result="Document should be processed successfully",
                actual_result="Processing fails with timeout error",
                data_used={"filename": "test.pdf", "size": "10MB"}
            )
        ]
        
        issue = bug_service.create_issue(
            title="PDF processing timeout",
            description="Large PDF documents fail to process within timeout",
            test_case="test_pdf_processing_large_files",
            expected_behavior="PDF should be processed within 60 seconds",
            actual_behavior="Processing times out after 30 seconds",
            environment={"os": "Ubuntu 20.04", "python": "3.9.0"},
            error_trace="TimeoutError: Processing exceeded 30 seconds",
            reproduction_steps=reproduction_steps
        )
        
        assert issue.id is not None
        assert issue.title == "PDF processing timeout"
        assert issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM]
        assert issue.category == IssueCategory.PERFORMANCE  # Should be auto-categorized
        assert issue.status == IssueStatus.OPEN
        assert len(issue.reproduction_steps) == 1
        assert issue.reproduction_steps[0].action == "Upload a PDF document"
    
    def test_list_issues_with_filters(self, bug_service):
        """Test listing issues with various filters"""
        # Create test issues
        issue1 = bug_service.create_issue(
            title="Critical security issue",
            description="SQL injection vulnerability",
            test_case="test_security",
            expected_behavior="No SQL injection",
            actual_behavior="SQL injection possible",
            environment={"test": "env"}
        )
        
        issue2 = bug_service.create_issue(
            title="Performance issue",
            description="Slow search response",
            test_case="test_performance",
            expected_behavior="Fast search",
            actual_behavior="Slow search",
            environment={"test": "env"}
        )
        
        # Test filtering by category
        security_issues = bug_service.list_issues(category=IssueCategory.SECURITY)
        performance_issues = bug_service.list_issues(category=IssueCategory.PERFORMANCE)
        
        assert len(security_issues) >= 1
        assert len(performance_issues) >= 1
        
        # Test filtering by status
        open_issues = bug_service.list_issues(status=IssueStatus.OPEN)
        assert len(open_issues) >= 2
        
        # Test limit
        limited_issues = bug_service.list_issues(limit=1)
        assert len(limited_issues) == 1
    
    def test_update_issue(self, bug_service):
        """Test updating an issue"""
        issue = bug_service.create_issue(
            title="Test issue",
            description="Test description",
            test_case="test_case",
            expected_behavior="Expected",
            actual_behavior="Actual",
            environment={"test": "env"}
        )
        
        # Update the issue
        updated_issue = bug_service.update_issue(
            issue.id,
            status=IssueStatus.IN_PROGRESS,
            assigned_to="developer@example.com",
            tags=["urgent", "backend"]
        )
        
        assert updated_issue.status == IssueStatus.IN_PROGRESS
        assert updated_issue.assigned_to == "developer@example.com"
        assert "urgent" in updated_issue.tags
        assert "backend" in updated_issue.tags
        assert updated_issue.updated_at > issue.updated_at
    
    def test_mark_issue_fixed(self, bug_service):
        """Test marking an issue as fixed"""
        issue = bug_service.create_issue(
            title="Test bug",
            description="Test bug description",
            test_case="test_case",
            expected_behavior="Expected",
            actual_behavior="Actual",
            environment={"test": "env"}
        )
        
        # Mark as fixed
        fixed_issue = bug_service.mark_issue_fixed(issue.id, "abc123def456")
        
        assert fixed_issue.status == IssueStatus.RESOLVED
        assert fixed_issue.fix_commit == "abc123def456"
        assert fixed_issue.verification_test is not None
    
    def test_detect_issues_from_logs(self, bug_service):
        """Test detecting issues from log entries"""
        log_entries = [
            "2023-01-01 10:00:00 INFO Processing document",
            "2023-01-01 10:01:00 ERROR Memory leak detected in parser",
            "2023-01-01 10:02:00 WARNING Slow response time: 5.2 seconds",
            "2023-01-01 10:03:00 ERROR Unauthorized access attempt blocked"
        ]
        
        detected_issues = bug_service.detect_issues_from_logs(log_entries)
        
        assert len(detected_issues) >= 2  # Should detect memory leak and performance issues
        
        # Check that issues were created with appropriate categories
        categories = [issue.category for issue in detected_issues]
        assert IssueCategory.PERFORMANCE in categories or IssueCategory.BUG in categories
    
    def test_detect_issues_from_test_failures(self, bug_service):
        """Test detecting issues from test failures"""
        test_results = {
            "failures": [
                {
                    "test_name": "test_document_processing",
                    "error": "AssertionError: Expected 5 chapters, got 3",
                    "traceback": "Traceback (most recent call last)..."
                },
                {
                    "test_name": "test_search_timeout",
                    "error": "TimeoutError: Search took too long",
                    "traceback": "Traceback (most recent call last)..."
                }
            ]
        }
        
        detected_issues = bug_service.detect_issues_from_test_failures(test_results)
        
        assert len(detected_issues) == 2
        assert any("document_processing" in issue.title for issue in detected_issues)
        assert any("search_timeout" in issue.title for issue in detected_issues)
    
    def test_issue_statistics(self, bug_service):
        """Test getting issue statistics"""
        # Create issues with different properties
        bug_service.create_issue(
            title="Critical issue",
            description="Critical security issue",
            test_case="test",
            expected_behavior="Expected",
            actual_behavior="Actual",
            environment={"test": "env"}
        )
        
        bug_service.create_issue(
            title="Performance issue",
            description="Slow performance",
            test_case="test",
            expected_behavior="Expected",
            actual_behavior="Actual",
            environment={"test": "env"}
        )
        
        stats = bug_service.get_issue_statistics()
        
        assert stats['total_issues'] >= 2
        assert 'status_distribution' in stats
        assert 'severity_distribution' in stats
        assert 'category_distribution' in stats
        assert stats['status_distribution']['open'] >= 2

class TestBugDetector:
    """Test bug detection functionality"""
    
    @pytest.fixture
    def detector(self):
        return BugDetector()
    
    def test_detect_from_logs(self, detector):
        """Test log-based bug detection"""
        log_entries = [
            "Memory usage increasing continuously",
            "Database connection timeout occurred",
            "XSS vulnerability detected in input",
            "Normal operation completed successfully"
        ]
        
        detected = detector.detect_from_logs(log_entries)
        
        assert len(detected) >= 2
        
        # Check detection types
        types = [d['type'] for d in detected]
        assert 'memory_leak' in types
        assert 'security_vulnerability' in types
    
    def test_classify_test_failure(self, detector):
        """Test test failure classification"""
        failures = [
            {"error": "TimeoutError: Operation timed out"},
            {"error": "AssertionError: Values don't match"},
            {"error": "ConnectionError: Database unreachable"},
            {"error": "MemoryError: Out of memory"}
        ]
        
        classifications = [detector._classify_test_failure(f) for f in failures]
        
        assert 'performance_degradation' in classifications
        assert 'logic_error' in classifications
        assert 'connectivity_issue' in classifications
        assert 'memory_issue' in classifications

class TestIssuePrioritizer:
    """Test issue prioritization functionality"""
    
    @pytest.fixture
    def prioritizer(self):
        return IssuePrioritizer()
    
    def test_categorize_issue(self, prioritizer):
        """Test automatic issue categorization"""
        test_cases = [
            {
                'description': 'SQL injection vulnerability found',
                'expected_category': IssueCategory.SECURITY
            },
            {
                'description': 'Search response is very slow',
                'expected_category': IssueCategory.PERFORMANCE
            },
            {
                'description': 'API endpoint returns wrong status code',
                'expected_category': IssueCategory.API
            },
            {
                'description': 'Button is not visible on mobile',
                'expected_category': IssueCategory.UI
            },
            {
                'description': 'Data corruption in database',
                'expected_category': IssueCategory.DATA_INTEGRITY
            }
        ]
        
        for test_case in test_cases:
            category = prioritizer.categorize_issue(test_case)
            assert category == test_case['expected_category']
    
    def test_determine_severity(self, prioritizer):
        """Test severity determination"""
        test_cases = [
            {
                'description': 'System crash when processing large files',
                'expected_severity': IssueSeverity.CRITICAL
            },
            {
                'description': 'Security breach in authentication',
                'category': IssueCategory.SECURITY,
                'expected_severity': IssueSeverity.HIGH
            },
            {
                'description': 'Search is slow but functional',
                'category': IssueCategory.PERFORMANCE,
                'expected_severity': IssueSeverity.MEDIUM
            }
        ]
        
        for test_case in test_cases:
            severity = prioritizer.determine_severity(test_case)
            assert severity == test_case['expected_severity']
    
    def test_calculate_priority_score(self, prioritizer):
        """Test priority score calculation"""
        # Create test issues with different properties
        critical_security = TestIssue(
            id="test-1",
            title="Critical Security Issue",
            description="Critical security vulnerability",
            severity=IssueSeverity.CRITICAL,
            category=IssueCategory.SECURITY,
            status=IssueStatus.OPEN,
            test_case="test",
            reproduction_steps=[],
            expected_behavior="Expected",
            actual_behavior="Actual",
            environment={},
            error_trace=None,
            created_at=datetime.now() - timedelta(days=5),
            updated_at=datetime.now()
        )
        
        low_ui = TestIssue(
            id="test-2",
            title="Minor UI Issue",
            description="Minor UI alignment issue",
            severity=IssueSeverity.LOW,
            category=IssueCategory.UI,
            status=IssueStatus.OPEN,
            test_case="test",
            reproduction_steps=[],
            expected_behavior="Expected",
            actual_behavior="Actual",
            environment={},
            error_trace=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        critical_score = prioritizer.calculate_priority_score(critical_security)
        low_score = prioritizer.calculate_priority_score(low_ui)
        
        assert critical_score > low_score

class TestBugReproductionService:
    """Test bug reproduction service"""
    
    @pytest.fixture
    def temp_storage(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repro_service(self, temp_storage):
        return BugReproductionService(storage_path=temp_storage)
    
    @pytest.fixture
    def sample_issue(self):
        return TestIssue(
            id="test-issue-123",
            title="Sample Bug",
            description="Sample bug for testing",
            severity=IssueSeverity.HIGH,
            category=IssueCategory.BUG,
            status=IssueStatus.OPEN,
            test_case="test_sample",
            reproduction_steps=[
                ReproductionStep(
                    step_number=1,
                    action="Click the submit button",
                    expected_result="Form should submit",
                    actual_result="Form submission fails",
                    data_used={"form_data": {"name": "test"}}
                )
            ],
            expected_behavior="Form submits successfully",
            actual_behavior="Form submission fails with error",
            environment={"browser": "Chrome", "os": "Windows"},
            error_trace="Error: Form validation failed",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_document_reproduction_steps(self, repro_service, sample_issue):
        """Test reproduction documentation generation"""
        documentation = repro_service.document_reproduction_steps(sample_issue)
        
        assert "Sample Bug" in documentation
        assert "test-issue-123" in documentation
        assert "Click the submit button" in documentation
        assert "Form should submit" in documentation
        assert "Form submission fails" in documentation
        assert "Error: Form validation failed" in documentation
    
    def test_create_reproduction_script_pytest(self, repro_service, sample_issue):
        """Test pytest reproduction script creation"""
        script = repro_service.create_reproduction_script(sample_issue, "pytest")
        
        assert script.script_id.startswith("repro_test-issue-123_pytest")
        assert script.script_type == "pytest"
        assert "def test_reproduce_issue_" in script.script_content
        assert "Sample Bug" in script.script_content
        assert len(script.setup_commands) > 0
        assert len(script.cleanup_commands) > 0
    
    def test_create_reproduction_script_playwright(self, repro_service, sample_issue):
        """Test Playwright reproduction script creation"""
        script = repro_service.create_reproduction_script(sample_issue, "playwright")
        
        assert script.script_type == "playwright"
        assert "from playwright.async_api import Page" in script.script_content
        assert "@pytest.mark.asyncio" in script.script_content
        assert "await page.goto" in script.script_content
    
    @patch('subprocess.run')
    def test_run_reproduction_script(self, mock_run, repro_service, sample_issue):
        """Test running reproduction script"""
        # Create a script first
        script = repro_service.create_reproduction_script(sample_issue, "pytest")
        
        # Mock subprocess results
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Test passed",
            stderr=""
        )
        
        result = repro_service.run_reproduction_script(script.script_id)
        
        assert 'script_result' in result
        assert result['overall_success'] == True
        assert mock_run.called
    
    def test_generate_environment_snapshot(self, repro_service, sample_issue):
        """Test environment snapshot generation"""
        with patch('platform.platform', return_value='Windows-10'):
            with patch('sys.version', '3.9.0'):
                env = repro_service.generate_environment_snapshot(sample_issue)
                
                assert env is not None
                assert env.os_version == 'Windows-10'
                assert '3.9.0' in env.python_version

class TestBugFixVerificationService:
    """Test bug fix verification service"""
    
    @pytest.fixture
    def temp_storage(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def verification_service(self, temp_storage):
        return BugFixVerificationService(storage_path=temp_storage)
    
    @pytest.fixture
    def sample_issue(self):
        return TestIssue(
            id="test-fix-123",
            title="Sample Bug for Fix",
            description="Sample bug for fix verification testing",
            severity=IssueSeverity.HIGH,
            category=IssueCategory.BUG,
            status=IssueStatus.RESOLVED,
            test_case="test_sample_fix",
            reproduction_steps=[],
            expected_behavior="Should work correctly",
            actual_behavior="Fails with error",
            environment={"test": "env"},
            error_trace="Error trace",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            fix_commit="abc123def456"
        )
    
    @patch('subprocess.run')
    def test_verify_unit_test_coverage(self, mock_run, verification_service, sample_issue):
        """Test unit test coverage verification"""
        # Mock pytest run
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Tests passed",
            stderr=""
        )
        
        # Mock coverage file
        coverage_data = {
            "files": {
                "app/services/test_service.py": {
                    "summary": {"percent_covered": 85.0}
                }
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open_coverage(coverage_data)):
                with patch.object(verification_service, '_get_changed_files', 
                                return_value=['app/services/test_service.py']):
                    
                    result = verification_service._verify_unit_test_coverage(
                        sample_issue, "abc123def456"
                    )
                    
                    assert result['passed'] == True
                    assert result['average_coverage'] == 85.0
    
    @patch('subprocess.run')
    def test_verify_integration_tests(self, mock_run, verification_service, sample_issue):
        """Test integration test verification"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="All integration tests passed",
            stderr=""
        )
        
        result = verification_service._verify_integration_tests(sample_issue, "abc123def456")
        
        assert result['passed'] == True
        assert "Integration tests passed" in result['details']
    
    def test_generate_recommendations(self, verification_service):
        """Test recommendation generation"""
        # Create a verification result with some failures
        result = FixVerificationResult(
            issue_id="test-123",
            fix_commit="abc123",
            verification_time=datetime.now(),
            tests_passed=False,
            reproduction_scripts_passed=True,
            regression_tests_passed=False,
            performance_impact={"search_response_time": 2.5},
            code_quality_score=65.0,
            verification_status='failed',
            detailed_results={},
            recommendations=[]
        )
        
        validation_results = {
            'security_scan': {'high_severity_issues': 1}
        }
        
        recommendations = verification_service._generate_recommendations(result, validation_results)
        
        assert len(recommendations) > 0
        assert any("unit tests" in rec.lower() for rec in recommendations)
        assert any("regression tests" in rec.lower() for rec in recommendations)
        assert any("search response time" in rec.lower() for rec in recommendations)
        assert any("code quality" in rec.lower() for rec in recommendations)
        assert any("security issues" in rec.lower() for rec in recommendations)

def mock_open_coverage(coverage_data):
    """Mock open function for coverage file"""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(coverage_data))

class TestBugTrackingIntegration:
    """Integration tests for the complete bug tracking workflow"""
    
    @pytest.fixture
    def temp_storage(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def services(self, temp_storage):
        """Create all services with shared storage"""
        bug_service = BugTrackingService(storage_path=temp_storage + "/bugs")
        repro_service = BugReproductionService(storage_path=temp_storage + "/repro")
        verification_service = BugFixVerificationService(storage_path=temp_storage + "/verification")
        
        return {
            'bug': bug_service,
            'repro': repro_service,
            'verification': verification_service
        }
    
    def test_complete_bug_workflow(self, services):
        """Test complete bug tracking workflow"""
        bug_service = services['bug']
        repro_service = services['repro']
        verification_service = services['verification']
        
        # 1. Create an issue
        issue = bug_service.create_issue(
            title="Integration test bug",
            description="Bug for integration testing",
            test_case="test_integration",
            expected_behavior="Should work",
            actual_behavior="Doesn't work",
            environment={"test": "integration"}
        )
        
        assert issue.status == IssueStatus.OPEN
        
        # 2. Create reproduction documentation
        documentation = repro_service.document_reproduction_steps(issue)
        assert "Integration test bug" in documentation
        
        # 3. Create reproduction script
        script = repro_service.create_reproduction_script(issue, "pytest")
        assert script.issue_id == issue.id
        
        # 4. Mark issue as fixed
        fixed_issue = bug_service.mark_issue_fixed(issue.id, "fix123abc")
        assert fixed_issue.status == IssueStatus.RESOLVED
        assert fixed_issue.fix_commit == "fix123abc"
        
        # 5. Verify the fix (mocked)
        with patch.object(verification_service, '_verify_reproduction_scripts', 
                         return_value={'passed': True, 'details': 'Scripts passed'}):
            with patch.object(verification_service, '_verify_regression_tests',
                             return_value={'passed': True, 'details': 'Regression tests passed'}):
                with patch.object(verification_service, '_verify_unit_test_coverage',
                                 return_value={'passed': True, 'details': 'Coverage OK'}):
                    
                    verification_result = verification_service.verify_fix(fixed_issue, "fix123abc")
                    
                    assert verification_result.issue_id == issue.id
                    assert verification_result.fix_commit == "fix123abc"
                    assert verification_result.verification_status in ['passed', 'partial']
    
    def test_automated_issue_detection_workflow(self, services):
        """Test automated issue detection and processing"""
        bug_service = services['bug']
        
        # Simulate log entries with issues
        log_entries = [
            "2023-01-01 ERROR: Memory leak detected in document processor",
            "2023-01-01 WARNING: Search response time exceeded 5 seconds",
            "2023-01-01 ERROR: Unauthorized access attempt from IP 192.168.1.100"
        ]
        
        # Detect issues from logs
        detected_issues = bug_service.detect_issues_from_logs(log_entries)
        
        assert len(detected_issues) >= 1
        
        # Verify issues were created with appropriate properties
        for issue in detected_issues:
            assert issue.status == IssueStatus.OPEN
            assert issue.test_case == "automated_log_analysis"
            assert "Automated detection" in issue.title
    
    @patch('subprocess.run')
    def test_fix_verification_workflow(self, mock_run, services):
        """Test fix verification workflow"""
        bug_service = services['bug']
        verification_service = services['verification']
        
        # Create and fix an issue
        issue = bug_service.create_issue(
            title="Verification test bug",
            description="Bug for verification testing",
            test_case="test_verification",
            expected_behavior="Should work",
            actual_behavior="Doesn't work",
            environment={"test": "verification"}
        )
        
        fixed_issue = bug_service.mark_issue_fixed(issue.id, "verify123abc")
        
        # Mock all subprocess calls to return success
        mock_run.return_value = Mock(
            returncode=0,
            stdout="All tests passed",
            stderr=""
        )
        
        # Mock file operations
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open_coverage({"files": {}})):
                with patch.object(verification_service, '_get_changed_files', return_value=[]):
                    
                    # Verify the fix
                    result = verification_service.verify_fix(fixed_issue, "verify123abc")
                    
                    assert result.issue_id == issue.id
                    assert result.fix_commit == "verify123abc"
                    assert result.verification_status in ['passed', 'partial', 'failed']
                    
                    # Check that verification was saved
                    history = verification_service.get_verification_history(issue.id)
                    assert len(history) == 1
                    assert history[0].fix_commit == "verify123abc"

if __name__ == '__main__':
    pytest.main([__file__])