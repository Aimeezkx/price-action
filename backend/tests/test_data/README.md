# Test Data Management System

A comprehensive test data management system that provides document generation, synthetic data creation, performance baselines, test result tracking, and data isolation for reliable testing.

## Features

- **Document Generation**: Create test documents in various formats (PDF, DOCX, Markdown)
- **Synthetic Data**: Generate realistic test data for users, documents, cards, and interactions
- **Data Isolation**: Run tests in isolated environments with clean data states
- **Performance Baselines**: Track performance metrics and detect regressions
- **Test Result Tracking**: Maintain history of test results and analyze trends
- **Snapshot Management**: Create and restore data snapshots for testing scenarios

## Quick Start

### 1. Generate Test Data

```bash
# Generate all test documents
python backend/tests/test_data/manage_test_data.py generate documents

# Generate synthetic data
python backend/tests/test_data/manage_test_data.py generate synthetic

# Generate sample test results
python backend/tests/test_data/manage_test_data.py generate results

# Create performance baselines
python backend/tests/test_data/manage_test_data.py create-baselines
```

### 2. Use in Tests

```python
import pytest
from backend.tests.test_data.conftest_integration import *

def test_document_processing(isolated_test_env, sample_document):
    """Test with isolated data environment"""
    # Test runs with clean, isolated data
    result = process_document(sample_document)
    assert result.status == "completed"

def test_with_performance_tracking(performance_tracker):
    """Test with automatic performance tracking"""
    with performance_tracker("search", "full_text_search") as tracker:
        results = search_documents("test query")
        # Performance is automatically recorded
        assert len(results) > 0
```

### 3. Manage Data

```bash
# Show statistics
python backend/tests/test_data/manage_test_data.py stats

# Create snapshot
python backend/tests/test_data/manage_test_data.py snapshot create --name "before_refactor"

# Clean up old data
python backend/tests/test_data/manage_test_data.py cleanup --all

# Show test report
python backend/tests/test_data/manage_test_data.py report --days 30
```

## Components

### 1. Test Document Generator

Generates test documents in various formats and sizes:

```python
from backend.tests.test_data.test_document_generator import TestDocumentGenerator

generator = TestDocumentGenerator()
generator.generate_all_test_documents()
```

**Generated Documents:**
- Small PDFs (1-5 pages) - for quick tests
- Medium PDFs (10-25 pages) - for realistic scenarios  
- Large PDFs (50+ pages) - for stress testing
- DOCX documents with tables and formatting
- Markdown documents with various structures
- Edge cases: empty files, corrupted files, multilingual content

### 2. Synthetic Data Generator

Creates realistic synthetic data for comprehensive testing:

```python
from backend.tests.test_data.synthetic_data_generator import SyntheticDataGenerator

generator = SyntheticDataGenerator()
generator.generate_all_synthetic_data()
```

**Generated Data:**
- User profiles with different activity levels
- Document metadata with various properties
- Chapter structures and knowledge points
- Flashcards of different types
- Learning sessions and review history
- Search queries and user interactions
- Performance metrics and error scenarios

### 3. Test Data Manager

Provides data isolation and lifecycle management:

```python
from backend.tests.test_data.test_data_manager import TestDataManager

manager = TestDataManager()

# Create isolated environment
with manager.isolated_test_environment("test_name", ["users", "documents"]) as context:
    # Test runs with isolated data
    run_test()

# Create snapshot
snapshot_id = manager.create_data_snapshot("baseline", "Initial baseline data")

# Restore snapshot
manager.restore_data_snapshot(snapshot_id)
```

**Features:**
- Isolated test environments
- Data snapshots and restoration
- Automatic cleanup
- Data validation
- Statistics and monitoring

### 4. Performance Baseline Manager

Tracks performance metrics and detects regressions:

