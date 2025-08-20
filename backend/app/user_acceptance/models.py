"""
User Acceptance Testing Models
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class TestScenarioType(str, Enum):
    """Types of user acceptance test scenarios"""
    DOCUMENT_UPLOAD = "document_upload"
    CARD_REVIEW = "card_review"
    SEARCH_USAGE = "search_usage"
    CHAPTER_BROWSING = "chapter_browsing"
    EXPORT_FUNCTIONALITY = "export_functionality"
    MOBILE_USAGE = "mobile_usage"
    ACCESSIBILITY = "accessibility"


class TestStatus(str, Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FeedbackType(str, Enum):
    """Types of user feedback"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY_ISSUE = "usability_issue"
    PERFORMANCE_COMPLAINT = "performance_complaint"
    GENERAL_FEEDBACK = "general_feedback"


class SatisfactionLevel(str, Enum):
    """User satisfaction levels"""
    VERY_DISSATISFIED = "very_dissatisfied"
    DISSATISFIED = "dissatisfied"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    VERY_SATISFIED = "very_satisfied"


class UserScenario(BaseModel):
    """Represents a user acceptance test scenario"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    scenario_type: TestScenarioType
    steps: List[str]
    expected_outcomes: List[str]
    success_criteria: List[str]
    estimated_duration: int  # minutes
    difficulty_level: str  # beginner, intermediate, advanced
    prerequisites: List[str] = []
    test_data_requirements: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserTestSession(BaseModel):
    """Represents a user test session"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    scenario_id: str
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    completion_rate: float = 0.0  # 0.0 to 1.0
    success_rate: float = 0.0  # 0.0 to 1.0
    user_satisfaction: Optional[SatisfactionLevel] = None
    feedback: str = ""
    issues_encountered: List[str] = []
    time_per_step: List[float] = []  # seconds per step
    user_actions: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.now)


class UserFeedback(BaseModel):
    """User feedback model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    session_id: Optional[str] = None
    feedback_type: FeedbackType
    title: str
    description: str
    severity: str  # low, medium, high, critical
    category: str  # ui, performance, functionality, etc.
    satisfaction_rating: Optional[int] = None  # 1-5 scale
    ease_of_use_rating: Optional[int] = None  # 1-5 scale
    feature_usefulness_rating: Optional[int] = None  # 1-5 scale
    tags: List[str] = []
    attachments: List[str] = []  # file paths or URLs
    status: str = "open"  # open, in_progress, resolved, closed
    created_at: datetime = Field(default_factory=datetime.now)


class ABTestVariant(BaseModel):
    """A/B test variant configuration"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    feature_flags: Dict[str, Any]
    traffic_percentage: float  # 0.0 to 1.0
    is_control: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class ABTest(BaseModel):
    """A/B test configuration"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    feature_name: str
    hypothesis: str
    success_metrics: List[str]
    variants: List[ABTestVariant]
    start_date: datetime
    end_date: datetime
    status: str = "draft"  # draft, running, completed, cancelled
    sample_size: int
    confidence_level: float = 0.95
    created_at: datetime = Field(default_factory=datetime.now)


class ABTestResult(BaseModel):
    """A/B test result data"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    test_id: str
    variant_id: str
    user_id: str
    session_id: str
    metrics: Dict[str, float]
    conversion_events: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class UXMetric(BaseModel):
    """User experience metric"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    session_id: str
    metric_name: str
    metric_value: float
    metric_unit: str
    context: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)


class UserSatisfactionSurvey(BaseModel):
    """User satisfaction survey"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    session_id: Optional[str] = None
    overall_satisfaction: int  # 1-5 scale
    ease_of_use: int  # 1-5 scale
    feature_completeness: int  # 1-5 scale
    performance_satisfaction: int  # 1-5 scale
    design_satisfaction: int  # 1-5 scale
    likelihood_to_recommend: int  # 1-10 scale (NPS)
    most_valuable_feature: str = ""
    least_valuable_feature: str = ""
    improvement_suggestions: str = ""
    additional_comments: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class TestExecutionResult(BaseModel):
    """Result of test scenario execution"""
    scenario_id: str
    session_id: str
    success: bool
    completion_time: float  # seconds
    steps_completed: int
    total_steps: int
    issues: List[str] = []
    user_feedback: str = ""
    satisfaction_score: Optional[int] = None
    metrics: Dict[str, float] = {}