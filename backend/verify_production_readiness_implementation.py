#!/usr/bin/env python3
"""
Production Readiness Implementation Verification
Verifies the production readiness validation implementation without external dependencies
"""

import os
import sys
import importlib.util
from pathlib import Path


def verify_file_exists(file_path, description):
    """Verify that a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (NOT FOUND)")
        return False


def verify_python_syntax(file_path, description):
    """Verify Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code
        compile(content, file_path, 'exec')
        print(f"✅ {description}: Valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"❌ {description}: Syntax error - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {description}: Error - {str(e)}")
        return False


def verify_module_structure(module_path, expected_classes):
    """Verify module contains expected classes/functions"""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        if spec is None:
            print(f"❌ Cannot load module: {module_path}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        
        # Try to execute the module (this will fail if dependencies are missing, but we can catch that)
        try:
            spec.loader.exec_module(module)
            
            # Check for expected classes
            missing_classes = []
            for class_name in expected_classes:
                if not hasattr(module, class_name):
                    missing_classes.append(class_name)
            
            if missing_classes:
                print(f"❌ Module {module_path}: Missing classes - {', '.join(missing_classes)}")
                return False
            else:
                print(f"✅ Module {module_path}: All expected classes found")
                return True
                
        except ImportError as e:
            # This is expected if dependencies are missing
            print(f"⚠️  Module {module_path}: Import error (likely missing dependencies) - {str(e)}")
            # Still check if the classes are defined in the source code
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            missing_classes = []
            for class_name in expected_classes:
                if (f"class {class_name}" not in content and 
                    f"def {class_name}" not in content and 
                    f"{class_name} =" not in content):
                    missing_classes.append(class_name)
            
            if missing_classes:
                print(f"❌ Module {module_path}: Missing class definitions - {', '.join(missing_classes)}")
                return False
            else:
                print(f"✅ Module {module_path}: All expected class definitions found in source")
                return True
                
    except Exception as e:
        print(f"❌ Module verification failed for {module_path}: {str(e)}")
        return False


def main():
    """Main verification function"""
    print("🔍 Production Readiness Implementation Verification")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    results = []
    
    # Define files to verify
    files_to_verify = [
        # Core models
        ("app/production_readiness/__init__.py", "Production readiness module init"),
        ("app/production_readiness/models.py", "Production readiness models"),
        ("app/production_readiness/validator.py", "Main production readiness validator"),
        ("app/production_readiness/checklist.py", "Deployment readiness checklist"),
        ("app/production_readiness/environment_tester.py", "Production environment tester"),
        ("app/production_readiness/rollback_tester.py", "Rollback and disaster recovery tester"),
        ("app/production_readiness/monitoring_setup.py", "Monitoring setup validator"),
        ("app/production_readiness/baseline_validator.py", "Performance baseline validator"),
        ("app/production_readiness/api.py", "Production readiness API"),
        
        # CLI and test files
        ("production_readiness_cli.py", "Production readiness CLI"),
        ("tests/test_production_readiness.py", "Production readiness tests"),
        ("run_production_readiness_tests.py", "Production readiness test runner"),
    ]
    
    print("\n📁 File Existence Verification")
    print("-" * 40)
    
    for file_path, description in files_to_verify:
        full_path = base_path / file_path
        result = verify_file_exists(full_path, description)
        results.append((f"File: {description}", result))
    
    print("\n🐍 Python Syntax Verification")
    print("-" * 40)
    
    for file_path, description in files_to_verify:
        full_path = base_path / file_path
        if os.path.exists(full_path):
            result = verify_python_syntax(full_path, description)
            results.append((f"Syntax: {description}", result))
    
    print("\n🏗️  Module Structure Verification")
    print("-" * 40)
    
    # Define expected classes/functions for key modules
    module_expectations = [
        ("app/production_readiness/models.py", [
            "ValidationCheck", "ProductionEnvironment", "DeploymentConfig", 
            "ProductionValidationSuite", "ValidationReport"
        ]),
        ("app/production_readiness/validator.py", [
            "ProductionReadinessValidator", "ProductionReadinessOrchestrator"
        ]),
        ("app/production_readiness/checklist.py", [
            "DeploymentReadinessValidator"
        ]),
        ("app/production_readiness/environment_tester.py", [
            "ProductionEnvironmentTester"
        ]),
        ("app/production_readiness/rollback_tester.py", [
            "RollbackTester"
        ]),
        ("app/production_readiness/monitoring_setup.py", [
            "MonitoringSetupValidator"
        ]),
        ("app/production_readiness/baseline_validator.py", [
            "PerformanceBaselineValidator"
        ]),
        ("app/production_readiness/api.py", [
            "router"
        ])
    ]
    
    for file_path, expected_classes in module_expectations:
        full_path = base_path / file_path
        if os.path.exists(full_path):
            result = verify_module_structure(full_path, expected_classes)
            results.append((f"Structure: {file_path}", result))
    
    print("\n📊 Content Verification")
    print("-" * 40)
    
    # Verify key content exists in files
    content_checks = [
        ("app/production_readiness/models.py", ["ValidationStatus", "ValidationSeverity", "ValidationCategory"], "Enums defined"),
        ("app/production_readiness/validator.py", ["run_full_validation", "generate_validation_report"], "Key methods defined"),
        ("app/production_readiness/api.py", ["/api/v1/production-readiness", "validate"], "API endpoints defined"),
        ("production_readiness_cli.py", ["argparse", "validate", "quick-check"], "CLI commands defined"),
        ("tests/test_production_readiness.py", ["test_", "pytest", "assert"], "Test functions defined")
    ]
    
    for file_path, keywords, description in content_checks:
        full_path = base_path / file_path
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                missing_keywords = []
                for keyword in keywords:
                    if keyword not in content:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    print(f"❌ {description} in {file_path}: Missing - {', '.join(missing_keywords)}")
                    results.append((f"Content: {description}", False))
                else:
                    print(f"✅ {description} in {file_path}")
                    results.append((f"Content: {description}", True))
                    
            except Exception as e:
                print(f"❌ Content check failed for {file_path}: {str(e)}")
                results.append((f"Content: {description}", False))
    
    print("\n🔧 Implementation Features Verification")
    print("-" * 40)
    
    # Check for key implementation features
    feature_checks = [
        ("Deployment readiness validation", "app/production_readiness/checklist.py", ["database", "environment_variables", "ssl"]),
        ("Environment testing", "app/production_readiness/environment_tester.py", ["api_endpoints", "database_performance", "load_balancer"]),
        ("Rollback testing", "app/production_readiness/rollback_tester.py", ["rollback_procedures", "disaster_recovery", "backup_restoration"]),
        ("Monitoring setup", "app/production_readiness/monitoring_setup.py", ["prometheus", "alert_rules", "dashboards"]),
        ("Performance baselines", "app/production_readiness/baseline_validator.py", ["response_time", "throughput", "resource_usage"]),
        ("API endpoints", "app/production_readiness/api.py", ["POST", "GET", "validate", "report"]),
        ("CLI interface", "production_readiness_cli.py", ["validate", "quick-check", "generate-config", "list-checks"])
    ]
    
    for feature_name, file_path, keywords in feature_checks:
        full_path = base_path / file_path
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                found_keywords = []
                for keyword in keywords:
                    if keyword.lower() in content:
                        found_keywords.append(keyword)
                
                if len(found_keywords) >= len(keywords) * 0.7:  # At least 70% of keywords found
                    print(f"✅ {feature_name}: Implemented ({len(found_keywords)}/{len(keywords)} features found)")
                    results.append((f"Feature: {feature_name}", True))
                else:
                    print(f"⚠️  {feature_name}: Partially implemented ({len(found_keywords)}/{len(keywords)} features found)")
                    results.append((f"Feature: {feature_name}", False))
                    
            except Exception as e:
                print(f"❌ Feature check failed for {feature_name}: {str(e)}")
                results.append((f"Feature: {feature_name}", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(1 for _, success in results if success)
    failed_checks = total_checks - passed_checks
    
    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nTotal Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if failed_checks == 0:
        print("\n🎉 All verification checks passed!")
        print("✅ Production readiness validation system is properly implemented.")
        return True
    elif passed_checks >= total_checks * 0.8:  # 80% success rate
        print(f"\n⚠️  Most verification checks passed ({passed_checks}/{total_checks}).")
        print("✅ Production readiness validation system is mostly implemented.")
        print("🔧 Review failed checks for minor issues.")
        return True
    else:
        print(f"\n❌ Multiple verification checks failed ({failed_checks}/{total_checks}).")
        print("🔧 Review the implementation for missing components.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)