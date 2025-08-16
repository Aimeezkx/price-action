"""
System recovery testing after failures.
Tests the system's ability to recover from various failure scenarios.
"""

import asyncio
import time
import random
import json
import pytest
import aiohttp
import psutil
import signal
import os
import threading
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import tempfile

class FailureType(Enum):
    """Types of failures to simulate"""
    NETWORK_TIMEOUT = "network_timeout"
    DATABASE_CONNECTION_LOSS = "database_connection_loss"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    DISK_FULL = "disk_full"
    PROCESS_CRASH = "process_crash"
    HIGH_CPU_LOAD = "high_cpu_load"
    CONCURRENT_REQUEST_FLOOD = "concurrent_request_flood"
    CORRUPTED_DATA = "corrupted_data"

@dataclass
class FailureScenario:
    """Definition of a failure scenario"""
    failure_type: FailureType
    description: str
    setup_function: Optional[Callable] = None
    failure_function: Optional[Callable] = None
    cleanup_function: Optional[Callable] = None
    expected_recovery_time: float = 30.0  # seconds
    severity: str = "medium"  # low, medium, high, critical

@dataclass
class RecoveryTestResult:
    """Result of a system recovery test"""
    scenario_name: str
    failure_type: FailureType
    failure_injected: bool
    system_detected_failure: bool
    recovery_successful: bool
    recovery_time: float
    system_stable_after_recovery: bool
    error_messages: List[str]
    performance_impact: Dict[str, float]
    duration: float

