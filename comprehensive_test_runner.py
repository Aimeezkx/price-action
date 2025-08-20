#!/usr/bin/env python3
"""
Comprehensive Test Runner
Executes all test suites and collects results for analysis and improvement planning.
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

class ComprehensiveTestRunner:
    """Execute all test suites and collect comprehensive results"""
    
    def __init__(self):
        self.results = {
            'execution_time': datetime.now().isoformat(),
            'test_suites': {},
            'overall_status': 'pending',
            'critical_issues': [],
            'performance_metrics': {},
            'coverage_data': {},
            'improvement_recommendations': []
        }
        
    async def run_all_tests(self):
        """Execute all test suites in order"""
        print("🚀 Starting comprehensive test execution...")
        start_time = time.time()
        
        # Test execution order based on dependencies
        test_suites = [
            ('unit_tests', self.run_unit_tests),
            ('integration_tests', self.run_integration_tests),
            ('api_tests', self.run_api_tests),
            ('frontend_tests', self.run_frontend_tests),
            ('e2e_tests', self.run_e2e_tests),
            ('performance_tests', self.run_performance_tests),
            ('security_tests', self.run_security_tests),
            ('accessibility_tests', self.run_accessibility_tests),
            ('cross_platform_tests', self.run_cross_platform_tests),
            ('load_tests', self.run_load_tests)
        ]
        
        for suite_name, test_function in test_suites:
            print(f"\n📋 Executing {suite_name}...")
            try:
                suite_result = await test_function()
                self.results['test_suites'][suite_name] = suite_result
                
                if not suite_result.get('passed', False):
                    print(f"❌ {suite_name} failed")
                    if suite_result.get('critical', False):
                        self.results['critical_issues'].extend(
                            suite_result.get('issues', [])
                        )
                else:
                    print(f"✅ {suite_name} passed")
                    
            except Exception as e:
                print(f"💥 {suite_name} crashed: {str(e)}")
                self.results['test_suites'][suite_name] = {
                    'passed': False,
                    'error': str(e),
                    'critical': True
                }
                
        total_time = time.time() - start_time
        self.results['total_execution_time'] = total_time
        
        # Calculate overall status
        self.calculate_overall_status()
        
        print(f"\n🏁 Test execution completed in {total_time:.2f} seconds")
        return self.results
        
    async def run_unit_tests(self) -> Dict[str, Any]:
        """Run backend unit tests with coverage"""
        try:
            # Run backend unit tests
            backend_result = subprocess.run([
                'python', '-m', 'pytest', 
                'backend/tests/', 
                '--cov=backend/app',
                '--cov-report=json:backend_coverage.json',
                '--json-report', '--json-report-file=backend_unit_results.json',
                '-v'
            ], cwd='.', capture_output=True, text=True, timeout=300)
            
            # Parse results
            coverage_data = self.load_json_file('backend_coverage.json')
            test_results = self.load_json_file('backend_unit_results.json')
            
            passed = backend_result.returncode == 0
            coverage_percent = coverage_data.get('totals', {}).get('percent_covered', 0)
            
            return {
                'passed': passed,
                'coverage_percent': coverage_percent,
                'test_count': test_results.get('summary', {}).get('total', 0),
                'failed_count': test_results.get('summary', {}).get('failed', 0),
                'duration': test_results.get('duration', 0),
                'critical': coverage_percent < 80 or not passed,
                'issues': self.extract_test_issues(test_results) if not passed else []
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': True
            }
            
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        try:
            # Run integration test files
            integration_files = [
                'backend/test_*_integration.py',
                'backend/verify_*_implementation.py'
            ]
            
            results = []
            for pattern in integration_files:
                result = subprocess.run([
                    'python', '-m', 'pytest', 
                    pattern,
                    '--json-report', '--json-report-file=integration_results.json',
                    '-v'
                ], cwd='.', capture_output=True, text=True, timeout=600)
                
                if os.path.exists('integration_results.json'):
                    test_data = self.load_json_file('integration_results.json')
                    results.append({
                        'pattern': pattern,
                        'passed': result.returncode == 0,
                        'test_count': test_data.get('summary', {}).get('total', 0),
                        'failed_count': test_data.get('summary', {}).get('failed', 0)
                    })
                    
            total_tests = sum(r['test_count'] for r in results)
            total_failed = sum(r['failed_count'] for r in results)
            all_passed = all(r['passed'] for r in results)
            
            return {
                'passed': all_passed,
                'test_count': total_tests,
                'failed_count': total_failed,
                'suite_results': results,
                'critical': total_failed > 5 or not all_passed
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': True
            }
            
    async def run_api_tests(self) -> Dict[str, Any]:
        """Run API endpoint tests"""
        try:
            # Test API endpoints
            result = subprocess.run([
                'python', '-m', 'pytest', 
                'backend/tests/test_*_api.py',
                'backend/test_task*_endpoints.py',
                '--json-report', '--json-report-file=api_results.json',
                '-v'
            ], cwd='.', capture_output=True, text=True, timeout=300)
            
            test_data = self.load_json_file('api_results.json')
            
            return {
                'passed': result.returncode == 0,
                'test_count': test_data.get('summary', {}).get('total', 0),
                'failed_count': test_data.get('summary', {}).get('failed', 0),
                'duration': test_data.get('duration', 0),
                'critical': result.returncode != 0
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': True
            }
            
    async def run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend tests"""
        try:
            # Run frontend unit tests
            result = subprocess.run([
                'npm', 'test', '--', '--run', '--reporter=json'
            ], cwd='frontend', capture_output=True, text=True, timeout=300)
            
            # Parse frontend test results
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'output': result.stdout,
                'error_output': result.stderr,
                'critical': not passed
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': True
            }
            
    async def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests"""
        try:
            # Run Playwright E2E tests
            result = subprocess.run([
                'npx', 'playwright', 'test', '--reporter=json'
            ], cwd='frontend', capture_output=True, text=True, timeout=900)
            
            passed = result.returncode == 0
            
            return {
                'passed': passed,
                'output': result.stdout,
                'error_output': result.stderr,
                'critical': not passed
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': False  # E2E failures are not always critical
            }
            
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmarks"""
        try:
            # Run performance test scripts
            performance_scripts = [
                'simple_performance_test.py',
                'run_performance_tests.py',
                'backend/test_performance_monitoring.py'
            ]
            
            results = []
            for script in performance_scripts:
                if os.path.exists(script):
                    result = subprocess.run([
                        'python', script
                    ], capture_output=True, text=True, timeout=300)
                    
                    results.append({
                        'script': script,
                        'passed': result.returncode == 0,
                        'output': result.stdout,
                        'error': result.stderr
                    })
                    
            all_passed = all(r['passed'] for r in results)
            
            return {
                'passed': all_passed,
                'benchmark_results': results,
                'critical': False  # Performance issues are optimization opportunities
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': False
            }
            
    async def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        try:
            # Run security test suite
            result = subprocess.run([
                'python', '-m', 'pytest', 
                'backend/tests/test_security_simple.py',
                'backend/run_security_tests.py',
                '--json-report', '--json-report-file=security_results.json',
                '-v'
            ], cwd='.', capture_output=True, text=True, timeout=300)
            
            test_data = self.load_json_file('security_results.json')
            
            return {
                'passed': result.returncode == 0,
                'test_count': test_data.get('summary', {}).get('total', 0),
                'failed_count': test_data.get('summary', {}).get('failed', 0),
                'critical': result.returncode != 0  # Security failures are critical
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': True
            }
            
    async def run_accessibility_tests(self) -> Dict[str, Any]:
        """Run accessibility tests"""
        try:
            # Run accessibility test configuration
            if os.path.exists('frontend/accessibility-usability-test.config.js'):
                result = subprocess.run([
                    'node', 'accessibility-usability-test.config.js'
                ], cwd='frontend', capture_output=True, text=True, timeout=300)
                
                return {
                    'passed': result.returncode == 0,
                    'output': result.stdout,
                    'critical': False  # Accessibility issues are important but not critical
                }
            else:
                return {
                    'passed': True,
                    'skipped': True,
                    'reason': 'No accessibility tests configured'
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': False
            }
            
    async def run_cross_platform_tests(self) -> Dict[str, Any]:
        """Run cross-platform compatibility tests"""
        try:
            # Run cross-platform test script
            if os.path.exists('scripts/run-cross-platform-tests.js'):
                result = subprocess.run([
                    'node', 'scripts/run-cross-platform-tests.js'
                ], capture_output=True, text=True, timeout=600)
                
                return {
                    'passed': result.returncode == 0,
                    'output': result.stdout,
                    'error_output': result.stderr,
                    'critical': False
                }
            else:
                return {
                    'passed': True,
                    'skipped': True,
                    'reason': 'Cross-platform tests not available'
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': False
            }
            
    async def run_load_tests(self) -> Dict[str, Any]:
        """Run load and stress tests"""
        try:
            # Run load test framework
            if os.path.exists('test_load_framework.py'):
                result = subprocess.run([
                    'python', 'test_load_framework.py'
                ], capture_output=True, text=True, timeout=600)
                
                return {
                    'passed': result.returncode == 0,
                    'output': result.stdout,
                    'error_output': result.stderr,
                    'critical': False
                }
            else:
                return {
                    'passed': True,
                    'skipped': True,
                    'reason': 'Load tests not configured'
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'critical': False
            }
            
    def calculate_overall_status(self):
        """Calculate overall test status"""
        critical_failures = [
            suite for suite, result in self.results['test_suites'].items()
            if not result.get('passed', False) and result.get('critical', False)
        ]
        
        total_suites = len(self.results['test_suites'])
        passed_suites = sum(
            1 for result in self.results['test_suites'].values()
            if result.get('passed', False)
        )
        
        if critical_failures:
            self.results['overall_status'] = 'critical_failure'
        elif passed_suites == total_suites:
            self.results['overall_status'] = 'all_passed'
        elif passed_suites >= total_suites * 0.8:
            self.results['overall_status'] = 'mostly_passed'
        else:
            self.results['overall_status'] = 'many_failures'
            
    def load_json_file(self, filepath: str) -> Dict[str, Any]:
        """Load JSON file safely"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
        
    def extract_test_issues(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract issues from test results"""
        issues = []
        
        # Extract failed tests
        tests = test_results.get('tests', [])
        for test in tests:
            if test.get('outcome') == 'failed':
                issues.append({
                    'test_name': test.get('nodeid', 'unknown'),
                    'error': test.get('call', {}).get('longrepr', 'No error details'),
                    'severity': 'high' if 'critical' in test.get('nodeid', '').lower() else 'medium'
                })
                
        return issues
        
    def save_results(self, filepath: str = 'comprehensive_test_results.json'):
        """Save test results to file"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📊 Test results saved to {filepath}")

async def main():
    """Main execution function"""
    runner = ComprehensiveTestRunner()
    
    try:
        results = await runner.run_all_tests()
        runner.save_results()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*60)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Execution Time: {results['total_execution_time']:.2f} seconds")
        print(f"Critical Issues: {len(results['critical_issues'])}")
        
        print("\nTest Suite Results:")
        for suite_name, suite_result in results['test_suites'].items():
            status = "✅ PASS" if suite_result.get('passed', False) else "❌ FAIL"
            critical = " (CRITICAL)" if suite_result.get('critical', False) else ""
            print(f"  {suite_name}: {status}{critical}")
            
        if results['critical_issues']:
            print("\n🚨 Critical Issues Found:")
            for issue in results['critical_issues'][:5]:  # Show first 5
                print(f"  - {issue.get('test_name', 'Unknown test')}")
                
        return results['overall_status'] in ['all_passed', 'mostly_passed']
        
    except Exception as e:
        print(f"💥 Test execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)