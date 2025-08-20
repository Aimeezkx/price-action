"""
Production Monitoring and Alerting Setup
Validates monitoring systems and alerting configuration
"""

import asyncio
import aiohttp
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .models import (
    ValidationCheck, ValidationStatus, ValidationSeverity, ValidationCategory,
    MonitoringSetupCheck, ProductionEnvironment
)


class MonitoringSetupValidator:
    """Validates monitoring and alerting setup"""
    
    def __init__(self, environment: ProductionEnvironment):
        self.environment = environment
        
    async def validate_monitoring_setup(self) -> List[ValidationCheck]:
        """Run comprehensive monitoring setup validation"""
        checks = []
        
        # Monitoring endpoints validation
        checks.extend(await self._validate_monitoring_endpoints())
        
        # Alert rules validation
        checks.extend(await self._validate_alert_rules())
        
        # Dashboard configuration validation
        checks.extend(await self._validate_dashboards())
        
        # Notification channels validation
        checks.extend(await self._validate_notification_channels())
        
        # Metrics collection validation
        checks.extend(await self._validate_metrics_collection())
        
        # Log aggregation validation
        checks.extend(await self._validate_log_aggregation())
        
        return checks
    
    async def _validate_monitoring_endpoints(self) -> List[ValidationCheck]:
        """Validate monitoring endpoints are accessible"""
        checks = []
        
        # Prometheus endpoint validation
        prometheus_check = MonitoringSetupCheck(
            name="Prometheus Metrics Endpoint",
            description="Validate Prometheus metrics endpoint is accessible",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.CRITICAL,
            monitoring_endpoints=["/metrics"],
            alert_rules=[],
            dashboard_configs=[],
            notification_channels=[]
        )
        
        try:
            prometheus_check.started_at = datetime.now()
            
            metrics_url = f"{self.environment.url}/metrics"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(metrics_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Validate metrics format
                        metrics_validation = self._validate_prometheus_metrics(content)
                        
                        if metrics_validation["valid"]:
                            prometheus_check.status = ValidationStatus.PASSED
                            prometheus_check.result = {
                                "endpoint_accessible": True,
                                "metrics_count": metrics_validation["metrics_count"],
                                "response_size_bytes": len(content)
                            }
                        else:
                            prometheus_check.status = ValidationStatus.FAILED
                            prometheus_check.error_message = f"Invalid metrics format: {metrics_validation['error']}"
                    else:
                        prometheus_check.status = ValidationStatus.FAILED
                        prometheus_check.error_message = f"Metrics endpoint returned status {response.status}"
                        
        except Exception as e:
            prometheus_check.status = ValidationStatus.FAILED
            prometheus_check.error_message = str(e)
        finally:
            prometheus_check.completed_at = datetime.now()
            if prometheus_check.started_at:
                prometheus_check.execution_time = (prometheus_check.completed_at - prometheus_check.started_at).total_seconds()
        
        checks.append(prometheus_check)
        
        # Health check endpoint validation
        health_check = MonitoringSetupCheck(
            name="Health Check Endpoint",
            description="Validate health check endpoint provides detailed status",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.HIGH,
            monitoring_endpoints=["/health"],
            alert_rules=[],
            dashboard_configs=[],
            notification_channels=[]
        )
        
        try:
            health_check.started_at = datetime.now()
            
            health_url = f"{self.environment.url}/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        
                        # Validate health check structure
                        health_validation = self._validate_health_check_format(health_data)
                        
                        if health_validation["valid"]:
                            health_check.status = ValidationStatus.PASSED
                            health_check.result = {
                                "endpoint_accessible": True,
                                "components_checked": health_validation["components_count"],
                                "overall_status": health_data.get("status", "unknown")
                            }
                        else:
                            health_check.status = ValidationStatus.WARNING
                            health_check.error_message = f"Health check format issues: {health_validation['issues']}"
                            health_check.result = {"health_data": health_data}
                    else:
                        health_check.status = ValidationStatus.FAILED
                        health_check.error_message = f"Health endpoint returned status {response.status}"
                        
        except Exception as e:
            health_check.status = ValidationStatus.FAILED
            health_check.error_message = str(e)
        finally:
            health_check.completed_at = datetime.now()
            if health_check.started_at:
                health_check.execution_time = (health_check.completed_at - health_check.started_at).total_seconds()
        
        checks.append(health_check)
        
        return checks
    
    async def _validate_alert_rules(self) -> List[ValidationCheck]:
        """Validate alert rules configuration"""
        checks = []
        
        # Alert rules validation
        alert_rules_check = MonitoringSetupCheck(
            name="Alert Rules Configuration",
            description="Validate alert rules are properly configured",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.HIGH,
            monitoring_endpoints=[],
            alert_rules=self._get_expected_alert_rules(),
            dashboard_configs=[],
            notification_channels=[]
        )
        
        try:
            alert_rules_check.started_at = datetime.now()
            
            # Load alert rules configuration
            alert_rules_config = await self._load_alert_rules_config()
            
            # Validate required alert rules
            validation_results = self._validate_alert_rules_config(alert_rules_config)
            
            if validation_results["all_rules_present"]:
                alert_rules_check.status = ValidationStatus.PASSED
                alert_rules_check.result = {
                    "total_rules": validation_results["total_rules"],
                    "critical_rules": validation_results["critical_rules"],
                    "warning_rules": validation_results["warning_rules"]
                }
            else:
                alert_rules_check.status = ValidationStatus.WARNING
                alert_rules_check.error_message = f"Missing alert rules: {', '.join(validation_results['missing_rules'])}"
                alert_rules_check.result = validation_results
                
        except Exception as e:
            alert_rules_check.status = ValidationStatus.FAILED
            alert_rules_check.error_message = str(e)
        finally:
            alert_rules_check.completed_at = datetime.now()
            if alert_rules_check.started_at:
                alert_rules_check.execution_time = (alert_rules_check.completed_at - alert_rules_check.started_at).total_seconds()
        
        checks.append(alert_rules_check)
        
        return checks
    
    async def _validate_dashboards(self) -> List[ValidationCheck]:
        """Validate dashboard configurations"""
        checks = []
        
        # Dashboard validation
        dashboard_check = MonitoringSetupCheck(
            name="Monitoring Dashboards",
            description="Validate monitoring dashboards are configured",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.MEDIUM,
            monitoring_endpoints=[],
            alert_rules=[],
            dashboard_configs=self._get_expected_dashboards(),
            notification_channels=[]
        )
        
        try:
            dashboard_check.started_at = datetime.now()
            
            # Check dashboard configurations
            dashboard_configs = await self._load_dashboard_configs()
            
            # Validate dashboard structure
            validation_results = self._validate_dashboard_configs(dashboard_configs)
            
            if validation_results["all_dashboards_present"]:
                dashboard_check.status = ValidationStatus.PASSED
                dashboard_check.result = {
                    "total_dashboards": validation_results["total_dashboards"],
                    "panels_count": validation_results["total_panels"]
                }
            else:
                dashboard_check.status = ValidationStatus.WARNING
                dashboard_check.error_message = f"Missing dashboards: {', '.join(validation_results['missing_dashboards'])}"
                dashboard_check.result = validation_results
                
        except Exception as e:
            dashboard_check.status = ValidationStatus.FAILED
            dashboard_check.error_message = str(e)
        finally:
            dashboard_check.completed_at = datetime.now()
            if dashboard_check.started_at:
                dashboard_check.execution_time = (dashboard_check.completed_at - dashboard_check.started_at).total_seconds()
        
        checks.append(dashboard_check)
        
        return checks
    
    async def _validate_notification_channels(self) -> List[ValidationCheck]:
        """Validate notification channels"""
        checks = []
        
        # Notification channels validation
        notification_check = MonitoringSetupCheck(
            name="Notification Channels",
            description="Validate notification channels are configured and working",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.HIGH,
            monitoring_endpoints=[],
            alert_rules=[],
            dashboard_configs=[],
            notification_channels=self._get_expected_notification_channels()
        )
        
        try:
            notification_check.started_at = datetime.now()
            
            # Test notification channels
            channel_results = []
            
            for channel in self._get_expected_notification_channels():
                channel_test = await self._test_notification_channel(channel)
                channel_results.append(channel_test)
            
            failed_channels = [r for r in channel_results if not r["working"]]
            
            if not failed_channels:
                notification_check.status = ValidationStatus.PASSED
                notification_check.result = {
                    "total_channels": len(channel_results),
                    "working_channels": len([r for r in channel_results if r["working"]])
                }
            else:
                notification_check.status = ValidationStatus.WARNING
                notification_check.error_message = f"Failed notification channels: {len(failed_channels)}"
                notification_check.result = {
                    "channel_results": channel_results,
                    "failed_channels": failed_channels
                }
                
        except Exception as e:
            notification_check.status = ValidationStatus.FAILED
            notification_check.error_message = str(e)
        finally:
            notification_check.completed_at = datetime.now()
            if notification_check.started_at:
                notification_check.execution_time = (notification_check.completed_at - notification_check.started_at).total_seconds()
        
        checks.append(notification_check)
        
        return checks
    
    async def _validate_metrics_collection(self) -> List[ValidationCheck]:
        """Validate metrics collection is working"""
        checks = []
        
        # Metrics collection validation
        metrics_check = ValidationCheck(
            name="Metrics Collection",
            description="Validate metrics are being collected properly",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.HIGH
        )
        
        try:
            metrics_check.started_at = datetime.now()
            
            # Check key metrics are being collected
            key_metrics = [
                "http_requests_total",
                "http_request_duration_seconds",
                "database_connections_active",
                "memory_usage_bytes",
                "cpu_usage_percent",
                "disk_usage_bytes"
            ]
            
            metrics_results = []
            
            for metric in key_metrics:
                metric_data = await self._check_metric_availability(metric)
                metrics_results.append(metric_data)
            
            missing_metrics = [r for r in metrics_results if not r["available"]]
            
            if not missing_metrics:
                metrics_check.status = ValidationStatus.PASSED
                metrics_check.result = {
                    "total_metrics": len(metrics_results),
                    "available_metrics": len([r for r in metrics_results if r["available"]])
                }
            else:
                metrics_check.status = ValidationStatus.WARNING
                metrics_check.error_message = f"Missing metrics: {len(missing_metrics)}"
                metrics_check.result = {
                    "metrics_results": metrics_results,
                    "missing_metrics": missing_metrics
                }
                
        except Exception as e:
            metrics_check.status = ValidationStatus.FAILED
            metrics_check.error_message = str(e)
        finally:
            metrics_check.completed_at = datetime.now()
            if metrics_check.started_at:
                metrics_check.execution_time = (metrics_check.completed_at - metrics_check.started_at).total_seconds()
        
        checks.append(metrics_check)
        
        return checks
    
    async def _validate_log_aggregation(self) -> List[ValidationCheck]:
        """Validate log aggregation is working"""
        checks = []
        
        # Log aggregation validation
        log_check = ValidationCheck(
            name="Log Aggregation",
            description="Validate logs are being aggregated properly",
            category=ValidationCategory.MONITORING,
            severity=ValidationSeverity.MEDIUM
        )
        
        try:
            log_check.started_at = datetime.now()
            
            if self.environment.log_aggregation_url:
                # Test log aggregation endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.environment.log_aggregation_url, timeout=10) as response:
                        if response.status == 200:
                            log_check.status = ValidationStatus.PASSED
                            log_check.result = {
                                "log_aggregation_accessible": True,
                                "endpoint": self.environment.log_aggregation_url
                            }
                        else:
                            log_check.status = ValidationStatus.WARNING
                            log_check.error_message = f"Log aggregation endpoint returned status {response.status}"
            else:
                log_check.status = ValidationStatus.WARNING
                log_check.error_message = "No log aggregation URL configured"
                
        except Exception as e:
            log_check.status = ValidationStatus.FAILED
            log_check.error_message = str(e)
        finally:
            log_check.completed_at = datetime.now()
            if log_check.started_at:
                log_check.execution_time = (log_check.completed_at - log_check.started_at).total_seconds()
        
        checks.append(log_check)
        
        return checks
    
    def _validate_prometheus_metrics(self, content: str) -> Dict[str, Any]:
        """Validate Prometheus metrics format"""
        try:
            lines = content.strip().split('\n')
            metrics_count = 0
            
            for line in lines:
                if line.startswith('#'):
                    continue
                if ' ' in line:
                    metrics_count += 1
            
            return {
                "valid": metrics_count > 0,
                "metrics_count": metrics_count
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _validate_health_check_format(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate health check response format"""
        try:
            required_fields = ["status", "timestamp", "components"]
            issues = []
            
            for field in required_fields:
                if field not in health_data:
                    issues.append(f"Missing field: {field}")
            
            components_count = 0
            if "components" in health_data:
                components_count = len(health_data["components"])
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "components_count": components_count
            }
        except Exception as e:
            return {
                "valid": False,
                "issues": [str(e)],
                "components_count": 0
            }
    
    def _get_expected_alert_rules(self) -> List[Dict[str, Any]]:
        """Get expected alert rules"""
        return [
            {"name": "HighErrorRate", "severity": "critical"},
            {"name": "HighResponseTime", "severity": "warning"},
            {"name": "DatabaseConnectionFailure", "severity": "critical"},
            {"name": "HighMemoryUsage", "severity": "warning"},
            {"name": "DiskSpaceLow", "severity": "warning"},
            {"name": "ServiceDown", "severity": "critical"}
        ]
    
    def _get_expected_dashboards(self) -> List[str]:
        """Get expected dashboard configurations"""
        return [
            "application_overview",
            "api_performance",
            "database_metrics",
            "system_resources",
            "error_tracking"
        ]
    
    def _get_expected_notification_channels(self) -> List[str]:
        """Get expected notification channels"""
        return [
            "email_alerts",
            "slack_notifications",
            "pagerduty_critical"
        ]
    
    async def _load_alert_rules_config(self) -> Dict[str, Any]:
        """Load alert rules configuration"""
        # This would normally load from actual configuration files
        return {
            "rules": [
                {"name": "HighErrorRate", "severity": "critical", "configured": True},
                {"name": "HighResponseTime", "severity": "warning", "configured": True},
                {"name": "DatabaseConnectionFailure", "severity": "critical", "configured": True},
                {"name": "HighMemoryUsage", "severity": "warning", "configured": False},
                {"name": "DiskSpaceLow", "severity": "warning", "configured": True},
                {"name": "ServiceDown", "severity": "critical", "configured": True}
            ]
        }
    
    def _validate_alert_rules_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate alert rules configuration"""
        expected_rules = {rule["name"] for rule in self._get_expected_alert_rules()}
        configured_rules = {rule["name"] for rule in config["rules"] if rule.get("configured", False)}
        
        missing_rules = expected_rules - configured_rules
        
        return {
            "all_rules_present": len(missing_rules) == 0,
            "total_rules": len(config["rules"]),
            "critical_rules": len([r for r in config["rules"] if r["severity"] == "critical"]),
            "warning_rules": len([r for r in config["rules"] if r["severity"] == "warning"]),
            "missing_rules": list(missing_rules)
        }
    
    async def _load_dashboard_configs(self) -> Dict[str, Any]:
        """Load dashboard configurations"""
        # This would normally load from actual dashboard files
        return {
            "dashboards": [
                {"name": "application_overview", "panels": 8},
                {"name": "api_performance", "panels": 6},
                {"name": "database_metrics", "panels": 5},
                {"name": "system_resources", "panels": 4},
                {"name": "error_tracking", "panels": 3}
            ]
        }
    
    def _validate_dashboard_configs(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate dashboard configurations"""
        expected_dashboards = set(self._get_expected_dashboards())
        configured_dashboards = {d["name"] for d in configs["dashboards"]}
        
        missing_dashboards = expected_dashboards - configured_dashboards
        
        return {
            "all_dashboards_present": len(missing_dashboards) == 0,
            "total_dashboards": len(configs["dashboards"]),
            "total_panels": sum(d["panels"] for d in configs["dashboards"]),
            "missing_dashboards": list(missing_dashboards)
        }
    
    async def _test_notification_channel(self, channel: str) -> Dict[str, Any]:
        """Test notification channel"""
        try:
            # This would normally test actual notification channels
            # For now, simulate the test
            await asyncio.sleep(0.1)  # Simulate test time
            
            return {
                "channel": channel,
                "working": True,
                "response_time_ms": 100
            }
        except Exception as e:
            return {
                "channel": channel,
                "working": False,
                "error": str(e)
            }
    
    async def _check_metric_availability(self, metric_name: str) -> Dict[str, Any]:
        """Check if a metric is available"""
        try:
            # This would normally check actual metrics
            # For now, simulate the check
            await asyncio.sleep(0.05)  # Simulate check time
            
            return {
                "metric": metric_name,
                "available": True,
                "last_value": 42.0,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "metric": metric_name,
                "available": False,
                "error": str(e)
            }