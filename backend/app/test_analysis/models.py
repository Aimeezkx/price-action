"""
Test Analysis Data Models
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class TestStatus(str, Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestCategory(str, Enum):
    """Test category types"""
    UNIT = "unit"
    INTEGRATION = "integration"
    API = "api"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    CROSS_PLATFORM = "cross_platform"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueCategory(str, Enum):
    """Issue category types"""
    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    ACCESSIBILITY = "accessibility"


class TestResult(BaseModel):
    """Individual test result"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    category: TestCategory
    status: TestStatus
    duration: float  # seconds
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class TestSuiteResult(BaseModel):
    """Test suite execution result"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    category: TestCategory
    status: TestStatus
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    duration: float
    coverage_percentage: Optional[float] = None
    test_results: List[TestResult] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class PerformanceBenchmark(BaseModel):
    """Performance benchmark result"""
    name: str
    metric: str  # e.g., "response_time", "throughput", "memory_usage"
    value: float
    unit: str  # e.g., "ms", "requests/sec", "MB"
    threshold: Optional[float] = None
    passed: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class CoverageReport(BaseModel):
    """Code coverage report"""
    total_lines: int
    covered_lines: int
    coverage_percentage: float
    uncovered_files: List[str] = Field(default_factory=list)
    coverage_by_file: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class TestIssue(BaseModel):
    """Test issue or bug report"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    test_case: str
    reproduction_steps: List[str] = Field(default_factory=list)
    expected_behavior: str
    actual_behavior: str
    environment: Dict[str, str] = Field(default_factory=dict)
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


class TestTrend(BaseModel):
    """Test trend data point"""
    date: datetime
    category: TestCategory
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    coverage_percentage: Optional[float] = None
    average_duration: float


class TestAnalysisReport(BaseModel):
    """Comprehensive test analysis report"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    report_date: datetime = Field(default_factory=datetime.now)
    test_suites: List[TestSuiteResult] = Field(default_factory=list)
    performance_benchmarks: List[PerformanceBenchmark] = Field(default_factory=list)
    coverage_report: Optional[CoverageReport] = None
    issues: List[TestIssue] = Field(default_factory=list)
    trends: List[TestTrend] = Field(default_factory=list)
    
    @property
    def overall_status(self) -> TestStatus:
        """Calculate overall test status"""
        if not self.test_suites:
            return TestStatus.PENDING
            
        statuses = [suite.status for suite in self.test_suites]
        
        if all(status == TestStatus.PASSED for status in statuses):
            return TestStatus.PASSED
        elif any(status == TestStatus.FAILED for status in statuses):
            return TestStatus.FAILED
        elif any(status == TestStatus.ERROR for status in statuses):
            return TestStatus.ERROR
        else:
            return TestStatus.PENDING
    
    @property
    def overall_pass_rate(self) -> float:
        """Calculate overall pass rate"""
        if not self.test_suites:
            return 0.0
            
        total_tests = sum(suite.total_tests for suite in self.test_suites)
        passed_tests = sum(suite.passed_tests for suite in self.test_suites)
        
        if total_tests == 0:
            return 0.0
        return (passed_tests / total_tests) * 100
    
    @property
    def critical_issues_count(self) -> int:
        """Count critical issues"""
        return len([issue for issue in self.issues if issue.severity == IssueSeverity.CRITICAL])


class ImprovementSuggestion(BaseModel):
    """Test improvement suggestion"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    priority: IssueSeverity
    category: IssueCategory
    suggested_actions: List[str] = Field(default_factory=list)
    impact_estimate: str  # "high", "medium", "low"
    effort_estimate: str  # "high", "medium", "low"
    created_at: datetime = Field(default_factory=datetime.now)


class ExecutiveSummary(BaseModel):
    """Executive summary for stakeholders"""
    report_date: datetime = Field(default_factory=datetime.now)
    overall_health_score: float  # 0-100
    total_tests_executed: int
    overall_pass_rate: float
    critical_issues: int
    high_priority_issues: int
    coverage_percentage: Optional[float] = None
    performance_status: str  # "excellent", "good", "needs_attention", "critical"
    key_achievements: List[str] = Field(default_factory=list)
    top_concerns: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    trend_summary: str