```python
from backend.tests.test_data.performance_baseline_manager import PerformanceBaselineManager, PerformanceMetric

manager = PerformanceBaselineManager()

# Record performance metric
metric = PerformanceMetric(
    name="document_processing_time",
    value=1250.0,
    unit="milliseconds",
    timestamp=datetime.now().isoformat(),
    test_case="medium_pdf_processing",
    environment="test",
    metadata={"file_size_mb": 5.0}
)
manager.record_performance_metric(metric)

# Check for regression
result = manager.check_performance_regression("document_processing_time", "medium_pdf_processing", 1500.0)
if result["has_regression"]:
    print(f"Performance regression detected: {result['change_percent']:.1f}% slower")
```

**Baseline Categories:**
- Document processing times
- Search performance
- API response times
- Frontend loading times
- Database query performance
- Memory usage patterns

### 5. Test Result Tracker

Maintains comprehensive test result history:

```python
from backend.tests.test_data.test_result_tracker import TestResultTracker, TestResult, TestStatus

tracker = TestResultTracker()

# Record test result
test_result = TestResult(
    id=str(uuid.uuid4()),
    test_name="test_document_upload",
    test_category=TestCategory.INTEGRATION,
    status=TestStatus.PASSED,
    duration_ms=1250.0,
    timestamp=datetime.now().isoformat(),
    environment="test",
    commit_hash="abc123",
    branch="main",
    error_message=None,
    stack_trace=None,
    metadata={}
)

# Get test history
history = tracker.get_test_history("test_document_upload", days=30)

# Get flaky tests
flaky_tests = tracker.get_flaky_tests(threshold=0.1)

# Generate report
report = tracker.generate_test_report(days=7)
```

**Analytics:**
- Test pass/fail rates over time
- Flaky test detection
- Performance trends
- Failure analysis
- Test duration tracking

## pytest Integration

The system integrates seamlessly with pytest through fixtures and hooks:

### Available Fixtures

```python
def test_with_isolated_data(isolated_test_env):
    """Test runs in isolated environment"""
    pass

def test_with_sample_data(sample_user, sample_document, sample_flashcard):
    """Test with pre-generated sample data"""
    pass

def test_with_performance_tracking(performance_tracker):
    """Test with automatic performance tracking"""
    with performance_tracker("test_name", "operation") as tracker:
        # Perform operation
        pass

def test_with_documents(test_documents_dir):
    """Test with temporary directory of test documents"""
    pass
```

### Parametrized Testing

```python
@pytest.mark.parametrize("document_type", ["small_pdf", "medium_pdf", "large_pdf"])
def test_document_processing(document_type):
    """Test with different document types"""
    pass

@pytest.mark.parametrize("card_type", ["basic", "cloze", "multiple_choice"])
def test_card_generation(card_type):
    """Test with different card types"""
    pass
```

### Custom Markers

```python
@pytest.mark.isolated_data
def test_requires_isolation():
    """Test that needs isolated data"""
    pass

@pytest.mark.performance_tracked
def test_performance_critical():
    """Test that should track performance"""
    pass

@pytest.mark.requires_documents
def test_needs_documents():
    """Test that requires test documents"""
    pass
```

## CLI Usage

The `manage_test_data.py` script provides comprehensive CLI management:

### Generate Data

```bash
# Generate test documents
python backend/tests/test_data/manage_test_data.py generate documents

# Generate synthetic data
python backend/tests/test_data/manage_test_data.py generate synthetic

# Generate sample test results
python backend/tests/test_data/manage_test_data.py generate results
```

### Manage Snapshots

```bash
# Create snapshot
python backend/tests/test_data/manage_test_data.py snapshot create --name "baseline" --description "Initial baseline"

# Restore snapshot
python backend/tests/test_data/manage_test_data.py snapshot restore baseline_20241201_143022
```

### Performance Baselines

```bash
# Create initial baselines
python backend/tests/test_data/manage_test_data.py create-baselines
```

### Cleanup

```bash
# Clean up all data
python backend/tests/test_data/manage_test_data.py cleanup --all

# Clean up old snapshots (keep 5 most recent)
python backend/tests/test_data/manage_test_data.py cleanup --snapshots --keep 5

# Clean up old test results (keep 30 days)
python backend/tests/test_data/manage_test_data.py cleanup --results --days 30
```

