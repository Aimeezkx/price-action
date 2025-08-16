#!/usr/bin/env python3
"""
Performance test runner for comprehensive benchmarking.
"""

import asyncio
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

import pytest
import psutil


@dataclass
class PerformanceTestSuite:
    """Configuration for performance test suite."""
    name: str
    test_modules: List[str]
    thresholds: Dict[str, Any]
    enabled: bool = True


@dataclass
class PerformanceReport:
    """Performance test report."""
    suite_name: str
    start_time: float
    end_time: float
    duration: float
    tests_run: int
    tests_passed: int
    tests_failed: int
    system_info: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    overall_status: str


class PerformanceTestRunner:
    """Run and manage performance tests."""
    
    def __init__(self):
        self.test_suites = {
            "document_processing": PerformanceTestSuite(
                name="Document Processing Performance",
                test_modules=[
                    "backend/tests/performance/test_document_processing_performance.py"
                ],
                thresholds={
                    "small_doc_time": 15.0,
                    "medium_doc_time": 45.0,
                    "large_doc_time": 120.0,
                    "memory_limit": 500.0,
                }
            ),
            "search_performance": PerformanceTestSuite(
                name="Search Performance",
                test_modules=[
                    "backend/tests/performance/test_search_performance.py"
                ],
                thresholds={
                    "response_time": 0.5,
                    "memory_limit": 100.0,
                }
            ),
            "memory_monitoring": PerformanceTestSuite(
                name="Memory Monitoring",
                test_modules=[
                    "backend/tests/performance/test_memory_monitoring.py"
                ],
                thresholds={
                    "memory_limit": 500.0,
                    "memory_leak_threshold": 50.0,
                }
            ),
            "concurrent_users": PerformanceTestSuite(
                name="Concurrent Users",
                test_modules=[
                    "backend/tests/performance/test_concurrent_users.py"
                ],
                thresholds={
                    "response_time_p95": 2.0,
                    "error_rate": 0.05,
                }
            ),
        }
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for the report."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage": {
                "total_gb": psutil.disk_usage('/').total / (1024**3),
                "free_gb": psutil.disk_usage('/').free / (1024**3),
            },
            "python_version": sys.version,
            "platform": sys.platform,
        }
    
    def run_test_suite(self, suite_name: str, verbose: bool = False) -> PerformanceReport:
        """Run a specific performance test suite."""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite = self.test_suites[suite_name]
        if not suite.enabled:
            print(f"Test suite '{suite_name}' is disabled")
            return None
        
        print(f"\n{'='*60}")
        print(f"Running Performance Test Suite: {suite.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        system_info = self.get_system_info()
        
        # Prepare pytest arguments
        pytest_args = [
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            "-x",  # Stop on first failure for performance tests
        ]
        
        # Add test modules
        pytest_args.extend(suite.test_modules)
        
        # Run tests
        try:
            exit_code = pytest.main(pytest_args)
            tests_passed = exit_code == 0
            
        except Exception as e:
            print(f"Error running test suite: {e}")
            tests_passed = False
            exit_code = 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Create report
        report = PerformanceReport(
            suite_name=suite.name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            tests_run=1,  # Simplified for now
            tests_passed=1 if tests_passed else 0,
            tests_failed=0 if tests_passed else 1,
            system_info=system_info,
            test_results=[],  # Would be populated with detailed results
            overall_status="PASSED" if tests_passed else "FAILED"
        )
        
        print(f"\nTest Suite Results:")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Status: {report.overall_status}")
        
        return report
    
    def run_all_suites(self, verbose: bool = False) -> List[PerformanceReport]:
        """Run all enabled performance test suites."""
        reports = []
        
        print(f"\n{'='*80}")
        print("PERFORMANCE TEST SUITE EXECUTION")
        print(f"{'='*80}")
        
        for suite_name, suite in self.test_suites.items():
            if suite.enabled:
                try:
                    report = self.run_test_suite(suite_name, verbose)
                    if report:
                        reports.append(report)
                except Exception as e:
                    print(f"Failed to run suite {suite_name}: {e}")
        
        # Print summary
        self.print_summary(reports)
        
        return reports
    
    def print_summary(self, reports: List[PerformanceReport]):
        """Print summary of all test results."""
        print(f"\n{'='*80}")
        print("PERFORMANCE TEST SUMMARY")
        print(f"{'='*80}")
        
        total_duration = sum(r.duration for r in reports)
        total_passed = sum(r.tests_passed for r in reports)
        total_failed = sum(r.tests_failed for r in reports)
        
        print(f"Total Suites Run: {len(reports)}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Tests Passed: {total_passed}")
        print(f"Tests Failed: {total_failed}")
        
        print(f"\nSuite Results:")
        for report in reports:
            status_symbol = "✓" if report.overall_status == "PASSED" else "✗"
            print(f"  {status_symbol} {report.suite_name}: {report.overall_status} ({report.duration:.2f}s)")
        
        overall_status = "PASSED" if total_failed == 0 else "FAILED"
        print(f"\nOverall Status: {overall_status}")
        
        if reports:
            # Print system info from first report
            system_info = reports[0].system_info
            print(f"\nSystem Information:")
            print(f"  CPU Cores: {system_info['cpu_count']}")
            print(f"  Memory: {system_info['memory_total_gb']:.1f}GB total, {system_info['memory_available_gb']:.1f}GB available")
            print(f"  Platform: {system_info['platform']}")
    
    def save_report(self, reports: List[PerformanceReport], output_file: str):
        """Save performance test reports to JSON file."""
        report_data = {
            "timestamp": time.time(),
            "reports": [asdict(report) for report in reports]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nPerformance report saved to: {output_file}")


def main():
    """Main entry point for performance test runner."""
    parser = argparse.ArgumentParser(description="Run performance tests")
    parser.add_argument(
        "--suite", 
        choices=["document_processing", "search_performance", "memory_monitoring", "concurrent_users", "all"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--output", "-o",
        default="performance_report.json",
        help="Output file for performance report"
    )
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner()
    
    try:
        if args.suite == "all":
            reports = runner.run_all_suites(verbose=args.verbose)
        else:
            report = runner.run_test_suite(args.suite, verbose=args.verbose)
            reports = [report] if report else []
        
        if reports:
            runner.save_report(reports, args.output)
        
        # Exit with appropriate code
        failed_reports = [r for r in reports if r.overall_status == "FAILED"]
        sys.exit(len(failed_reports))
        
    except KeyboardInterrupt:
        print("\nPerformance tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running performance tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()