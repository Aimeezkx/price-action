#!/usr/bin/env python3
"""
Test script to verify the performance testing framework is working correctly.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

try:
    from backend.tests.performance.conftest import PerformanceMonitor, BenchmarkResult
    print("✅ Successfully imported performance monitoring components")
except ImportError as e:
    print(f"❌ Failed to import performance components: {e}")
    sys.exit(1)


async def test_performance_monitor():
    """Test the performance monitor functionality."""
    print("\n🔍 Testing Performance Monitor...")
    
    monitor = PerformanceMonitor()
    
    # Test basic monitoring
    monitor.start_monitoring()
    
    # Simulate some work
    await asyncio.sleep(0.5)
    
    # Sample metrics
    for _ in range(5):
        monitor.sample_metrics()
        await asyncio.sleep(0.1)
    
    metrics = monitor.stop_monitoring()
    
    print(f"  Execution time: {metrics.execution_time:.3f}s")
    print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
    print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
    print(f"  CPU usage: {metrics.cpu_usage_percent:.2f}%")
    print(f"  Success: {metrics.success}")
    
    # Validate results
    assert metrics.execution_time > 0.4, "Execution time should be at least 0.4s"
    assert metrics.execution_time < 1.5, "Execution time should be less than 1.5s"  # Allow more time for system variations
    assert metrics.peak_memory_mb > 0, "Peak memory should be positive"
    
    print("✅ Performance monitor test passed")


async def test_benchmark_result():
    """Test benchmark result creation."""
    print("\n📊 Testing Benchmark Result...")
    
    # Create mock metrics
    from backend.tests.performance.conftest import PerformanceMetrics
    
    metrics = PerformanceMetrics(
        execution_time=0.5,
        memory_usage_mb=50.0,
        cpu_usage_percent=25.0,
        peak_memory_mb=75.0,
        success=True
    )
    
    # Create benchmark result
    result = BenchmarkResult(
        test_name="test_benchmark",
        metrics=metrics,
        threshold_passed=True,
        threshold_values={"max_time": 1.0, "max_memory": 100.0}
    )
    
    print(f"  Test name: {result.test_name}")
    print(f"  Threshold passed: {result.threshold_passed}")
    print(f"  Execution time: {result.metrics.execution_time:.3f}s")
    print(f"  Memory usage: {result.metrics.memory_usage_mb:.2f}MB")
    
    assert result.test_name == "test_benchmark"
    assert result.threshold_passed == True
    assert result.metrics.success == True
    
    print("✅ Benchmark result test passed")


async def test_async_operations():
    """Test async performance measurement."""
    print("\n⚡ Testing Async Operations...")
    
    async def sample_async_operation():
        """Sample async operation to measure."""
        await asyncio.sleep(0.2)
        return "completed"
    
    # Measure async operation
    start_time = time.time()
    result = await sample_async_operation()
    end_time = time.time()
    
    duration = end_time - start_time
    
    print(f"  Async operation result: {result}")
    print(f"  Duration: {duration:.3f}s")
    
    assert result == "completed"
    assert duration >= 0.2, "Duration should be at least 0.2s"
    assert duration < 0.3, "Duration should be less than 0.3s"
    
    print("✅ Async operations test passed")


def test_config_loading():
    """Test configuration loading."""
    print("\n⚙️  Testing Configuration Loading...")
    
    config_file = Path("performance-test-config.json")
    
    if config_file.exists():
        import json
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"  Config file loaded successfully")
        print(f"  Backend tests enabled: {config.get('performance_testing', {}).get('backend_tests', {}).get('document_processing', {}).get('enabled', False)}")
        print(f"  Frontend tests enabled: {config.get('performance_testing', {}).get('frontend_tests', {}).get('loading_performance', {}).get('enabled', False)}")
        
        assert "performance_testing" in config, "Config should have performance_testing section"
        
        print("✅ Configuration loading test passed")
    else:
        print("⚠️  Configuration file not found, skipping test")


def test_directory_structure():
    """Test that required directories and files exist."""
    print("\n📁 Testing Directory Structure...")
    
    required_paths = [
        "backend/tests/performance",
        "backend/tests/performance/conftest.py",
        "backend/tests/performance/test_document_processing_performance.py",
        "backend/tests/performance/test_search_performance.py",
        "backend/tests/performance/test_memory_monitoring.py",
        "backend/tests/performance/test_concurrent_users.py",
        "backend/tests/performance/run_performance_tests.py",
        "frontend/src/test/performance",
        "frontend/src/test/performance/frontend-performance.test.ts",
        "frontend/src/test/performance/performance-runner.ts",
        "performance-test-config.json",
        "run_performance_tests.py"
    ]
    
    missing_paths = []
    existing_paths = []
    
    for path_str in required_paths:
        path = Path(path_str)
        if path.exists():
            existing_paths.append(path_str)
            print(f"  ✅ {path_str}")
        else:
            missing_paths.append(path_str)
            print(f"  ❌ {path_str}")
    
    print(f"\n  Summary: {len(existing_paths)}/{len(required_paths)} files exist")
    
    if missing_paths:
        print(f"  Missing files: {missing_paths}")
        return False
    
    print("✅ Directory structure test passed")
    return True


async def main():
    """Run all framework tests."""
    print("🧪 Testing Performance Testing Framework")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test directory structure first
    tests_total += 1
    if test_directory_structure():
        tests_passed += 1
    
    # Test configuration loading
    tests_total += 1
    try:
        test_config_loading()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
    
    # Test performance monitor
    tests_total += 1
    try:
        await test_performance_monitor()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Performance monitor test failed: {e}")
    
    # Test benchmark result
    tests_total += 1
    try:
        await test_benchmark_result()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Benchmark result test failed: {e}")
    
    # Test async operations
    tests_total += 1
    try:
        await test_async_operations()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Async operations test failed: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("PERFORMANCE FRAMEWORK TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Success rate: {tests_passed/tests_total*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! Performance framework is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)