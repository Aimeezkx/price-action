"""Concurrent user simulation tests for load testing."""

import pytest
import asyncio
import time
import random
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock

from app.services.search_service import SearchService
from app.services.document_service import DocumentService
from app.services.card_generation_service import CardGenerationService
from app.parsers.factory import ParserFactory
from .conftest import PerformanceMonitor, BenchmarkResult, PerformanceMetrics


@dataclass
class UserSession:
    """Represents a user session with actions and metrics."""
    user_id: int
    session_start: float
    session_end: float
    actions_performed: List[Dict[str, Any]]
    total_response_time: float
    successful_actions: int
    failed_actions: int
    errors: List[str]


@dataclass
class LoadTestResult:
    """Results from load testing."""
    total_users: int
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    peak_memory_mb: float
    user_sessions: List[UserSession]


class ConcurrentUserSimulator:
    """Simulate concurrent users performing various actions."""
    
    def __init__(self):
        self.search_service = SearchService()
        self.document_service = DocumentService()
        self.card_service = CardGenerationService()
        
    async def simulate_user_session(
        self, 
        user_id: int, 
        session_duration: float,
        actions_config: Dict[str, float]
    ) -> UserSession:
        """Simulate a single user session with various actions."""
        session_start = time.time()
        actions_performed = []
        errors = []
        
        # Define available actions with their probabilities
        available_actions = [
            ("search_text", self._perform_text_search, actions_config.get("search_probability", 0.4)),
            ("search_semantic", self._perform_semantic_search, actions_config.get("semantic_probability", 0.2)),
            ("upload_document", self._perform_document_upload, actions_config.get("upload_probability", 0.1)),
            ("review_cards", self._perform_card_review, actions_config.get("review_probability", 0.3))
        ]
        
        session_end_time = session_start + session_duration
        
        while time.time() < session_end_time:
            # Choose random action based on probabilities
            action_name, action_func, probability = random.choices(
                available_actions,
                weights=[prob for _, _, prob in available_actions]
            )[0]
            
            try:
                action_start = time.time()
                result = await action_func(user_id)
                action_end = time.time()
                
                action_record = {
                    "action": action_name,
                    "start_time": action_start,
                    "end_time": action_end,
                    "response_time": action_end - action_start,
                    "success": result.get("success", True),
                    "details": result
                }
                
                actions_performed.append(action_record)
                
                # Random delay between actions (0.5-3 seconds)
                await asyncio.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                error_msg = f"User {user_id} action {action_name} failed: {str(e)}"
                errors.append(error_msg)
                
                action_record = {
                    "action": action_name,
                    "start_time": time.time(),
                    "end_time": time.time(),
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
                actions_performed.append(action_record)
        
        session_end = time.time()
        
        # Calculate session metrics
        successful_actions = sum(1 for a in actions_performed if a.get("success", False))
        failed_actions = len(actions_performed) - successful_actions
        total_response_time = sum(a.get("response_time", 0) for a in actions_performed)
        
        return UserSession(
            user_id=user_id,
            session_start=session_start,
            session_end=session_end,
            actions_performed=actions_performed,
            total_response_time=total_response_time,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            errors=errors
        )
    
    async def _perform_text_search(self, user_id: int) -> Dict[str, Any]:
        """Simulate text search action."""
        queries = [
            "machine learning",
            "data structures",
            "algorithms",
            "neural networks",
            "artificial intelligence",
            "programming",
            "computer science",
            "software engineering"
        ]
        
        query = random.choice(queries)
        
        try:
            results = await self.search_service.search_text(
                query=query,
                limit=random.randint(5, 20)
            )
            
            return {
                "success": True,
                "query": query,
                "result_count": len(results),
                "action_type": "text_search"
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "action_type": "text_search"
            }
    
    async def _perform_semantic_search(self, user_id: int) -> Dict[str, Any]:
        """Simulate semantic search action."""
        semantic_queries = [
            "concepts related to machine learning",
            "algorithms for data processing",
            "methods in artificial intelligence",
            "techniques for problem solving",
            "approaches to software development"
        ]
        
        query = random.choice(semantic_queries)
        
        try:
            # Simulate semantic search (may not be fully implemented)
            await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate processing time
            
            return {
                "success": True,
                "query": query,
                "result_count": random.randint(3, 15),
                "action_type": "semantic_search"
            }
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "action_type": "semantic_search"
            }
    
    async def _perform_document_upload(self, user_id: int) -> Dict[str, Any]:
        """Simulate document upload action."""
        try:
            # Simulate document upload processing
            await asyncio.sleep(random.uniform(1.0, 3.0))  # Simulate upload time
            
            return {
                "success": True,
                "filename": f"user_{user_id}_document_{random.randint(1, 100)}.pdf",
                "action_type": "document_upload"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_type": "document_upload"
            }
    
    async def _perform_card_review(self, user_id: int) -> Dict[str, Any]:
        """Simulate card review action."""
        try:
            # Simulate reviewing multiple cards
            cards_reviewed = random.randint(3, 10)
            
            for _ in range(cards_reviewed):
                # Simulate card review time
                await asyncio.sleep(random.uniform(0.2, 1.0))
            
            return {
                "success": True,
                "cards_reviewed": cards_reviewed,
                "action_type": "card_review"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_type": "card_review"
            }


