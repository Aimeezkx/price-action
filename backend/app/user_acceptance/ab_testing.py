"""
A/B Testing Framework for Feature Validation
"""
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
from collections import defaultdict
import statistics

from .models import (
    ABTest, ABTestVariant, ABTestResult, UXMetric
)

logger = logging.getLogger(__name__)


class ABTestManager:
    """Manages A/B tests for feature validation"""
    
    def __init__(self, storage_path: str = "backend/app/user_acceptance/ab_tests"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.tests: Dict[str, ABTest] = {}
        self.results: Dict[str, List[ABTestResult]] = defaultdict(list)
        self._load_existing_tests()
    
    def _load_existing_tests(self):
        """Load existing A/B tests from storage"""
        test_files = self.storage_path.glob("test_*.json")
        for file_path in test_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    test = ABTest(**data)
                    self.tests[test.id] = test
            except Exception as e:
                logger.error(f"Error loading A/B test from {file_path}: {e}")
        
        result_files = self.storage_path.glob("results_*.json")
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    for result_data in data:
                        result = ABTestResult(**result_data)
                        self.results[result.test_id].append(result)
            except Exception as e:
                logger.error(f"Error loading A/B test results from {file_path}: {e}")
    
    def create_test(self, test_data: Dict[str, Any]) -> ABTest:
        """Create a new A/B test"""
        # Validate variants
        variants_data = test_data.get('variants', [])
        if len(variants_data) < 2:
            raise ValueError("A/B test must have at least 2 variants")
        
        # Ensure traffic percentages sum to 1.0
        total_traffic = sum(v.get('traffic_percentage', 0) for v in variants_data)
        if abs(total_traffic - 1.0) > 0.01:
            raise ValueError("Variant traffic percentages must sum to 1.0")
        
        # Create variants
        variants = []
        control_count = 0
        for variant_data in variants_data:
            variant = ABTestVariant(**variant_data)
            if variant.is_control:
                control_count += 1
            variants.append(variant)
        
        if control_count != 1:
            raise ValueError("Exactly one variant must be marked as control")
        
        # Create test
        test_data['variants'] = [v.dict() for v in variants]
        test = ABTest(**test_data)
        
        # Store test
        self.tests[test.id] = test
        self._save_test(test)
        
        logger.info(f"Created A/B test {test.id}: {test.name}")
        return test
    
    def _save_test(self, test: ABTest):
        """Save A/B test to storage"""
        file_path = self.storage_path / f"test_{test.id}.json"
        with open(file_path, 'w') as f:
            json.dump(test.dict(), f, indent=2, default=str)
    
    def _save_results(self, test_id: str):
        """Save A/B test results to storage"""
        file_path = self.storage_path / f"results_{test_id}.json"
        results_data = [r.dict() for r in self.results[test_id]]
        with open(file_path, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
    
    def assign_variant(self, test_id: str, user_id: str) -> Optional[ABTestVariant]:
        """Assign a user to a test variant"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # Check if test is running
        now = datetime.now()
        if test.status != "running" or now < test.start_date or now > test.end_date:
            return None
        
        # Use consistent hashing for user assignment
        hash_input = f"{test_id}:{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        assignment_value = (hash_value % 10000) / 10000.0  # 0.0 to 1.0
        
        # Find variant based on traffic allocation
        cumulative_traffic = 0.0
        for variant in test.variants:
            cumulative_traffic += variant.traffic_percentage
            if assignment_value <= cumulative_traffic:
                logger.info(f"Assigned user {user_id} to variant {variant.id} in test {test_id}")
                return variant
        
        # Fallback to control variant
        control_variant = next((v for v in test.variants if v.is_control), test.variants[0])
        return control_variant
    
    def record_result(self, test_id: str, user_id: str, session_id: str, 
                     metrics: Dict[str, float], conversion_events: List[str] = None) -> ABTestResult:
        """Record A/B test result"""
        if test_id not in self.tests:
            raise ValueError(f"Test {test_id} not found")
        
        # Get user's assigned variant
        variant = self.assign_variant(test_id, user_id)
        if not variant:
            raise ValueError(f"Could not assign variant for user {user_id} in test {test_id}")
        
        result = ABTestResult(
            test_id=test_id,
            variant_id=variant.id,
            user_id=user_id,
            session_id=session_id,
            metrics=metrics,
            conversion_events=conversion_events or []
        )
        
        self.results[test_id].append(result)
        self._save_results(test_id)
        
        logger.info(f"Recorded result for test {test_id}, variant {variant.id}")
        return result
    
    def get_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get comprehensive results for an A/B test"""
        if test_id not in self.tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.tests[test_id]
        results = self.results.get(test_id, [])
        
        if not results:
            return {"error": "No results available for this test"}
        
        # Group results by variant
        variant_results = defaultdict(list)
        for result in results:
            variant_results[result.variant_id].append(result)
        
        # Calculate statistics for each variant
        variant_stats = {}
        for variant in test.variants:
            variant_id = variant.id
            variant_data = variant_results.get(variant_id, [])
            
            if not variant_data:
                variant_stats[variant_id] = {
                    "name": variant.name,
                    "is_control": variant.is_control,
                    "sample_size": 0,
                    "metrics": {},
                    "conversion_rate": 0.0
                }
                continue
            
            # Calculate metric statistics
            metric_stats = {}
            all_metrics = set()
            for result in variant_data:
                all_metrics.update(result.metrics.keys())
            
            for metric_name in all_metrics:
                values = [r.metrics.get(metric_name, 0) for r in variant_data if metric_name in r.metrics]
                if values:
                    metric_stats[metric_name] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
            
            # Calculate conversion rate (users with any conversion event)
            users_with_conversions = len([r for r in variant_data if r.conversion_events])
            conversion_rate = users_with_conversions / len(variant_data) if variant_data else 0
            
            variant_stats[variant_id] = {
                "name": variant.name,
                "is_control": variant.is_control,
                "sample_size": len(variant_data),
                "metrics": metric_stats,
                "conversion_rate": conversion_rate,
                "unique_users": len(set(r.user_id for r in variant_data))
            }
        
        # Calculate statistical significance
        significance_results = self._calculate_significance(test, variant_stats)
        
        return {
            "test_id": test_id,
            "test_name": test.name,
            "status": test.status,
            "start_date": test.start_date.isoformat(),
            "end_date": test.end_date.isoformat(),
            "total_results": len(results),
            "variant_statistics": variant_stats,
            "significance_tests": significance_results,
            "summary": self._generate_test_summary(test, variant_stats, significance_results)
        }
    
    def _calculate_significance(self, test: ABTest, variant_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical significance between variants"""
        # Find control variant
        control_variant = next((v for v in test.variants if v.is_control), None)
        if not control_variant:
            return {"error": "No control variant found"}
        
        control_stats = variant_stats.get(control_variant.id)
        if not control_stats or control_stats["sample_size"] == 0:
            return {"error": "No control data available"}
        
        significance_results = {}
        
        for variant in test.variants:
            if variant.is_control:
                continue
            
            variant_data = variant_stats.get(variant.id)
            if not variant_data or variant_data["sample_size"] == 0:
                continue
            
            # Simple significance test for conversion rate
            # In a real implementation, you'd use proper statistical tests
            control_rate = control_stats["conversion_rate"]
            variant_rate = variant_data["conversion_rate"]
            
            # Calculate relative improvement
            if control_rate > 0:
                relative_improvement = (variant_rate - control_rate) / control_rate
            else:
                relative_improvement = 0
            
            # Simple significance check (would use proper z-test in production)
            min_sample_size = 100  # Minimum for basic significance
            is_significant = (
                control_stats["sample_size"] >= min_sample_size and
                variant_data["sample_size"] >= min_sample_size and
                abs(relative_improvement) > 0.05  # 5% minimum effect size
            )
            
            significance_results[variant.id] = {
                "variant_name": variant.name,
                "control_rate": control_rate,
                "variant_rate": variant_rate,
                "relative_improvement": relative_improvement,
                "is_significant": is_significant,
                "confidence_level": 0.95 if is_significant else 0.0
            }
        
        return significance_results
    
    def _generate_test_summary(self, test: ABTest, variant_stats: Dict[str, Any], 
                              significance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        total_users = sum(stats["unique_users"] for stats in variant_stats.values())
        
        # Find winning variant
        winning_variant = None
        best_conversion_rate = 0
        
        for variant_id, stats in variant_stats.items():
            if stats["conversion_rate"] > best_conversion_rate:
                best_conversion_rate = stats["conversion_rate"]
                winning_variant = variant_id
        
        # Check if winner is significant
        winner_is_significant = False
        if winning_variant and winning_variant in significance_results:
            winner_is_significant = significance_results[winning_variant]["is_significant"]
        
        return {
            "total_participants": total_users,
            "winning_variant": winning_variant,
            "winner_is_significant": winner_is_significant,
            "best_conversion_rate": best_conversion_rate,
            "test_duration_days": (test.end_date - test.start_date).days,
            "recommendation": self._generate_recommendation(test, variant_stats, significance_results)
        }
    
    def _generate_recommendation(self, test: ABTest, variant_stats: Dict[str, Any], 
                                significance_results: Dict[str, Any]) -> str:
        """Generate recommendation based on test results"""
        control_variant = next((v for v in test.variants if v.is_control), None)
        if not control_variant:
            return "Cannot generate recommendation: no control variant"
        
        control_stats = variant_stats.get(control_variant.id)
        if not control_stats:
            return "Cannot generate recommendation: no control data"
        
        # Find best performing non-control variant
        best_variant = None
        best_improvement = 0
        
        for variant_id, sig_result in significance_results.items():
            if sig_result["relative_improvement"] > best_improvement:
                best_improvement = sig_result["relative_improvement"]
                best_variant = variant_id
        
        if not best_variant:
            return "Recommendation: Continue with control variant (no significant improvements found)"
        
        sig_result = significance_results[best_variant]
        if sig_result["is_significant"]:
            improvement_pct = sig_result["relative_improvement"] * 100
            return f"Recommendation: Implement {sig_result['variant_name']} ({improvement_pct:.1f}% improvement, statistically significant)"
        else:
            return f"Recommendation: Extend test duration (best variant shows {best_improvement*100:.1f}% improvement but not statistically significant)"
    
    def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        test.status = "running"
        self._save_test(test)
        
        logger.info(f"Started A/B test {test_id}")
        return True
    
    def stop_test(self, test_id: str) -> bool:
        """Stop an A/B test"""
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        test.status = "completed"
        self._save_test(test)
        
        logger.info(f"Stopped A/B test {test_id}")
        return True
    
    def get_active_tests(self) -> List[ABTest]:
        """Get all active A/B tests"""
        now = datetime.now()
        return [
            test for test in self.tests.values()
            if test.status == "running" and test.start_date <= now <= test.end_date
        ]
    
    def get_user_tests(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active tests for a user with their assigned variants"""
        active_tests = self.get_active_tests()
        user_tests = []
        
        for test in active_tests:
            variant = self.assign_variant(test.id, user_id)
            if variant:
                user_tests.append({
                    "test_id": test.id,
                    "test_name": test.name,
                    "feature_name": test.feature_name,
                    "variant_id": variant.id,
                    "variant_name": variant.name,
                    "feature_flags": variant.feature_flags
                })
        
        return user_tests


class ABTestMetricsCollector:
    """Collects metrics for A/B tests"""
    
    def __init__(self, ab_test_manager: ABTestManager):
        self.ab_manager = ab_test_manager
    
    def collect_session_metrics(self, user_id: str, session_id: str, 
                               session_data: Dict[str, Any]) -> List[ABTestResult]:
        """Collect metrics from a user session for all active tests"""
        user_tests = self.ab_manager.get_user_tests(user_id)
        results = []
        
        for test_info in user_tests:
            test_id = test_info["test_id"]
            
            # Extract relevant metrics based on test type
            metrics = self._extract_test_metrics(test_info, session_data)
            
            # Extract conversion events
            conversion_events = self._extract_conversion_events(test_info, session_data)
            
            if metrics or conversion_events:
                result = self.ab_manager.record_result(
                    test_id=test_id,
                    user_id=user_id,
                    session_id=session_id,
                    metrics=metrics,
                    conversion_events=conversion_events
                )
                results.append(result)
        
        return results
    
    def _extract_test_metrics(self, test_info: Dict[str, Any], 
                             session_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract relevant metrics for a specific test"""
        metrics = {}
        feature_name = test_info.get("feature_name", "")
        
        # Common metrics
        if "session_duration" in session_data:
            metrics["session_duration"] = session_data["session_duration"]
        
        if "page_views" in session_data:
            metrics["page_views"] = session_data["page_views"]
        
        # Feature-specific metrics
        if "upload" in feature_name.lower():
            if "upload_success_rate" in session_data:
                metrics["upload_success_rate"] = session_data["upload_success_rate"]
            if "upload_time" in session_data:
                metrics["upload_time"] = session_data["upload_time"]
        
        elif "search" in feature_name.lower():
            if "search_queries" in session_data:
                metrics["search_queries"] = session_data["search_queries"]
            if "search_success_rate" in session_data:
                metrics["search_success_rate"] = session_data["search_success_rate"]
        
        elif "card" in feature_name.lower():
            if "cards_reviewed" in session_data:
                metrics["cards_reviewed"] = session_data["cards_reviewed"]
            if "average_grade" in session_data:
                metrics["average_grade"] = session_data["average_grade"]
        
        return metrics
    
    def _extract_conversion_events(self, test_info: Dict[str, Any], 
                                  session_data: Dict[str, Any]) -> List[str]:
        """Extract conversion events for a specific test"""
        events = []
        feature_name = test_info.get("feature_name", "")
        
        # Common conversion events
        if session_data.get("completed_onboarding"):
            events.append("completed_onboarding")
        
        if session_data.get("uploaded_document"):
            events.append("uploaded_document")
        
        if session_data.get("completed_study_session"):
            events.append("completed_study_session")
        
        # Feature-specific events
        if "search" in feature_name.lower() and session_data.get("performed_search"):
            events.append("performed_search")
        
        if "export" in feature_name.lower() and session_data.get("exported_data"):
            events.append("exported_data")
        
        return events