"""
Bug Tracking and Issue Management Service

This service provides comprehensive bug tracking, issue categorization,
and automated bug detection capabilities for the document learning application.
"""

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import traceback
import hashlib
import re
from pathlib import Path

class IssueSeverity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IssueCategory(Enum):
    """Issue categories"""
    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"
    DATA_INTEGRITY = "data_integrity"
    API = "api"
    UI = "ui"

class IssueStatus(Enum):
    """Issue status values"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"
    WONT_FIX = "wont_fix"

@dataclass
class ReproductionStep:
    """Single step in bug reproduction"""
    step_number: int
    action: str
    expected_result: str
    actual_result: str
    screenshot_path: Optional[str] = None
    data_used: Optional[Dict[str, Any]] = None

@dataclass
class TestIssue:
    """Represents an issue found during testing"""
    id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    status: IssueStatus
    test_case: str
    reproduction_steps: List[ReproductionStep]
    expected_behavior: str
    actual_behavior: str
    environment: Dict[str, str]
    error_trace: Optional[str]
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    tags: List[str] = None
    related_issues: List[str] = None
    fix_commit: Optional[str] = None
    verification_test: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_issues is None:
            self.related_issues = []

class BugDetector:
    """Automated bug detection system"""
    
    def __init__(self):
        self.detection_patterns = {
            'memory_leak': [
                r'memory.*leak',
                r'out of memory',
                r'memory usage.*increasing'
            ],
            'performance_degradation': [
                r'timeout',
                r'slow.*response',
                r'performance.*degraded'
            ],
            'data_corruption': [
                r'data.*corrupt',
                r'invalid.*data',
                r'checksum.*mismatch'
            ],
            'security_vulnerability': [
                r'unauthorized.*access',
                r'injection.*attack',
                r'xss.*vulnerability'
            ]
        }
    
    def detect_from_logs(self, log_entries: List[str]) -> List[Dict[str, Any]]:
        """Detect potential bugs from log entries"""
        detected_issues = []
        
        for log_entry in log_entries:
            for issue_type, patterns in self.detection_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, log_entry, re.IGNORECASE):
                        detected_issues.append({
                            'type': issue_type,
                            'log_entry': log_entry,
                            'pattern_matched': pattern,
                            'timestamp': datetime.now()
                        })
                        break
        
        return detected_issues
    
    def detect_from_test_failures(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect bugs from test failure patterns"""
        detected_issues = []
        
        if 'failures' in test_results:
            for failure in test_results['failures']:
                issue_type = self._classify_test_failure(failure)
                detected_issues.append({
                    'type': issue_type,
                    'test_name': failure.get('test_name'),
                    'error_message': failure.get('error'),
                    'stack_trace': failure.get('traceback'),
                    'timestamp': datetime.now()
                })
        
        return detected_issues
    
    def _classify_test_failure(self, failure: Dict[str, Any]) -> str:
        """Classify test failure type"""
        error_msg = failure.get('error', '').lower()
        
        if 'timeout' in error_msg:
            return 'performance_degradation'
        elif 'assertion' in error_msg:
            return 'logic_error'
        elif 'connection' in error_msg:
            return 'connectivity_issue'
        elif 'memory' in error_msg:
            return 'memory_issue'
        else:
            return 'unknown_error'

