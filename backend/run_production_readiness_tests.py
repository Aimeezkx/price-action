#!/usr/bin/env python3
"""
Production Readiness Test Runner
Runs comprehensive tests for production readiness validation system
"""

import asyncio
import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
        else:
            print(f"❌ FAILED (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


async def test_production_readiness_models():
    """Test production readiness models"""
    print("\n🧪 Testing Production Readiness Models...")
    
    try:
        from app.production_readiness.models import (
            ProductionEnvironment, DeploymentConfig, ValidationCheck,
            ValidationStatus, ValidationSeverity, ValidationCategory,
            ProductionValidationSuite
        )
        
        # Test ProductionEnvironment creation
        env = ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test",
            health_check_endpoints=["/health"],
            expected_services=["database"]
        )
        
        assert env.name == "test"
        assert env.url == "https://test.example.com"
        print("✅ ProductionEnvironment model works correctly")
        
        # Test DeploymentConfig creation
        config = DeploymentConfig(
            version="1.0.0",
            image_tag="app:1.0.0",
            environment_variables={"TEST": "value"},
            resource_limits={"memory": "1Gi"},
            scaling_config={},
            health_check_config={},
            rollback_config={}
        )
        
        assert config.version == "1.0.0"
        assert config.image_tag == "app:1.0.0"
        print("✅ DeploymentConfig model works correctly")
        
        # Test ValidationCheck creation
        check = ValidationCheck(
            name="Test Check",
            description="Test description",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.HIGH,
            status=ValidationStatus.PASSED
        )
        
        assert check.name == "Test Check"
        assert check.category == ValidationCategory.DEPLOYMENT
        print("✅ ValidationCheck model works correctly")
        
        # Test ProductionValidationSuite
        suite = ProductionValidationSuite(
            name="Test Suite",
            environment="test",
            version="1.0.0"
        )
        
        suite.add_check(check)
        summary = suite.calculate_summary()
        
        assert summary["total_checks"] == 1
        assert summary["passed_checks"] == 1
        print("✅ ProductionValidationSuite model works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {str(e)}")
        return False


async def test_production_readiness_validators():
    """Test production readiness validators"""
    print("\n🧪 Testing Production Readiness Validators...")
    
    try:
        from app.production_readiness.models import ProductionEnvironment, DeploymentConfig
        from app.production_readiness.validator import ProductionReadinessValidator
        from unittest.mock import patch, AsyncMock
        
        # Create test environment and config
        environment = ProductionEnvironment(
            name="test",
            url="https://test.example.com",
            database_url="postgresql://user:pass@db.test.com:5432/app_test",
            health_check_endpoints=["/health"],
            expected_services=["database"]
        )
        
        config = DeploymentConfig(
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
        
        # Create validator
        validator = ProductionReadinessValidator(environment, config)
        
        # Test deployment validator
        with patch.object(validator.deployment_validator, '_test_database_connection', return_value={"connected": True}):
            with patch.object(validator.deployment_validator, '_check_service_availability', return_value={"available": True}):
                deployment_checks = await validator.deployment_validator.validate_deployment_readiness()
                
        assert len(deployment_checks) > 0
        print("✅ Deployment validator works correctly")
        
        # Test environment tester
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "OK"
            mock_get.return_value.__aenter__.return_value = mock_response
            
            environment_checks = await validator.environment_tester.run_environment_tests()
            
        assert len(environment_checks) > 0
        print("✅ Environment tester works correctly")
        
        # Test rollback tester
        rollback_checks = await validator.rollback_tester.run_rollback_tests()
        assert len(rollback_checks) > 0
        print("✅ Rollback tester works correctly")
        
        # Test monitoring validator
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "# HELP test_metric\ntest_metric 1.0"
            mock_response.json.return_value = {"status": "healthy", "timestamp": "2024-01-19T10:00:00Z", "components": {}}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            monitoring_checks = await validator.monitoring_validator.validate_monitoring_setup()
            
        assert len(monitoring_checks) > 0
        print("✅ Monitoring validator works correctly")
        
        # Test baseline validator
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            baseline_checks = await validator.baseline_validator.validate_performance_baselines()
            
        assert len(baseline_checks) > 0
        print("✅ Baseline validator works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Validator test failed: {str(e)}")
        return False


async def test_production_readiness_orchestrator():
    """Test production readiness orchestrator"""
    print("\n🧪 Testing Production Readiness Orchestrator...")
    
    try:
        from app.production_readiness.validator import ProductionReadinessOrchestrator
        from unittest.mock import patch, Mock
        
        # Test sample configuration creation
        env_config = ProductionReadinessOrchestrator.create_sample_environment_config()
        deploy_config = ProductionReadinessOrchestrator.create_sample_deployment_config()
        
        assert "name" in env_config
        assert "url" in env_config
        assert "version" in deploy_config
        assert "image_tag" in deploy_config
        print("✅ Sample configuration creation works correctly")
        
        # Test orchestrator validation (mocked)
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
                env_config,
                deploy_config
            )
            
            assert report is not None
            mock_validator.run_full_validation.assert_called_once()
            mock_validator.generate_validation_report.assert_called_once()
            
        print("✅ Orchestrator validation works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {str(e)}")
        return False


async def test_production_readiness_cli():
    """Test production readiness CLI"""
    print("\n🧪 Testing Production Readiness CLI...")
    
    try:
        # Test CLI help
        result = subprocess.run(
            [sys.executable, "production_readiness_cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        assert result.returncode == 0
        assert "Production Readiness Validation CLI" in result.stdout
        print("✅ CLI help works correctly")
        
        # Test generate-config command
        result = subprocess.run(
            [sys.executable, "production_readiness_cli.py", "generate-config", "--output-dir", "/tmp/test_configs"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        assert result.returncode == 0
        print("✅ CLI generate-config works correctly")
        
        # Test list-checks command
        result = subprocess.run(
            [sys.executable, "production_readiness_cli.py", "list-checks"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        assert result.returncode == 0
        assert "Available Validation Checks" in result.stdout
        print("✅ CLI list-checks works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {str(e)}")
        return False


async def run_integration_test():
    """Run integration test"""
    print("\n🧪 Running Integration Test...")
    
    try:
        from app.production_readiness.models import ProductionEnvironment, DeploymentConfig
        from app.production_readiness.validator import ProductionReadinessValidator
        from unittest.mock import patch, Mock, AsyncMock
        
        # Create test configurations
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
        
        # Mock external dependencies
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
        
        print("✅ Integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False


async def main():
    """Main test runner"""
    print("🚀 Production Readiness Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    test_results = []
    
    # Run unit tests with pytest
    print("\n📋 Running Unit Tests with pytest...")
    pytest_success = run_command(
        [sys.executable, "-m", "pytest", "tests/test_production_readiness.py", "-v"],
        "Running pytest unit tests"
    )
    test_results.append(("Pytest Unit Tests", pytest_success))
    
    # Run model tests
    model_success = await test_production_readiness_models()
    test_results.append(("Model Tests", model_success))
    
    # Run validator tests
    validator_success = await test_production_readiness_validators()
    test_results.append(("Validator Tests", validator_success))
    
    # Run orchestrator tests
    orchestrator_success = await test_production_readiness_orchestrator()
    test_results.append(("Orchestrator Tests", orchestrator_success))
    
    # Run CLI tests
    cli_success = await test_production_readiness_cli()
    test_results.append(("CLI Tests", cli_success))
    
    # Run integration test
    integration_success = await run_integration_test()
    test_results.append(("Integration Test", integration_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed! Production readiness validation system is working correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ {failed_tests} test(s) failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())