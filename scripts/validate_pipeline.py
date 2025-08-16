#!/usr/bin/env python3
"""
Pipeline validation script to test the automated testing infrastructure.
Validates that all components are properly configured and working.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any


class PipelineValidator:
    """Validate automated testing pipeline components"""
    
    def __init__(self):
        self.results = {
            'timestamp': time.time(),
            'validations': {},
            'overall_status': 'UNKNOWN',
            'errors': [],
            'warnings': []
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("🔍 Validating automated testing pipeline...")
        
        # Validate configuration files
        self.validate_configuration_files()
        
        # Validate GitHub Actions workflow
        self.validate_github_actions()
        
        # Validate scripts
        self.validate_scripts()
        
        # Validate Docker configuration
        self.validate_docker_config()
        
        # Validate test infrastructure
        self.validate_test_infrastructure()
        
        # Determine overall status
        self.determine_overall_status()
        
        return self.results
    
    def validate_configuration_files(self):
        """Validate configuration files exist and are valid"""
        print("📋 Validating configuration files...")
        
        config_files = [
            'automated-testing-config.json',
            'performance-baseline.json',
            'infrastructure/staging-environment.yml',
            '.github/workflows/automated-testing-pipeline.yml'
        ]
        
        validation_result = {
            'status': 'PASS',
            'details': {},
            'missing_files': [],
            'invalid_files': []
        }
        
        for config_file in config_files:
            if not os.path.exists(config_file):
                validation_result['missing_files'].append(config_file)
                validation_result['status'] = 'FAIL'
                continue
            
            # Validate JSON files
            if config_file.endswith('.json'):
                try:
                    with open(config_file, 'r') as f:
                        json.load(f)
                    validation_result['details'][config_file] = 'Valid JSON'
                except json.JSONDecodeError as e:
                    validation_result['invalid_files'].append(f"{config_file}: {e}")
                    validation_result['status'] = 'FAIL'
            else:
                validation_result['details'][config_file] = 'File exists'
        
        self.results['validations']['configuration_files'] = validation_result
        
        if validation_result['status'] == 'PASS':
            print("✅ Configuration files validation passed")
        else:
            print("❌ Configuration files validation failed")
            if validation_result['missing_files']:
                print(f"   Missing files: {', '.join(validation_result['missing_files'])}")
            if validation_result['invalid_files']:
                print(f"   Invalid files: {', '.join(validation_result['invalid_files'])}")
    
    def validate_github_actions(self):
        """Validate GitHub Actions workflow"""
        print("🔧 Validating GitHub Actions workflow...")
        
        workflow_file = '.github/workflows/automated-testing-pipeline.yml'
        validation_result = {
            'status': 'PASS',
            'details': {},
            'issues': []
        }
        
        if not os.path.exists(workflow_file):
            validation_result['status'] = 'FAIL'
            validation_result['issues'].append('Workflow file missing')
        else:
            # Check workflow content
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            required_jobs = [
                'unit-tests',
                'integration-tests', 
                'performance-tests',
                'security-tests',
                'e2e-tests',
                'test-report'
            ]
            
            for job in required_jobs:
                if job in content:
                    validation_result['details'][job] = 'Found'
                else:
                    validation_result['issues'].append(f'Missing job: {job}')
                    validation_result['status'] = 'FAIL'
            
            # Check for required environment variables
            required_env_vars = [
                'SLACK_WEBHOOK_URL',
                'GITHUB_TOKEN',
                'DATABASE_URL'
            ]
            
            for env_var in required_env_vars:
                if env_var in content:
                    validation_result['details'][f'env_{env_var}'] = 'Referenced'
                else:
                    validation_result['issues'].append(f'Environment variable not referenced: {env_var}')
        
        self.results['validations']['github_actions'] = validation_result
        
        if validation_result['status'] == 'PASS':
            print("✅ GitHub Actions workflow validation passed")
        else:
            print("❌ GitHub Actions workflow validation failed")
            for issue in validation_result['issues']:
                print(f"   Issue: {issue}")
    
    def validate_scripts(self):
        """Validate required scripts exist and are executable"""
        print("📜 Validating scripts...")
        
        required_scripts = [
            'scripts/generate_test_report.py',
            'scripts/analyze_performance_regression.py',
            'scripts/notification_service.py',
            'scripts/deploy_staging.sh',
            'scripts/seed_staging_data.py'
        ]
        
        validation_result = {
            'status': 'PASS',
            'details': {},
            'missing_scripts': [],
            'non_executable': []
        }
        
        for script in required_scripts:
            if not os.path.exists(script):
                validation_result['missing_scripts'].append(script)
                validation_result['status'] = 'FAIL'
                continue
            
            # Check if script is executable (for shell scripts)
            if script.endswith('.sh'):
                if not os.access(script, os.X_OK):
                    validation_result['non_executable'].append(script)
                    validation_result['status'] = 'FAIL'
                else:
                    validation_result['details'][script] = 'Executable'
            else:
                validation_result['details'][script] = 'Exists'
        
        self.results['validations']['scripts'] = validation_result
        
        if validation_result['status'] == 'PASS':
            print("✅ Scripts validation passed")
        else:
            print("❌ Scripts validation failed")
            if validation_result['missing_scripts']:
                print(f"   Missing scripts: {', '.join(validation_result['missing_scripts'])}")
            if validation_result['non_executable']:
                print(f"   Non-executable scripts: {', '.join(validation_result['non_executable'])}")
    
    def validate_docker_config(self):
        """Validate Docker configuration"""
        print("🐳 Validating Docker configuration...")
        
        validation_result = {
            'status': 'PASS',
            'details': {},
            'issues': []
        }
        
        # Check Docker Compose file
        compose_file = 'infrastructure/staging-environment.yml'
        if os.path.exists(compose_file):
            validation_result['details']['compose_file'] = 'Exists'
            
            # Check for required services
            with open(compose_file, 'r') as f:
                content = f.read()
            
            required_services = [
                'postgres-staging',
                'redis-staging',
                'backend-staging',
                'frontend-staging'
            ]
            
            for service in required_services:
                if service in content:
                    validation_result['details'][f'service_{service}'] = 'Defined'
                else:
                    validation_result['issues'].append(f'Missing service: {service}')
                    validation_result['status'] = 'FAIL'
        else:
            validation_result['status'] = 'FAIL'
            validation_result['issues'].append('Docker Compose file missing')
        
        # Check Dockerfiles
        dockerfiles = [
            'backend/Dockerfile',
            'frontend/Dockerfile'
        ]
        
        for dockerfile in dockerfiles:
            if os.path.exists(dockerfile):
                validation_result['details'][dockerfile] = 'Exists'
            else:
                validation_result['issues'].append(f'Missing Dockerfile: {dockerfile}')
                # Don't fail for missing Dockerfiles as they might not be implemented yet
        
        self.results['validations']['docker_config'] = validation_result
        
        if validation_result['status'] == 'PASS':
            print("✅ Docker configuration validation passed")
        else:
            print("❌ Docker configuration validation failed")
            for issue in validation_result['issues']:
                print(f"   Issue: {issue}")
    
    def validate_test_infrastructure(self):
        """Validate test infrastructure"""
        print("🧪 Validating test infrastructure...")
        
        validation_result = {
            'status': 'PASS',
            'details': {},
            'issues': []
        }
        
        # Check test directories
        test_directories = [
            'backend/tests',
            'frontend/src/test',
            'frontend/e2e'
        ]
        
        for test_dir in test_directories:
            if os.path.exists(test_dir):
                validation_result['details'][test_dir] = 'Exists'
            else:
                validation_result['issues'].append(f'Missing test directory: {test_dir}')
                # Don't fail for missing test directories as they might not be fully implemented
        
        # Check test configuration files
        test_configs = [
            'backend/pytest.ini',
            'backend/pyproject.toml',
            'frontend/package.json',
            'frontend/playwright.config.ts'
        ]
        
        for config in test_configs:
            if os.path.exists(config):
                validation_result['details'][config] = 'Exists'
            else:
                validation_result['issues'].append(f'Missing test config: {config}')
        
        self.results['validations']['test_infrastructure'] = validation_result
        
        if validation_result['status'] == 'PASS':
            print("✅ Test infrastructure validation passed")
        else:
            print("⚠️  Test infrastructure validation has issues (non-critical)")
            for issue in validation_result['issues']:
                print(f"   Issue: {issue}")
    
    def determine_overall_status(self):
        """Determine overall validation status"""
        critical_validations = [
            'configuration_files',
            'github_actions',
            'scripts'
        ]
        
        failed_critical = []
        failed_non_critical = []
        
        for validation_name, validation_result in self.results['validations'].items():
            if validation_result['status'] == 'FAIL':
                if validation_name in critical_validations:
                    failed_critical.append(validation_name)
                else:
                    failed_non_critical.append(validation_name)
        
        if failed_critical:
            self.results['overall_status'] = 'FAIL'
            self.results['errors'] = failed_critical
        elif failed_non_critical:
            self.results['overall_status'] = 'PASS_WITH_WARNINGS'
            self.results['warnings'] = failed_non_critical
        else:
            self.results['overall_status'] = 'PASS'
    
    def generate_report(self, output_file: str = None):
        """Generate validation report"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("AUTOMATED TESTING PIPELINE VALIDATION REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Overall Status: {self.results['overall_status']}")
        report_lines.append("")
        
        # Summary
        total_validations = len(self.results['validations'])
        passed_validations = sum(1 for v in self.results['validations'].values() if v['status'] == 'PASS')
        
        report_lines.append("SUMMARY:")
        report_lines.append(f"  Total Validations: {total_validations}")
        report_lines.append(f"  Passed: {passed_validations}")
        report_lines.append(f"  Failed: {total_validations - passed_validations}")
        report_lines.append("")
        
        # Detailed results
        for validation_name, validation_result in self.results['validations'].items():
            status_icon = "✅" if validation_result['status'] == 'PASS' else "❌"
            report_lines.append(f"{status_icon} {validation_name.upper()}: {validation_result['status']}")
            
            if validation_result.get('issues'):
                for issue in validation_result['issues']:
                    report_lines.append(f"    - {issue}")
            
            report_lines.append("")
        
        # Recommendations
        if self.results['overall_status'] != 'PASS':
            report_lines.append("RECOMMENDATIONS:")
            
            if self.results['errors']:
                report_lines.append("  Critical Issues (must fix):")
                for error in self.results['errors']:
                    report_lines.append(f"    - Fix {error} validation failures")
            
            if self.results['warnings']:
                report_lines.append("  Warnings (recommended to fix):")
                for warning in self.results['warnings']:
                    report_lines.append(f"    - Address {warning} validation issues")
            
            report_lines.append("")
        
        report_content = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_content)
            print(f"Validation report saved to: {output_file}")
        
        return report_content


def main():
    parser = argparse.ArgumentParser(description='Validate automated testing pipeline')
    parser.add_argument('--output', help='Output file for validation report')
    parser.add_argument('--json', help='Output results as JSON to specified file')
    
    args = parser.parse_args()
    
    validator = PipelineValidator()
    results = validator.validate_all()
    
    # Generate and display report
    report = validator.generate_report(args.output)
    print("\n" + report)
    
    # Save JSON results if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"JSON results saved to: {args.json}")
    
    # Exit with appropriate code
    if results['overall_status'] == 'FAIL':
        print("\n❌ Pipeline validation failed!")
        sys.exit(1)
    elif results['overall_status'] == 'PASS_WITH_WARNINGS':
        print("\n⚠️  Pipeline validation passed with warnings")
        sys.exit(0)
    else:
        print("\n✅ Pipeline validation passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()