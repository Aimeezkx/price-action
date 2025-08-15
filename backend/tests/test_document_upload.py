"""
Test document upload and queue system
"""

import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio

from main import app
from app.core.database import get_async_db, Base, async_engine
from app.models.document import Document, ProcessingStatus
from app.services.queue_service import QueueService


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """Create test database session"""
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Get session
    async for session in get_async_db():
        yield session
        break
    
    # Clean up
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    # Create a minimal PDF content (just for testing file upload)
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
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
181
%%EOF"""
    
    return BytesIO(pdf_content)


class TestDocumentUpload:
    """Test document upload functionality"""
    
    @pytest.mark.asyncio
    async def test_upload_valid_pdf(self, async_client, sample_pdf_file):
        """Test uploading a valid PDF file"""
        
        # Mock the queue service to avoid Redis dependency in tests
        with patch('app.services.document_service.QueueService') as mock_queue:
            mock_queue_instance = AsyncMock()
            mock_queue.return_value = mock_queue_instance
            
            files = {"file": ("test.pdf", sample_pdf_file, "application/pdf")}
            response = await async_client.post("/api/ingest", files=files)
            
            assert response.status_code == 201
            data = response.json()
            
            assert "id" in data
            assert data["filename"] == "test.pdf"
            assert data["file_type"] == "pdf"
            assert data["status"] == "pending"
            
            # Verify queue was called
            mock_queue_instance.enqueue_document_processing.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_unsupported_file_type(self, async_client):
        """Test uploading unsupported file type"""
        
        fake_file = BytesIO(b"fake content")
        files = {"file": ("test.txt", fake_file, "text/plain")}
        
        response = await async_client.post("/api/ingest", files=files)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_no_file(self, async_client):
        """Test uploading without file"""
        
        response = await async_client.post("/api/ingest")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_upload_large_file(self, async_client):
        """Test uploading file that exceeds size limit"""
        
        # Create a large file (simulate)
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        large_file = BytesIO(large_content)
        
        files = {"file": ("large.pdf", large_file, "application/pdf")}
        response = await async_client.post("/api/ingest", files=files)
        
        # Should be rejected due to size
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]


class TestDocumentAPI:
    """Test document management API endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, async_client):
        """Test listing documents when none exist"""
        
        response = await async_client.get("/api/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, async_client):
        """Test getting a document that doesn't exist"""
        
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.get(f"/api/documents/{fake_uuid}")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_document_status_nonexistent(self, async_client):
        """Test getting status of nonexistent document"""
        
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = await async_client.get(f"/api/documents/{fake_uuid}/status")
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]


class TestQueueService:
    """Test Redis Queue service"""
    
    def test_queue_service_initialization(self):
        """Test queue service can be initialized"""
        
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value = AsyncMock()
            
            queue_service = QueueService()
            assert queue_service is not None
            mock_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enqueue_document_processing(self):
        """Test enqueueing document for processing"""
        
        with patch('redis.from_url') as mock_redis, \
             patch('rq.Queue') as mock_queue_class:
            
            mock_redis_conn = AsyncMock()
            mock_redis.return_value = mock_redis_conn
            
            mock_queue = AsyncMock()
            mock_job = AsyncMock()
            mock_job.id = "test-job-id"
            mock_queue.enqueue.return_value = mock_job
            mock_queue_class.return_value = mock_queue
            
            queue_service = QueueService()
            
            from uuid import uuid4
            doc_id = uuid4()
            
            job_id = await queue_service.enqueue_document_processing(doc_id)
            
            assert job_id == "test-job-id"
            mock_queue.enqueue.assert_called_once()


class TestFileValidation:
    """Test file validation utilities"""
    
    @pytest.mark.asyncio
    async def test_validate_pdf_file(self, sample_pdf_file):
        """Test validating a PDF file"""
        
        from fastapi import UploadFile
        from app.utils.file_validation import validate_file
        
        upload_file = UploadFile(
            filename="test.pdf",
            file=sample_pdf_file,
            content_type="application/pdf"
        )
        
        result = await validate_file(upload_file)
        
        assert result.is_valid
        assert result.error_message == ""
    
    @pytest.mark.asyncio
    async def test_validate_unsupported_file(self):
        """Test validating unsupported file type"""
        
        from fastapi import UploadFile
        from app.utils.file_validation import validate_file
        
        fake_file = BytesIO(b"fake content")
        upload_file = UploadFile(
            filename="test.xyz",
            file=fake_file,
            content_type="application/unknown"
        )
        
        result = await validate_file(upload_file)
        
        assert not result.is_valid
        assert "Unsupported file type" in result.error_message
    
    def test_get_file_type(self):
        """Test file type detection"""
        
        from app.utils.file_validation import get_file_type
        
        assert get_file_type("document.pdf") == "pdf"
        assert get_file_type("document.docx") == "docx"
        assert get_file_type("document.md") == "md"
        assert get_file_type("document.xyz") == "unknown"
    
    def test_is_supported_file_type(self):
        """Test supported file type checking"""
        
        from app.utils.file_validation import is_supported_file_type
        
        assert is_supported_file_type("document.pdf") is True
        assert is_supported_file_type("document.docx") is True
        assert is_supported_file_type("document.md") is True
        assert is_supported_file_type("document.xyz") is False


if __name__ == "__main__":
    pytest.main([__file__])