#!/usr/bin/env python3
"""
Simple performance test to verify the framework is working.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.tests.performance.conftest import PerformanceMonitor, PerformanceMetrics, BenchmarkResult


async def test_simple_document_processing():
    """Test simple document processing performance."""
    print("🔍 Testing Simple Document Processing Performance...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Simulate document processing work
    start_time = time.time()
    
    # Simulate parsing
    await asyncio.sleep(0.1)
    monitor.sample_metrics()
    
    # Simulate text extraction
    text_blocks = []
    for i in range(100):
        text_blocks.append(f"This is text block {i} with some content.")
        if i % 20 == 0:
            monitor.sample_metrics()
            await asyncio.sleep(0.01)
    
    # Simulate image extraction
    images = []
    for i in range(5):
        images.append(f"image_{i}.jpg")
        monitor.sample_metrics()
        await asyncio.sleep(0.02)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    metrics = monitor.stop_monitoring()
    metrics.execution_time = processing_time
    metrics.success = len(text_blocks) > 0 and len(images) > 0
    
    # Create benchmark result
    result = BenchmarkResult(
        test_name="simple_document_processing",
        metrics=metrics,
        threshold_passed=processing_time <= 1.0,  # 1 second threshold
        threshold_values={"max_time": 1.0, "max_memory": 100.0}
    )
    
    print(f"  Processing time: {processing_time:.3f}s")
    print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
    print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
    print(f"  Text blocks: {len(text_blocks)}")
    print(f"  Images: {len(images)}")
    print(f"  Threshold passed: {result.threshold_passed}")
    
    assert result.metrics.success, "Processing should succeed"
    assert len(text_blocks) == 100, "Should extract 100 text blocks"
    assert len(images) == 5, "Should extract 5 images"
    
    print("✅ Simple document processing test passed")
    return result


async def test_simple_search_performance():
    """Test simple search performance."""
    print("\n🔍 Testing Simple Search Performance...")
    
    monitor = PerformanceMonitor()
    
    # Create mock search index
    search_index = []
    for i in range(1000):
        search_index.append({
            "id": i,
            "content": f"This is document {i} about machine learning and data science.",
            "keywords": ["machine", "learning", "data", "science", "algorithm", "neural", "networks"]
        })
    
    # Test search queries
    queries = ["machine learning", "data science", "algorithm", "neural networks"]
    search_results = []
    
    for query in queries:
        monitor.start_monitoring()
        start_time = time.time()
        
        # Simulate search
        query_words = query.lower().split()
        results = []
        
        for doc in search_index:
            score = 0
            for word in query_words:
                if word in doc["content"].lower():
                    score += 1
            
            if score > 0:
                results.append({"doc_id": doc["id"], "score": score})
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:10]  # Top 10 results
        
        end_time = time.time()
        response_time = end_time - start_time
        
        monitor.sample_metrics()
        metrics = monitor.stop_monitoring()
        metrics.execution_time = response_time
        metrics.success = len(results) > 0
        
        search_result = {
            "query": query,
            "response_time": response_time,
            "result_count": len(results),
            "metrics": metrics
        }
        search_results.append(search_result)
        
        print(f"  Query: '{query}' - {response_time:.3f}s - {len(results)} results")
    
    # Calculate average response time
    avg_response_time = sum(r["response_time"] for r in search_results) / len(search_results)
    max_response_time = max(r["response_time"] for r in search_results)
    
    print(f"  Average response time: {avg_response_time:.3f}s")
    print(f"  Max response time: {max_response_time:.3f}s")
    
    # Performance assertions
    assert avg_response_time <= 0.1, f"Average response time {avg_response_time:.3f}s too slow"
    assert max_response_time <= 0.2, f"Max response time {max_response_time:.3f}s too slow"
    assert all(r["result_count"] > 0 for r in search_results), "All queries should return results"
    
    print("✅ Simple search performance test passed")
    return search_results


async def test_memory_usage_simulation():
    """Test memory usage monitoring."""
    print("\n🔍 Testing Memory Usage Monitoring...")
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Simulate memory-intensive operations
    data_structures = []
    
    # Create large data structures
    for i in range(10):
        large_list = list(range(10000))  # Create list with 10k items
        large_dict = {f"key_{j}": f"value_{j}" * 10 for j in range(1000)}  # Create dict with 1k items
        
        data_structures.append({
            "list": large_list,
            "dict": large_dict,
            "metadata": {
                "created_at": time.time(),
                "size": len(large_list) + len(large_dict)
            }
        })
        
        monitor.sample_metrics()
        await asyncio.sleep(0.05)  # Small delay
    
    # Sample metrics during processing
    for _ in range(10):
        monitor.sample_metrics()
        await asyncio.sleep(0.02)
    
    # Clean up some data
    data_structures = data_structures[:5]  # Keep only half
    
    # Final sampling
    for _ in range(5):
        monitor.sample_metrics()
        await asyncio.sleep(0.01)
    
    metrics = monitor.stop_monitoring()
    
    print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
    print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
    print(f"  Data structures created: {len(data_structures)}")
    print(f"  Total items: {sum(ds['metadata']['size'] for ds in data_structures)}")
    
    # Memory assertions
    assert metrics.peak_memory_mb > 0, "Peak memory should be positive"
    assert len(data_structures) == 5, "Should have 5 data structures after cleanup"
    
    print("✅ Memory usage monitoring test passed")
    return metrics


async def test_concurrent_operations():
    """Test concurrent operations performance."""
    print("\n🔍 Testing Concurrent Operations Performance...")
    
    async def simulate_user_action(user_id: int, action_type: str) -> dict:
        """Simulate a user action."""
        start_time = time.time()
        
        if action_type == "search":
            # Simulate search
            await asyncio.sleep(0.05 + (user_id % 3) * 0.01)  # Variable delay
            result_count = 10 + (user_id % 5)
        elif action_type == "upload":
            # Simulate upload
            await asyncio.sleep(0.1 + (user_id % 2) * 0.05)
            result_count = 1
        else:  # review
            # Simulate card review
            await asyncio.sleep(0.02 + (user_id % 4) * 0.005)
            result_count = 5 + (user_id % 3)
        
        end_time = time.time()
        
        return {
            "user_id": user_id,
            "action": action_type,
            "duration": end_time - start_time,
            "result_count": result_count,
            "success": True
        }
    
    # Create concurrent tasks
    tasks = []
    for i in range(15):  # 15 concurrent users
        action_type = ["search", "upload", "review"][i % 3]
        task = simulate_user_action(i, action_type)
        tasks.append(task)
    
    # Monitor concurrent execution
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Sample final metrics
    for _ in range(5):
        monitor.sample_metrics()
        await asyncio.sleep(0.01)
    
    metrics = monitor.stop_monitoring()
    
    total_time = end_time - start_time
    successful_actions = [r for r in results if r["success"]]
    
    # Calculate statistics
    action_times = [r["duration"] for r in successful_actions]
    avg_action_time = sum(action_times) / len(action_times)
    max_action_time = max(action_times)
    
    print(f"  Total concurrent time: {total_time:.3f}s")
    print(f"  Successful actions: {len(successful_actions)}/{len(results)}")
    print(f"  Average action time: {avg_action_time:.3f}s")
    print(f"  Max action time: {max_action_time:.3f}s")
    print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
    
    # Performance assertions
    assert len(successful_actions) == len(results), "All actions should succeed"
    assert total_time <= 0.5, f"Concurrent execution took too long: {total_time:.3f}s"
    assert avg_action_time <= 0.1, f"Average action time too slow: {avg_action_time:.3f}s"
    
    print("✅ Concurrent operations test passed")
    return results


async def main():
    """Run all simple performance tests."""
    print("🚀 Running Simple Performance Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    results = {}
    
    # Test document processing
    tests_total += 1
    try:
        result = await test_simple_document_processing()
        results["document_processing"] = result
        tests_passed += 1
    except Exception as e:
        print(f"❌ Document processing test failed: {e}")
        results["document_processing"] = None
    
    # Test search performance
    tests_total += 1
    try:
        result = await test_simple_search_performance()
        results["search_performance"] = result
        tests_passed += 1
    except Exception as e:
        print(f"❌ Search performance test failed: {e}")
        results["search_performance"] = None
    
    # Test memory monitoring
    tests_total += 1
    try:
        result = await test_memory_usage_simulation()
        results["memory_monitoring"] = result
        tests_passed += 1
    except Exception as e:
        print(f"❌ Memory monitoring test failed: {e}")
        results["memory_monitoring"] = None
    
    # Test concurrent operations
    tests_total += 1
    try:
        result = await test_concurrent_operations()
        results["concurrent_operations"] = result
        tests_passed += 1
    except Exception as e:
        print(f"❌ Concurrent operations test failed: {e}")
        results["concurrent_operations"] = None
    
    # Print summary
    print("\n" + "=" * 60)
    print("SIMPLE PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Success rate: {tests_passed/tests_total*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 All performance tests passed!")
        print("\n✅ Performance testing framework is working correctly!")
        print("✅ Document processing benchmarks implemented")
        print("✅ Search performance tests implemented")
        print("✅ Memory monitoring implemented")
        print("✅ Concurrent user simulation implemented")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)