"""
Load and stress testing runner.
Orchestrates all load testing scenarios and generates comprehensive reports.
"""

import asyncio
import time
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import psutil

# Import test classes
from .test_concurrent_document_processing import ConcurrentDocumentProcessor
from .test_multi_user_simulation import RealisticUserSimulator
from .test_database_load import DatabaseLoadTester
from .test_memory_resource_limits import MemoryStressTester
from .test_system_recovery import SystemRecoveryTester

class LoadTestOrchestrator:
    """Orchestrate comprehensive load and stress testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {
            "test_run_info": {
                "start_time": datetime.now().isoformat(),
                "config": config,
                "system_info": self._get_system_info()
            },
            "test_results": {}
        }
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
            "platform": sys.platform
        }
    
    async def run_concurrent_document_processing_tests(self) -> Dict[str, Any]:
        """Run concurrent document processing tests"""
        print("\n=== Running Concurrent Document Processing Tests ===")
        
        processor = ConcurrentDocumentProcessor(self.config["base_url"])
        
        test_scenarios = [
            {"name": "low_concurrency", "concurrent_uploads": 5, "iterations": 2},
            {"name": "medium_concurrency", "concurrent_uploads": 15, "iterations": 2},
            {"name": "high_concurrency", "concurrent_uploads": 25, "iterations": 1}
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            print(f"Running {scenario['name']} scenario...")
            try:
                result = await processor.run_concurrent_test(
                    concurrent_uploads=scenario["concurrent_uploads"],
                    iterations=scenario["iterations"]
                )
                results[scenario["name"]] = result
                print(f"✓ {scenario['name']}: {result['success_rate']:.1f}% success rate")
            except Exception as e:
                results[scenario["name"]] = {"error": str(e)}
                print(f"✗ {scenario['name']}: Failed with error: {e}")
        
        return results
    
    async def run_multi_user_simulation_tests(self) -> Dict[str, Any]:
        """Run multi-user simulation tests"""
        print("\n=== Running Multi-User Simulation Tests ===")
        
        simulator = RealisticUserSimulator(self.config["base_url"])
        
        test_scenarios = [
            {"name": "short_simulation", "duration": 5},
            {"name": "medium_simulation", "duration": 10},
            {"name": "extended_simulation", "duration": 15}
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            print(f"Running {scenario['name']} ({scenario['duration']} minutes)...")
            try:
                result = await simulator.run_simulation(duration_minutes=scenario["duration"])
                results[scenario["name"]] = result
                success_rate = result["simulation_summary"]["overall_success_rate"]
                print(f"✓ {scenario['name']}: {success_rate:.1f}% overall success rate")
            except Exception as e:
                results[scenario["name"]] = {"error": str(e)}
                print(f"✗ {scenario['name']}: Failed with error: {e}")
        
        return results
    
    async def run_database_load_tests(self) -> Dict[str, Any]:
        """Run database load tests"""
        print("\n=== Running Database Load Tests ===")
        
        db_tester = DatabaseLoadTester()
        
        try:
            # Setup test data
            await db_tester.setup_test_data(
                num_documents=100, 
                num_knowledge_points=1000, 
                num_cards=2000
            )
            
            test_scenarios = [
                {"name": "low_concurrency", "threads": 5, "operations": 20, "ratio": 0.8},
                {"name": "medium_concurrency", "threads": 15, "operations": 30, "ratio": 0.7},
                {"name": "high_concurrency", "threads": 25, "operations": 20, "ratio": 0.6},
                {"name": "write_heavy", "threads": 10, "operations": 25, "ratio": 0.3}
            ]
            
            results = {}
            
            for scenario in test_scenarios:
                print(f"Running database {scenario['name']} scenario...")
                try:
                    test_results = await db_tester.run_concurrent_operations(
                        num_threads=scenario["threads"],
                        operations_per_thread=scenario["operations"],
                        read_write_ratio=scenario["ratio"]
                    )
                    
                    analysis = db_tester.analyze_performance_results(test_results)
                    results[scenario["name"]] = analysis
                    
                    success_rate = analysis["summary"]["success_rate"]
                    avg_duration = analysis["summary"]["avg_operation_duration"]
                    print(f"✓ {scenario['name']}: {success_rate:.1f}% success, {avg_duration:.3f}s avg duration")
                    
                except Exception as e:
                    results[scenario["name"]] = {"error": str(e)}
                    print(f"✗ {scenario['name']}: Failed with error: {e}")
            
            return results
            
        finally:
            # Cleanup test data
            db_tester.cleanup_test_data()
    
    async def run_memory_resource_tests(self) -> Dict[str, Any]:
        """Run memory and resource limit tests"""
        print("\n=== Running Memory and Resource Tests ===")
        
        memory_tester = MemoryStressTester()
        
        test_scenarios = [
            {
                "name": "gradual_growth",
                "test_func": lambda: memory_tester.test_memory_growth(5, 30)
            },
            {
                "name": "concurrent_allocation", 
                "test_func": lambda: memory_tester.test_concurrent_memory_usage(3, 50)
            },
            {
                "name": "document_processing_memory",
                "test_func": lambda: memory_tester.test_document_processing_memory(150)
            }
        ]
        
        results = {}
        test_results = []
        
        for scenario in test_scenarios:
            print(f"Running memory {scenario['name']} test...")
            try:
                result = await scenario["test_func"]()
                test_results.append(result)
                
                results[scenario["name"]] = {
                    "success": result.success,
                    "peak_memory_mb": result.peak_resources.process_memory_mb,
                    "memory_leaked": result.memory_leaked,
                    "memory_leak_mb": result.memory_leak_mb,
                    "duration": result.duration
                }
                
                status = "✓" if result.success else "✗"
                print(f"{status} {scenario['name']}: Peak {result.peak_resources.process_memory_mb:.1f}MB")
                
            except Exception as e:
                results[scenario["name"]] = {"error": str(e)}
                print(f"✗ {scenario['name']}: Failed with error: {e}")
        
        # Add overall analysis
        if test_results:
            analysis = memory_tester.analyze_memory_test_results(test_results)
            results["overall_analysis"] = analysis
        
        return results
    
    async def run_system_recovery_tests(self) -> Dict[str, Any]:
        """Run system recovery tests"""
        print("\n=== Running System Recovery Tests ===")
        
        if not self.config.get("enable_recovery_tests", True):
            print("Recovery tests disabled in configuration")
            return {"disabled": True}
        
        recovery_tester = SystemRecoveryTester(self.config["base_url"])
        
        try:
            # Run a subset of recovery tests to avoid system instability
            limited_scenarios = [
                scenario for scenario in recovery_tester.failure_scenarios
                if scenario.severity in ["low", "medium"]
            ]
            
            results = {}
            test_results = []
            
            for scenario in limited_scenarios[:3]:  # Limit to 3 scenarios
                print(f"Testing recovery from {scenario.failure_type.value}...")
                try:
                    result = await recovery_tester.test_recovery_scenario(scenario)
                    test_results.append(result)
                    
                    results[scenario.failure_type.value] = {
                        "recovery_successful": result.recovery_successful,
                        "recovery_time": result.recovery_time,
                        "stable_after_recovery": result.system_stable_after_recovery,
                        "errors": result.error_messages
                    }
                    
                    status = "✓" if result.recovery_successful else "✗"
                    print(f"{status} {scenario.failure_type.value}: Recovery in {result.recovery_time:.1f}s")
                    
                except Exception as e:
                    results[scenario.failure_type.value] = {"error": str(e)}
                    print(f"✗ {scenario.failure_type.value}: Failed with error: {e}")
            
            # Add overall analysis
            if test_results:
                analysis = recovery_tester.analyze_recovery_results(test_results)
                results["overall_analysis"] = analysis
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all load and stress tests"""
        print("Starting comprehensive load and stress testing...")
        print(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        start_time = time.time()
        
        # Run test suites
        test_suites = [
            ("concurrent_document_processing", self.run_concurrent_document_processing_tests),
            ("multi_user_simulation", self.run_multi_user_simulation_tests),
            ("database_load", self.run_database_load_tests),
            ("memory_resource", self.run_memory_resource_tests),
            ("system_recovery", self.run_system_recovery_tests)
        ]
        
        for suite_name, test_func in test_suites:
            try:
                print(f"\n{'='*60}")
                suite_results = await test_func()
                self.results["test_results"][suite_name] = suite_results
            except Exception as e:
                print(f"Test suite {suite_name} failed: {e}")
                self.results["test_results"][suite_name] = {"error": str(e)}
        
        # Add summary
        self.results["test_run_info"]["end_time"] = datetime.now().isoformat()
        self.results["test_run_info"]["total_duration"] = time.time() - start_time
        
        return self.results
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive test report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"load_test_report_{timestamp}.json"
        
        # Write detailed JSON report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate summary report
        summary_file = output_file.replace('.json', '_summary.txt')
        with open(summary_file, 'w') as f:
            f.write("LOAD AND STRESS TESTING SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Test run info
            run_info = self.results["test_run_info"]
            f.write(f"Test Run: {run_info['start_time']} to {run_info['end_time']}\n")
            f.write(f"Duration: {run_info['total_duration']:.1f} seconds\n")
            f.write(f"System: {run_info['system_info']['cpu_count']} CPUs, "
                   f"{run_info['system_info']['memory_total_gb']:.1f}GB RAM\n\n")
            
            # Test results summary
            for suite_name, suite_results in self.results["test_results"].items():
                f.write(f"{suite_name.upper().replace('_', ' ')} TESTS:\n")
                f.write("-" * 30 + "\n")
                
                if "error" in suite_results:
                    f.write(f"  ERROR: {suite_results['error']}\n")
                else:
                    # Extract key metrics based on test type
                    if "overall_analysis" in suite_results:
                        analysis = suite_results["overall_analysis"]
                        if "summary" in analysis:
                            summary = analysis["summary"]
                            for key, value in summary.items():
                                f.write(f"  {key}: {value}\n")
                    else:
                        # Show individual test results
                        for test_name, test_result in suite_results.items():
                            if isinstance(test_result, dict) and "error" not in test_result:
                                f.write(f"  {test_name}: PASSED\n")
                            else:
                                f.write(f"  {test_name}: FAILED\n")
                
                f.write("\n")
        
        print(f"\nDetailed report saved to: {output_file}")
        print(f"Summary report saved to: {summary_file}")
        
        return output_file

async def main():
    """Main function to run load tests"""
    parser = argparse.ArgumentParser(description="Run load and stress tests")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for the application")
    parser.add_argument("--max-users", type=int, default=20,
                       help="Maximum concurrent users")
    parser.add_argument("--duration", type=int, default=10,
                       help="Test duration in minutes")
    parser.add_argument("--skip-recovery", action="store_true",
                       help="Skip recovery tests")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    config = {
        "base_url": args.base_url,
        "max_concurrent_users": args.max_users,
        "test_duration_minutes": args.duration,
        "memory_limit_mb": 1024,
        "cpu_threshold_percent": 80,
        "enable_recovery_tests": not args.skip_recovery
    }
    
    orchestrator = LoadTestOrchestrator(config)
    
    try:
        results = await orchestrator.run_all_tests()
        report_file = orchestrator.generate_report(args.output)
        
        print(f"\n{'='*60}")
        print("LOAD TESTING COMPLETED")
        print(f"{'='*60}")
        print(f"Report saved to: {report_file}")
        
        # Print quick summary
        total_suites = len(results["test_results"])
        failed_suites = sum(1 for suite in results["test_results"].values() 
                           if "error" in suite)
        
        print(f"Test suites: {total_suites - failed_suites}/{total_suites} passed")
        
        if failed_suites > 0:
            print("Some test suites failed. Check the detailed report for more information.")
            sys.exit(1)
        else:
            print("All test suites completed successfully!")
            
    except KeyboardInterrupt:
        print("\nLoad testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Load testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())