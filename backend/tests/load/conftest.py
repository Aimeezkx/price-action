"""
Configuration and fixtures for load testing.
"""

import pytest
import asyncio
import os
import psutil
from pathlib import Path

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def load_test_config():
    """Configuration for load tests"""
    return {
        "base_url": os.getenv("TEST_BASE_URL", "http://localhost:8000"),
        "max_concurrent_users": int(os.getenv("MAX_CONCURRENT_USERS", "50")),
        "test_duration_minutes": int(os.getenv("TEST_DURATION_MINUTES", "10")),
        "memory_limit_mb": int(os.getenv("MEMORY_LIMIT_MB", "1024")),
        "cpu_threshold_percent": int(os.getenv("CPU_THRESHOLD_PERCENT", "80")),
        "enable_recovery_tests": os.getenv("ENABLE_RECOVERY_TESTS", "true").lower() == "true"
    }

@pytest.fixture(scope="session")
def system_resources():
    """Get system resource information"""
    return {
        "total_memory_gb": psutil.virtual_memory().total / (1024**3),
        "cpu_count": psutil.cpu_count(),
        "disk_space_gb": psutil.disk_usage('/').total / (1024**3)
    }

@pytest.fixture
def test_data_dir():
    """Create and return test data directory"""
    test_dir = Path("backend/tests/test_data/load_tests")
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up resources after each test"""
    yield
    # Force garbage collection after each test
    import gc
    gc.collect()

def pytest_configure(config):
    """Configure pytest for load testing"""
    config.addinivalue_line(
        "markers", "load: mark test as a load test"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as a stress test"
    )
    config.addinivalue_line(
        "markers", "recovery: mark test as a recovery test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection for load tests"""
    # Skip load tests if not explicitly requested
    if not config.getoption("--run-load-tests", default=False):
        skip_load = pytest.mark.skip(reason="Load tests not requested (use --run-load-tests)")
        for item in items:
            if "load" in item.keywords:
                item.add_marker(skip_load)

def pytest_addoption(parser):
    """Add command line options for load testing"""
    parser.addoption(
        "--run-load-tests",
        action="store_true",
        default=False,
        help="Run load tests"
    )
    parser.addoption(
        "--load-test-duration",
        action="store",
        default="10",
        help="Duration for load tests in minutes"
    )
    parser.addoption(
        "--max-concurrent-users",
        action="store",
        default="20",
        help="Maximum concurrent users for load tests"
    )