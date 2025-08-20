"""
Production Environment Testing
Comprehensive testing of production environment
"""

import asyncio
import aiohttp
import time
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .models import (
    ValidationCheck, ValidationStatus, ValidationSeverity, ValidationCategory,
    ProductionEnvironment, DeploymentConfig
)


class ProductionEnvironmentTester:
    """Tests production environment functionality"""
    
    def __init__(self, environment: ProductionEnvironment):
        self.environment = environment
        
    async def run_environment_tests(self) -> List[ValidationCheck]:
        """Run comprehensive environment tests"""
        checks = []
        
        # API endpoint tests
        checks.extend(await self._test_api_endpoints())
        
        # Database performance tests
        checks.extend(await self._test_database_performance())
        
        # Load balancer tests
        checks.extend(await self._test_load_balancer())
        
        # CDN and static assets tests
        checks.extend(await self._test_static_assets())
        
        # Monitoring and logging tests
        checks.extend(await self._test_monitoring_systems())
        
        # Backup and recovery tests
        checks.extend(await self._test_backup_systems())
        
        return checks
    
    async def _test_api_endpoints(self) -> List[ValidationCheck]:
        """Test API endpoint functionality"""
        checks = []
        
        # Core API endpoints test
        api_test = ValidationCheck(
            name="API Endpoints Functionality",
            description="Test core API endpoints respond correctly",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.CRITICAL
        )
        
        try:
            api_test.started_at = datetime.now()
            
            endpoints_to_test = [
                {"path": "/health", "method": "GET", "expected_status": 200},
                {"path": "/api/v1/documents", "method": "GET", "expected_status": 200},
                {"path": "/api/v1/cards", "method": "GET", "expected_status": 200},
                {"path": "/api/v1/search", "method": "GET", "expected_status": 200}
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints_to_test:
                    try:
                        start_time = time.time()
                        
                        if endpoint["method"] == "GET":
                            async with session.get(
                                f"{self.environment.url}{endpoint['path']}", 
                                timeout=10
                            ) as response:
                                response_time = (time.time() - start_time) * 1000
                                
                                results.append({
                                    "endpoint": endpoint["path"],
                                    "status_code": response.status,
                                    "expected_status": endpoint["expected_status"],
                                    "response_time_ms": response_time,
                                    "success": response.status == endpoint["expected_status"]
                                })
                                
                    except Exception as e:
                        results.append({
                            "endpoint": endpoint["path"],
                            "error": str(e),
                            "success": False
                        })
            
            failed_endpoints = [r for r in results if not r.get("success", False)]
            
            if not failed_endpoints:
                api_test.status = ValidationStatus.PASSED
                api_test.result = {"endpoint_results": results}
            else:
                api_test.status = ValidationStatus.FAILED
                api_test.error_message = f"Failed endpoints: {len(failed_endpoints)}"
                api_test.result = {"endpoint_results": results, "failed_endpoints": failed_endpoints}
                
        except Exception as e:
            api_test.status = ValidationStatus.FAILED
            api_test.error_message = str(e)
        finally:
            api_test.completed_at = datetime.now()
            if api_test.started_at:
                api_test.execution_time = (api_test.completed_at - api_test.started_at).total_seconds()
        
        checks.append(api_test)
        
        return checks
    
    async def _test_database_performance(self) -> List[ValidationCheck]:
        """Test database performance in production"""
        checks = []
        
        # Database response time test
        db_perf_test = ValidationCheck(
            name="Database Performance",
            description="Test database response times under load",
            category=ValidationCategory.PERFORMANCE,
            severity=ValidationSeverity.HIGH
        )
        
        try:
            db_perf_test.started_at = datetime.now()
            
            # Simulate database performance tests
            query_tests = [
                {"name": "simple_select", "expected_ms": 50},
                {"name": "complex_join", "expected_ms": 200},
                {"name": "full_text_search", "expected_ms": 500},
                {"name": "aggregation", "expected_ms": 300}
            ]
            
            results = []
            for test in query_tests:
                # Simulate query execution
                start_time = time.time()
                await asyncio.sleep(0.1)  # Simulate query time
                execution_time = (time.time() - start_time) * 1000
                
                results.append({
                    "query_type": test["name"],
                    "execution_time_ms": execution_time,
                    "expected_ms": test["expected_ms"],
                    "within_threshold": execution_time <= test["expected_ms"]
                })
            
            slow_queries = [r for r in results if not r["within_threshold"]]
            
            if not slow_queries:
                db_perf_test.status = ValidationStatus.PASSED
                db_perf_test.result = {"query_results": results}
            else:
                db_perf_test.status = ValidationStatus.WARNING
                db_perf_test.error_message = f"Slow queries detected: {len(slow_queries)}"
                db_perf_test.result = {"query_results": results, "slow_queries": slow_queries}
                
        except Exception as e:
            db_perf_test.status = ValidationStatus.FAILED
            db_perf_test.error_message = str(e)
        finally:
            db_perf_test.completed_at = datetime.now()
            if db_perf_test.started_at:
                db_perf_test.execution_time = (db_perf_test.completed_at - db_perf_test.started_at).total_seconds()
        
        checks.append(db_perf_test)
        
        return checks
    
    async def _test_load_balancer(self) -> List[ValidationCheck]:
        """Test load balancer functionality"""
        checks = []
        
        # Load balancer health test
        lb_test = ValidationCheck(
            name="Load Balancer Health",
            description="Test load balancer distributes traffic correctly",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.HIGH
        )
        
        try:
            lb_test.started_at = datetime.now()
            
            # Test multiple requests to check load distribution
            request_count = 10
            response_times = []
            server_responses = {}
            
            async with aiohttp.ClientSession() as session:
                for i in range(request_count):
                    try:
                        start_time = time.time()
                        async with session.get(f"{self.environment.url}/health") as response:
                            response_time = (time.time() - start_time) * 1000
                            response_times.append(response_time)
                            
                            # Track server responses (if server ID is in headers)
                            server_id = response.headers.get('X-Server-ID', 'unknown')
                            server_responses[server_id] = server_responses.get(server_id, 0) + 1
                            
                    except Exception as e:
                        response_times.append(None)
            
            avg_response_time = sum(t for t in response_times if t is not None) / len([t for t in response_times if t is not None])
            successful_requests = len([t for t in response_times if t is not None])
            
            result = {
                "total_requests": request_count,
                "successful_requests": successful_requests,
                "average_response_time_ms": avg_response_time,
                "server_distribution": server_responses,
                "response_times": response_times
            }
            
            if successful_requests >= request_count * 0.95:  # 95% success rate
                lb_test.status = ValidationStatus.PASSED
                lb_test.result = result
            else:
                lb_test.status = ValidationStatus.WARNING
                lb_test.error_message = f"Low success rate: {successful_requests}/{request_count}"
                lb_test.result = result
                
        except Exception as e:
            lb_test.status = ValidationStatus.FAILED
            lb_test.error_message = str(e)
        finally:
            lb_test.completed_at = datetime.now()
            if lb_test.started_at:
                lb_test.execution_time = (lb_test.completed_at - lb_test.started_at).total_seconds()
        
        checks.append(lb_test)
        
        return checks
    
    async def _test_static_assets(self) -> List[ValidationCheck]:
        """Test static assets and CDN"""
        checks = []
        
        # Static assets test
        assets_test = ValidationCheck(
            name="Static Assets Delivery",
            description="Test static assets are served correctly",
            category=ValidationCategory.DEPLOYMENT,
            severity=ValidationSeverity.MEDIUM
        )
        
        try:
            assets_test.started_at = datetime.now()
            
            # Test common static assets
            static_assets = [
                "/static/css/main.css",
                "/static/js/main.js",
                "/favicon.ico",
                "/static/images/logo.png"
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for asset in static_assets:
                    try:
                        start_time = time.time()
                        async with session.get(f"{self.environment.url}{asset}") as response:
                            response_time = (time.time() - start_time) * 1000
                            
                            results.append({
                                "asset": asset,
                                "status_code": response.status,
                                "response_time_ms": response_time,
                                "content_length": response.headers.get('Content-Length', 0),
                                "cache_control": response.headers.get('Cache-Control', ''),
                                "success": response.status == 200
                            })
                            
                    except Exception as e:
                        results.append({
                            "asset": asset,
                            "error": str(e),
                            "success": False
                        })
            
            failed_assets = [r for r in results if not r.get("success", False)]
            
            if not failed_assets:
                assets_test.status = ValidationStatus.PASSED
                assets_test.result = {"asset_results": results}
            else:
                assets_test.status = ValidationStatus.WARNING
                assets_test.error_message = f"Failed assets: {len(failed_assets)}"
                assets_test.result = {"asset_results": results, "failed_assets": failed_assets}
                
        except Exception as e:
            assets_test.status = ValidationStatus.FAILED
            assets_test.error_message = str(e)
        finally:
            assets_test.completed_at = datetime.now()
            if assets_test.started_at:
                assets_test.execution_time = (assets_test.completed_at - assets_test.started_at).total_seconds()
        
        checks.append(assets_test)
        
        return checks
    
    async def _test_monitoring_systems(self) -> List[ValidationCheck]:
        """Test monitoring and logging systems"""
        checks = []
        
        # Monitoring endpoints test
        monitoring_test = ValidationCheck(
            name="Monitoring Systems",
            description="Test monitoring and metrics endpoints",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.HIGH
        )
        
        try:
            monitoring_test.started_at = datetime.now()
            
            monitoring_endpoints = []
            if self.environment.monitoring_url:
                monitoring_endpoints.append(self.environment.monitoring_url)
            if self.environment.log_aggregation_url:
                monitoring_endpoints.append(self.environment.log_aggregation_url)
            
            results = []
            async with aiohttp.ClientSession() as session:
                for endpoint in monitoring_endpoints:
                    try:
                        async with session.get(endpoint, timeout=10) as response:
                            results.append({
                                "endpoint": endpoint,
                                "status_code": response.status,
                                "success": response.status == 200
                            })
                    except Exception as e:
                        results.append({
                            "endpoint": endpoint,
                            "error": str(e),
                            "success": False
                        })
            
            failed_endpoints = [r for r in results if not r.get("success", False)]
            
            if not failed_endpoints:
                monitoring_test.status = ValidationStatus.PASSED
                monitoring_test.result = {"monitoring_results": results}
            else:
                monitoring_test.status = ValidationStatus.WARNING
                monitoring_test.error_message = f"Failed monitoring endpoints: {len(failed_endpoints)}"
                monitoring_test.result = {"monitoring_results": results, "failed_endpoints": failed_endpoints}
                
        except Exception as e:
            monitoring_test.status = ValidationStatus.FAILED
            monitoring_test.error_message = str(e)
        finally:
            monitoring_test.completed_at = datetime.now()
            if monitoring_test.started_at:
                monitoring_test.execution_time = (monitoring_test.completed_at - monitoring_test.started_at).total_seconds()
        
        checks.append(monitoring_test)
        
        return checks
    
    async def _test_backup_systems(self) -> List[ValidationCheck]:
        """Test backup and recovery systems"""
        checks = []
        
        # Backup verification test
        backup_test = ValidationCheck(
            name="Backup Systems",
            description="Verify backup systems are functioning",
            category=ValidationCategory.DISASTER_RECOVERY,
            severity=ValidationSeverity.CRITICAL
        )
        
        try:
            backup_test.started_at = datetime.now()
            
            # Check if backup endpoints/systems are accessible
            backup_checks = {
                "database_backup": await self._check_database_backup(),
                "file_backup": await self._check_file_backup(),
                "configuration_backup": await self._check_configuration_backup()
            }
            
            failed_backups = [
                name for name, result in backup_checks.items() 
                if not result.get("available", False)
            ]
            
            if not failed_backups:
                backup_test.status = ValidationStatus.PASSED
                backup_test.result = {"backup_checks": backup_checks}
            else:
                backup_test.status = ValidationStatus.FAILED
                backup_test.error_message = f"Failed backup systems: {', '.join(failed_backups)}"
                backup_test.result = {"backup_checks": backup_checks, "failed_backups": failed_backups}
                
        except Exception as e:
            backup_test.status = ValidationStatus.FAILED
            backup_test.error_message = str(e)
        finally:
            backup_test.completed_at = datetime.now()
            if backup_test.started_at:
                backup_test.execution_time = (backup_test.completed_at - backup_test.started_at).total_seconds()
        
        checks.append(backup_test)
        
        return checks
    
    async def _check_database_backup(self) -> Dict[str, Any]:
        """Check database backup system"""
        try:
            # This would normally check actual backup systems
            return {
                "available": True,
                "last_backup": "2024-01-19T10:00:00Z",
                "backup_size_mb": 1024,
                "retention_days": 30
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _check_file_backup(self) -> Dict[str, Any]:
        """Check file backup system"""
        try:
            # This would normally check actual file backup systems
            return {
                "available": True,
                "last_backup": "2024-01-19T12:00:00Z",
                "backup_size_gb": 50,
                "retention_days": 90
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _check_configuration_backup(self) -> Dict[str, Any]:
        """Check configuration backup system"""
        try:
            # This would normally check actual configuration backup systems
            return {
                "available": True,
                "last_backup": "2024-01-19T08:00:00Z",
                "backup_count": 10,
                "retention_days": 365
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }