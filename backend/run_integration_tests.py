#!/usr/bin/env python3
"""
Integration test runner for the document learning application.
Runs comprehensive integration tests and generates reports.
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


class IntegrationTestRunner:
    """Runs and manages integration tests"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_tests(
        self, 
        test_pattern: Optional[str] = None,
        verbose: bool = True,
        coverage: bool = True,
        parallel: bool = False
    ) -> Dict:
        """Run integration tests with specified options"""
        
        print("🚀 Starting Integration Test Suite")
        print("=" * 50)
        
        self.start_time = time.time()
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test directory
        cmd.append("tests/integration/")
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html:htmlcov/integration",
                "--cov-report=term-missing"
            ])
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        if test_pattern:
            cmd.extend(["-k", test_pattern])
        
        # Add markers for integration tests
        cmd.extend(["-m", "integration"])
        
        # Add output formatting
        cmd.extend([
            "--tb=short",
            "--junit-xml=test-results/integration-results.xml"
        ])
        
        print(f"Running command: {' '.join(cmd)}")
        print()
        
        # Create results directory
        os.makedirs("test-results", exist_ok=True)
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            self.end_time = time.time()
            
            # Parse results
            self.test_results = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': self.end_time - self.start_time,
                'success': result.returncode == 0
            }
            
            # Print results
            self._print_results()
            
            return self.test_results
            
        except subprocess.TimeoutExpired:
            print("❌ Tests timed out after 30 minutes")
            return {
                'exit_code': -1,
                'error': 'Timeout',
                'success': False,
                'duration': 1800
            }
        
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return {
                'exit_code': -1,
                'error': str(e),
                'success': False,
                'duration': 0
            }
    
    def _print_results(self):
        """Print test results summary"""
        
        print("\n" + "=" * 50)
        print("📊 Integration Test Results")
        print("=" * 50)
        
        if self.test_results['success']:
            print("✅ All integration tests passed!")
        else:
            print("❌ Some integration tests failed")
        
        print(f"⏱️  Duration: {self.test_results['duration']:.2f} seconds")
        print(f"🔢 Exit Code: {self.test_results['exit_code']}")
        
        # Print stdout (test output)
        if self.test_results['stdout']:
            print("\n📝 Test Output:")
            print("-" * 30)
            print(self.test_results['stdout'])
        
        # Print stderr (errors)
        if self.test_results['stderr']:
            print("\n🚨 Errors:")
            print("-" * 30)
            print(self.test_results['stderr'])
        
        print("\n" + "=" * 50)
    
    def run_specific_test_suite(self, suite_name: str) -> Dict:
        """Run a specific test suite"""
        
        suite_patterns = {
            'pipeline': 'test_document_processing_pipeline',
            'api': 'test_api_integration',
            'database': 'test_database_operations',
            'storage': 'test_file_upload_storage',
            'workflows': 'test_cross_component_workflows'
        }
        
        if suite_name not in suite_patterns:
            print(f"❌ Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(suite_patterns.keys())}")
            return {'success': False, 'error': 'Unknown suite'}
        
        pattern = suite_patterns[suite_name]
        print(f"🎯 Running {suite_name} test suite")
        
        return self.run_tests(test_pattern=pattern)
    
    def run_performance_tests(self) -> Dict:
        """Run performance-focused integration tests"""
        
        print("🏃‍♂️ Running Performance Integration Tests")
        
        return self.run_tests(
            test_pattern="performance or concurrent",
            verbose=True,
            coverage=False,  # Skip coverage for performance tests
            parallel=False   # Run sequentially for accurate timing
        )
    
    def run_smoke_tests(self) -> Dict:
        """Run smoke tests (quick validation)"""
        
        print("💨 Running Smoke Tests")
        
        # Run a subset of critical tests
        return self.run_tests(
            test_pattern="test_complete_document_processing_workflow or test_document_upload_api_workflow",
            verbose=True,
            coverage=False,
            parallel=False
        )
    
    def generate_report(self, output_file: str = "integration-test-report.json"):
        """Generate detailed test report"""
        
        if not self.test_results:
            print("❌ No test results to report")
            return
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_type': 'integration',
            'results': self.test_results,
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': os.getcwd()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Test report saved to: {output_file}")


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument(
        '--suite', 
        choices=['pipeline', 'api', 'database', 'storage', 'workflows', 'all'],
        default='all',
        help='Test suite to run'
    )
    parser.add_argument(
        '--pattern', 
        help='Test pattern to match'
    )
    parser.add_argument(
        '--performance', 
        action='store_true',
        help='Run performance tests'
    )
    parser.add_argument(
        '--smoke', 
        action='store_true',
        help='Run smoke tests only'
    )
    parser.add_argument(
        '--no-coverage', 
        action='store_true',
        help='Skip coverage reporting'
    )
    parser.add_argument(
        '--parallel', 
        action='store_true',
        help='Run tests in parallel'
    )
    parser.add_argument(
        '--report', 
        help='Generate report file'
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    # Run appropriate test suite
    if args.smoke:
        results = runner.run_smoke_tests()
    elif args.performance:
        results = runner.run_performance_tests()
    elif args.suite != 'all':
        results = runner.run_specific_test_suite(args.suite)
    else:
        results = runner.run_tests(
            test_pattern=args.pattern,
            coverage=not args.no_coverage,
            parallel=args.parallel
        )
    
    # Generate report if requested
    if args.report:
        runner.generate_report(args.report)
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()