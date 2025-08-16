"""
Test Data Integration with pytest

Provides pytest fixtures and configuration for seamless integration
with the test data management system.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, List

from .test_data_manager import TestDataManager, TestDataFixtures
from .performance_baseline_manager import PerformanceBaselineManager, PerformanceMetric
from .test_result_tracker import TestResultTracker, TestResult, TestStatus, TestCategory


@pytest.fixture(scope="session")
def test_data_manager() -> TestDataManager:
    """Provide test data manager for the session"""
    return TestDataManager()


@pytest.fixture(scope="session")
def test_fixtures(test_data_manager: TestDataManager) -> TestDataFixtures:
    """Provide test fixtures for the session"""
    return TestDataFixtures(test_data_manager)


@pytest.fixture(scope="session")
def performance_baseline_manager() -> PerformanceBaselineManager:
    """Provide performance baseline manager for the session"""
    return PerformanceBaselineManager()


@pytest.fixture(scope="session")
def test_result_tracker() -> TestResultTracker:
    """Provide test result tracker for the session"""
    return TestResultTracker()


@pytest.fixture
def isolated_test_env(test_data_manager: TestDataManager, request):
    """
    Provide isolated test environment for individual tests
    
    Usage:
        def test_something(isolated_test_env):
            # Test runs in isolated environment
            # with clean data state
    """
    test_name = request.node.name
    data_sets = getattr(request, 'param', None)
    
    with test_data_manager.isolated_test_environment(test_name, data_sets) as context:
        yield context


@pytest.fixture
def sample_user(test_fixtures: TestDataFixtures) -> Dict[str, Any]:
    """Provide a sample user for testing"""
    return test_fixtures.get_sample_user()


@pytest.fixture
def sample_document(test_fixtures: TestDataFixtures) -> Dict[str, Any]:
    """Provide a sample document for testing"""
    return test_fixtures.get_sample_document()


@pytest.fixture
def sample_flashcard(test_fixtures: TestDataFixtures) -> Dict[str, Any]:
    """Provide a sample flashcard for testing"""
    return test_fixtures.get_sample_flashcard()


@pytest.fixture
def sample_review(test_fixtures: TestDataFixtures) -> Dict[str, Any]:
    """Provide a sample review for testing"""
    return test_fixtures.get_sample_review()


@pytest.fixture
def test_documents_dir() -> Generator[Path, None, None]:
    """Provide temporary directory with test documents"""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Copy test documents to temporary directory
        source_dir = Path("backend/tests/test_data/documents")
        if source_dir.exists():
            for doc_file in source_dir.glob("*.pdf"):
                shutil.copy2(doc_file, temp_dir)
            for doc_file in source_dir.glob("*.docx"):
                shutil.copy2(doc_file, temp_dir)
                
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def performance_tracker(performance_baseline_manager: PerformanceBaselineManager):
    """
    Provide performance tracking context manager
    
    Usage:
        def test_performance(performance_tracker):
            with performance_tracker("test_name", "operation") as tracker:
                # Perform operation
                result = some_operation()
                tracker.record_result(result)
    """
    class PerformanceTracker:
        def __init__(self, baseline_manager: PerformanceBaselineManager):
            self.baseline_manager = baseline_manager
            
        def __call__(self, test_name: str, operation: str):
            return PerformanceContext(self.baseline_manager, test_name, operation)
            
    return PerformanceTracker(performance_baseline_manager)


class PerformanceContext:
    """Context manager for performance tracking"""
    
    def __init__(self, baseline_manager: PerformanceBaselineManager, test_name: str, operation: str):
        self.baseline_manager = baseline_manager
        self.test_name = test_name
        self.operation = operation
        self.start_time = None
        
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time and not exc_type:
            import time
            duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            
            metric = PerformanceMetric(
                name=self.operation,
                value=duration,
                unit="milliseconds",
                timestamp=time.time(),
                test_case=self.test_name,
                environment="test",
                metadata={}
            )
            
            self.baseline_manager.record_performance_metric(metric)
            
    def record_custom_metric(self, name: str, value: float, unit: str, metadata: Dict[str, Any] = None):
        """Record a custom performance metric"""
        import time
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=time.time(),
            test_case=self.test_name,
            environment="test",
            metadata=metadata or {}
        )
        
        self.baseline_manager.record_performance_metric(metric)


# Pytest hooks for automatic test result tracking
def pytest_runtest_makereport(item, call):
    """Hook to capture test results"""
    if call.when == "call":
        # Store test result information on the item
        item.test_result = {
            "name": item.nodeid,
            "duration": call.duration * 1000,  # Convert to milliseconds
            "outcome": call.excinfo is None,
            "error": str(call.excinfo.value) if call.excinfo else None
        }


def pytest_sessionfinish(session, exitstatus):
    """Hook to save test results at session end"""
    try:
        tracker = TestResultTracker()
        
        # Collect all test results
        test_results = []
        for item in session.items:
            if hasattr(item, 'test_result'):
                result_data = item.test_result
                
                # Determine test category from path
                category = TestCategory.UNIT
                if "integration" in item.nodeid:
                    category = TestCategory.INTEGRATION
                elif "e2e" in item.nodeid:
                    category = TestCategory.E2E
                elif "performance" in item.nodeid:
                    category = TestCategory.PERFORMANCE
                elif "security" in item.nodeid:
                    category = TestCategory.SECURITY
                elif "load" in item.nodeid:
                    category = TestCategory.LOAD
                    
                # Determine status
                status = TestStatus.PASSED if result_data["outcome"] else TestStatus.FAILED
                
                test_result = TestResult(
                    id=f"test_{hash(item.nodeid)}",
                    test_name=result_data["name"],
                    test_category=category,
                    status=status,
                    duration_ms=result_data["duration"],
                    timestamp=session.starttime.isoformat(),
                    environment="test",
                    commit_hash=None,  # Could be populated from git
                    branch="main",     # Could be populated from git
                    error_message=result_data["error"],
                    stack_trace=None,  # Could be populated from traceback
                    metadata={"pytest_session": True}
                )
                
                test_results.append(test_result)
                
        # Create suite result if we have test results
        if test_results:
            from .test_result_tracker import TestSuiteResult
            import uuid
            
            suite_result = TestSuiteResult(
                id=str(uuid.uuid4()),
                suite_name="pytest_session",
                timestamp=session.starttime.isoformat(),
                environment="test",
                commit_hash=None,
                branch="main",
                total_tests=len(test_results),
                passed_tests=len([r for r in test_results if r.status == TestStatus.PASSED]),
                failed_tests=len([r for r in test_results if r.status == TestStatus.FAILED]),
                skipped_tests=0,
                error_tests=0,
                total_duration_ms=sum(r.duration_ms for r in test_results),
                test_results=test_results,
                metadata={"pytest_session": True, "exit_status": exitstatus}
            )
            
            tracker.record_test_suite_result(suite_result)
            
    except Exception as e:
        # Don't fail the test session if result tracking fails
        print(f"Warning: Could not save test results: {e}")


# Custom pytest markers for test data management
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "isolated_data: mark test to run with isolated test data"
    )
    config.addinivalue_line(
        "markers", "performance_tracked: mark test for performance tracking"
    )
    config.addinivalue_line(
        "markers", "requires_documents: mark test as requiring test documents"
    )
    config.addinivalue_line(
        "markers", "requires_synthetic_data: mark test as requiring synthetic data"
    )


# Parametrized fixtures for different data scenarios
@pytest.fixture(params=[
    {"users": 10, "documents": 5},
    {"users": 100, "documents": 50},
    {"users": 1000, "documents": 500}
])
def load_test_scenario(request):
    """Provide different load test scenarios"""
    return request.param


@pytest.fixture(params=["small_pdf", "medium_pdf", "large_pdf", "docx", "markdown"])
def document_type(request):
    """Provide different document types for testing"""
    return request.param


@pytest.fixture(params=["basic", "cloze", "multiple_choice", "true_false"])
def card_type(request):
    """Provide different card types for testing"""
    return request.param


# Helper functions for test data assertions
def assert_performance_within_baseline(baseline_manager: PerformanceBaselineManager,
                                     metric_name: str, test_case: str, 
                                     actual_value: float, tolerance: float = 0.2):
    """Assert that performance is within acceptable range of baseline"""
    result = baseline_manager.check_performance_regression(metric_name, test_case, actual_value)
    
    if result["has_regression"]:
        change_percent = result["change_percent"]
        if change_percent > (tolerance * 100):
            pytest.fail(
                f"Performance regression detected: {metric_name} for {test_case} "
                f"increased by {change_percent:.1f}% (baseline: {result['baseline_value']}, "
                f"actual: {actual_value})"
            )


def assert_test_data_valid(test_data_manager: TestDataManager):
    """Assert that test data is valid and not corrupted"""
    validation = test_data_manager.validate_test_data_integrity()
    
    if not validation["valid"]:
        error_msg = "Test data validation failed:\n"
        for error in validation["errors"]:
            error_msg += f"  - {error}\n"
        pytest.fail(error_msg)


# Example usage in test files:
"""
# In your test files, you can use these fixtures like this:

def test_document_processing(isolated_test_env, sample_document, performance_tracker):
    '''Test document processing with isolated data and performance tracking'''
    with performance_tracker("document_processing", "pdf_parsing") as tracker:
        # Your test code here
        result = process_document(sample_document)
        
        # Record custom metrics
        tracker.record_custom_metric("pages_processed", result.page_count, "pages")
        
    assert result.status == "completed"

@pytest.mark.parametrize("isolated_test_env", [["users", "documents"]], indirect=True)
def test_with_specific_data(isolated_test_env):
    '''Test that requires specific data sets'''
    # Test runs with users and documents data loaded
    pass

@pytest.mark.performance_tracked
def test_search_performance(performance_tracker):
    '''Test that automatically tracks performance'''
    with performance_tracker("search", "full_text_search") as tracker:
        results = search_documents("machine learning")
        assert len(results) > 0
"""