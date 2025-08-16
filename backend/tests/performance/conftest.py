"""Performance testing configuration and fixtures."""

import pytest
import asyncio
import time
import psutil
import os
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    peak_memory_mb: float
    success: bool
    error_message: str = ""

@dataclass
class BenchmarkResult:
    """Container for benchmark test results."""
    test_name: str
    metrics: PerformanceMetrics
    threshold_passed: bool
    threshold_values: Dict[str, float]

class PerformanceMonitor:
    """Monitor system performance during test execution."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None
        self.peak_memory = 0
        self.cpu_samples = []
        
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.cpu_samples = []
        
    def sample_metrics(self):
        """Sample current performance metrics."""
        current_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, current_memory)
        
        try:
            cpu_percent = self.process.cpu_percent()
            self.cpu_samples.append(cpu_percent)
        except psutil.NoSuchProcess:
            pass
            
    def stop_monitoring(self) -> PerformanceMetrics:
        """Stop monitoring and return metrics."""
        end_time = time.time()
        execution_time = end_time - self.start_time if self.start_time else 0
        
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_usage = current_memory - self.start_memory if self.start_memory else 0
        
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        
        return PerformanceMetrics(
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=avg_cpu,
            peak_memory_mb=self.peak_memory,
            success=True
        )

@pytest.fixture
def performance_monitor():
    """Provide performance monitoring fixture."""
    return PerformanceMonitor()

@pytest.fixture
def test_documents_path():
    """Path to test documents directory."""
    return Path(__file__).parent.parent.parent / "uploads"

@pytest.fixture
def performance_thresholds():
    """Performance threshold configurations."""
    return {
        "document_processing": {
            "small_doc_time": 15.0,  # seconds
            "medium_doc_time": 45.0,
            "large_doc_time": 120.0,
            "memory_limit": 500.0,  # MB
        },
        "search": {
            "response_time": 0.5,  # seconds
            "memory_limit": 100.0,  # MB
        },
        "frontend": {
            "load_time": 2.0,  # seconds
            "memory_limit": 200.0,  # MB
        },
        "concurrent_users": {
            "response_time_p95": 2.0,  # seconds
            "error_rate": 0.05,  # 5%
        }
    }

@pytest.fixture
async def sample_documents():
    """Create sample documents for testing."""
    documents = {
        "small": {
            "filename": "small_test.pdf",
            "pages": 5,
            "size_mb": 1.2
        },
        "medium": {
            "filename": "medium_test.pdf", 
            "pages": 20,
            "size_mb": 5.8
        },
        "large": {
            "filename": "large_test.pdf",
            "pages": 50,
            "size_mb": 15.3
        }
    }
    return documents

class AsyncPerformanceTimer:
    """Context manager for timing async operations."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        
    async def __aenter__(self):
        self.start_time = time.time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

@pytest.fixture
def async_timer():
    """Provide async performance timer."""
    return AsyncPerformanceTimer()