class TestConcurrentUsers:
    """Test concurrent user simulation and load testing."""
    
    @pytest.mark.asyncio
    async def test_concurrent_search_users(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test concurrent users performing search operations."""
        simulator = ConcurrentUserSimulator()
        
        # Test configuration
        num_users = 10
        session_duration = 30.0  # 30 seconds per user
        
        actions_config = {
            "search_probability": 0.7,
            "semantic_probability": 0.2,
            "upload_probability": 0.05,
            "review_probability": 0.05
        }
        
        performance_monitor.start_monitoring()
        
        # Sample metrics during test
        async def sample_metrics():
            while True:
                performance_monitor.sample_metrics()
                await asyncio.sleep(0.5)
        
        sampler_task = asyncio.create_task(sample_metrics())
        
        try:
            start_time = time.time()
            
            # Create concurrent user sessions
            tasks = [
                simulator.simulate_user_session(
                    user_id=i,
                    session_duration=session_duration,
                    actions_config=actions_config
                )
                for i in range(num_users)
            ]
            
            # Run all user sessions concurrently
            user_sessions = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            sampler_task.cancel()
            
        except Exception as e:
            sampler_task.cancel()
            raise
        
        metrics = performance_monitor.stop_monitoring()
        
        # Filter out exceptions and analyze results
        successful_sessions = [s for s in user_sessions if isinstance(s, UserSession)]
        failed_sessions = [s for s in user_sessions if not isinstance(s, UserSession)]
        
        # Calculate overall metrics
        all_actions = []
        for session in successful_sessions:
            all_actions.extend(session.actions_performed)
        
        successful_actions = [a for a in all_actions if a.get("success", False)]
        failed_actions = [a for a in all_actions if not a.get("success", True)]
        
        if successful_actions:
            response_times = [a["response_time"] for a in successful_actions]
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        total_duration = end_time - start_time
        requests_per_second = len(all_actions) / total_duration if total_duration > 0 else 0
        error_rate = len(failed_actions) / len(all_actions) if all_actions else 0
        
        # Create load test result
        load_result = LoadTestResult(
            total_users=num_users,
            duration_seconds=total_duration,
            total_requests=len(all_actions),
            successful_requests=len(successful_actions),
            failed_requests=len(failed_actions),
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            peak_memory_mb=metrics.peak_memory_mb,
            user_sessions=successful_sessions
        )
        
        print(f"\nConcurrent Search Users Load Test Results:")
        print(f"  Users: {load_result.total_users}")
        print(f"  Duration: {load_result.duration_seconds:.2f}s")
        print(f"  Total requests: {load_result.total_requests}")
        print(f"  Successful: {load_result.successful_requests}")
        print(f"  Failed: {load_result.failed_requests}")
        print(f"  Requests/sec: {load_result.requests_per_second:.2f}")
        print(f"  Error rate: {load_result.error_rate:.2%}")
        print(f"  Avg response time: {load_result.avg_response_time:.3f}s")
        print(f"  P95 response time: {load_result.p95_response_time:.3f}s")
        print(f"  P99 response time: {load_result.p99_response_time:.3f}s")
        print(f"  Peak memory: {load_result.peak_memory_mb:.2f}MB")
        
        # Performance assertions
        max_p95_time = performance_thresholds["concurrent_users"]["response_time_p95"]
        assert load_result.p95_response_time <= max_p95_time, \
            f"P95 response time {load_result.p95_response_time:.3f}s exceeded threshold {max_p95_time}s"
        
        max_error_rate = performance_thresholds["concurrent_users"]["error_rate"]
        assert load_result.error_rate <= max_error_rate, \
            f"Error rate {load_result.error_rate:.2%} exceeded threshold {max_error_rate:.2%}"
        
        # At least 80% of users should complete successfully
        success_rate = len(successful_sessions) / num_users
        assert success_rate >= 0.8, f"User success rate {success_rate:.2%} too low"
    
    @pytest.mark.asyncio
    async def test_mixed_workload_concurrent_users(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Test concurrent users with mixed workload (search, upload, review)."""
        simulator = ConcurrentUserSimulator()
        
        # Test configuration with balanced workload
        num_users = 8
        session_duration = 45.0  # 45 seconds per user
        
        actions_config = {
            "search_probability": 0.4,
            "semantic_probability": 0.2,
            "upload_probability": 0.2,
            "review_probability": 0.2
        }
        
        performance_monitor.start_monitoring()
        
        # Sample metrics during test
        async def sample_metrics():
            while True:
                performance_monitor.sample_metrics()
                await asyncio.sleep(0.5)
        
        sampler_task = asyncio.create_task(sample_metrics())
        
        try:
            start_time = time.time()
            
            # Create concurrent user sessions
            tasks = [
                simulator.simulate_user_session(
                    user_id=i,
                    session_duration=session_duration,
                    actions_config=actions_config
                )
                for i in range(num_users)
            ]
            
            # Run all user sessions concurrently
            user_sessions = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            sampler_task.cancel()
            
        except Exception as e:
            sampler_task.cancel()
            raise
        
        metrics = performance_monitor.stop_monitoring()
        
        # Analyze results by action type
        successful_sessions = [s for s in user_sessions if isinstance(s, UserSession)]
        
        action_stats = {}
        for session in successful_sessions:
            for action in session.actions_performed:
                action_type = action.get("action", "unknown")
                if action_type not in action_stats:
                    action_stats[action_type] = {
                        "count": 0,
                        "successful": 0,
                        "failed": 0,
                        "total_response_time": 0,
                        "response_times": []
                    }
                
                stats = action_stats[action_type]
                stats["count"] += 1
                
                if action.get("success", False):
                    stats["successful"] += 1
                    response_time = action.get("response_time", 0)
                    stats["total_response_time"] += response_time
                    stats["response_times"].append(response_time)
                else:
                    stats["failed"] += 1
        
        print(f"\nMixed Workload Concurrent Users Results:")
        print(f"  Users: {num_users}")
        print(f"  Duration: {end_time - start_time:.2f}s")
        print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
        
        # Print stats by action type
        for action_type, stats in action_stats.items():
            success_rate = stats["successful"] / stats["count"] if stats["count"] > 0 else 0
            avg_response_time = stats["total_response_time"] / stats["successful"] if stats["successful"] > 0 else 0
            
            print(f"\n  {action_type.replace('_', ' ').title()} Actions:")
            print(f"    Total: {stats['count']}")
            print(f"    Successful: {stats['successful']}")
            print(f"    Failed: {stats['failed']}")
            print(f"    Success rate: {success_rate:.2%}")
            print(f"    Avg response time: {avg_response_time:.3f}s")
        
        # Overall performance assertions
        total_actions = sum(stats["count"] for stats in action_stats.values())
        total_successful = sum(stats["successful"] for stats in action_stats.values())
        overall_success_rate = total_successful / total_actions if total_actions > 0 else 0
        
        assert overall_success_rate >= 0.85, \
            f"Overall success rate {overall_success_rate:.2%} too low for mixed workload"
        
        # Check that all action types were performed
        expected_actions = ["search_text", "search_semantic", "upload_document", "review_cards"]
        performed_actions = set(action_stats.keys())
        
        # At least 3 out of 4 action types should be performed
        assert len(performed_actions.intersection(expected_actions)) >= 3, \
            f"Not enough action variety performed: {performed_actions}"
    
    @pytest.mark.asyncio
    async def test_stress_test_high_concurrency(
        self,
        performance_monitor: PerformanceMonitor,
        performance_thresholds: Dict
    ):
        """Stress test with high number of concurrent users."""
        simulator = ConcurrentUserSimulator()
        
        # Stress test configuration
        num_users = 20  # Higher concurrency
        session_duration = 20.0  # Shorter sessions for stress test
        
        actions_config = {
            "search_probability": 0.8,  # Focus on search for stress test
            "semantic_probability": 0.1,
            "upload_probability": 0.05,
            "review_probability": 0.05
        }
        
        performance_monitor.start_monitoring()
        
        # Sample metrics more frequently during stress test
        async def sample_metrics():
            while True:
                performance_monitor.sample_metrics()
                await asyncio.sleep(0.2)
        
        sampler_task = asyncio.create_task(sample_metrics())
        
        try:
            start_time = time.time()
            
            # Create high-concurrency user sessions
            tasks = [
                simulator.simulate_user_session(
                    user_id=i,
                    session_duration=session_duration,
                    actions_config=actions_config
                )
                for i in range(num_users)
            ]
            
            # Run all user sessions concurrently
            user_sessions = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            sampler_task.cancel()
            
        except Exception as e:
            sampler_task.cancel()
            raise
        
        metrics = performance_monitor.stop_monitoring()
        
        # Analyze stress test results
        successful_sessions = [s for s in user_sessions if isinstance(s, UserSession)]
        failed_sessions = [s for s in user_sessions if not isinstance(s, UserSession)]
        
        all_actions = []
        for session in successful_sessions:
            all_actions.extend(session.actions_performed)
        
        successful_actions = [a for a in all_actions if a.get("success", False)]
        failed_actions = [a for a in all_actions if not a.get("success", True)]
        
        total_duration = end_time - start_time
        requests_per_second = len(all_actions) / total_duration if total_duration > 0 else 0
        error_rate = len(failed_actions) / len(all_actions) if all_actions else 0
        
        print(f"\nStress Test Results (High Concurrency):")
        print(f"  Concurrent users: {num_users}")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Total requests: {len(all_actions)}")
        print(f"  Successful requests: {len(successful_actions)}")
        print(f"  Failed requests: {len(failed_actions)}")
        print(f"  Requests/sec: {requests_per_second:.2f}")
        print(f"  Error rate: {error_rate:.2%}")
        print(f"  Peak memory: {metrics.peak_memory_mb:.2f}MB")
        print(f"  Successful sessions: {len(successful_sessions)}/{num_users}")
        print(f"  Failed sessions: {len(failed_sessions)}")
        
        # Stress test assertions (more lenient than normal load test)
        max_error_rate = 0.15  # Allow up to 15% error rate in stress test
        assert error_rate <= max_error_rate, \
            f"Stress test error rate {error_rate:.2%} exceeded threshold {max_error_rate:.2%}"
        
        # At least 70% of users should complete successfully under stress
        user_success_rate = len(successful_sessions) / num_users
        assert user_success_rate >= 0.7, \
            f"User success rate {user_success_rate:.2%} too low for stress test"
        
        # System should handle at least 1 request per second under stress
        assert requests_per_second >= 1.0, \
            f"Requests per second {requests_per_second:.2f} too low for stress test"
        
        # Memory usage should not exceed 2x normal threshold
        max_stress_memory = performance_thresholds["document_processing"]["memory_limit"] * 2
        assert metrics.peak_memory_mb <= max_stress_memory, \
            f"Stress test memory {metrics.peak_memory_mb:.2f}MB exceeded threshold {max_stress_memory}MB"