class IssuePrioritizer:
    """Issue categorization and prioritization logic"""
    
    def __init__(self):
        self.severity_weights = {
            IssueSeverity.CRITICAL: 100,
            IssueSeverity.HIGH: 75,
            IssueSeverity.MEDIUM: 50,
            IssueSeverity.LOW: 25
        }
        
        self.category_weights = {
            IssueCategory.SECURITY: 90,
            IssueCategory.DATA_INTEGRITY: 85,
            IssueCategory.BUG: 70,
            IssueCategory.PERFORMANCE: 60,
            IssueCategory.API: 55,
            IssueCategory.UI: 40,
            IssueCategory.USABILITY: 35,
            IssueCategory.ACCESSIBILITY: 30
        }
    
    def categorize_issue(self, issue_data: Dict[str, Any]) -> IssueCategory:
        """Automatically categorize an issue"""
        description = issue_data.get('description', '').lower()
        test_case = issue_data.get('test_case', '').lower()
        error_trace = issue_data.get('error_trace', '').lower()
        
        # Security-related keywords
        if any(keyword in description or keyword in test_case for keyword in 
               ['security', 'auth', 'permission', 'injection', 'xss', 'csrf']):
            return IssueCategory.SECURITY
        
        # Performance-related keywords
        if any(keyword in description or keyword in test_case for keyword in 
               ['performance', 'slow', 'timeout', 'memory', 'cpu']):
            return IssueCategory.PERFORMANCE
        
        # API-related keywords
        if any(keyword in description or keyword in test_case for keyword in 
               ['api', 'endpoint', 'request', 'response', 'http']):
            return IssueCategory.API
        
        # UI-related keywords
        if any(keyword in description or keyword in test_case for keyword in 
               ['ui', 'interface', 'button', 'form', 'display']):
            return IssueCategory.UI
        
        # Data integrity keywords
        if any(keyword in description or keyword in test_case for keyword in 
               ['data', 'corrupt', 'integrity', 'validation']):
            return IssueCategory.DATA_INTEGRITY
        
        # Default to bug category
        return IssueCategory.BUG
    
    def determine_severity(self, issue_data: Dict[str, Any]) -> IssueSeverity:
        """Determine issue severity based on impact and urgency"""
        description = issue_data.get('description', '').lower()
        test_case = issue_data.get('test_case', '').lower()
        category = issue_data.get('category', IssueCategory.BUG)
        
        # Critical severity indicators
        critical_keywords = ['crash', 'data loss', 'security breach', 'system down']
        if any(keyword in description for keyword in critical_keywords):
            return IssueSeverity.CRITICAL
        
        # High severity for security and data integrity issues
        if category in [IssueCategory.SECURITY, IssueCategory.DATA_INTEGRITY]:
            return IssueSeverity.HIGH
        
        # High severity indicators
        high_keywords = ['error', 'fail', 'broken', 'not working']
        if any(keyword in description for keyword in high_keywords):
            return IssueSeverity.HIGH
        
        # Medium severity for performance issues
        if category == IssueCategory.PERFORMANCE:
            return IssueSeverity.MEDIUM
        
        # Default to medium
        return IssueSeverity.MEDIUM
    
    def calculate_priority_score(self, issue: TestIssue) -> int:
        """Calculate priority score for issue ranking"""
        severity_score = self.severity_weights.get(issue.severity, 50)
        category_score = self.category_weights.get(issue.category, 50)
        
        # Age factor (older issues get slightly higher priority)
        age_days = (datetime.now() - issue.created_at).days
        age_factor = min(age_days * 2, 20)  # Max 20 points for age
        
        return severity_score + category_score + age_factor

