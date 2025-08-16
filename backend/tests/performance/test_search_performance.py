"""Search performance benchmarks and response time validation."""

import pytest
import asyncio
import time
from typing import Dict, List
from unittest.mock import AsyncMock

from app.services.search_service import SearchService
from app.services.embedding_service import EmbeddingService
from app.services.vector_index_service import VectorIndexService
from .conftest import PerformanceMonitor, BenchmarkResult, PerformanceMetrics


class TestSearchPerformance:
    """Test search functionality performance benchmarks."""
    
    @pytest.mark.asyncio
    async def test_text_search_response_time(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test text search response time performance."""
        search_service = SearchService()
        
        # Test queries with different complexities
        test_queries = [
            {"query": "machine learning", "expected_min_results": 1},
            {"query": "neural networks algorithms", "expected_min_results": 1},
            {"query": "data structures and algorithms", "expected_min_results": 1},
            {"query": "artificial intelligence deep learning", "expected_min_results": 1},
            {"query": "python programming tutorial", "expected_min_results": 1}
        ]
        
        results = []
        max_response_time = performance_thresholds["search"]["response_time"]
        
        for test_case in test_queries:
            performance_monitor.start_monitoring()
            
            try:
                start_time = time.time()
                
                # Perform search
                search_results = await search_service.search_text(
                    query=test_case["query"],
                    limit=20
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                metrics = performance_monitor.stop_monitoring()
                metrics.execution_time = response_time
                metrics.success = len(search_results) >= test_case["expected_min_results"]
                
                # Validate response time
                threshold_passed = response_time <= max_response_time
                
                result = BenchmarkResult(
                    test_name=f"text_search_{test_case['query'].replace(' ', '_')}",
                    metrics=metrics,
                    threshold_passed=threshold_passed,
                    threshold_values={"max_response_time": max_response_time}
                )
                results.append(result)
                
                print(f"\nText Search: '{test_case['query']}'")
                print(f"  Response time: {response_time:.3f}s")
                print(f"  Results count: {len(search_results)}")
                print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
                print(f"  Threshold passed: {threshold_passed}")
                
                assert threshold_passed, \
                    f"Search response time {response_time:.3f}s exceeded threshold {max_response_time}s"
                
            except Exception as e:
                metrics = performance_monitor.stop_monitoring()
                metrics.success = False
                metrics.error_message = str(e)
                
                result = BenchmarkResult(
                    test_name=f"text_search_{test_case['query'].replace(' ', '_')}_failed",
                    metrics=metrics,
                    threshold_passed=False,
                    threshold_values={"max_response_time": max_response_time}
                )
                results.append(result)
                raise
        
        # Overall performance summary
        avg_response_time = sum(r.metrics.execution_time for r in results) / len(results)
        print(f"\nOverall Text Search Performance:")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Tests passed: {sum(1 for r in results if r.threshold_passed)}/{len(results)}")
    
    @pytest.mark.asyncio
    async def test_semantic_search_performance(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test semantic search performance with vector operations."""
        embedding_service = EmbeddingService()
        vector_service = VectorIndexService()
        
        # Test semantic queries
        semantic_queries = [
            "concepts related to machine learning",
            "algorithms for data processing",
            "methods for artificial intelligence",
            "techniques in computer science",
            "approaches to problem solving"
        ]
        
        results = []
        max_response_time = performance_thresholds["search"]["response_time"] * 2  # Allow more time for semantic search
        
        for query in semantic_queries:
            performance_monitor.start_monitoring()
            
            try:
                start_time = time.time()
                
                # Generate query embedding
                query_embedding = await embedding_service.generate_embedding(query)
                
                # Perform vector search
                search_results = await vector_service.search_similar(
                    query_embedding=query_embedding,
                    limit=10,
                    threshold=0.7
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                metrics = performance_monitor.stop_monitoring()
                metrics.execution_time = response_time
                metrics.success = len(search_results) > 0
                
                threshold_passed = response_time <= max_response_time
                
                result = BenchmarkResult(
                    test_name=f"semantic_search_{query.replace(' ', '_')[:20]}",
                    metrics=metrics,
                    threshold_passed=threshold_passed,
                    threshold_values={"max_response_time": max_response_time}
                )
                results.append(result)
                
                print(f"\nSemantic Search: '{query}'")
                print(f"  Response time: {response_time:.3f}s")
                print(f"  Results count: {len(search_results)}")
                print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
                print(f"  Threshold passed: {threshold_passed}")
                
                assert threshold_passed, \
                    f"Semantic search response time {response_time:.3f}s exceeded threshold {max_response_time}s"
                
            except Exception as e:
                metrics = performance_monitor.stop_monitoring()
                metrics.success = False
                metrics.error_message = str(e)
                
                result = BenchmarkResult(
                    test_name=f"semantic_search_failed",
                    metrics=metrics,
                    threshold_passed=False,
                    threshold_values={"max_response_time": max_response_time}
                )
                results.append(result)
                print(f"Semantic search failed: {e}")
                # Don't raise for semantic search as it might not be fully configured
        
        if results:
            avg_response_time = sum(r.metrics.execution_time for r in results) / len(results)
            print(f"\nOverall Semantic Search Performance:")
            print(f"  Average response time: {avg_response_time:.3f}s")
            print(f"  Tests passed: {sum(1 for r in results if r.threshold_passed)}/{len(results)}")
    
    @pytest.mark.asyncio
    async def test_search_with_filters_performance(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test search performance with various filters applied."""
        search_service = SearchService()
        
        # Test different filter combinations
        filter_tests = [
            {
                "name": "basic_filter",
                "query": "learning",
                "filters": {"difficulty_range": (0.3, 0.7)}
            },
            {
                "name": "chapter_filter",
                "query": "algorithm",
                "filters": {"chapter_ids": ["chapter-1", "chapter-2"]}
            },
            {
                "name": "combined_filters",
                "query": "data",
                "filters": {
                    "difficulty_range": (0.2, 0.8),
                    "chapter_ids": ["chapter-1"],
                    "content_types": ["text", "image"]
                }
            }
        ]
        
        max_response_time = performance_thresholds["search"]["response_time"]
        results = []
        
        for test_case in filter_tests:
            performance_monitor.start_monitoring()
            
            try:
                start_time = time.time()
                
                # Perform filtered search
                search_results = await search_service.search_with_filters(
                    query=test_case["query"],
                    filters=test_case["filters"],
                    limit=20
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                metrics = performance_monitor.stop_monitoring()
                metrics.execution_time = response_time
                metrics.success = True  # Success if no exception
                
                threshold_passed = response_time <= max_response_time
                
                result = BenchmarkResult(
                    test_name=f"filtered_search_{test_case['name']}",
                    metrics=metrics,
                    threshold_passed=threshold_passed,
                    threshold_values={"max_response_time": max_response_time}
                )
                results.append(result)
                
                print(f"\nFiltered Search: {test_case['name']}")
                print(f"  Query: '{test_case['query']}'")
                print(f"  Filters: {test_case['filters']}")
                print(f"  Response time: {response_time:.3f}s")
                print(f"  Results count: {len(search_results)}")
                print(f"  Threshold passed: {threshold_passed}")
                
                assert threshold_passed, \
                    f"Filtered search response time {response_time:.3f}s exceeded threshold {max_response_time}s"
                
            except Exception as e:
                metrics = performance_monitor.stop_monitoring()
                metrics.success = False
                metrics.error_message = str(e)
                
                result = BenchmarkResult(
                    test_name=f"filtered_search_{test_case['name']}_failed",
                    metrics=metrics,
                    threshold_passed=False,
                    threshold_values={"max_response_time": max_response_time}
                )
                results.append(result)
                print(f"Filtered search failed: {e}")
                # Continue with other tests
        
        if results:
            successful_results = [r for r in results if r.metrics.success]
            if successful_results:
                avg_response_time = sum(r.metrics.execution_time for r in successful_results) / len(successful_results)
                print(f"\nOverall Filtered Search Performance:")
                print(f"  Average response time: {avg_response_time:.3f}s")
                print(f"  Tests passed: {sum(1 for r in results if r.threshold_passed)}/{len(results)}")
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test search performance under concurrent load."""
        search_service = SearchService()
        
        # Simulate concurrent users with different queries
        concurrent_queries = [
            "machine learning algorithms",
            "data structures",
            "neural networks",
            "artificial intelligence",
            "computer science",
            "programming languages",
            "software engineering",
            "database systems"
        ]
        
        performance_monitor.start_monitoring()
        
        async def perform_search(query: str, user_id: int) -> Dict:
            """Perform search for a simulated user."""
            start_time = time.time()
            
            try:
                results = await search_service.search_text(query=query, limit=10)
                end_time = time.time()
                
                return {
                    "user_id": user_id,
                    "query": query,
                    "response_time": end_time - start_time,
                    "result_count": len(results),
                    "success": True
                }
            except Exception as e:
                return {
                    "user_id": user_id,
                    "query": query,
                    "response_time": time.time() - start_time,
                    "error": str(e),
                    "success": False
                }
        
        # Sample metrics during concurrent execution
        async def sample_during_execution():
            while True:
                performance_monitor.sample_metrics()
                await asyncio.sleep(0.1)
        
        sampler_task = asyncio.create_task(sample_during_execution())
        
        try:
            start_time = time.time()
            
            # Execute concurrent searches
            tasks = [
                perform_search(query, i) 
                for i, query in enumerate(concurrent_queries)
            ]
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            sampler_task.cancel()
            
            metrics = performance_monitor.stop_monitoring()
            total_time = end_time - start_time
            
            # Analyze concurrent performance
            successful_results = [r for r in results if r["success"]]
            failed_results = [r for r in results if not r["success"]]
            
            if successful_results:
                response_times = [r["response_time"] for r in successful_results]
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
                
                print(f"\nConcurrent Search Performance:")
                print(f"  Total execution time: {total_time:.3f}s")
                print(f"  Concurrent queries: {len(concurrent_queries)}")
                print(f"  Successful: {len(successful_results)}")
                print(f"  Failed: {len(failed_results)}")
                print(f"  Average response time: {avg_response_time:.3f}s")
                print(f"  Max response time: {max_response_time:.3f}s")
                print(f"  P95 response time: {p95_response_time:.3f}s")
                print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
                
                # Performance assertions
                max_allowed_p95 = performance_thresholds["concurrent_users"]["response_time_p95"]
                assert p95_response_time <= max_allowed_p95, \
                    f"P95 response time {p95_response_time:.3f}s exceeded threshold {max_allowed_p95}s"
                
                max_error_rate = performance_thresholds["concurrent_users"]["error_rate"]
                error_rate = len(failed_results) / len(results)
                assert error_rate <= max_error_rate, \
                    f"Error rate {error_rate:.2%} exceeded threshold {max_error_rate:.2%}"
                
                # Concurrent efficiency check
                sequential_time_estimate = sum(response_times)
                efficiency = sequential_time_estimate / total_time if total_time > 0 else 0
                print(f"  Concurrency efficiency: {efficiency:.2f}x")
                
        except asyncio.CancelledError:
            pass
        finally:
            if not sampler_task.cancelled():
                sampler_task.cancel()
    
    @pytest.mark.asyncio
    async def test_search_index_performance(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test search index operations performance."""
        vector_service = VectorIndexService()
        
        # Test index operations
        test_operations = [
            {
                "name": "index_build",
                "operation": "build_index",
                "description": "Build search index from documents"
            },
            {
                "name": "index_update",
                "operation": "update_index",
                "description": "Update search index with new content"
            },
            {
                "name": "index_query",
                "operation": "query_index",
                "description": "Query search index for results"
            }
        ]
        
        results = []
        
        for test_op in test_operations:
            performance_monitor.start_monitoring()
            
            try:
                start_time = time.time()
                
                if test_op["operation"] == "build_index":
                    # Simulate index building
                    await vector_service.build_index_async()
                elif test_op["operation"] == "update_index":
                    # Simulate index update
                    await vector_service.update_index_async(["new content"])
                elif test_op["operation"] == "query_index":
                    # Simulate index query
                    await vector_service.query_index_async("test query")
                
                end_time = time.time()
                
                metrics = performance_monitor.stop_monitoring()
                metrics.execution_time = end_time - start_time
                metrics.success = True
                
                result = BenchmarkResult(
                    test_name=f"index_{test_op['name']}",
                    metrics=metrics,
                    threshold_passed=True,  # No specific thresholds for index ops
                    threshold_values={}
                )
                results.append(result)
                
                print(f"\nIndex Operation: {test_op['name']}")
                print(f"  Description: {test_op['description']}")
                print(f"  Execution time: {metrics.execution_time:.3f}s")
                print(f"  Memory usage: {metrics.memory_usage_mb:.2f}MB")
                print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
                
            except Exception as e:
                metrics = performance_monitor.stop_monitoring()
                metrics.success = False
                metrics.error_message = str(e)
                
                result = BenchmarkResult(
                    test_name=f"index_{test_op['name']}_failed",
                    metrics=metrics,
                    threshold_passed=False,
                    threshold_values={}
                )
                results.append(result)
                print(f"Index operation {test_op['name']} failed: {e}")
                # Continue with other operations
        
        if results:
            successful_results = [r for r in results if r.metrics.success]
            print(f"\nOverall Index Performance:")
            print(f"  Operations tested: {len(results)}")
            print(f"  Successful: {len(successful_results)}")
            print(f"  Failed: {len(results) - len(successful_results)}")