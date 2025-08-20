"""
Models for the continuous improvement system
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid


class ImprovementPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImprovementCategory(str, Enum):
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    USER_EXPERIENCE = "user_experience"
    SECURITY = "security"
    ACCESSIBILITY = "accessibility"
    FEATURE_ENHANCEMENT = "feature_enhancement"


class ImprovementStatus(str, Enum):
    IDENTIFIED = "identified"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class CodeQualityMetric(BaseModel):
    """Code quality metrics"""
    file_path: str
    complexity: float
    maintainability_index: float
    test_coverage: float
    code_smells: int
    duplicated_lines: int
    technical_debt_ratio: float
    timestamp: datetime = datetime.now()


class PerformanceMetric(BaseModel):
    """Performance metrics"""
    operation: str
    response_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    error_rate: float
    timestamp: datetime = datetime.now()


class UserFeedback(BaseModel):
    """User feedback data"""
    id: str = str(uuid.uuid4())
    user_id: Optional[str] = None
    feature: str
    rating: int  # 1-5 scale
    comment: str
    category: str
    severity: str
    timestamp: datetime = datetime.now()
    processed: bool = False


class Improvement(BaseModel):
    """Improvement suggestion"""
    id: str = str(uuid.uuid4())
    title: str
    description: str
    priority: ImprovementPriority
    category: ImprovementCategory
    status: ImprovementStatus = ImprovementStatus.IDENTIFIED
    suggested_actions: List[str]
    estimated_effort: int  # hours
    expected_impact: float  # 0-1 scale
    confidence: float  # 0-1 scale
    source_data: Dict[str, Any]
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class ImprovementImpact(BaseModel):
    """Measurement of improvement impact"""
    improvement_id: str
    metric_name: str
    before_value: float
    after_value: float
    improvement_percentage: float
    measurement_date: datetime = datetime.now()
    validation_method: str


class FeatureRequest(BaseModel):
    """Feature enhancement request"""
    id: str = str(uuid.uuid4())
    title: str
    description: str
    requested_by: str
    priority_score: float
    user_votes: int
    business_value: float
    technical_complexity: float
    estimated_effort: int
    status: str = "pending"
    created_at: datetime = datetime.now()


class QualityGate(BaseModel):
    """Quality gate configuration"""
    name: str
    metric: str
    threshold: float
    operator: str  # >, <, >=, <=, ==
    enabled: bool = True
    description: str