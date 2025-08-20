"""
Production Readiness Validator
Main orchestrator for production readiness validation
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from .models import (
    ProductionValidationSuite, ValidationCheck, ValidationStatus, 
    ValidationSeverity, ValidationCategory, ProductionEnvironment, 
    DeploymentConfig, ValidationReport
)
from .checklist import DeploymentReadinessValidator
from .environment_tester import ProductionEnvironmentTester
from .rollback_tester import RollbackTester
from .monitoring_setup import MonitoringSetupValidator
from .baseline_validator import PerformanceBaselineValidator


class ProductionReadinessValidator:
    """Main production readiness validation orchestrator"""
    
    def __init__(self, environment: ProductionEnvironment, config: DeploymentConfig):
        self.environment = environment
        self.config = config
        
        # Initialize validators
        self.deployment_validator = DeploymentReadinessValidator(environment, config)
        self.environment_tester = ProductionEnvironmentTester(environment)
        self.rollback_tester = RollbackTester(environment, config)
        self.monitoring_validator = MonitoringSetupValidator(environment)
        self.baseline_validator = PerformanceBaselineValidator(environment)
        
    async def run_full_validation(self) -> ProductionValidationSuite:
        """Run complete production readiness validation"""
        suite = ProductionValidationSuite(
            name="Production Readiness Validation",
            environment=self.environment.name,
            version=self.config.version
        )
        
        suite.started_at = datetime.now()
        suite.status = ValidationStatus.RUNNING
        
        try:
            # Run all validation categories
            validation_tasks = [
                self._run_deployment_validation(),
                self._run_environment_testing(),
                self._run_rollback_testing(),
                self._run_monitoring_validation(),
                self._run_baseline_validation()
            ]
            
            # Execute all validations concurrently
            validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Collect all checks
            for result in validation_results:
                if isinstance(result, Exception):
                    # Create error check for failed validation category
                    error_check = ValidationCheck(
                        name="Validation Category Error",
                        description=f"Validation category failed: {str(result)}",
                        category=ValidationCategory.DEPLOYMENT,
                        severity=ValidationSeverity.CRITICAL,
                        status=ValidationStatus.FAILED,
                        error_message=str(result)
                    )
                    suite.add_check(error_check)
                else:
                    # Add successful validation checks
                    for check in result:
                        suite.add_check(check)
            
            # Calculate final status
            suite.status = self._calculate_suite_status(suite.checks)
            suite.summary = suite.calculate_summary()
            
        except Exception as e:
            suite.status = ValidationStatus.FAILED
            error_check = ValidationCheck(
                name="Validation Suite Error",
                description=f"Validation suite failed: {str(e)}",
                category=ValidationCategory.DEPLOYMENT,
                severity=ValidationSeverity.CRITICAL,
                status=ValidationStatus.FAILED,
                error_message=str(e)
            )
            suite.add_check(error_check)
            suite.summary = suite.calculate_summary()
        
        finally:
            suite.completed_at = datetime.now()
        
        return suite
    
    async def _run_deployment_validation(self) -> List[ValidationCheck]:
        """Run deployment readiness validation"""
        try:
            return await self.deployment_validator.validate_deployment_readiness()
        except Exception as e:
            error_check = ValidationCheck(
                name="Deployment Validation Error",
                description="Deployment validation failed",
                category=ValidationCategory.DEPLOYMENT,
                severity=ValidationSeverity.CRITICAL,
                status=ValidationStatus.FAILED,
                error_message=str(e)
            )
            return [error_check]
    
    async def _run_environment_testing(self) -> List[ValidationCheck]:
        """Run production environment testing"""
        try:
            return await self.environment_tester.run_environment_tests()
        except Exception as e:
            error_check = ValidationCheck(
                name="Environment Testing Error",
                description="Environment testing failed",
                category=ValidationCategory.DEPLOYMENT,
                severity=ValidationSeverity.HIGH,
                status=ValidationStatus.FAILED,
                error_message=str(e)
            )
            return [error_check]
    
    async def _run_rollback_testing(self) -> List[ValidationCheck]:
        """Run rollback and disaster recovery testing"""
        try:
            return await self.rollback_tester.run_rollback_tests()
        except Exception as e:
            error_check = ValidationCheck(
                name="Rollback Testing Error",
                description="Rollback testing failed",
                category=ValidationCategory.ROLLBACK,
                severity=ValidationSeverity.CRITICAL,
                status=ValidationStatus.FAILED,
                error_message=str(e)
            )
            return [error_check]
    
    async def _run_monitoring_validation(self) -> List[ValidationCheck]:
        """Run monitoring and alerting validation"""
        try:
            return await self.monitoring_validator.validate_monitoring_setup()
        except Exception as e:
            error_check = ValidationCheck(
                name="Monitoring Validation Error",
                description="Monitoring validation failed",
                category=ValidationCategory.MONITORING,
                severity=ValidationSeverity.HIGH,
                status=ValidationStatus.FAILED,
                error_message=str(e)
            )
            return [error_check]
    
    async def _run_baseline_validation(self) -> List[ValidationCheck]:
        """Run performance baseline validation"""
        try:
            return await self.baseline_validator.validate_performance_baselines()
        except Exception as e:
            error_check = ValidationCheck(
                name="Baseline Validation Error",
                description="Baseline validation failed",
                category=ValidationCategory.BASELINE,
                severity=ValidationSeverity.MEDIUM,
                status=ValidationStatus.FAILED,
                error_message=str(e)
            )
            return [error_check]
    
    def _calculate_suite_status(self, checks: List[ValidationCheck]) -> ValidationStatus:
        """Calculate overall suite status based on individual checks"""
        if not checks:
            return ValidationStatus.FAILED
        
        # Count check statuses
        failed_checks = [c for c in checks if c.status == ValidationStatus.FAILED]
        critical_failures = [
            c for c in failed_checks 
            if c.severity == ValidationSeverity.CRITICAL
        ]
        
        # Determine overall status
        if critical_failures:
            return ValidationStatus.FAILED
        elif failed_checks:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED
    
    def generate_validation_report(self, suite: ProductionValidationSuite) -> ValidationReport:
        """Generate comprehensive validation report"""
        # Collect check results
        check_results = []
        for check in suite.checks:
            check_results.append({
                "id": check.id,
                "name": check.name,
                "description": check.description,
                "category": check.category.value,
                "severity": check.severity.value,
                "status": check.status.value,
                "execution_time": check.execution_time,
                "error_message": check.error_message,
                "result": check.result
            })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(suite)
        
        # Determine production readiness
        production_ready = suite.summary["production_ready"] if suite.summary else False
        
        # Generate next steps
        next_steps = self._generate_next_steps(suite)
        
        return ValidationReport(
            suite_id=suite.id,
            environment=suite.environment,
            version=suite.version,
            generated_at=datetime.now(),
            summary=suite.summary or {},
            check_results=check_results,
            recommendations=recommendations,
            production_ready=production_ready,
            next_steps=next_steps
        )
    
    def _generate_recommendations(self, suite: ProductionValidationSuite) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Analyze failed checks by category
        failed_checks = [c for c in suite.checks if c.status == ValidationStatus.FAILED]
        warning_checks = [c for c in suite.checks if c.status == ValidationStatus.WARNING]
        
        # Critical deployment issues
        critical_deployment_failures = [
            c for c in failed_checks 
            if c.category == ValidationCategory.DEPLOYMENT and c.severity == ValidationSeverity.CRITICAL
        ]
        
        if critical_deployment_failures:
            recommendations.append(
                "CRITICAL: Fix deployment readiness issues before proceeding to production. "
                "Review database connectivity, environment variables, and service dependencies."
            )
        
        # Rollback and disaster recovery issues
        rollback_failures = [
            c for c in failed_checks 
            if c.category in [ValidationCategory.ROLLBACK, ValidationCategory.DISASTER_RECOVERY]
        ]
        
        if rollback_failures:
            recommendations.append(
                "Implement and test rollback procedures. Ensure disaster recovery plans are "
                "validated and meet recovery time objectives."
            )
        
        # Monitoring issues
        monitoring_issues = [
            c for c in failed_checks + warning_checks 
            if c.category == ValidationCategory.MONITORING
        ]
        
        if monitoring_issues:
            recommendations.append(
                "Complete monitoring and alerting setup. Ensure all critical metrics are "
                "being collected and alert rules are properly configured."
            )
        
        # Performance baseline issues
        baseline_issues = [
            c for c in warning_checks 
            if c.category == ValidationCategory.BASELINE
        ]
        
        if baseline_issues:
            recommendations.append(
                "Review performance baselines that exceed thresholds. Consider optimization "
                "or adjusting thresholds based on business requirements."
            )
        
        # Security recommendations
        security_issues = [
            c for c in failed_checks + warning_checks 
            if c.category == ValidationCategory.SECURITY
        ]
        
        if security_issues:
            recommendations.append(
                "Address security configuration issues. Ensure SSL/TLS is properly configured "
                "and all security requirements are met."
            )
        
        # General recommendations if no specific issues
        if not recommendations:
            recommendations.append(
                "All validation checks passed. The system appears ready for production deployment."
            )
        
        return recommendations
    
    def _generate_next_steps(self, suite: ProductionValidationSuite) -> List[str]:
        """Generate next steps based on validation results"""
        next_steps = []
        
        if suite.summary and suite.summary.get("production_ready", False):
            next_steps.extend([
                "1. Schedule production deployment",
                "2. Notify stakeholders of deployment readiness",
                "3. Prepare deployment runbook and rollback procedures",
                "4. Schedule post-deployment validation",
                "5. Monitor system performance after deployment"
            ])
        else:
            # Prioritize next steps based on failed checks
            critical_failures = [
                c for c in suite.checks 
                if c.status == ValidationStatus.FAILED and c.severity == ValidationSeverity.CRITICAL
            ]
            
            if critical_failures:
                next_steps.append("1. URGENT: Fix critical validation failures before deployment")
                
                # Group by category for specific guidance
                deployment_failures = [c for c in critical_failures if c.category == ValidationCategory.DEPLOYMENT]
                rollback_failures = [c for c in critical_failures if c.category in [ValidationCategory.ROLLBACK, ValidationCategory.DISASTER_RECOVERY]]
                
                if deployment_failures:
                    next_steps.append("2. Resolve deployment readiness issues (database, dependencies, configuration)")
                
                if rollback_failures:
                    next_steps.append("3. Implement and test rollback procedures")
                
                next_steps.extend([
                    "4. Re-run production readiness validation",
                    "5. Schedule deployment only after all critical issues are resolved"
                ])
            else:
                # Handle warnings and minor issues
                next_steps.extend([
                    "1. Review and address warning-level validation issues",
                    "2. Consider if warning-level issues are acceptable for production",
                    "3. Update monitoring and alerting configurations",
                    "4. Re-run validation to confirm fixes",
                    "5. Proceed with deployment planning"
                ])
        
        return next_steps


class ProductionReadinessOrchestrator:
    """High-level orchestrator for production readiness validation"""
    
    @staticmethod
    async def validate_production_readiness(
        environment_config: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> ValidationReport:
        """Run complete production readiness validation and return report"""
        
        # Create environment and deployment config objects
        environment = ProductionEnvironment(**environment_config)
        config = DeploymentConfig(**deployment_config)
        
        # Create validator
        validator = ProductionReadinessValidator(environment, config)
        
        # Run validation
        suite = await validator.run_full_validation()
        
        # Generate report
        report = validator.generate_validation_report(suite)
        
        return report
    
    @staticmethod
    def create_sample_environment_config() -> Dict[str, Any]:
        """Create sample environment configuration for testing"""
        return {
            "name": "production",
            "url": "https://app.example.com",
            "database_url": "postgresql://user:pass@db.example.com:5432/app_prod",
            "redis_url": "redis://redis.example.com:6379/0",
            "monitoring_url": "https://monitoring.example.com",
            "log_aggregation_url": "https://logs.example.com",
            "health_check_endpoints": [
                "https://app.example.com/health",
                "https://api.example.com/health"
            ],
            "expected_services": [
                "database",
                "redis",
                "file_storage",
                "email_service"
            ],
            "performance_thresholds": {
                "response_time_ms": 500,
                "throughput_rps": 100,
                "error_rate_percent": 1.0
            },
            "security_requirements": {
                "ssl_required": True,
                "min_tls_version": "1.2",
                "security_headers": True
            }
        }
    
    @staticmethod
    def create_sample_deployment_config() -> Dict[str, Any]:
        """Create sample deployment configuration for testing"""
        return {
            "version": "1.0.0",
            "image_tag": "app:1.0.0",
            "environment_variables": {
                "DATABASE_URL": "postgresql://user:pass@db.example.com:5432/app_prod",
                "SECRET_KEY": "production-secret-key",
                "ENVIRONMENT": "production",
                "LOG_LEVEL": "INFO",
                "REDIS_URL": "redis://redis.example.com:6379/0"
            },
            "resource_limits": {
                "memory": "2Gi",
                "cpu": "1000m"
            },
            "scaling_config": {
                "min_replicas": 2,
                "max_replicas": 10,
                "target_cpu_percent": 70
            },
            "health_check_config": {
                "path": "/health",
                "port": 8000,
                "initial_delay_seconds": 30,
                "period_seconds": 10
            },
            "rollback_config": {
                "strategy": "blue_green",
                "max_rollback_time_seconds": 300,
                "auto_rollback_on_failure": True
            }
        }