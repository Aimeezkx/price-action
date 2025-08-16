"""
Configuration and fixtures for integration tests.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from pathlib import Path

from app.core.database import Base, get_db
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for testing
    test_database_url = "sqlite+aiosqlite:///:memory:"
    
    engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create database session for testing."""
    async_session = sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def temp_directory():
    """Create temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_test_files():
    """Create sample test files for integration testing."""
    files = {}
    
    # Create sample PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(pdf_content)
        files['sample_pdf'] = f.name
    
    # Create sample text file
    text_content = """
    This is a sample document for testing.
    
    Chapter 1: Introduction
    This chapter introduces the main concepts.
    
    Chapter 2: Advanced Topics
    This chapter covers more complex material.
    
    Conclusion
    This concludes our sample document.
    """
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as f:
        f.write(text_content)
        files['sample_text'] = f.name
    
    yield files
    
    # Cleanup
    for filepath in files.values():
        if os.path.exists(filepath):
            os.unlink(filepath)


@pytest.fixture
async def mock_external_services():
    """Mock external services for integration testing."""
    from unittest.mock import AsyncMock, patch
    
    mocks = {}
    
    # Mock OpenAI API
    with patch('openai.ChatCompletion.acreate') as mock_openai:
        mock_openai.return_value = AsyncMock()
        mock_openai.return_value.choices = [
            AsyncMock(message=AsyncMock(content="Mocked AI response"))
        ]
        mocks['openai'] = mock_openai
        
        # Mock embedding service
        with patch('app.services.embedding_service.EmbeddingService.get_embeddings') as mock_embeddings:
            mock_embeddings.return_value = [[0.1, 0.2, 0.3] * 100]  # Mock 300-dim embedding
            mocks['embeddings'] = mock_embeddings
            
            yield mocks


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'allowed_file_types': ['.pdf', '.docx', '.txt'],
        'processing_timeout': 30,  # seconds
        'test_user_id': 'integration_test_user',
        'batch_size': 100
    }


@pytest.fixture
async def cleanup_test_data(db_session):
    """Cleanup test data after each test."""
    yield
    
    # Clean up test data
    from app.models.document import Document
    from app.models.knowledge import Chapter, KnowledgePoint
    from app.models.learning import Card, SRSState, ReviewHistory
    
    # Delete in reverse dependency order
    await db_session.execute("DELETE FROM review_history")
    await db_session.execute("DELETE FROM srs_states")
    await db_session.execute("DELETE FROM cards")
    await db_session.execute("DELETE FROM knowledge_points")
    await db_session.execute("DELETE FROM chapters")
    await db_session.execute("DELETE FROM documents")
    
    await db_session.commit()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if "performance" in item.name or "concurrent" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Mark tests requiring external services
        if "api" in item.name or "search" in item.name:
            item.add_marker(pytest.mark.external)