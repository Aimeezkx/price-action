"""
Production Readiness Models
Defines data structures for production validation
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import uuid


class ValidationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class ValidationSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationCategory(Enum):
    DEPLOYMENT = "deployment"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MONITORING = "monitoring"
    ROLLBACK = "rollback"
    DISASTER_RECOVERY = "disaster_recovery"
    BASELINE = "baseline"


class ValidationCheck(BaseModel):
    """Individual validation check"""
    id: str
    name: str
    description: str
    category: ValidationCategory
    severity: ValidationSeverity
    status: ValidationStatus = ValidationStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        super().__init__(**data)


class DeploymentReadinessCheck(ValidationCheck):
    """Deployment readiness validation"""
    environment: str
    deployment_config: Dict[str, Any]
    dependencies: List[str]
    health_checks: List[str]


class PerformanceBaselineCheck(ValidationCheck):
    """Performance baseline validation"""
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    baseline_data: Optional[Dict[str, Any]] = None
    comparison_results: Optional[Dict[str, Any]] = None


class MonitoringSetupCheck(ValidationCheck):
    """Monitoring and alerting setup validation"""
    monitoring_endpoints: List[str]
    alert_rules: List[Dict[str, Any]]
    dashboard_configs: List[str]
    notification_channels: List[str]


class RollbackTestCheck(ValidationCheck):
    """Rollback and disaster recovery validation"""
    rollback_strategy: str
    recovery_time_objective: int  # seconds
    recovery_point_objective: int  # seconds
    backup_verification: bool
    rollback_test_results: Optional[Dict[str, Any]] = None


class ProductionValidationSuite(BaseModel):
    """Complete production validation suite"""
    id: str
    name: str
    environment: str
    version: str
    status: ValidationStatus = ValidationStatus.PENDING
    checks: List[ValidationCheck] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    summary: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        super().__init__(**data)
    
    def add_check(self, check: ValidationCheck):
        """Add validation check to suite"""
        self.checks.append(check)
    
    def get_checks_by_category(self, category: ValidationCategory) -> List[ValidationCheck]:
        """Get checks by category"""
        return [check for check in self.checks if check.category == category]
    
    def get_checks_by_severity(self, severity: ValidationSeverity) -> List[ValidationCheck]:
        """Get checks by severity"""
        return [check for check in self.checks if check.severity == severity]
    
    def calculate_summary(self) -> Dict[str, Any]:
        """Calculate validation summary"""
        total_checks = len(self.checks)
        passed_checks = len([c for c in self.checks if c.status == ValidationStatus.PASSED])
        failed_checks = len([c for c in self.checks if c.status == ValidationStatus.FAILED])
        warning_checks = len([c for c in self.checks if c.status == ValidationStatus.WARNING])
        
        critical_failures = len([
            c for c in self.checks 
            if c.status == ValidationStatus.FAILED and c.severity == ValidationSeverity.CRITICAL
        ])
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "warning_checks": warning_checks,
            "critical_failures": critical_failures,
            "success_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            "production_ready": critical_failures == 0 and failed_checks == 0
        }


class ProductionEnvironment(BaseModel):
    """Production environment configuration"""
    name: str
    url: str
    database_url: str
    redis_url: Optional[str] = None
    monitoring_url: Optional[str] = None
    log_aggregation_url: Optional[str] = None
    health_check_endpoints: List[str] = []
    expected_services: List[str] = []
    performance_thresholds: Dict[str, float] = {}
    security_requirements: Dict[str, Any] = {}


class DeploymentConfig(BaseModel):
    """Deployment configuration"""
    version: str
    image_tag: str
    environment_variables: Dict[str, str]
    resource_limits: Dict[str, Any]
    scaling_config: Dict[str, Any]
    health_check_config: Dict[str, Any]
    rollback_config: Dict[str, Any]


class ValidationReport(BaseModel):
    """Production readiness validation report"""
    suite_id: str
    environment: str
    version: str
    generated_at: datetime
    summary: Dict[str, Any]
    check_results: List[Dict[str, Any]]
    recommendations: List[str]
    production_ready: bool
    next_steps: List[str]