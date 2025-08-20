"""
Tests for Production Readiness Validation
Comprehensive tests for production readiness validation system
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.production_readiness.models import (
    ProductionEnvironment, DeploymentConfig, ValidationStatus,
    ValidationSeverity, ValidationCategory, ProductionValidationSuite
)
from app.production_readiness.validator import (
    ProductionReadinessValidator, ProductionReadinessOrchestrator
)
from app.production_readiness.checklist import DeploymentReadinessValidator
from app.production_readiness.environment_tester import ProductionEnvironmentTester
from app.production_readiness.rollback_tester import RollbackTester
from app.production_readiness.monitoring_setup import MonitoringSetupValidator
from app.production_readiness.baseline_validator import PerformanceBaselineValidator


class TestProductionReadinessModels:
    """Test production readiness data models"""
    
    def test_production_environment_creation(self):
        """Test ProductionEnvironment model creation"""
        env_data = {
            "name": "production",
            "url": "https://app.example.com",
            "database_url": "postgresql://user:pass@db.example.com:5432/app_prod",
            "health_check_endpoints": ["/health", "/api/health"],
            "expected_services": ["database", "redis"],
            "performance_thresholds": {"response_time_ms": 500}
        }
        
        env = ProductionEnvironment(**env_data)
        
        assert env.name == "production"
        assert env.url == "https://app.example.com"
        assert len(env.health_check_endpoints) == 2
        assert len(env.expected_services) == 2
        assert env.performance_thresholds["response_time_ms"] == 500
    
    def test_deployment_config_creation(self):
        """Test DeploymentConfig model creation"""
        config_data = {
            "version": "1.0.0",
            "image_tag": "app:1.0.0",
            "environment_variables": {
                "DATABASE_URL": "postgresql://...",
                "SECRET_KEY": "secret"
            },
            "resource_limits": {"memory": "2Gi", "cpu": "1000m"},
            "scaling_config": {"min_replicas": 2, "max_replicas": 10},
            "health_check_config": {"path": "/health", "port": 8000},
            "rollback_config": {"strategy": "blue_green"}
        }
        
        config = DeploymentConfig(**config_data)
        
        assert config.version == "1.0.0"
        assert config.image_tag == "app:1.0.0"
        assert len(config.environment_variables) == 2
        assert config.resource_limits["memory"] == "2Gi"
    
    def test_validation_suite_summary_calculation(self):
        """Test validation suite summary calculation"""
        suite = ProductionValidationSuite(
            name="Test Suite",
            environment="test",
            version="1.0.0"
        )
        
        # Add some mock checks
        from app.production_readiness.models import ValidationCheck
        
        # Passed check
        passed_check = ValidationCheck(
            name="Test Check 1",
            description="Test description",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.HIGH,
            status=ValidationStatus.PASSED
        )
        suite.add_check(passed_check)
        
        # Failed critical check
        failed_check = ValidationCheck(
            name="Test Check 2",
            description="Test description",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.CRITICAL,
            status=ValidationStatus.FAILED
        )
        suite.add_check(failed_check)
        
        # Warning check
        warning_check = ValidationCheck(
            name="Test Check 3",
            description="Test description",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.MEDIUM,
            status=ValidationStatus.WARNING
        )
        suite.add_check(warning_check)
        
        summary = suite.calculate_summary()
        
        assert summary["total_checks"] == 3
        assert summary["passed_checks"] == 1
        assert summary["failed_checks"] == 1
        assert summary["warning_checks"] == 1
        assert summary["critical_failures"] == 1
        assert summary["production_ready"] == False  # Due to critical failure


class TestDeploymentReadinessValidator:
    """Test deployment readiness validation"""
    
    @pytest.fixture
    def sample_environment(self):
        """Sample production environment"""
        return ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test",
            health_check_endpoints=["/health"],
            expected_services=["database"]
        )
    
    @pytest.fixture
    def sample_config(self):
        """Sample deployment configuration"""
        return DeploymentConfig(
            version="1.0.0",
            image_tag="app:1.0.0",
            environment_variables={
                "DATABASE_URL": "postgresql://user:pass@db.test.com:5432/app_test",
                "SECRET_KEY": "test-secret",
                "ENVIRONMENT": "test",
                "LOG_LEVEL": "INFO"
            },
            resource_limits={"memory": "1Gi", "cpu": "500m"},
            scaling_config={},
            health_check_config={},
            rollback_config={}
        )
    
    @pytest.mark.asyncio
    async def test_validate_deployment_readiness(self, sample_environment, sample_config):
        """Test deployment readiness validation"""
        validator = DeploymentReadinessValidator(sample_environment, sample_config)
        
        with patch.object(validator, '_test_database_connection', return_value={"connected": True}):
            with patch.object(validator, '_check_service_availability', return_value={"available": True}):
                checks = await validator.validate_deployment_readiness()
        
        assert len(checks) > 0
        
        # Check that we have different types of validation checks
        check_names = [check.name for check in checks]
        assert any("Database" in name for name in check_names)
        assert any("Environment" in name for name in check_names)
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self, sample_environment, sample_config):
        """Test handling of database connection failure"""
        validator = DeploymentReadinessValidator(sample_environment, sample_config)
        
        with patch.object(validator, '_test_database_connection', return_value={"connected": False, "error": "Connection failed"}):
            checks = await validator.validate_deployment_readiness()
        
        # Find database connectivity check
        db_checks = [c for c in checks if "Database" in c.name]
        assert len(db_checks) > 0
        
        db_check = db_checks[0]
        assert db_check.status == ValidationStatus.FAILED
        assert "Connection failed" in db_check.error_message


class TestProductionEnvironmentTester:
    """Test production environment testing"""
    
    @pytest.fixture
    def sample_environment(self):
        """Sample production environment"""
        return ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test"
        )
    
    @pytest.mark.asyncio
    async def test_run_environment_tests(self, sample_environment):
        """Test running environment tests"""
        tester = ProductionEnvironmentTester(sample_environment)
        
        # Mock HTTP responses
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "OK"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            checks = await tester.run_environment_tests()
        
        assert len(checks) > 0
        
        # Verify we have API endpoint tests
        api_checks = [c for c in checks if "API" in c.name]
        assert len(api_checks) > 0


class TestRollbackTester:
    """Test rollback and disaster recovery testing"""
    
    @pytest.fixture
    def sample_environment(self):
        """Sample production environment"""
        return ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test"
        )
    
    @pytest.fixture
    def sample_config(self):
        """Sample deployment configuration"""
        return DeploymentConfig(
            version="1.0.0",
            image_tag="app:1.0.0",
            environment_variables={},
            resource_limits={},
            scaling_config={},
            health_check_config={},
            rollback_config={"strategy": "blue_green"}
        )
    
    @pytest.mark.asyncio
    async def test_run_rollback_tests(self, sample_environment, sample_config):
        """Test rollback testing"""
        tester = RollbackTester(sample_environment, sample_config)
        
        checks = await tester.run_rollback_tests()
        
        assert len(checks) > 0
        
        # Verify we have rollback-related checks
        rollback_checks = [c for c in checks if c.category in [ValidationCategory.ROLLBACK, ValidationCategory.DISASTER_RECOVERY]]
        assert len(rollback_checks) > 0
        
        # Check that rollback tests have proper RTO/RPO settings
        for check in rollback_checks:
            if hasattr(check, 'recovery_time_objective'):
                assert check.recovery_time_objective > 0


class TestMonitoringSetupValidator:
    """Test monitoring setup validation"""
    
    @pytest.fixture
    def sample_environment(self):
        """Sample production environment"""
        return ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test",
            monitoring_url="https://monitoring.test.com",
            log_aggregation_url="https://logs.test.com"
        )
    
    @pytest.mark.asyncio
    async def test_validate_monitoring_setup(self, sample_environment):
        """Test monitoring setup validation"""
        validator = MonitoringSetupValidator(sample_environment)
        
        # Mock HTTP responses for monitoring endpoints
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "# HELP test_metric Test metric\ntest_metric 1.0"
            mock_response.json.return_value = {"status": "healthy", "timestamp": "2024-01-19T10:00:00Z", "components": {"db": "ok"}}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            checks = await validator.validate_monitoring_setup()
        
        assert len(checks) > 0
        
        # Verify we have monitoring-related checks
        monitoring_checks = [c for c in checks if c.category == ValidationCategory.MONITORING]
        assert len(monitoring_checks) > 0


class TestPerformanceBaselineValidator:
    """Test performance baseline validation"""
    
    @pytest.fixture
    def sample_environment(self):
        """Sample production environment"""
        return ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test",
            performance_thresholds={
                "response_time_ms": 500,
                "throughput_rps": 100
            }
        )
    
    @pytest.mark.asyncio
    async def test_validate_performance_baselines(self, sample_environment):
        """Test performance baseline validation"""
        validator = PerformanceBaselineValidator(sample_environment)
        
        # Mock HTTP responses for API calls
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            checks = await validator.validate_performance_baselines()
        
        assert len(checks) > 0
        
        # Verify we have baseline-related checks
        baseline_checks = [c for c in checks if c.category == ValidationCategory.BASELINE]
        assert len(baseline_checks) > 0
        
        # Check that baseline checks have metrics and thresholds
        for check in baseline_checks:
            if hasattr(check, 'metrics') and hasattr(check, 'thresholds'):
                assert isinstance(check.metrics, dict)
                assert isinstance(check.thresholds, dict)


class TestProductionReadinessValidator:
    """Test main production readiness validator"""
    
    @pytest.fixture
    def sample_environment(self):
        """Sample production environment"""
        return ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test"
        )
    
    @pytest.fixture
    def sample_config(self):
        """Sample deployment configuration"""
        return DeploymentConfig(
            version="1.0.0",
            image_tag="app:1.0.0",
            environment_variables={
                "DATABASE_URL": "postgresql://user:pass@db.test.com:5432/app_test",
                "SECRET_KEY": "test-secret",
                "ENVIRONMENT": "test",
                "LOG_LEVEL": "INFO"
            },
            resource_limits={"memory": "1Gi"},
            scaling_config={},
            health_check_config={},
            rollback_config={}
        )
    
    @pytest.mark.asyncio
    async def test_run_full_validation(self, sample_environment, sample_config):
        """Test running full validation suite"""
        validator = ProductionReadinessValidator(sample_environment, sample_config)
        
        # Mock all the sub-validators
        with patch.object(validator.deployment_validator, 'validate_deployment_readiness', return_value=[]):
            with patch.object(validator.environment_tester, 'run_environment_tests', return_value=[]):
                with patch.object(validator.rollback_tester, 'run_rollback_tests', return_value=[]):
                    with patch.object(validator.monitoring_validator, 'validate_monitoring_setup', return_value=[]):
                        with patch.object(validator.baseline_validator, 'validate_performance_baselines', return_value=[]):
                            suite = await validator.run_full_validation()
        
        assert isinstance(suite, ProductionValidationSuite)
        assert suite.name == "Production Readiness Validation"
        assert suite.environment == "test"
        assert suite.version == "1.0.0"
        assert suite.started_at is not None
        assert suite.completed_at is not None
    
    def test_generate_validation_report(self, sample_environment, sample_config):
        """Test validation report generation"""
        validator = ProductionReadinessValidator(sample_environment, sample_config)
        
        # Create a mock suite with some checks
        suite = ProductionValidationSuite(
            name="Test Suite",
            environment="test",
            version="1.0.0"
        )
        
        from app.production_readiness.models import ValidationCheck
        
        # Add a passed check
        passed_check = ValidationCheck(
            name="Test Check",
            description="Test description",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.HIGH,
            status=ValidationStatus.PASSED
        )
        suite.add_check(passed_check)
        
        suite.summary = suite.calculate_summary()
        
        report = validator.generate_validation_report(suite)
        
        assert report.suite_id == suite.id
        assert report.environment == "test"
        assert report.version == "1.0.0"
        assert len(report.check_results) == 1
        assert len(report.recommendations) > 0
        assert len(report.next_steps) > 0


class TestProductionReadinessOrchestrator:
    """Test production readiness orchestrator"""
    
    @pytest.mark.asyncio
    async def test_validate_production_readiness(self):
        """Test orchestrator validation"""
        environment_config = ProductionReadinessOrchestrator.create_sample_environment_config()
        deployment_config = ProductionReadinessOrchestrator.create_sample_deployment_config()
        
        # Mock the validator to avoid actual network calls
        with patch('app.production_readiness.validator.ProductionReadinessValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_suite = Mock()
            mock_suite.id = "test-suite-id"
            mock_suite.environment = "production"
            mock_suite.version = "1.0.0"
            mock_suite.checks = []
            mock_suite.summary = {"production_ready": True}
            
            mock_validator.run_full_validation.return_value = mock_suite
            mock_validator.generate_validation_report.return_value = Mock(
                suite_id="test-suite-id",
                environment="production",
                version="1.0.0",
                generated_at=datetime.now(),
                summary={"production_ready": True},
                check_results=[],
                recommendations=[],
                production_ready=True,
                next_steps=[]
            )
            
            mock_validator_class.return_value = mock_validator
            
            report = await ProductionReadinessOrchestrator.validate_production_readiness(
                environment_config,
                deployment_config
            )
            
            assert report is not None
            mock_validator.run_full_validation.assert_called_once()
            mock_validator.generate_validation_report.assert_called_once()
    
    def test_create_sample_configurations(self):
        """Test sample configuration creation"""
        env_config = ProductionReadinessOrchestrator.create_sample_environment_config()
        deploy_config = ProductionReadinessOrchestrator.create_sample_deployment_config()
        
        # Validate environment config structure
        assert "name" in env_config
        assert "url" in env_config
        assert "database_url" in env_config
        assert "health_check_endpoints" in env_config
        assert "expected_services" in env_config
        
        # Validate deployment config structure
        assert "version" in deploy_config
        assert "image_tag" in deploy_config
        assert "environment_variables" in deploy_config
        assert "resource_limits" in deploy_config
        
        # Test that configurations can be used to create model instances
        env = ProductionEnvironment(**env_config)
        config = DeploymentConfig(**deploy_config)
        
        assert env.name == env_config["name"]
        assert config.version == deploy_config["version"]


@pytest.mark.asyncio
async def test_production_readiness_integration():
    """Integration test for production readiness validation"""
    
    # Create sample configurations
    environment_config = {
        "name": "integration_test",
        "url": "https://test.example.com",
        "database_url": "postgresql://user:pass@db.test.com:5432/app_test",
        "health_check_endpoints": ["/health"],
        "expected_services": ["database"],
        "performance_thresholds": {"response_time_ms": 500}
    }
    
    deployment_config = {
        "version": "1.0.0-test",
        "image_tag": "app:test",
        "environment_variables": {
            "DATABASE_URL": "postgresql://user:pass@db.test.com:5432/app_test",
            "SECRET_KEY": "test-secret",
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "DEBUG"
        },
        "resource_limits": {"memory": "512Mi", "cpu": "250m"},
        "scaling_config": {"min_replicas": 1, "max_replicas": 3},
        "health_check_config": {"path": "/health", "port": 8000},
        "rollback_config": {"strategy": "rolling_update"}
    }
    
    # Create environment and config objects
    environment = ProductionEnvironment(**environment_config)
    config = DeploymentConfig(**deployment_config)
    
    # Create validator
    validator = ProductionReadinessValidator(environment, config)
    
    # Mock external dependencies to avoid actual network calls
    with patch('aiohttp.ClientSession.get') as mock_get:
        with patch('psutil.virtual_memory') as mock_memory:
            with patch('psutil.cpu_count') as mock_cpu:
                with patch('psutil.disk_usage') as mock_disk:
                    with patch('psutil.cpu_percent') as mock_cpu_percent:
                        
                        # Setup mocks
                        mock_response = AsyncMock()
                        mock_response.status = 200
                        mock_response.text.return_value = "# HELP test_metric\ntest_metric 1.0"
                        mock_response.json.return_value = {"status": "healthy", "timestamp": "2024-01-19T10:00:00Z", "components": {}}
                        mock_get.return_value.__aenter__.return_value = mock_response
                        
                        mock_memory.return_value = Mock(total=8*1024**3, available=4*1024**3, percent=50)
                        mock_cpu.return_value = 4
                        mock_disk.return_value = Mock(total=100*1024**3, free=50*1024**3, used=50*1024**3)
                        mock_cpu_percent.return_value = 25.0
                        
                        # Run validation
                        suite = await validator.run_full_validation()
                        
                        # Verify results
                        assert suite is not None
                        assert suite.environment == "integration_test"
                        assert suite.version == "1.0.0-test"
                        assert suite.started_at is not None
                        assert suite.completed_at is not None
                        
                        # Generate report
                        report = validator.generate_validation_report(suite)
                        
                        assert report is not None
                        assert report.environment == "integration_test"
                        assert report.version == "1.0.0-test"
                        assert isinstance(report.recommendations, list)
                        assert isinstance(report.next_steps, list)