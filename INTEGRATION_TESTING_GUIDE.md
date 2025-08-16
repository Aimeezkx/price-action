# Integration Testing Guide

This guide covers the comprehensive integration testing framework for the Document Learning Application.

## Overview

The integration testing framework validates complete workflows and interactions between different components of the system, including:

- Document processing pipeline (upload → parsing → knowledge extraction → card generation)
- API integration between frontend and backend
- Database operations and data consistency
- File upload and storage operations
- Cross-component workflows and data flow

## Test Structure

### Backend Integration Tests

Located in `backend/tests/integration/`:

#### 1. Document Processing Pipeline (`test_document_processing_pipeline.py`)
- **Purpose**: Tests the complete document processing workflow
- **Coverage**:
  - Document upload and validation
  - Content parsing (PDF, DOCX, Markdown)
  - Chapter extraction
  - Knowledge point extraction
  - Card generation
  - SRS initialization
  - Error handling and recovery
  - Performance benchmarks
  - Concurrent processing
  - Data consistency validation

#### 2. API Integration (`test_api_integration.py`)
- **Purpose**: Tests API endpoints and frontend-backend communication
- **Coverage**:
  - Document upload API workflow
  - Search API integration
  - Card review API workflow
  - Export API integration
  - Error handling and status codes
  - Authentication and authorization
  - Rate limiting
  - WebSocket integration (if applicable)
  - Performance benchmarks

#### 3. Database Operations (`test_database_operations.py`)
- **Purpose**: Tests database transactions and data integrity
- **Coverage**:
  - Transaction integrity and rollback
  - Foreign key constraints
  - Cascade deletions
  - Concurrent operations
  - Connection pooling
  - Performance optimization
  - Data validation constraints
  - Backup and recovery scenarios
  - Migration compatibility

#### 4. File Upload and Storage (`test_file_upload_storage.py`)
- **Purpose**: Tests file handling and storage operations
- **Coverage**:
  - Local storage operations
  - File validation and security
  - Upload integration
  - File deduplication
  - Concurrent uploads
  - Error handling
  - Metadata extraction
  - Cleanup operations
  - Quota management
  - Versioning
  - Backend switching

#### 5. Cross-Component Workflows (`test_cross_component_workflows.py`)
- **Purpose**: Tests complex workflows spanning multiple services
- **Coverage**:
  - Complete learning workflow
  - Multi-document processing
  - Error recovery workflows
  - Concurrent user workflows
  - Data synchronization
  - Performance optimization
  - Monitoring and logging

### Frontend Integration Tests

Located in `frontend/src/test/integration/`:

#### 1. API Integration (`api-integration.test.ts`)
- **Purpose**: Tests frontend-backend API integration
- **Coverage**:
  - Document upload integration
  - Document list display
  - Search functionality
  - Card review interface
  - Error handling
  - Performance testing
  - Real API integration (when available)

## Running Integration Tests

### Backend Tests

#### Run All Integration Tests
```bash
cd backend
python run_integration_tests.py
```

#### Run Specific Test Suite
```bash
# Document processing pipeline
python run_integration_tests.py --suite pipeline

# API integration
python run_integration_tests.py --suite api

# Database operations
python run_integration_tests.py --suite database

# File storage
python run_integration_tests.py --suite storage

# Cross-component workflows
python run_integration_tests.py --suite workflows
```

#### Run Performance Tests
```bash
python run_integration_tests.py --performance
```

#### Run Smoke Tests
```bash
python run_integration_tests.py --smoke
```

#### Run with Coverage
```bash
python run_integration_tests.py --suite all --report integration-report.json
```

### Frontend Tests

#### Run Frontend Integration Tests
```bash
cd frontend
npm run test:integration
```

#### Run with Coverage
```bash
npm run test:integration -- --coverage
```

### Using pytest Directly

```bash
cd backend

# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_document_processing_pipeline.py -v

# Run with coverage
pytest tests/integration/ --cov=app --cov-report=html

# Run in parallel
pytest tests/integration/ -n auto

# Run with specific markers
pytest tests/integration/ -m "not slow"
```

## Test Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_URL=sqlite+aiosqlite:///:memory:  # For testing
TEST_DATABASE_URL=postgresql://user:pass@localhost/test_db

# Storage configuration
STORAGE_BACKEND=local
STORAGE_PATH=/tmp/test_storage

# External services (for testing)
OPENAI_API_KEY=test_key  # Mock key for testing
ENABLE_EXTERNAL_SERVICES=false

