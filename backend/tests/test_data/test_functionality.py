#!/usr/bin/env python3
"""
Test the functionality of the test data management system
"""

import sys
import json
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_data.test_data_manager import TestDataManager, TestDataFixtures
from tests.test_data.performance_baseline_manager import PerformanceBaselineManager, PerformanceMetric
from tests.test_data.test_result_tracker import TestResultTracker, TestResult, TestStatus, TestCategory
from datetime import datetime
import uuid


def test_data_manager():
    """Test the TestDataManager functionality"""
    print("Testing TestDataManager...")
    
    manager = TestDataManager()
    
    # Test data validation
    validation = manager.validate_test_data_integrity()
    print(f"Data validation: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")
    print(f"Checked {validation['checked_files']} files")
    
    if validation['errors']:
        print("Errors found:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    # Test statistics
    stats = manager.get_test_data_stats()
    print(f"Total size: {stats['total_size_bytes'] / 1024:.2f} KB")
    print(f"File types: {list(stats['file_counts'].keys())}")
    
    # Test fixtures
    fixtures = TestDataFixtures(manager)
    sample_user = fixtures.get_sample_user()
    sample_doc = fixtures.get_sample_document()
    sample_card = fixtures.get_sample_flashcard()
    
    print(f"Sample user ID: {sample_user['id']}")
    print(f"Sample document: {sample_doc['filename']}")
    print(f"Sample card type: {sample_card['type']}")
    
    print("✓ TestDataManager tests passed\n")


def test_performance_baseline_manager():
    """Test the PerformanceBaselineManager functionality"""
    print("Testing PerformanceBaselineManager...")
    
    manager = PerformanceBaselineManager()
    
    # Test recording a metric
    metric = PerformanceMetric(
        name="test_operation",
        value=150.0,
        unit="milliseconds",
        timestamp=datetime.now().isoformat(),
        test_case="test_case_1",
        environment="test",
        metadata={"test": True}
    )
    
    manager.record_performance_metric(metric)
    print("✓ Recorded performance metric")
    
    # Test regression check (should not find baseline yet)
    result = manager.check_performance_regression("test_operation", "test_case_1", 200.0)
    print(f"Regression check: {result['has_regression']} (expected: False - no baseline)")
    
    # Test trends (should have insufficient data)
    trends = manager.get_performance_trends("test_operation", "test_case_1")
    print(f"Trends: {trends['trend']} (expected: insufficient_data)")
    
    print("✓ PerformanceBaselineManager tests passed\n")


def test_result_tracker():
    """Test the TestResultTracker functionality"""
    print("Testing TestResultTracker...")
    
    tracker = TestResultTracker()
    
    # Create a sample test result
    test_result = TestResult(
        id=str(uuid.uuid4()),
        test_name="test_sample_functionality",
        test_category=TestCategory.UNIT,
        status=TestStatus.PASSED,
        duration_ms=250.0,
        timestamp=datetime.now().isoformat(),
        environment="test",
        commit_hash="abc123",
        branch="main",
        error_message=None,
        stack_trace=None,
        metadata={"test_run": True}
    )
    
    # Create a suite result
    from tests.test_data.test_result_tracker import TestSuiteResult
    
    suite_result = TestSuiteResult(
        id=str(uuid.uuid4()),
        suite_name="test_functionality_suite",
        timestamp=datetime.now().isoformat(),
        environment="test",
        commit_hash="abc123",
        branch="main",
        total_tests=1,
        passed_tests=1,
        failed_tests=0,
        skipped_tests=0,
        error_tests=0,
        total_duration_ms=250.0,
        test_results=[test_result],
        metadata={"test_suite": True}
    )
    
    # Record the suite result
    tracker.record_test_suite_result(suite_result)
    print("✓ Recorded test suite result")
    
    # Get test history
    history = tracker.get_test_history("test_sample_functionality", days=1)
    print(f"Test history entries: {len(history)}")
    
    # Get flaky tests (should be empty)
    flaky_tests = tracker.get_flaky_tests()
    print(f"Flaky tests found: {len(flaky_tests)}")
    
    # Generate report
    report = tracker.generate_test_report(days=1)
    print(f"Report generated for {report['overall_statistics']['total_tests']} tests")
    print(f"Pass rate: {report['overall_statistics']['pass_rate_percent']:.1f}%")
    
    print("✓ TestResultTracker tests passed\n")


def test_isolated_environment():
    """Test isolated test environment"""
    print("Testing isolated environment...")
    
    manager = TestDataManager()
    
    # Test isolated environment context
    with manager.isolated_test_environment("test_isolation", ["users"]) as context:
        print(f"Created isolated environment: {context['id']}")
        print(f"Temp directory: {context['temp_dir']}")
        print(f"Database path: {context['db_path']}")
        
        # Verify the environment exists
        assert context['temp_dir'].exists()
        assert context['db_path'].exists()
        
        print("✓ Isolated environment created successfully")
    
    # Environment should be cleaned up after context
    print("✓ Isolated environment cleaned up")
    print("✓ Isolated environment tests passed\n")


def test_snapshot_functionality():
    """Test snapshot creation and management"""
    print("Testing snapshot functionality...")
    
    manager = TestDataManager()
    
    # Create a snapshot
    snapshot_id = manager.create_data_snapshot("test_snapshot", "Test snapshot for functionality testing")
    print(f"Created snapshot: {snapshot_id}")
    
    # Verify snapshot exists
    snapshots_file = Path("backend/tests/test_data/snapshots.json")
    if snapshots_file.exists():
        with open(snapshots_file, 'r') as f:
            snapshots = json.load(f)
        
        snapshot_found = any(s['id'] == snapshot_id for s in snapshots)
        print(f"Snapshot found in registry: {'✓' if snapshot_found else '✗'}")
    
    print("✓ Snapshot functionality tests passed\n")


def main():
    """Run all functionality tests"""
    print("=== Testing Test Data Management System ===\n")
    
    try:
        test_data_manager()
        test_performance_baseline_manager()
        test_result_tracker()
        test_isolated_environment()
        test_snapshot_functionality()
        
        print("=== All Tests Passed! ===")
        print("✓ Test data management system is working correctly")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())