"""
Performance Baseline Manager

Creates and manages performance baseline data for comparison and regression detection.
Tracks performance metrics over time and identifies performance regressions.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid


@dataclass
class PerformanceMetric:
    """Represents a single performance metric measurement"""
    name: str
    value: float
    unit: str
    timestamp: str
    test_case: str
    environment: str
    metadata: Dict[str, Any]


@dataclass
class PerformanceBaseline:
    """Represents a performance baseline for a specific metric"""
    metric_name: str
    test_case: str
    environment: str
    baseline_value: float
    unit: str
    confidence_interval: Tuple[float, float]
    sample_size: int
    created_at: str
    last_updated: str
    metadata: Dict[str, Any]


class PerformanceBaselineManager:
    """Manages performance baselines and regression detection"""
    
    def __init__(self, data_dir: str = "backend/tests/test_data/performance"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.baselines_file = self.data_dir / "baselines.json"
        self.metrics_file = self.data_dir / "metrics_history.json"
        self.regressions_file = self.data_dir / "regressions.json"
        
        # Performance thresholds
        self.regression_threshold = 0.15  # 15% degradation
        self.improvement_threshold = 0.10  # 10% improvement
        self.min_sample_size = 10
        
    def create_initial_baselines(self):
        """Create initial performance baselines for all test scenarios"""
        print("Creating initial performance baselines...")
        
        # Document processing baselines
        self._create_document_processing_baselines()
        
        # Search performance baselines
        self._create_search_performance_baselines()
        
        # API response time baselines
        self._create_api_response_baselines()
        
        # Frontend performance baselines
        self._create_frontend_performance_baselines()
        
        # Database performance baselines
        self._create_database_performance_baselines()
        
        # Memory usage baselines
        self._create_memory_usage_baselines()
        
        print("Initial performance baselines created!")
        
    def _create_document_processing_baselines(self):
        """Create baselines for document processing performance"""
        baselines = [
            {
                "metric_name": "pdf_processing_time",
                "test_case": "small_pdf_5_pages",
                "baseline_value": 8.5,
                "unit": "seconds",
                "confidence_interval": [7.2, 9.8],
                "sample_size": 50,
                "metadata": {
                    "file_size_mb": 2.1,
                    "page_count": 5,
                    "has_images": True,
                    "complexity": "medium"
                }
            },
            {
                "metric_name": "pdf_processing_time",
                "test_case": "medium_pdf_20_pages",
                "baseline_value": 32.4,
                "unit": "seconds",
                "confidence_interval": [28.1, 36.7],
                "sample_size": 50,
                "metadata": {
                    "file_size_mb": 8.7,
                    "page_count": 20,
                    "has_images": True,
                    "complexity": "high"
                }
            },
            {
                "metric_name": "pdf_processing_time",
                "test_case": "large_pdf_50_pages",
                "baseline_value": 89.2,
                "unit": "seconds",
                "confidence_interval": [78.5, 99.9],
                "sample_size": 30,
                "metadata": {
                    "file_size_mb": 25.3,
                    "page_count": 50,
                    "has_images": True,
                    "complexity": "high"
                }
            },
            {
                "metric_name": "docx_processing_time",
                "test_case": "medium_docx_15_pages",
                "baseline_value": 12.8,
                "unit": "seconds",
                "confidence_interval": [10.9, 14.7],
                "sample_size": 40,
                "metadata": {
                    "file_size_mb": 3.2,
                    "page_count": 15,
                    "has_tables": True,
                    "complexity": "medium"
                }
            }
        ]
        
        self._save_baselines("document_processing", baselines)
        
    def _create_search_performance_baselines(self):
        """Create baselines for search performance"""
        baselines = [
            {
                "metric_name": "full_text_search_time",
                "test_case": "simple_query_small_corpus",
                "baseline_value": 145.0,
                "unit": "milliseconds",
                "confidence_interval": [120.0, 170.0],
                "sample_size": 100,
                "metadata": {
                    "corpus_size": 100,
                    "query_length": 2,
                    "result_count": 15
                }
            },
            {
                "metric_name": "full_text_search_time",
                "test_case": "complex_query_large_corpus",
                "baseline_value": 380.0,
                "unit": "milliseconds",
                "confidence_interval": [320.0, 440.0],
                "sample_size": 100,
                "metadata": {
                    "corpus_size": 1000,
                    "query_length": 8,
                    "result_count": 45
                }
            },
            {
                "metric_name": "semantic_search_time",
                "test_case": "vector_similarity_search",
                "baseline_value": 280.0,
                "unit": "milliseconds",
                "confidence_interval": [240.0, 320.0],
                "sample_size": 80,
                "metadata": {
                    "vector_dimension": 768,
                    "corpus_size": 500,
                    "similarity_threshold": 0.7
                }
            },
            {
                "metric_name": "search_indexing_time",
                "test_case": "index_medium_document",
                "baseline_value": 5.2,
                "unit": "seconds",
                "confidence_interval": [4.1, 6.3],
                "sample_size": 60,
                "metadata": {
                    "document_size_mb": 5.0,
                    "text_blocks": 150,
                    "unique_terms": 2500
                }
            }
        ]
        
        self._save_baselines("search_performance", baselines)
        
    def _create_api_response_baselines(self):
        """Create baselines for API response times"""
        baselines = [
            {
                "metric_name": "api_response_time",
                "test_case": "get_documents_list",
                "baseline_value": 85.0,
                "unit": "milliseconds",
                "confidence_interval": [70.0, 100.0],
                "sample_size": 200,
                "metadata": {
                    "endpoint": "/api/documents",
                    "method": "GET",
                    "result_count": 20,
                    "includes_pagination": True
                }
            },
            {
                "metric_name": "api_response_time",
                "test_case": "upload_document",
                "baseline_value": 1250.0,
                "unit": "milliseconds",
                "confidence_interval": [1000.0, 1500.0],
                "sample_size": 150,
                "metadata": {
                    "endpoint": "/api/documents/upload",
                    "method": "POST",
                    "file_size_mb": 5.0,
                    "includes_validation": True
                }
            },
            {
                "metric_name": "api_response_time",
                "test_case": "get_flashcards",
                "baseline_value": 120.0,
                "unit": "milliseconds",
                "confidence_interval": [95.0, 145.0],
                "sample_size": 180,
                "metadata": {
                    "endpoint": "/api/cards",
                    "method": "GET",
                    "card_count": 50,
                    "includes_srs_data": True
                }
            },
            {
                "metric_name": "api_response_time",
                "test_case": "submit_card_review",
                "baseline_value": 65.0,
                "unit": "milliseconds",
                "confidence_interval": [50.0, 80.0],
                "sample_size": 300,
                "metadata": {
                    "endpoint": "/api/reviews",
                    "method": "POST",
                    "includes_srs_update": True,
                    "includes_statistics": True
                }
            }
        ]
        
        self._save_baselines("api_performance", baselines)
        
    def _create_frontend_performance_baselines(self):
        """Create baselines for frontend performance"""
        baselines = [
            {
                "metric_name": "page_load_time",
                "test_case": "home_page_initial_load",
                "baseline_value": 1.8,
                "unit": "seconds",
                "confidence_interval": [1.5, 2.1],
                "sample_size": 100,
                "metadata": {
                    "page": "/",
                    "cache_state": "cold",
                    "bundle_size_kb": 450,
                    "network_speed": "3g"
                }
            },
            {
                "metric_name": "page_load_time",
                "test_case": "documents_page_with_data",
                "baseline_value": 2.3,
                "unit": "seconds",
                "confidence_interval": [1.9, 2.7],
                "sample_size": 80,
                "metadata": {
                    "page": "/documents",
                    "document_count": 50,
                    "includes_thumbnails": True,
                    "network_speed": "3g"
                }
            },
            {
                "metric_name": "component_render_time",
                "test_case": "flashcard_component_render",
                "baseline_value": 45.0,
                "unit": "milliseconds",
                "confidence_interval": [35.0, 55.0],
                "sample_size": 200,
                "metadata": {
                    "component": "FlashCard",
                    "card_type": "basic",
                    "has_images": False,
                    "complexity": "medium"
                }
            },
            {
                "metric_name": "interaction_response_time",
                "test_case": "card_flip_animation",
                "baseline_value": 250.0,
                "unit": "milliseconds",
                "confidence_interval": [200.0, 300.0],
                "sample_size": 150,
                "metadata": {
                    "interaction": "card_flip",
                    "animation_duration": 200,
                    "includes_content_load": True
                }
            }
        ]
        
        self._save_baselines("frontend_performance", baselines)
        
    def _create_database_performance_baselines(self):
        """Create baselines for database performance"""
        baselines = [
            {
                "metric_name": "query_execution_time",
                "test_case": "select_user_documents",
                "baseline_value": 25.0,
                "unit": "milliseconds",
                "confidence_interval": [20.0, 30.0],
                "sample_size": 500,
                "metadata": {
                    "query_type": "SELECT",
                    "table": "documents",
                    "result_count": 20,
                    "includes_joins": True,
                    "uses_index": True
                }
            },
            {
                "metric_name": "query_execution_time",
                "test_case": "insert_flashcard_batch",
                "baseline_value": 180.0,
                "unit": "milliseconds",
                "confidence_interval": [150.0, 210.0],
                "sample_size": 200,
                "metadata": {
                    "query_type": "INSERT",
                    "table": "flashcards",
                    "batch_size": 100,
                    "includes_validation": True
                }
            },
            {
                "metric_name": "query_execution_time",
                "test_case": "complex_analytics_query",
                "baseline_value": 450.0,
                "unit": "milliseconds",
                "confidence_interval": [380.0, 520.0],
                "sample_size": 100,
                "metadata": {
                    "query_type": "SELECT",
                    "complexity": "high",
                    "includes_aggregations": True,
                    "table_count": 4,
                    "result_count": 1
                }
            }
        ]
        
        self._save_baselines("database_performance", baselines)
        
    def _create_memory_usage_baselines(self):
        """Create baselines for memory usage"""
        baselines = [
            {
                "metric_name": "memory_usage",
                "test_case": "document_processing_peak",
                "baseline_value": 512.0,
                "unit": "megabytes",
                "confidence_interval": [450.0, 574.0],
                "sample_size": 50,
                "metadata": {
                    "operation": "pdf_processing",
                    "file_size_mb": 10.0,
                    "concurrent_processes": 1,
                    "includes_ocr": False
                }
            },
            {
                "metric_name": "memory_usage",
                "test_case": "search_index_loading",
                "baseline_value": 256.0,
                "unit": "megabytes",
                "confidence_interval": [220.0, 292.0],
                "sample_size": 60,
                "metadata": {
                    "operation": "index_loading",
                    "index_size_mb": 150.0,
                    "vector_dimension": 768,
                    "document_count": 1000
                }
            },
            {
                "metric_name": "memory_usage",
                "test_case": "concurrent_user_simulation",
                "baseline_value": 1024.0,
                "unit": "megabytes",
                "confidence_interval": [900.0, 1148.0],
                "sample_size": 30,
                "metadata": {
                    "operation": "load_test",
                    "concurrent_users": 100,
                    "session_duration": 300,
                    "includes_caching": True
                }
            }
        ]
        
        self._save_baselines("memory_usage", baselines)
        
    def record_performance_metric(self, metric: PerformanceMetric):
        """Record a new performance metric measurement"""
        # Load existing metrics
        metrics = self._load_metrics_history()
        
        # Add new metric
        metrics.append(asdict(metric))
        
        # Save updated metrics
        self._save_metrics_history(metrics)
        
        # Check for regressions
        self._check_for_regression(metric)
        
    def check_performance_regression(self, metric_name: str, test_case: str, 
                                   current_value: float, environment: str = "test") -> Dict[str, Any]:
        """
        Check if current performance represents a regression
        
        Returns:
            Dictionary with regression analysis results
        """
        baselines = self._load_baselines()
        
        # Find matching baseline
        baseline = None
        for b in baselines:
            if (b["metric_name"] == metric_name and 
                b["test_case"] == test_case and 
                b["environment"] == environment):
                baseline = b
                break
                
        if not baseline:
            return {
                "has_regression": False,
                "reason": "No baseline found",
                "baseline_value": None,
                "current_value": current_value,
                "change_percent": None
            }
            
        baseline_value = baseline["baseline_value"]
        change_percent = ((current_value - baseline_value) / baseline_value) * 100
        
        # Check if this is a regression (performance got worse)
        is_regression = change_percent > (self.regression_threshold * 100)
        is_improvement = change_percent < -(self.improvement_threshold * 100)
        
        return {
            "has_regression": is_regression,
            "has_improvement": is_improvement,
            "baseline_value": baseline_value,
            "current_value": current_value,
            "change_percent": change_percent,
            "threshold_percent": self.regression_threshold * 100,
            "confidence_interval": baseline["confidence_interval"],
            "within_confidence_interval": (
                baseline["confidence_interval"][0] <= current_value <= baseline["confidence_interval"][1]
            )
        }
        
    def update_baseline(self, metric_name: str, test_case: str, environment: str = "test"):
        """Update baseline based on recent performance data"""
        metrics = self._load_metrics_history()
        
        # Filter metrics for this specific test case
        relevant_metrics = [
            m for m in metrics 
            if (m["name"] == metric_name and 
                m["test_case"] == test_case and 
                m["environment"] == environment)
        ]
        
        if len(relevant_metrics) < self.min_sample_size:
            return False
            
        # Calculate new baseline from recent data (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_metrics = [
            m for m in relevant_metrics
            if datetime.fromisoformat(m["timestamp"]) > cutoff_date
        ]
        
        if len(recent_metrics) < self.min_sample_size:
            recent_metrics = relevant_metrics[-self.min_sample_size:]
            
        values = [m["value"] for m in recent_metrics]
        
        # Calculate statistics
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        # 95% confidence interval
        margin = 1.96 * (std_dev / (len(values) ** 0.5))
        confidence_interval = [mean_value - margin, mean_value + margin]
        
        # Update baseline
        baselines = self._load_baselines()
        
        # Find and update existing baseline
        for i, baseline in enumerate(baselines):
            if (baseline["metric_name"] == metric_name and 
                baseline["test_case"] == test_case and 
                baseline["environment"] == environment):
                
                baselines[i].update({
                    "baseline_value": mean_value,
                    "confidence_interval": confidence_interval,
                    "sample_size": len(recent_metrics),
                    "last_updated": datetime.now().isoformat()
                })
                break
        else:
            # Create new baseline if not found
            new_baseline = {
                "metric_name": metric_name,
                "test_case": test_case,
                "environment": environment,
                "baseline_value": mean_value,
                "unit": recent_metrics[0]["unit"],
                "confidence_interval": confidence_interval,
                "sample_size": len(recent_metrics),
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "metadata": recent_metrics[0]["metadata"]
            }
            baselines.append(new_baseline)
            
        self._save_baselines_data(baselines)
        return True
        
    def get_performance_trends(self, metric_name: str, test_case: str, 
                             days: int = 30) -> Dict[str, Any]:
        """Get performance trends for a specific metric over time"""
        metrics = self._load_metrics_history()
        
        # Filter and sort metrics
        cutoff_date = datetime.now() - timedelta(days=days)
        relevant_metrics = [
            m for m in metrics
            if (m["name"] == metric_name and 
                m["test_case"] == test_case and
                datetime.fromisoformat(m["timestamp"]) > cutoff_date)
        ]
        
        relevant_metrics.sort(key=lambda x: x["timestamp"])
        
        if len(relevant_metrics) < 2:
            return {"trend": "insufficient_data", "data_points": len(relevant_metrics)}
            
        values = [m["value"] for m in relevant_metrics]
        timestamps = [m["timestamp"] for m in relevant_metrics]
        
        # Calculate trend
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        trend_percent = ((second_avg - first_avg) / first_avg) * 100
        
        trend_direction = "stable"
        if trend_percent > 5:
            trend_direction = "degrading"
        elif trend_percent < -5:
            trend_direction = "improving"
            
        return {
            "trend": trend_direction,
            "trend_percent": trend_percent,
            "data_points": len(relevant_metrics),
            "first_period_avg": first_avg,
            "second_period_avg": second_avg,
            "min_value": min(values),
            "max_value": max(values),
            "current_value": values[-1],
            "timestamps": timestamps,
            "values": values
        }
        
    def _save_baselines(self, category: str, baselines: List[Dict[str, Any]]):
        """Save baselines for a specific category"""
        timestamp = datetime.now().isoformat()
        
        for baseline in baselines:
            baseline.update({
                "environment": "test",
                "created_at": timestamp,
                "last_updated": timestamp
            })
            
        # Load existing baselines
        all_baselines = self._load_baselines()
        
        # Add new baselines
        all_baselines.extend(baselines)
        
        # Save updated baselines
        self._save_baselines_data(all_baselines)
        
    def _load_baselines(self) -> List[Dict[str, Any]]:
        """Load performance baselines"""
        if not self.baselines_file.exists():
            return []
            
        with open(self.baselines_file, 'r') as f:
            return json.load(f)
            
    def _save_baselines_data(self, baselines: List[Dict[str, Any]]):
        """Save baselines data"""
        with open(self.baselines_file, 'w') as f:
            json.dump(baselines, f, indent=2)
            
    def _load_metrics_history(self) -> List[Dict[str, Any]]:
        """Load metrics history"""
        if not self.metrics_file.exists():
            return []
            
        with open(self.metrics_file, 'r') as f:
            return json.load(f)
            
    def _save_metrics_history(self, metrics: List[Dict[str, Any]]):
        """Save metrics history"""
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
    def _check_for_regression(self, metric: PerformanceMetric):
        """Check if metric represents a regression and record it"""
        regression_result = self.check_performance_regression(
            metric.name, metric.test_case, metric.value, metric.environment
        )
        
        if regression_result["has_regression"]:
            regression_record = {
                "id": str(uuid.uuid4()),
                "metric_name": metric.name,
                "test_case": metric.test_case,
                "environment": metric.environment,
                "detected_at": datetime.now().isoformat(),
                "baseline_value": regression_result["baseline_value"],
                "current_value": regression_result["current_value"],
                "change_percent": regression_result["change_percent"],
                "severity": self._calculate_regression_severity(regression_result["change_percent"]),
                "resolved": False
            }
            
            # Load and save regressions
            regressions = self._load_regressions()
            regressions.append(regression_record)
            self._save_regressions(regressions)
            
    def _calculate_regression_severity(self, change_percent: float) -> str:
        """Calculate regression severity based on change percentage"""
        if change_percent > 50:
            return "critical"
        elif change_percent > 30:
            return "high"
        elif change_percent > 15:
            return "medium"
        else:
            return "low"
            
    def _load_regressions(self) -> List[Dict[str, Any]]:
        """Load regression records"""
        if not self.regressions_file.exists():
            return []
            
        with open(self.regressions_file, 'r') as f:
            return json.load(f)
            
    def _save_regressions(self, regressions: List[Dict[str, Any]]):
        """Save regression records"""
        with open(self.regressions_file, 'w') as f:
            json.dump(regressions, f, indent=2)


if __name__ == "__main__":
    manager = PerformanceBaselineManager()
    manager.create_initial_baselines()