#!/usr/bin/env python3
"""
Comprehensive performance test runner for the document learning application.
This script runs both backend and frontend performance tests and generates reports.
"""

import asyncio
import sys
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import argparse

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

try:
    from backend.tests.performance.run_performance_tests import PerformanceTestRunner
except ImportError:
    print("Warning: Could not import backend performance test runner")
    PerformanceTestRunner = None


@dataclass
class PerformanceTestSuite:
    """Performance test suite configuration."""
    name: str
    type: str  # 'backend', 'frontend', 'integration'
    enabled: bool
    command: Optional[str] = None
    working_directory: Optional[str] = None
    timeout_seconds: int = 300


@dataclass
class PerformanceTestResult:
    """Results from a performance test suite."""
    suite_name: str
    suite_type: str
    start_time: float
    end_time: float
    duration: float
    exit_code: int
    stdout: str
    stderr: str
    success: bool
    metrics: Dict[str, Any]


class ComprehensivePerformanceRunner:
    """Run comprehensive performance tests across all components."""
    
    def __init__(self, config_file: str = "performance-test-config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.results: List[PerformanceTestResult] = []
        
        # Define test suites
        self.test_suites = [
            PerformanceTestSuite(
                name="Backend Document Processing",
                type="backend",
                enabled=self.config.get("backend_tests", {}).get("document_processing", {}).get("enabled", True),
                command="python backend/tests/performance/run_performance_tests.py --suite document_processing",
                timeout_seconds=600
            ),
            PerformanceTestSuite(
                name="Backend Search Performance",
                type="backend",
                enabled=self.config.get("backend_tests", {}).get("search_performance", {}).get("enabled", True),
                command="python backend/tests/performance/run_performance_tests.py --suite search_performance",
                timeout_seconds=300
            ),
            PerformanceTestSuite(
                name="Backend Memory Monitoring",
                type="backend",
                enabled=self.config.get("backend_tests", {}).get("memory_monitoring", {}).get("enabled", True),
                command="python backend/tests/performance/run_performance_tests.py --suite memory_monitoring",
                timeout_seconds=400
            ),
            PerformanceTestSuite(
                name="Backend Concurrent Users",
                type="backend",
                enabled=self.config.get("backend_tests", {}).get("concurrent_users", {}).get("enabled", True),
                command="python backend/tests/performance/run_performance_tests.py --suite concurrent_users",
                timeout_seconds=800
            ),
            PerformanceTestSuite(
                name="Frontend Performance",
                type="frontend",
                enabled=self.config.get("frontend_tests", {}).get("loading_performance", {}).get("enabled", True),
                command="npm test -- --run frontend/src/test/performance/frontend-performance.test.ts",
                working_directory="frontend",
                timeout_seconds=300
            ),
        ]
    
    def load_config(self) -> Dict[str, Any]:
        """Load performance test configuration."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            return config.get("performance_testing", {})
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_file} not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}")
            return {}
    
    async def run_test_suite(self, suite: PerformanceTestSuite) -> PerformanceTestResult:
        """Run a single performance test suite."""
        if not suite.enabled:
            print(f"⏭️  Skipping disabled suite: {suite.name}")
            return PerformanceTestResult(
                suite_name=suite.name,
                suite_type=suite.type,
                start_time=time.time(),
                end_time=time.time(),
                duration=0,
                exit_code=0,
                stdout="Suite disabled",
                stderr="",
                success=True,
                metrics={}
            )
        
        print(f"🚀 Running {suite.name}...")
        
        start_time = time.time()
        
        try:
            # Prepare command
            if not suite.command:
                raise ValueError(f"No command specified for suite {suite.name}")
            
            cmd_parts = suite.command.split()
            
            # Set working directory
            cwd = suite.working_directory if suite.working_directory else None
            if cwd:
                cwd = Path(cwd).resolve()
                if not cwd.exists():
                    raise FileNotFoundError(f"Working directory not found: {cwd}")
            
            # Run command
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=suite.timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Test suite {suite.name} timed out after {suite.timeout_seconds} seconds")
            
            end_time = time.time()
            duration = end_time - start_time
            
            stdout_str = stdout.decode('utf-8') if stdout else ""
            stderr_str = stderr.decode('utf-8') if stderr else ""
            
            success = process.returncode == 0
            
            # Extract metrics from output (simplified)
            metrics = self.extract_metrics_from_output(stdout_str, stderr_str)
            
            result = PerformanceTestResult(
                suite_name=suite.name,
                suite_type=suite.type,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                success=success,
                metrics=metrics
            )
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {status} - Duration: {duration:.2f}s")
            
            if not success and stderr_str:
                print(f"  Error: {stderr_str[:200]}...")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"  ❌ FAILED - Error: {str(e)}")
            
            return PerformanceTestResult(
                suite_name=suite.name,
                suite_type=suite.type,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                exit_code=1,
                stdout="",
                stderr=str(e),
                success=False,
                metrics={}
            )
    
    def extract_metrics_from_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract performance metrics from test output."""
        metrics = {}
        
        # Look for common performance indicators in output
        lines = (stdout + "\n" + stderr).split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract timing information
            if "time:" in line.lower() and "ms" in line.lower():
                try:
                    # Simple regex-like extraction
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "ms" in part:
                            time_value = float(part.replace("ms", "").replace(",", ""))
                            metric_name = "_".join(parts[:i]).lower().replace(":", "")
                            metrics[f"{metric_name}_ms"] = time_value
                            break
                except (ValueError, IndexError):
                    continue
            
            # Extract memory information
            if "memory:" in line.lower() and "mb" in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "mb" in part.lower():
                            memory_value = float(part.lower().replace("mb", "").replace(",", ""))
                            metric_name = "_".join(parts[:i]).lower().replace(":", "")
                            metrics[f"{metric_name}_mb"] = memory_value
                            break
                except (ValueError, IndexError):
                    continue
            
            # Extract success/failure counts
            if "passed:" in line.lower():
                try:
                    passed_count = int(line.lower().split("passed:")[1].strip().split()[0])
                    metrics["tests_passed"] = passed_count
                except (ValueError, IndexError):
                    continue
            
            if "failed:" in line.lower():
                try:
                    failed_count = int(line.lower().split("failed:")[1].strip().split()[0])
                    metrics["tests_failed"] = failed_count
                except (ValueError, IndexError):
                    continue
        
        return metrics
    
    async def run_all_suites(self, suite_filter: Optional[str] = None) -> List[PerformanceTestResult]:
        """Run all enabled performance test suites."""
        print("🎯 Starting Comprehensive Performance Testing")
        print("=" * 80)
        
        # Filter suites if requested
        suites_to_run = self.test_suites
        if suite_filter:
            suites_to_run = [s for s in self.test_suites if suite_filter.lower() in s.name.lower() or suite_filter.lower() in s.type.lower()]
        
        # Run suites
        results = []
        for suite in suites_to_run:
            result = await self.run_test_suite(suite)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def generate_report(self, results: List[PerformanceTestResult]) -> Dict[str, Any]:
        """Generate comprehensive performance test report."""
        total_duration = sum(r.duration for r in results)
        successful_suites = [r for r in results if r.success]
        failed_suites = [r for r in results if not r.success]
        
        # Aggregate metrics
        all_metrics = {}
        for result in results:
            for metric_name, metric_value in result.metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(metric_value)
        
        # Calculate summary statistics
        summary_metrics = {}
        for metric_name, values in all_metrics.items():
            if values:
                summary_metrics[metric_name] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values)
                }
        
        report = {
            "timestamp": time.time(),
            "total_suites": len(results),
            "successful_suites": len(successful_suites),
            "failed_suites": len(failed_suites),
            "total_duration_seconds": total_duration,
            "success_rate": len(successful_suites) / len(results) if results else 0,
            "suite_results": [asdict(result) for result in results],
            "summary_metrics": summary_metrics,
            "system_info": self.get_system_info()
        }
        
        return report
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for the report."""
        try:
            import psutil
            
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_free_gb": psutil.disk_usage('/').free / (1024**3),
                "python_version": sys.version,
                "platform": sys.platform,
            }
        except ImportError:
            return {
                "python_version": sys.version,
                "platform": sys.platform,
            }
    
    def print_summary(self, results: List[PerformanceTestResult]):
        """Print performance test summary."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        successful_suites = [r for r in results if r.success]
        failed_suites = [r for r in results if not r.success]
        total_duration = sum(r.duration for r in results)
        
        print(f"\nExecution Summary:")
        print(f"  Total Suites: {len(results)}")
        print(f"  Successful: {len(successful_suites)}")
        print(f"  Failed: {len(failed_suites)}")
        print(f"  Success Rate: {len(successful_suites)/len(results)*100:.1f}%")
        print(f"  Total Duration: {total_duration:.2f} seconds")
        
        print(f"\nSuite Results:")
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.suite_name} ({result.suite_type}): {result.duration:.2f}s")
            
            if result.metrics:
                key_metrics = []
                for key, value in result.metrics.items():
                    if isinstance(value, (int, float)):
                        key_metrics.append(f"{key}: {value}")
                if key_metrics:
                    print(f"    Metrics: {', '.join(key_metrics[:3])}")
        
        if failed_suites:
            print(f"\nFailed Suites Details:")
            for result in failed_suites:
                print(f"  ❌ {result.suite_name}:")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}...")
        
        overall_status = "PASSED" if len(failed_suites) == 0 else "FAILED"
        print(f"\nOverall Status: {overall_status}")
        print("=" * 80)
    
    def save_report(self, report: Dict[str, Any], filename: str):
        """Save performance test report to file."""
        output_dir = Path("performance_reports")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / filename
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Performance report saved to: {output_file}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive performance tests")
    parser.add_argument(
        "--filter",
        help="Filter test suites by name or type (e.g., 'backend', 'frontend', 'search')"
    )
    parser.add_argument(
        "--config",
        default="performance-test-config.json",
        help="Configuration file path"
    )
    parser.add_argument(
        "--output",
        default=f"performance_report_{int(time.time())}.json",
        help="Output report filename"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        runner = ComprehensivePerformanceRunner(config_file=args.config)
        
        # Run performance tests
        results = await runner.run_all_suites(suite_filter=args.filter)
        
        # Generate and print report
        report = runner.generate_report(results)
        runner.print_summary(results)
        
        # Save report
        runner.save_report(report, args.output)
        
        # Exit with appropriate code
        failed_count = len([r for r in results if not r.success])
        sys.exit(failed_count)
        
    except KeyboardInterrupt:
        print("\n⚠️  Performance tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())