# Logging
LOG_LEVEL=DEBUG
TEST_LOG_FILE=test.log
```

### Test Data

Test fixtures are located in:
- `backend/tests/fixtures/` - Sample documents and data
- `frontend/src/test/fixtures/` - Mock API responses

### Mock Services

Integration tests use mocked external services by default:
- OpenAI API calls are mocked
- File storage operations use temporary directories
- External APIs return predefined responses

## CI/CD Integration

### GitHub Actions

The integration tests run automatically on:
- Push to main/develop branches
- Pull requests
- Daily scheduled runs (2 AM UTC)
- Manual triggers with specific labels

### Workflow Files

- `.github/workflows/integration-tests.yml` - Main integration test workflow
- `.github/workflows/comprehensive-testing.yml` - Full test suite including integration

### Test Matrix

Tests run across multiple environments:
- Python versions: 3.9, 3.10, 3.11
- Node.js versions: 18, 20
- Databases: SQLite (memory), PostgreSQL

## Test Reports and Artifacts

### Generated Reports

- **JUnit XML**: `test-results/integration-results.xml`
- **Coverage HTML**: `htmlcov/integration/`
- **JSON Report**: `integration-test-report.json`
- **Performance Metrics**: `performance-results.json`

### Artifacts

CI/CD uploads the following artifacts:
- Test results and reports
- Coverage reports
- Performance benchmarks
- Error logs and screenshots
- Database dumps (on failure)

## Performance Benchmarks

### Expected Performance Metrics

| Operation | Target Time | Measured |
|-----------|-------------|----------|
| Document Upload (10MB PDF) | < 5s | - |
| Document Processing (10 pages) | < 30s | - |
| Search Query | < 500ms | - |
| Card Review | < 200ms | - |
| API Response | < 1s | - |

### Performance Tests

Performance tests are included in the integration suite:
- Document processing benchmarks
- Search performance validation
- Concurrent user simulation
- Memory usage monitoring
- Database query optimization

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database is running
pg_isready -h localhost -p 5432

# Reset test database
dropdb test_db && createdb test_db
```

#### File Permission Errors
```bash
# Ensure test directories are writable
chmod 755 /tmp/test_storage
```

#### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/backend:$PYTHONPATH
```

### Debug Mode

Run tests with debug output:
```bash
python run_integration_tests.py --suite all -v --log-level DEBUG
```

### Test Isolation

Each test runs in isolation with:
- Fresh database session
- Temporary file directories
- Mocked external services
- Clean application state

## Best Practices

### Writing Integration Tests

1. **Test Real Workflows**: Focus on complete user journeys
2. **Use Realistic Data**: Test with actual file formats and sizes
3. **Handle Async Operations**: Properly await async operations
4. **Clean Up Resources**: Ensure proper cleanup after tests
5. **Mock External Services**: Don't depend on external APIs
6. **Test Error Scenarios**: Include failure cases and recovery
7. **Performance Awareness**: Monitor test execution time
8. **Data Isolation**: Ensure tests don't interfere with each other

### Test Organization

1. **Group Related Tests**: Use test classes for related functionality
2. **Clear Test Names**: Use descriptive test method names
3. **Document Test Purpose**: Include docstrings explaining test goals
4. **Use Fixtures**: Share common setup code via fixtures
5. **Parameterize Tests**: Use pytest.mark.parametrize for variations

### Maintenance

1. **Regular Updates**: Keep tests updated with code changes
2. **Performance Monitoring**: Track test execution time trends
3. **Coverage Tracking**: Maintain high integration test coverage
4. **Failure Analysis**: Investigate and fix flaky tests
5. **Documentation**: Keep this guide updated with changes

## Integration with Development Workflow

### Pre-commit Hooks

Run smoke tests before commits:
```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: integration-smoke-tests
      name: Integration Smoke Tests
      entry: python backend/run_integration_tests.py --smoke
      language: system
      pass_filenames: false
```

### Development Testing

During development:
1. Run relevant integration tests for changed components
2. Use smoke tests for quick validation
3. Run full integration suite before major releases
4. Monitor performance regressions

### Release Validation

Before releases:
1. Run complete integration test suite
2. Validate performance benchmarks
3. Test with production-like data
4. Verify cross-platform compatibility

## Monitoring and Alerting

### Test Metrics

Track key metrics:
- Test success rate
- Test execution time
- Coverage percentage
- Performance regressions
- Failure patterns

### Alerts

Set up alerts for:
- Test failure rate > 5%
- Performance regression > 20%
- Coverage drop > 5%
- Critical test failures

### Dashboards

Monitor integration test health via:
- GitHub Actions dashboard
- Test result trends
- Performance metrics
- Coverage reports

## Future Enhancements

### Planned Improvements

1. **Visual Regression Testing**: Add screenshot comparison tests
2. **Load Testing**: Implement comprehensive load testing
3. **Security Testing**: Add automated security vulnerability tests
4. **Mobile Testing**: Add mobile app integration tests
5. **Multi-tenant Testing**: Test data isolation between users
6. **Disaster Recovery**: Test backup and recovery procedures

### Tool Upgrades

1. **Test Frameworks**: Keep pytest and vitest updated
2. **CI/CD**: Enhance GitHub Actions workflows
3. **Reporting**: Improve test result visualization
4. **Monitoring**: Add real-time test monitoring
5. **Documentation**: Automated test documentation generation

This integration testing framework ensures the reliability, performance, and correctness of the Document Learning Application across all its components and workflows.