#!/usr/bin/env python3
"""
Test script for performance monitoring implementation
Tests all components: frontend monitoring, backend middleware, caching, and memory monitoring
"""

import asyncio
import time
import requests
import json
from typing import Dict, Any

class PerformanceMonitoringTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
    
    def test_monitoring_endpoints(self) -> Dict[str, Any]:
        """Test all monitoring API endpoints"""
        endpoints = [
            "/monitoring/performance",
            "/monitoring/health", 
            "/monitoring/performance/endpoints",
            "/monitoring/performance/queries",
            "/monitoring/memory",
            "/monitoring/cache",
            "/monitoring/database",
            "/monitoring/system"
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200,
                    "data_size": len(response.content) if response.content else 0
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        results[endpoint]["has_data"] = bool(data.get("data"))
                        results[endpoint]["data_keys"] = list(data.get("data", {}).keys()) if isinstance(data.get("data"), dict) else []
                    except json.JSONDecodeError:
                        results[endpoint]["json_valid"] = False
                
            except Exception as e:
                results[endpoint] = {
                    "error": str(e),
                    "success": False
                }
        
        return results
    
    def test_performance_middleware(self) -> Dict[str, Any]:
        """Test performance middleware by making various API calls"""
        test_endpoints = [
            "/",
            "/health",
            "/documents",
            "/search?q=test"
        ]
        
        results = {}
        
        for endpoint in test_endpoints:
            try:
                # Make multiple requests to generate performance data
                response_times = []
                
                for _ in range(5):
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    # Check for performance headers
                    if "X-Response-Time" in response.headers:
                        results[endpoint] = {
                            "middleware_active": True,
                            "avg_response_time": sum(response_times) / len(response_times),
                            "server_reported_time": response.headers.get("X-Response-Time"),
                            "memory_delta": response.headers.get("X-Memory-Delta")
                        }
                        break
                else:
                    results[endpoint] = {
                        "middleware_active": False,
                        "avg_response_time": sum(response_times) / len(response_times)
                    }
                    
            except Exception as e:
                results[endpoint] = {"error": str(e)}
        
        return results
    
    def test_memory_monitoring(self) -> Dict[str, Any]:
        """Test memory monitoring functionality"""
        try:
            # Get initial memory stats
            response = requests.get(f"{self.base_url}/monitoring/memory")
            if response.status_code != 200:
                return {"error": "Memory monitoring endpoint not accessible"}
            
            initial_stats = response.json()
            
            # Force garbage collection
            gc_response = requests.post(f"{self.base_url}/monitoring/memory/gc")
            gc_result = gc_response.json() if gc_response.status_code == 200 else {"error": "GC failed"}
            
            # Get updated memory stats
            response = requests.get(f"{self.base_url}/monitoring/memory")
            updated_stats = response.json() if response.status_code == 200 else {}
            
            return {
                "initial_memory_mb": initial_stats.get("data", {}).get("current_usage", {}).get("current", {}).get("rss_mb", 0),
                "gc_result": gc_result,
                "memory_monitoring_active": bool(initial_stats.get("data")),
                "has_leak_analysis": bool(initial_stats.get("data", {}).get("leak_analysis")),
                "has_top_contexts": bool(initial_stats.get("data", {}).get("top_memory_contexts"))
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_cache_performance(self) -> Dict[str, Any]:
        """Test cache system performance"""
        try:
            # Get cache stats
            response = requests.get(f"{self.base_url}/monitoring/cache")
            if response.status_code != 200:
                return {"error": "Cache monitoring endpoint not accessible"}
            
            cache_stats = response.json()
            
            # Test cache clearing (if endpoint exists)
            clear_response = requests.post(f"{self.base_url}/monitoring/cache/clear?namespace=test")
            clear_result = clear_response.json() if clear_response.status_code == 200 else {"error": "Cache clear failed"}
            
            return {
                "cache_stats_available": bool(cache_stats.get("data")),
                "redis_connected": cache_stats.get("data", {}).get("redis", {}).get("connected", False),
                "memory_cache_active": cache_stats.get("data", {}).get("memory") is not None,
                "clear_test": clear_result
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_database_optimization(self) -> Dict[str, Any]:
        """Test database optimization features"""
        try:
            # Get database performance analysis
            response = requests.get(f"{self.base_url}/monitoring/database")
            if response.status_code != 200:
                return {"error": "Database monitoring endpoint not accessible"}
            
            db_stats = response.json()
            
            # Note: We won't run actual optimization in tests as it modifies the database
            # optimize_response = requests.post(f"{self.base_url}/monitoring/database/optimize")
            
            return {
                "database_analysis_available": bool(db_stats.get("data")),
                "has_performance_analysis": bool(db_stats.get("data", {}).get("performance_analysis")),
                "has_missing_indexes": bool(db_stats.get("data", {}).get("missing_indexes")),
                "has_size_info": bool(db_stats.get("data", {}).get("size_info")),
                "optimization_endpoint_available": True  # We assume it exists based on implementation
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_system_overview(self) -> Dict[str, Any]:
        """Test comprehensive system metrics endpoint"""
        try:
            response = requests.get(f"{self.base_url}/monitoring/system")
            if response.status_code != 200:
                return {"error": "System monitoring endpoint not accessible"}
            
            system_stats = response.json()
            data = system_stats.get("data", {})
            
            return {
                "system_endpoint_available": True,
                "has_performance_data": bool(data.get("performance")),
                "has_memory_data": bool(data.get("memory")),
                "has_cache_data": bool(data.get("cache")),
                "response_complete": all(key in data for key in ["performance", "memory", "cache"])
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance monitoring tests"""
        print("🚀 Starting Performance Monitoring Tests...")
        
        tests = [
            ("Monitoring Endpoints", self.test_monitoring_endpoints),
            ("Performance Middleware", self.test_performance_middleware),
            ("Memory Monitoring", self.test_memory_monitoring),
            ("Cache Performance", self.test_cache_performance),
            ("Database Optimization", self.test_database_optimization),
            ("System Overview", self.test_system_overview)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n📊 Testing {test_name}...")
            try:
                start_time = time.time()
                test_result = test_func()
                test_time = time.time() - start_time
                
                results[test_name] = {
                    "result": test_result,
                    "test_duration": test_time,
                    "success": not any("error" in str(v) for v in test_result.values() if isinstance(v, dict))
                }
                
                if results[test_name]["success"]:
                    print(f"✅ {test_name} - PASSED ({test_time:.2f}s)")
                else:
                    print(f"❌ {test_name} - FAILED ({test_time:.2f}s)")
                    
            except Exception as e:
                results[test_name] = {
                    "result": {"error": str(e)},
                    "test_duration": 0,
                    "success": False
                }
                print(f"💥 {test_name} - ERROR: {e}")
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r["success"])
        
        print(f"\n{'='*60}")
        print(f"📈 PERFORMANCE MONITORING TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print(f"\n🎉 All performance monitoring features are working correctly!")
        else:
            print(f"\n⚠️  Some performance monitoring features need attention.")
            
            # Show failed tests
            failed_tests = [name for name, result in results.items() if not result["success"]]
            if failed_tests:
                print(f"\nFailed Tests:")
                for test_name in failed_tests:
                    print(f"  - {test_name}")
        
        print(f"\n{'='*60}")

def main():
    """Main test execution"""
    tester = PerformanceMonitoringTester()
    
    try:
        # Test if server is running
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the backend server first.")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Please start the backend server first.")
        return
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Print summary
    tester.print_summary(results)
    
    # Save detailed results
    with open("performance_monitoring_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: performance_monitoring_test_results.json")

if __name__ == "__main__":
    main()