### Statistics and Reports

```bash
# Show data statistics
python backend/tests/test_data/manage_test_data.py stats

# Validate data integrity
python backend/tests/test_data/manage_test_data.py validate

# Show test results report
python backend/tests/test_data/manage_test_data.py report --days 30
```

## Directory Structure

```
backend/tests/test_data/
├── README.md                          # This documentation
├── manage_test_data.py                # CLI management script
├── test_document_generator.py         # Document generation
├── synthetic_data_generator.py        # Synthetic data generation
├── test_data_manager.py              # Data lifecycle management
├── performance_baseline_manager.py    # Performance tracking
├── test_result_tracker.py            # Test result history
├── conftest_integration.py           # pytest integration
├── documents/                         # Generated test documents
│   ├── README.md
│   ├── small_text.pdf
│   ├── medium_textbook.pdf
│   └── ...
├── synthetic/                         # Synthetic test data
│   ├── user_profiles.json
│   ├── document_metadata.json
│   └── ...
├── performance/                       # Performance baselines
│   ├── baselines.json
│   ├── metrics_history.json
│   └── regressions.json
├── results/                          # Test result history
│   ├── test_results.db
│   └── test_analytics.json
├── isolated/                         # Isolated test environments
├── snapshots/                        # Data snapshots
│   ├── snapshots.json
│   └── baseline_20241201_143022/
└── ...
```

## Best Practices

### 1. Test Isolation

Always use isolated environments for tests that modify data:

```python
def test_document_upload(isolated_test_env):
    """Test runs in isolated environment"""
    # Upload and process document
    # No interference with other tests
```

### 2. Performance Tracking

Track performance for critical operations:

```python
def test_search_performance(performance_tracker):
    with performance_tracker("search", "full_text_search") as tracker:
        results = search_documents("query")
        # Performance automatically recorded and compared to baseline
```

### 3. Data Snapshots

Create snapshots before major changes:

```bash
# Before refactoring
python manage_test_data.py snapshot create --name "before_search_refactor"

# After refactoring, if tests fail:
python manage_test_data.py snapshot restore before_search_refactor_20241201_143022
```

### 4. Regular Cleanup

Clean up old data regularly:

```bash
# Weekly cleanup
python manage_test_data.py cleanup --snapshots --keep 10
python manage_test_data.py cleanup --results --days 60
```

### 5. Monitor Test Health

Check test reports regularly:

```bash
# Check for flaky tests
python manage_test_data.py report --days 30

# Look for performance regressions
python manage_test_data.py stats
```

## Configuration

### Environment Variables

- `TEST_DATA_DIR`: Base directory for test data (default: `backend/tests/test_data`)
- `TEST_ISOLATION_ENABLED`: Enable test isolation (default: `true`)
- `PERFORMANCE_TRACKING_ENABLED`: Enable performance tracking (default: `true`)

### pytest Configuration

Add to `pytest.ini`:

```ini
[tool:pytest]
markers =
    isolated_data: mark test to run with isolated test data
    performance_tracked: mark test for performance tracking
    requires_documents: mark test as requiring test documents
    requires_synthetic_data: mark test as requiring synthetic data
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure write permissions to test data directory
2. **Disk Space**: Monitor disk usage, clean up old data regularly
3. **Performance Regressions**: Check for environmental factors (CPU load, memory pressure)
4. **Flaky Tests**: Use isolation and investigate test dependencies

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Data Validation

Validate data integrity:

```bash
python manage_test_data.py validate
```

## Contributing

When adding new test data types:

1. Add generation logic to appropriate generator
2. Update CLI commands
3. Add pytest fixtures if needed
4. Update documentation
5. Add validation logic

## Dependencies

- `pytest`: Test framework integration
- `sqlite3`: Test result storage
- `reportlab`: PDF generation
- `python-docx`: DOCX generation
- `faker`: Synthetic data generation
- `PIL`: Image processing

Install dependencies:

```bash
pip install pytest reportlab python-docx faker pillow
```