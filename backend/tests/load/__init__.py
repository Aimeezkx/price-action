"""
Load and stress testing framework.

This package contains comprehensive load and stress testing capabilities including:
- Concurrent document processing tests
- Multi-user simulation with realistic usage patterns  
- Database performance tests under load
- Memory and resource limit testing
- System recovery testing after failures

Usage:
    # Run all load tests
    python backend/tests/load/run_load_tests.py
    
    # Run specific test suites
    pytest backend/tests/load/test_concurrent_document_processing.py -v
    pytest backend/tests/load/test_multi_user_simulation.py -v
    pytest backend/tests/load/test_database_load.py -v
    pytest backend/tests/load/test_memory_resource_limits.py -v
    pytest backend/tests/load/test_system_recovery.py -v
"""

__version__ = "1.0.0"
__author__ = "Load Testing Framework"

# Import main classes for easy access
try:
    from .test_concurrent_document_processing import ConcurrentDocumentProcessor
    from .test_multi_user_simulation import RealisticUserSimulator
    from .test_database_load import DatabaseLoadTester
    from .test_memory_resource_limits import MemoryStressTester
    from .test_system_recovery import SystemRecoveryTester
    from .run_load_tests import LoadTestOrchestrator
    
    __all__ = [
        "ConcurrentDocumentProcessor",
        "RealisticUserSimulator", 
        "DatabaseLoadTester",
        "MemoryStressTester",
        "SystemRecoveryTester",
        "LoadTestOrchestrator"
    ]
except ImportError as e:
    # Handle import errors gracefully during development
    print(f"Warning: Some load testing components could not be imported: {e}")
    __all__ = []