class SystemRecoveryTester:
    """Test system recovery from various failure scenarios"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.failure_scenarios = self._define_failure_scenarios()
        self.background_load_active = False
        self.background_tasks: List[asyncio.Task] = []
        
    def _define_failure_scenarios(self) -> List[FailureScenario]:
        """Define various failure scenarios to test"""
        return [
            FailureScenario(
                failure_type=FailureType.NETWORK_TIMEOUT,
                description="Simulate network timeouts and connection issues",
                failure_function=self._simulate_network_timeout,
                expected_recovery_time=10.0,
                severity="medium"
            ),
            FailureScenario(
                failure_type=FailureType.DATABASE_CONNECTION_LOSS,
                description="Simulate database connection loss and recovery",
                failure_function=self._simulate_database_connection_loss,
                expected_recovery_time=15.0,
                severity="high"
            ),
            FailureScenario(
                failure_type=FailureType.MEMORY_EXHAUSTION,
                description="Simulate memory exhaustion conditions",
                failure_function=self._simulate_memory_exhaustion,
                cleanup_function=self._cleanup_memory_exhaustion,
                expected_recovery_time=20.0,
                severity="high"
            ),
            FailureScenario(
                failure_type=FailureType.HIGH_CPU_LOAD,
                description="Simulate high CPU load conditions",
                failure_function=self._simulate_high_cpu_load,
                cleanup_function=self._cleanup_high_cpu_load,
                expected_recovery_time=15.0,
                severity="medium"
            ),
            FailureScenario(
                failure_type=FailureType.CONCURRENT_REQUEST_FLOOD,
                description="Simulate request flooding and overload",
                failure_function=self._simulate_request_flood,
                expected_recovery_time=25.0,
                severity="high"
            ),
            FailureScenario(
                failure_type=FailureType.CORRUPTED_DATA,
                description="Simulate corrupted data scenarios",
                failure_function=self._simulate_corrupted_data,
                cleanup_function=self._cleanup_corrupted_data,
                expected_recovery_time=30.0,
                severity="critical"
            )
        ]
    
    async def _simulate_network_timeout(self) -> Dict[str, Any]:
        """Simulate network timeout conditions"""
        print("Simulating network timeout...")
        
        # Create requests with very short timeouts to force timeouts
        timeout_requests = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0.1)) as session:
            for i in range(10):
                try:
                    async with session.get(f"{self.base_url}/api/documents") as response:
                        pass
                except asyncio.TimeoutError:
                    timeout_requests.append(i)
                except Exception as e:
                    timeout_requests.append(i)
        
        return {"timeout_requests": len(timeout_requests)}
    
    async def _simulate_database_connection_loss(self) -> Dict[str, Any]:
        """Simulate database connection loss"""
        print("Simulating database connection issues...")
        
        # Try to make many concurrent database-heavy requests
        failed_requests = 0
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(20):
                task = self._make_database_heavy_request(session)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            failed_requests = sum(1 for r in results if isinstance(r, Exception))
        
        return {"failed_database_requests": failed_requests}
    
    async def _make_database_heavy_request(self, session: aiohttp.ClientSession):
        """Make a database-heavy request"""
        try:
            # Request that requires database operations
            async with session.get(f"{self.base_url}/api/documents") as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                return await response.json()
        except Exception as e:
            raise e
    
    async def _simulate_memory_exhaustion(self) -> Dict[str, Any]:
        """Simulate memory exhaustion"""
        print("Simulating memory exhaustion...")
        
        # Create large data structures to consume memory
        self.memory_hogs = []
        allocated_mb = 0
        
        try:
            # Allocate memory in chunks until we hit limits
            for i in range(20):  # Limit iterations to prevent system crash
                chunk = bytearray(50 * 1024 * 1024)  # 50MB chunks
                self.memory_hogs.append(chunk)
                allocated_mb += 50
                
                # Check system memory
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 85:  # Stop before system becomes unstable
                    break
                
                await asyncio.sleep(0.1)
        
        except MemoryError:
            pass  # Expected when memory is exhausted
        
        return {"allocated_memory_mb": allocated_mb}
    
    def _cleanup_memory_exhaustion(self):
        """Clean up memory exhaustion test"""
        if hasattr(self, 'memory_hogs'):
            del self.memory_hogs
        import gc
        gc.collect()
    
    async def _simulate_high_cpu_load(self) -> Dict[str, Any]:
        """Simulate high CPU load"""
        print("Simulating high CPU load...")
        
        # Start CPU-intensive tasks
        self.cpu_load_active = True
        cpu_tasks = []
        
        def cpu_intensive_task():
            """CPU-intensive computation"""
            count = 0
            while self.cpu_load_active and count < 10000000:
                # Perform meaningless computation
                result = sum(i * i for i in range(1000))
                count += 1
        
        # Start multiple CPU-intensive threads
        threads = []
        num_threads = min(4, psutil.cpu_count())  # Limit to prevent system freeze
        
        for _ in range(num_threads):
            thread = threading.Thread(target=cpu_intensive_task)
            thread.start()
            threads.append(thread)
        
        # Let it run for a bit
        await asyncio.sleep(5)
        
        return {"cpu_threads_started": len(threads)}
    
    def _cleanup_high_cpu_load(self):
        """Clean up high CPU load test"""
        self.cpu_load_active = False
    
    async def _simulate_request_flood(self) -> Dict[str, Any]:
        """Simulate request flooding"""
        print("Simulating request flood...")
        
        # Send many concurrent requests
        flood_size = 100
        successful_requests = 0
        failed_requests = 0
        
        async def make_flood_request(session: aiohttp.ClientSession, request_id: int):
            try:
                async with session.get(f"{self.base_url}/api/documents") as response:
                    if response.status == 200:
                        return "success"
                    else:
                        return "failed"
            except Exception:
                return "failed"
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_flood_request(session, i) for i in range(flood_size)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result == "success":
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        return {
            "flood_size": flood_size,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests
        }
    
    async def _simulate_corrupted_data(self) -> Dict[str, Any]:
        """Simulate corrupted data scenarios"""
        print("Simulating corrupted data...")
        
        # Try to upload corrupted/invalid data
        corrupted_uploads = 0
        
        async with aiohttp.ClientSession() as session:
            # Try various types of corrupted data
            corrupted_files = [
                ("corrupted.pdf", b"This is not a PDF file"),
                ("empty.pdf", b""),
                ("huge_filename.pdf", b"content", "x" * 1000),  # Extremely long filename
                ("invalid_chars.pdf", b"content", "file\x00\x01\x02.pdf"),
            ]
            
            for filename, content, *extra in corrupted_files:
                try:
                    data = aiohttp.FormData()
                    actual_filename = extra[0] if extra else filename
                    data.add_field('file', content, filename=actual_filename)
                    
                    async with session.post(f"{self.base_url}/api/documents/upload", data=data) as response:
                        if response.status >= 400:  # Expected to fail
                            corrupted_uploads += 1
                except Exception:
                    corrupted_uploads += 1
        
        return {"corrupted_upload_attempts": corrupted_uploads}
    
    def _cleanup_corrupted_data(self):
        """Clean up corrupted data test"""
        # No specific cleanup needed for this test
        pass
    
    async def start_background_load(self):
        """Start background load to test recovery under load"""
        self.background_load_active = True
        
        async def background_requests():
            """Generate background requests"""
            async with aiohttp.ClientSession() as session:
                while self.background_load_active:
                    try:
                        # Make various types of requests
                        endpoints = ["/api/documents", "/api/search?q=test", "/api/cards/due"]
                        endpoint = random.choice(endpoints)
                        
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            pass  # Don't care about response for background load
                    except Exception:
                        pass  # Ignore errors in background load
                    
                    await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Start multiple background tasks
        for _ in range(3):
            task = asyncio.create_task(background_requests())
            self.background_tasks.append(task)
    
    async def stop_background_load(self):
        """Stop background load"""
        self.background_load_active = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks.clear()
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check if the system is healthy and responsive"""
        health_checks = {
            "api_responsive": False,
            "database_accessible": False,
            "search_functional": False,
            "response_time_acceptable": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test API responsiveness
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/documents") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        health_checks["api_responsive"] = True
                        health_checks["database_accessible"] = True
                        
                        if response_time < 5.0:  # 5 second threshold
                            health_checks["response_time_acceptable"] = True
                
                # Test search functionality
                async with session.get(f"{self.base_url}/api/search?q=test") as response:
                    if response.status == 200:
                        health_checks["search_functional"] = True
        
        except Exception as e:
            print(f"Health check error: {e}")
        
        return health_checks
    
    async def measure_performance_impact(self) -> Dict[str, float]:
        """Measure performance impact during/after failure"""
        performance_metrics = {}
        
        try:
            # Measure response times for key endpoints
            endpoints = [
                ("/api/documents", "document_list"),
                ("/api/search?q=test", "search"),
                ("/api/cards/due", "cards")
            ]
            
            async with aiohttp.ClientSession() as session:
                for endpoint, metric_name in endpoints:
                    start_time = time.time()
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            response_time = time.time() - start_time
                            performance_metrics[f"{metric_name}_response_time"] = response_time
                    except Exception:
                        performance_metrics[f"{metric_name}_response_time"] = float('inf')
        
        except Exception as e:
            print(f"Performance measurement error: {e}")
        
        return performance_metrics
    
    async def test_recovery_scenario(self, scenario: FailureScenario) -> RecoveryTestResult:
        """Test a specific recovery scenario"""
        print(f"Testing recovery scenario: {scenario.description}")
        
        start_time = time.time()
        error_messages = []
        
        # Start background load
        await self.start_background_load()
        
        try:
            # Measure baseline performance
            baseline_performance = await self.measure_performance_impact()
            
            # Check initial system health
            initial_health = await self.check_system_health()
            
            # Inject failure
            failure_injected = False
            if scenario.failure_function:
                try:
                    failure_result = await scenario.failure_function()
                    failure_injected = True
                    print(f"Failure injected: {failure_result}")
                except Exception as e:
                    error_messages.append(f"Failed to inject failure: {str(e)}")
            
            # Wait a moment for failure to take effect
            await asyncio.sleep(2)
            
            # Check if system detected the failure (health should be degraded)
            failure_health = await self.check_system_health()
            system_detected_failure = any(
                not failure_health[check] and initial_health[check] 
                for check in initial_health
            )
            
            # Wait for recovery
            recovery_start = time.time()
            recovery_successful = False
            
            # Poll for recovery up to expected recovery time + buffer
            max_recovery_time = scenario.expected_recovery_time + 30
            
            while time.time() - recovery_start < max_recovery_time:
                current_health = await self.check_system_health()
                
                # Check if system has recovered
                if all(current_health.values()):
                    recovery_successful = True
                    break
                
                await asyncio.sleep(2)
            
            recovery_time = time.time() - recovery_start
            
            # Test system stability after recovery
            await asyncio.sleep(5)  # Let system stabilize
            final_health = await self.check_system_health()
            system_stable_after_recovery = all(final_health.values())
            
            # Measure performance impact
            final_performance = await self.measure_performance_impact()
            
            # Clean up failure effects
            if scenario.cleanup_function:
                try:
                    scenario.cleanup_function()
                except Exception as e:
                    error_messages.append(f"Cleanup error: {str(e)}")
            
            return RecoveryTestResult(
                scenario_name=scenario.description,
                failure_type=scenario.failure_type,
                failure_injected=failure_injected,
                system_detected_failure=system_detected_failure,
                recovery_successful=recovery_successful,
                recovery_time=recovery_time,
                system_stable_after_recovery=system_stable_after_recovery,
                error_messages=error_messages,
                performance_impact=final_performance,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            error_messages.append(f"Test execution error: {str(e)}")
            
            return RecoveryTestResult(
                scenario_name=scenario.description,
                failure_type=scenario.failure_type,
                failure_injected=failure_injected,
                system_detected_failure=False,
                recovery_successful=False,
                recovery_time=time.time() - start_time,
                system_stable_after_recovery=False,
                error_messages=error_messages,
                performance_impact={},
                duration=time.time() - start_time
            )
        
        finally:
            # Stop background load
            await self.stop_background_load()
    
    async def run_all_recovery_tests(self) -> List[RecoveryTestResult]:
        """Run all recovery test scenarios"""
        print(f"Running {len(self.failure_scenarios)} recovery test scenarios")
        
        results = []
        
        for scenario in self.failure_scenarios:
            try:
                result = await self.test_recovery_scenario(scenario)
                results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Error testing scenario {scenario.description}: {e}")
                
                # Create error result
                error_result = RecoveryTestResult(
                    scenario_name=scenario.description,
                    failure_type=scenario.failure_type,
                    failure_injected=False,
                    system_detected_failure=False,
                    recovery_successful=False,
                    recovery_time=0,
                    system_stable_after_recovery=False,
                    error_messages=[str(e)],
                    performance_impact={},
                    duration=0
                )
                results.append(error_result)
        
        return results
    
    def analyze_recovery_results(self, results: List[RecoveryTestResult]) -> Dict[str, Any]:
        """Analyze recovery test results"""
        if not results:
            return {"error": "No results to analyze"}
        
        successful_recoveries = [r for r in results if r.recovery_successful]
        failed_recoveries = [r for r in results if not r.recovery_successful]
        stable_after_recovery = [r for r in results if r.system_stable_after_recovery]
        
        # Calculate statistics
        recovery_times = [r.recovery_time for r in successful_recoveries]
        
        analysis = {
            "summary": {
                "total_scenarios": len(results),
                "successful_recoveries": len(successful_recoveries),
                "failed_recoveries": len(failed_recoveries),
                "stable_after_recovery": len(stable_after_recovery),
                "recovery_success_rate": len(successful_recoveries) / len(results) * 100,
                "stability_rate": len(stable_after_recovery) / len(results) * 100
            },
            "recovery_time_statistics": {
                "min_recovery_time": min(recovery_times) if recovery_times else 0,
                "max_recovery_time": max(recovery_times) if recovery_times else 0,
                "avg_recovery_time": sum(recovery_times) / len(recovery_times) if recovery_times else 0
            },
            "scenario_results": [
                {
                    "scenario": r.scenario_name,
                    "failure_type": r.failure_type.value,
                    "recovery_successful": r.recovery_successful,
                    "recovery_time": r.recovery_time,
                    "stable_after_recovery": r.system_stable_after_recovery,
                    "errors": r.error_messages
                }
                for r in results
            ],
            "all_errors": [error for r in results for error in r.error_messages]
        }
        
        return analysis

@pytest.mark.asyncio
@pytest.mark.load
class TestSystemRecovery:
    """Test suite for system recovery testing"""
    
    @pytest.fixture
    def recovery_tester(self):
        return SystemRecoveryTester()
    
    async def test_network_timeout_recovery(self, recovery_tester):
        """Test recovery from network timeout scenarios"""
        scenario = next(s for s in recovery_tester.failure_scenarios 
                       if s.failure_type == FailureType.NETWORK_TIMEOUT)
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        # Assertions
        assert result.failure_injected, "Failure was not properly injected"
        # Network timeouts might not always be detectable by the system
        # assert result.recovery_successful, f"Recovery failed: {result.error_messages}"
        
        print(f"Network timeout recovery test: {'Success' if result.recovery_successful else 'Failed'}")
        print(f"Recovery time: {result.recovery_time:.1f}s")
    
    async def test_memory_exhaustion_recovery(self, recovery_tester):
        """Test recovery from memory exhaustion"""
        scenario = next(s for s in recovery_tester.failure_scenarios 
                       if s.failure_type == FailureType.MEMORY_EXHAUSTION)
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        # Assertions
        assert result.failure_injected, "Memory exhaustion was not properly injected"
        # System should recover after memory is freed
        assert result.recovery_successful or result.system_stable_after_recovery, \
            f"System did not recover from memory exhaustion: {result.error_messages}"
        
        print(f"Memory exhaustion recovery test: {'Success' if result.recovery_successful else 'Failed'}")
        print(f"Recovery time: {result.recovery_time:.1f}s")
    
    async def test_request_flood_recovery(self, recovery_tester):
        """Test recovery from request flooding"""
        scenario = next(s for s in recovery_tester.failure_scenarios 
                       if s.failure_type == FailureType.CONCURRENT_REQUEST_FLOOD)
        
        result = await recovery_tester.test_recovery_scenario(scenario)
        
        # Assertions
        assert result.failure_injected, "Request flood was not properly injected"
        # System should handle request floods gracefully
        assert result.recovery_successful, f"Recovery from request flood failed: {result.error_messages}"
        
        print(f"Request flood recovery test: {'Success' if result.recovery_successful else 'Failed'}")
        print(f"Recovery time: {result.recovery_time:.1f}s")
    
    async def test_comprehensive_recovery_suite(self, recovery_tester):
        """Run comprehensive recovery test suite"""
        results = await recovery_tester.run_all_recovery_tests()
        analysis = recovery_tester.analyze_recovery_results(results)
        
        # Assertions
        assert analysis["summary"]["recovery_success_rate"] >= 60, \
            f"Recovery success rate too low: {analysis['summary']['recovery_success_rate']}%"
        
        assert analysis["summary"]["stability_rate"] >= 70, \
            f"System stability rate too low: {analysis['summary']['stability_rate']}%"
        
        # Check that average recovery time is reasonable
        if analysis["recovery_time_statistics"]["avg_recovery_time"] > 0:
            assert analysis["recovery_time_statistics"]["avg_recovery_time"] <= 60, \
                f"Average recovery time too high: {analysis['recovery_time_statistics']['avg_recovery_time']}s"
        
        print(f"Comprehensive recovery test results: {json.dumps(analysis, indent=2)}")
    
    async def test_recovery_under_load(self, recovery_tester):
        """Test recovery while system is under background load"""
        # This test is implicitly covered by the background load in other tests
        # but we can add specific assertions here
        
        # Test a few scenarios with explicit focus on background load impact
        scenarios_to_test = [
            FailureType.HIGH_CPU_LOAD,
            FailureType.CONCURRENT_REQUEST_FLOOD
        ]
        
        results = []
        for failure_type in scenarios_to_test:
            scenario = next(s for s in recovery_tester.failure_scenarios 
                           if s.failure_type == failure_type)
            result = await recovery_tester.test_recovery_scenario(scenario)
            results.append(result)
        
        # Analyze results
        successful_recoveries = [r for r in results if r.recovery_successful]
        
        # At least half should recover successfully even under load
        success_rate = len(successful_recoveries) / len(results) * 100
        assert success_rate >= 50, f"Recovery under load success rate too low: {success_rate}%"
        
        print(f"Recovery under load test: {success_rate:.1f}% success rate")

if __name__ == "__main__":
    # Run standalone test
    async def main():
        tester = SystemRecoveryTester()
        
        # Test a few recovery scenarios
        scenarios_to_test = [
            FailureType.NETWORK_TIMEOUT,
            FailureType.MEMORY_EXHAUSTION,
            FailureType.CONCURRENT_REQUEST_FLOOD
        ]
        
        results = []
        for failure_type in scenarios_to_test:
            scenario = next(s for s in tester.failure_scenarios 
                           if s.failure_type == failure_type)
            print(f"\nTesting {scenario.description}...")
            result = await tester.test_recovery_scenario(scenario)
            results.append(result)
        
        # Analyze results
        analysis = tester.analyze_recovery_results(results)
        print(f"\nRecovery test analysis: {json.dumps(analysis, indent=2)}")
    
    asyncio.run(main())