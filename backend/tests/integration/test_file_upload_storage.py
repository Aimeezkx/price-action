"""
Integration tests for file upload and storage operations.
Tests file handling, storage backends, and file validation.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, AsyncMock
import hashlib
import mimetypes

from app.storage.base import StorageBackend
from app.storage.local import LocalStorage
from app.services.document_service import DocumentService
from app.utils.file_validation import FileValidator
from app.core.config import settings


class TestFileUploadStorage:
    """Test file upload and storage operations"""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def local_storage(self, temp_storage_dir):
        """Create local storage instance"""
        return LocalStorage(base_path=temp_storage_dir)
    
    @pytest.fixture
    def file_validator(self):
        """Create file validator instance"""
        return FileValidator()
    
    @pytest.fixture
    def document_service(self, db_session):
        """Create document service instance"""
        return DocumentService(db_session)
    
    @pytest.fixture
    def sample_files(self):
        """Create sample files for testing"""
        files = {}
        
        # Create sample PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(pdf_content)
            files['pdf'] = f.name
        
        # Create sample DOCX (minimal structure)
        docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # ZIP header for DOCX
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(docx_content)
            files['docx'] = f.name
        
        # Create sample text file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as f:
            f.write("This is a test document with some content.")
            files['txt'] = f.name
        
        # Create large file for testing size limits
        large_content = b"x" * (50 * 1024 * 1024)  # 50MB
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(large_content)
            files['large'] = f.name
        
        # Create malicious file
        malicious_content = b"#!/bin/bash\necho 'malicious script'"
        with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as f:
            f.write(malicious_content)
            files['malicious'] = f.name
        
        yield files
        
        # Cleanup
        for filepath in files.values():
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    async def test_local_storage_operations(self, local_storage, sample_files):
        """Test local storage backend operations"""
        
        # Test file upload
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        file_path = await local_storage.store_file(
            content=content,
            filename="test_document.pdf",
            content_type="application/pdf"
        )
        
        assert file_path is not None
        assert os.path.exists(os.path.join(local_storage.base_path, file_path))
        
        # Test file retrieval
        retrieved_content = await local_storage.get_file(file_path)
        assert retrieved_content == content
        
        # Test file metadata
        metadata = await local_storage.get_file_metadata(file_path)
        assert metadata['size'] == len(content)
        assert metadata['content_type'] == "application/pdf"
        
        # Test file existence check
        exists = await local_storage.file_exists(file_path)
        assert exists is True
        
        # Test file deletion
        await local_storage.delete_file(file_path)
        exists = await local_storage.file_exists(file_path)
        assert exists is False
    
    async def test_file_validation(self, file_validator, sample_files):
        """Test file validation logic"""
        
        # Test valid PDF
        with open(sample_files['pdf'], 'rb') as f:
            is_valid, error = await file_validator.validate_file(
                content=f.read(),
                filename="test.pdf",
                content_type="application/pdf"
            )
        assert is_valid is True
        assert error is None
        
        # Test invalid file type
        with open(sample_files['txt'], 'rb') as f:
            is_valid, error = await file_validator.validate_file(
                content=f.read(),
                filename="test.txt",
                content_type="text/plain"
            )
        assert is_valid is False
        assert "not supported" in error.lower()
        
        # Test file size limit
        with open(sample_files['large'], 'rb') as f:
            is_valid, error = await file_validator.validate_file(
                content=f.read(),
                filename="large.pdf",
                content_type="application/pdf"
            )
        assert is_valid is False
        assert "too large" in error.lower()
        
        # Test malicious file detection
        with open(sample_files['malicious'], 'rb') as f:
            is_valid, error = await file_validator.validate_file(
                content=f.read(),
                filename="malicious.sh",
                content_type="application/x-sh"
            )
        assert is_valid is False
        assert "not supported" in error.lower()
    
    async def test_file_upload_integration(
        self, 
        document_service, 
        local_storage, 
        sample_files
    ):
        """Test complete file upload integration"""
        
        # Mock storage backend
        with patch('app.services.document_service.get_storage_backend') as mock_storage:
            mock_storage.return_value = local_storage
            
            # Upload valid file
            with open(sample_files['pdf'], 'rb') as f:
                document = await document_service.create_document(
                    filename="integration_test.pdf",
                    content=f.read(),
                    user_id="test_user"
                )
            
            assert document.id is not None
            assert document.filename == "integration_test.pdf"
            assert document.file_path is not None
            
            # Verify file was stored
            stored_content = await local_storage.get_file(document.file_path)
            assert len(stored_content) > 0
            
            # Test file retrieval through service
            retrieved_content = await document_service.get_document_content(document.id)
            assert retrieved_content == stored_content
    
    async def test_file_deduplication(self, local_storage, sample_files):
        """Test file deduplication based on content hash"""
        
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        # Calculate content hash
        content_hash = hashlib.sha256(content).hexdigest()
        
        # Store file first time
        file_path1 = await local_storage.store_file(
            content=content,
            filename="document1.pdf",
            content_type="application/pdf"
        )
        
        # Store same content with different filename
        file_path2 = await local_storage.store_file(
            content=content,
            filename="document2.pdf",
            content_type="application/pdf"
        )
        
        # If deduplication is implemented, paths might be the same
        # or point to the same underlying file
        stored_content1 = await local_storage.get_file(file_path1)
        stored_content2 = await local_storage.get_file(file_path2)
        
        assert stored_content1 == stored_content2 == content
    
    async def test_concurrent_file_uploads(self, local_storage, sample_files):
        """Test concurrent file upload operations"""
        
        import asyncio
        
        async def upload_file(filename: str, content: bytes):
            return await local_storage.store_file(
                content=content,
                filename=filename,
                content_type="application/pdf"
            )
        
        # Read file content
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        # Upload multiple files concurrently
        tasks = [
            upload_file(f"concurrent_{i}.pdf", content)
            for i in range(5)
        ]
        
        file_paths = await asyncio.gather(*tasks)
        
        # All uploads should succeed
        assert len(file_paths) == 5
        assert all(path is not None for path in file_paths)
        
        # Verify all files exist
        for file_path in file_paths:
            exists = await local_storage.file_exists(file_path)
            assert exists is True
    
    async def test_storage_error_handling(self, local_storage):
        """Test storage error handling"""
        
        # Test storing to invalid path
        with patch.object(local_storage, 'base_path', '/invalid/path'):
            with pytest.raises(Exception):
                await local_storage.store_file(
                    content=b"test content",
                    filename="test.pdf",
                    content_type="application/pdf"
                )
        
        # Test retrieving non-existent file
        with pytest.raises(FileNotFoundError):
            await local_storage.get_file("non_existent_file.pdf")
        
        # Test deleting non-existent file
        # Should not raise exception (idempotent operation)
        await local_storage.delete_file("non_existent_file.pdf")
    
    async def test_file_metadata_extraction(self, local_storage, sample_files):
        """Test file metadata extraction"""
        
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        file_path = await local_storage.store_file(
            content=content,
            filename="metadata_test.pdf",
            content_type="application/pdf"
        )
        
        metadata = await local_storage.get_file_metadata(file_path)
        
        assert 'size' in metadata
        assert 'content_type' in metadata
        assert 'created_at' in metadata
        assert 'modified_at' in metadata
        
        assert metadata['size'] == len(content)
        assert metadata['content_type'] == "application/pdf"
    
    async def test_file_cleanup_operations(self, local_storage, sample_files):
        """Test file cleanup and garbage collection"""
        
        # Store multiple files
        file_paths = []
        
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        for i in range(3):
            file_path = await local_storage.store_file(
                content=content,
                filename=f"cleanup_test_{i}.pdf",
                content_type="application/pdf"
            )
            file_paths.append(file_path)
        
        # Verify files exist
        for file_path in file_paths:
            exists = await local_storage.file_exists(file_path)
            assert exists is True
        
        # Cleanup files
        for file_path in file_paths:
            await local_storage.delete_file(file_path)
        
        # Verify files are deleted
        for file_path in file_paths:
            exists = await local_storage.file_exists(file_path)
            assert exists is False
    
    async def test_storage_quota_management(self, local_storage, sample_files):
        """Test storage quota and space management"""
        
        # Get initial storage usage
        initial_usage = await local_storage.get_storage_usage()
        
        # Store a file
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        file_path = await local_storage.store_file(
            content=content,
            filename="quota_test.pdf",
            content_type="application/pdf"
        )
        
        # Check storage usage increased
        new_usage = await local_storage.get_storage_usage()
        assert new_usage > initial_usage
        
        # Delete file
        await local_storage.delete_file(file_path)
        
        # Check storage usage decreased
        final_usage = await local_storage.get_storage_usage()
        assert final_usage <= new_usage
    
    async def test_file_versioning(self, local_storage, sample_files):
        """Test file versioning capabilities"""
        
        with open(sample_files['pdf'], 'rb') as f:
            original_content = f.read()
        
        # Store original version
        file_path_v1 = await local_storage.store_file(
            content=original_content,
            filename="versioned_document.pdf",
            content_type="application/pdf"
        )
        
        # Store updated version
        updated_content = original_content + b"\nUpdated content"
        file_path_v2 = await local_storage.store_file(
            content=updated_content,
            filename="versioned_document.pdf",
            content_type="application/pdf",
            version=2
        )
        
        # Both versions should be accessible
        v1_content = await local_storage.get_file(file_path_v1)
        v2_content = await local_storage.get_file(file_path_v2)
        
        assert v1_content == original_content
        assert v2_content == updated_content
        assert len(v2_content) > len(v1_content)
    
    async def test_storage_backend_switching(self, temp_storage_dir, sample_files):
        """Test switching between different storage backends"""
        
        # Create two different storage backends
        storage1 = LocalStorage(base_path=os.path.join(temp_storage_dir, "storage1"))
        storage2 = LocalStorage(base_path=os.path.join(temp_storage_dir, "storage2"))
        
        with open(sample_files['pdf'], 'rb') as f:
            content = f.read()
        
        # Store file in first backend
        file_path1 = await storage1.store_file(
            content=content,
            filename="backend_test.pdf",
            content_type="application/pdf"
        )
        
        # Migrate to second backend
        retrieved_content = await storage1.get_file(file_path1)
        file_path2 = await storage2.store_file(
            content=retrieved_content,
            filename="backend_test.pdf",
            content_type="application/pdf"
        )
        
        # Verify content is the same
        content1 = await storage1.get_file(file_path1)
        content2 = await storage2.get_file(file_path2)
        
        assert content1 == content2 == content
        
        # Clean up first backend
        await storage1.delete_file(file_path1)
        
        # Second backend should still have the file
        exists1 = await storage1.file_exists(file_path1)
        exists2 = await storage2.file_exists(file_path2)
        
        assert exists1 is False
        assert exists2 is True