class RegressionTestGenerator:
    """Generate regression tests for fixed bugs"""
    
    def __init__(self):
        self.test_templates = {
            IssueCategory.BUG: self._generate_bug_regression_test,
            IssueCategory.PERFORMANCE: self._generate_performance_regression_test,
            IssueCategory.API: self._generate_api_regression_test,
            IssueCategory.UI: self._generate_ui_regression_test
        }
    
    def generate_regression_test(self, issue: TestIssue) -> str:
        """Generate regression test code for a fixed issue"""
        generator = self.test_templates.get(issue.category, self._generate_generic_regression_test)
        return generator(issue)
    
    def _generate_bug_regression_test(self, issue: TestIssue) -> str:
        """Generate regression test for bug fixes"""
        test_name = f"test_regression_{issue.id.replace('-', '_')}"
        
        return f'''
def {test_name}():
    """
    Regression test for issue: {issue.title}
    
    Issue ID: {issue.id}
    Description: {issue.description}
    Fixed in commit: {issue.fix_commit or 'TBD'}
    """
    # Setup test data based on reproduction steps
    {self._generate_setup_code(issue)}
    
    # Execute the scenario that previously caused the bug
    {self._generate_execution_code(issue)}
    
    # Verify the fix works correctly
    {self._generate_assertion_code(issue)}
'''
    
    def _generate_performance_regression_test(self, issue: TestIssue) -> str:
        """Generate performance regression test"""
        test_name = f"test_performance_regression_{issue.id.replace('-', '_')}"
        
        return f'''
import time
import pytest

def {test_name}():
    """
    Performance regression test for: {issue.title}
    
    Issue ID: {issue.id}
    Performance requirement: Response time should be acceptable
    """
    start_time = time.time()
    
    # Execute the operation that had performance issues
    {self._generate_execution_code(issue)}
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Assert performance is within acceptable limits
    assert execution_time < 5.0, f"Operation took {{execution_time}}s, expected < 5.0s"
'''
    
    def _generate_api_regression_test(self, issue: TestIssue) -> str:
        """Generate API regression test"""
        test_name = f"test_api_regression_{issue.id.replace('-', '_')}"
        
        return f'''
import pytest
from fastapi.testclient import TestClient

def {test_name}(client: TestClient):
    """
    API regression test for: {issue.title}
    
    Issue ID: {issue.id}
    API endpoint regression test
    """
    # Setup test data
    {self._generate_setup_code(issue)}
    
    # Make API request that previously failed
    response = client.post("/api/endpoint", json=test_data)
    
    # Verify the API works correctly now
    assert response.status_code == 200
    assert "error" not in response.json()
'''
    
    def _generate_ui_regression_test(self, issue: TestIssue) -> str:
        """Generate UI regression test"""
        test_name = f"test_ui_regression_{issue.id.replace('-', '_')}"
        
        return f'''
from playwright.async_api import Page
import pytest

@pytest.mark.asyncio
async def {test_name}(page: Page):
    """
    UI regression test for: {issue.title}
    
    Issue ID: {issue.id}
    UI component regression test
    """
    # Navigate to the page with the issue
    await page.goto("/")
    
    # Reproduce the steps that caused the UI issue
    {self._generate_ui_steps_code(issue)}
    
    # Verify the UI works correctly now
    {self._generate_ui_assertions_code(issue)}
'''
    
    def _generate_generic_regression_test(self, issue: TestIssue) -> str:
        """Generate generic regression test"""
        test_name = f"test_regression_{issue.id.replace('-', '_')}"
        
        return f'''
def {test_name}():
    """
    Regression test for: {issue.title}
    
    Issue ID: {issue.id}
    Category: {issue.category.value}
    Severity: {issue.severity.value}
    """
    # TODO: Implement specific test logic based on issue details
    # Reproduction steps:
    {self._format_reproduction_steps(issue)}
    
    # Expected behavior: {issue.expected_behavior}
    # Previous actual behavior: {issue.actual_behavior}
    
    pass  # Replace with actual test implementation
'''
    
    def _generate_setup_code(self, issue: TestIssue) -> str:
        """Generate setup code based on reproduction steps"""
        if not issue.reproduction_steps:
            return "# No specific setup required"
        
        setup_lines = []
        for step in issue.reproduction_steps:
            if step.data_used:
                setup_lines.append(f"# Step {step.step_number}: {step.action}")
                setup_lines.append(f"test_data = {step.data_used}")
        
        return "\n    ".join(setup_lines) if setup_lines else "# No specific setup required"
    
    def _generate_execution_code(self, issue: TestIssue) -> str:
        """Generate execution code based on issue details"""
        return f"# Execute the scenario that caused: {issue.title}\n    # TODO: Implement execution logic"
    
    def _generate_assertion_code(self, issue: TestIssue) -> str:
        """Generate assertion code"""
        return f"# Verify: {issue.expected_behavior}\n    assert True  # TODO: Implement proper assertions"
    
    def _generate_ui_steps_code(self, issue: TestIssue) -> str:
        """Generate UI interaction steps"""
        if not issue.reproduction_steps:
            return "# No specific UI steps"
        
        steps = []
        for step in issue.reproduction_steps:
            steps.append(f"# {step.action}")
            steps.append("# TODO: Implement UI interaction")
        
        return "\n    ".join(steps)
    
    def _generate_ui_assertions_code(self, issue: TestIssue) -> str:
        """Generate UI assertion code"""
        return f"# Verify UI behavior: {issue.expected_behavior}\n    # TODO: Implement UI assertions"
    
    def _format_reproduction_steps(self, issue: TestIssue) -> str:
        """Format reproduction steps as comments"""
        if not issue.reproduction_steps:
            return "# No reproduction steps provided"
        
        steps = []
        for step in issue.reproduction_steps:
            steps.append(f"# {step.step_number}. {step.action}")
            steps.append(f"#    Expected: {step.expected_result}")
            steps.append(f"#    Actual: {step.actual_result}")
        
        return "\n    ".join(steps)

class BugTrackingService:
    """Main bug tracking and issue management service"""
    
    def __init__(self, storage_path: str = "bug_tracking"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        self.detector = BugDetector()
        self.prioritizer = IssuePrioritizer()
        self.test_generator = RegressionTestGenerator()
        
        self.issues: Dict[str, TestIssue] = {}
        self._load_existing_issues()
    
    def _load_existing_issues(self):
        """Load existing issues from storage"""
        issues_file = self.storage_path / "issues.json"
        if issues_file.exists():
            try:
                with open(issues_file, 'r') as f:
                    issues_data = json.load(f)
                
                for issue_data in issues_data:
                    # Convert datetime strings back to datetime objects
                    issue_data['created_at'] = datetime.fromisoformat(issue_data['created_at'])
                    issue_data['updated_at'] = datetime.fromisoformat(issue_data['updated_at'])
                    
                    # Convert enum strings back to enums
                    issue_data['severity'] = IssueSeverity(issue_data['severity'])
                    issue_data['category'] = IssueCategory(issue_data['category'])
                    issue_data['status'] = IssueStatus(issue_data['status'])
                    
                    # Convert reproduction steps
                    steps = []
                    for step_data in issue_data.get('reproduction_steps', []):
                        steps.append(ReproductionStep(**step_data))
                    issue_data['reproduction_steps'] = steps
                    
                    issue = TestIssue(**issue_data)
                    self.issues[issue.id] = issue
                    
            except Exception as e:
                print(f"Error loading existing issues: {e}")
    
    def _save_issues(self):
        """Save issues to storage"""
        issues_file = self.storage_path / "issues.json"
        
        issues_data = []
        for issue in self.issues.values():
            issue_dict = asdict(issue)
            # Convert datetime objects to strings
            issue_dict['created_at'] = issue.created_at.isoformat()
            issue_dict['updated_at'] = issue.updated_at.isoformat()
            # Convert enums to strings
            issue_dict['severity'] = issue.severity.value
            issue_dict['category'] = issue.category.value
            issue_dict['status'] = issue.status.value
            
            issues_data.append(issue_dict)
        
        with open(issues_file, 'w') as f:
            json.dump(issues_data, f, indent=2)
    
    def create_issue(self, 
                    title: str,
                    description: str,
                    test_case: str,
                    expected_behavior: str,
                    actual_behavior: str,
                    environment: Dict[str, str],
                    error_trace: Optional[str] = None,
                    reproduction_steps: Optional[List[ReproductionStep]] = None) -> TestIssue:
        """Create a new issue"""
        
        issue_data = {
            'description': description,
            'test_case': test_case,
            'error_trace': error_trace or ''
        }
        
        # Auto-categorize and prioritize
        category = self.prioritizer.categorize_issue(issue_data)
        severity = self.prioritizer.determine_severity({**issue_data, 'category': category})
        
        issue = TestIssue(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            severity=severity,
            category=category,
            status=IssueStatus.OPEN,
            test_case=test_case,
            reproduction_steps=reproduction_steps or [],
            expected_behavior=expected_behavior,
            actual_behavior=actual_behavior,
            environment=environment,
            error_trace=error_trace,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.issues[issue.id] = issue
        self._save_issues()
        
        return issue
    
    def update_issue(self, issue_id: str, **updates) -> Optional[TestIssue]:
        """Update an existing issue"""
        if issue_id not in self.issues:
            return None
        
        issue = self.issues[issue_id]
        
        for key, value in updates.items():
            if hasattr(issue, key):
                setattr(issue, key, value)
        
        issue.updated_at = datetime.now()
        self._save_issues()
        
        return issue
    
    def get_issue(self, issue_id: str) -> Optional[TestIssue]:
        """Get issue by ID"""
        return self.issues.get(issue_id)
    
    def list_issues(self, 
                   status: Optional[IssueStatus] = None,
                   category: Optional[IssueCategory] = None,
                   severity: Optional[IssueSeverity] = None,
                   limit: Optional[int] = None) -> List[TestIssue]:
        """List issues with optional filtering"""
        filtered_issues = list(self.issues.values())
        
        if status:
            filtered_issues = [i for i in filtered_issues if i.status == status]
        if category:
            filtered_issues = [i for i in filtered_issues if i.category == category]
        if severity:
            filtered_issues = [i for i in filtered_issues if i.severity == severity]
        
        # Sort by priority score (highest first)
        filtered_issues.sort(key=self.prioritizer.calculate_priority_score, reverse=True)
        
        if limit:
            filtered_issues = filtered_issues[:limit]
        
        return filtered_issues
    
    def detect_issues_from_logs(self, log_entries: List[str]) -> List[TestIssue]:
        """Detect and create issues from log entries"""
        detected = self.detector.detect_from_logs(log_entries)
        created_issues = []
        
        for detection in detected:
            # Check if similar issue already exists
            existing = self._find_similar_issue(detection['log_entry'])
            if existing:
                continue
            
            issue = self.create_issue(
                title=f"Automated detection: {detection['type']}",
                description=f"Detected from log: {detection['log_entry']}",
                test_case="automated_log_analysis",
                expected_behavior="No errors in logs",
                actual_behavior=detection['log_entry'],
                environment={"source": "log_analysis"},
                error_trace=detection['log_entry']
            )
            created_issues.append(issue)
        
        return created_issues
    
    def detect_issues_from_test_failures(self, test_results: Dict[str, Any]) -> List[TestIssue]:
        """Detect and create issues from test failures"""
        detected = self.detector.detect_from_test_failures(test_results)
        created_issues = []
        
        for detection in detected:
            # Check if similar issue already exists
            existing = self._find_similar_issue(detection.get('error_message', ''))
            if existing:
                continue
            
            issue = self.create_issue(
                title=f"Test failure: {detection.get('test_name', 'Unknown test')}",
                description=f"Test failed with: {detection.get('error_message', 'Unknown error')}",
                test_case=detection.get('test_name', 'unknown'),
                expected_behavior="Test should pass",
                actual_behavior=detection.get('error_message', 'Test failed'),
                environment={"source": "test_failure"},
                error_trace=detection.get('stack_trace')
            )
            created_issues.append(issue)
        
        return created_issues
    
    def _find_similar_issue(self, error_text: str) -> Optional[TestIssue]:
        """Find similar existing issue to avoid duplicates"""
        error_hash = hashlib.md5(error_text.encode()).hexdigest()
        
        for issue in self.issues.values():
            if issue.status in [IssueStatus.CLOSED, IssueStatus.RESOLVED]:
                continue
            
            issue_hash = hashlib.md5(issue.description.encode()).hexdigest()
            if error_hash == issue_hash:
                return issue
        
        return None
    
    def generate_regression_test(self, issue_id: str) -> Optional[str]:
        """Generate regression test for a fixed issue"""
        issue = self.get_issue(issue_id)
        if not issue:
            return None
        
        test_code = self.test_generator.generate_regression_test(issue)
        
        # Save the test to file
        test_file = self.storage_path / f"regression_test_{issue.id}.py"
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        # Update issue with test file reference
        self.update_issue(issue_id, verification_test=str(test_file))
        
        return test_code
    
    def mark_issue_fixed(self, issue_id: str, fix_commit: str) -> Optional[TestIssue]:
        """Mark issue as fixed and generate regression test"""
        issue = self.update_issue(issue_id, 
                                status=IssueStatus.RESOLVED,
                                fix_commit=fix_commit)
        
        if issue:
            # Generate regression test
            self.generate_regression_test(issue_id)
        
        return issue
    
    def get_issue_statistics(self) -> Dict[str, Any]:
        """Get issue statistics"""
        total_issues = len(self.issues)
        
        status_counts = {}
        for status in IssueStatus:
            status_counts[status.value] = len([i for i in self.issues.values() if i.status == status])
        
        severity_counts = {}
        for severity in IssueSeverity:
            severity_counts[severity.value] = len([i for i in self.issues.values() if i.severity == severity])
        
        category_counts = {}
        for category in IssueCategory:
            category_counts[category.value] = len([i for i in self.issues.values() if i.category == category])
        
        return {
            'total_issues': total_issues,
            'status_distribution': status_counts,
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'open_critical_issues': len([i for i in self.issues.values() 
                                       if i.status == IssueStatus.OPEN and i.severity == IssueSeverity.CRITICAL])
        }