"""Tests for storage abstraction layer."""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO

from app.storage import LocalStorage, StorageError


class TestLocalStorage:
    """Test cases for LocalStorage implementation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create LocalStorage instance for testing."""
        return LocalStorage(base_path=temp_dir, base_url="/test-files/")
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_bytes(self, storage):
        """Test saving and retrieving file as bytes."""
        test_data = b"Hello, World! This is test data."
        filename = "test.txt"
        
        # Save file
        storage_path = await storage.save(test_data, filename)
        assert storage_path is not None
        assert storage_path.endswith(".txt")
        
        # Retrieve file
        retrieved_data = await storage.retrieve(storage_path)
        assert retrieved_data == test_data
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_file_object(self, storage):
        """Test saving and retrieving file from file-like object."""
        test_data = b"File object test data"
        file_obj = BytesIO(test_data)
        filename = "fileobj.txt"
        
        # Save file
        storage_path = await storage.save(file_obj, filename)
        assert storage_path is not None
        
        # Retrieve file
        retrieved_data = await storage.retrieve(storage_path)
        assert retrieved_data == test_data
    
    @pytest.mark.asyncio
    async def test_save_with_content_type(self, storage):
        """Test saving file with content type."""
        test_data = b"Image data"
        filename = "image.jpg"
        content_type = "image/jpeg"
        
        storage_path = await storage.save(test_data, filename, content_type)
        assert storage_path.endswith(".jpg")
        
        retrieved_data = await storage.retrieve(storage_path)
        assert retrieved_data == test_data
    
    @pytest.mark.asyncio
    async def test_delete_existing_file(self, storage):
        """Test deleting an existing file."""
        test_data = b"Data to be deleted"
        filename = "delete_me.txt"
        
        # Save file
        storage_path = await storage.save(test_data, filename)
        
        # Verify file exists
        assert await storage.exists(storage_path)
        
        # Delete file
        deleted = await storage.delete(storage_path)
        assert deleted is True
        
        # Verify file no longer exists
        assert not await storage.exists(storage_path)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage):
        """Test deleting a file that doesn't exist."""
        nonexistent_path = "nonexistent/file.txt"
        
        deleted = await storage.delete(nonexistent_path)
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Test checking file existence."""
        test_data = b"Existence test"
        filename = "exists.txt"
        
        # File doesn't exist initially
        storage_path = storage.generate_storage_path(filename)
        assert not await storage.exists(storage_path)
        
        # Save file
        actual_path = await storage.save(test_data, filename)
        
        # File exists now
        assert await storage.exists(actual_path)
    
    @pytest.mark.asyncio
    async def test_get_url(self, storage):
        """Test getting URL for file access."""
        test_data = b"URL test data"
        filename = "url_test.txt"
        
        # Save file
        storage_path = await storage.save(test_data, filename)
        
        # Get URL
        url = await storage.get_url(storage_path)
        assert url.startswith("/test-files/")
        assert url.endswith(".txt")
    
    @pytest.mark.asyncio
    async def test_get_url_nonexistent_file(self, storage):
        """Test getting URL for nonexistent file raises error."""
        nonexistent_path = "nonexistent.txt"
        
        with pytest.raises(StorageError, match="File not found"):
            await storage.get_url(nonexistent_path)
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_file(self, storage):
        """Test retrieving nonexistent file raises error."""
        nonexistent_path = "nonexistent.txt"
        
        with pytest.raises(StorageError, match="File not found"):
            await storage.retrieve(nonexistent_path)
    
    def test_generate_storage_path(self, storage):
        """Test storage path generation."""
        filename = "test.jpg"
        
        # Generate path without prefix
        path1 = storage.generate_storage_path(filename)
        assert path1.endswith(".jpg")
        assert len(path1) > len(".jpg")  # Should have UUID
        
        # Generate path with prefix
        path2 = storage.generate_storage_path(filename, "images")
        assert path2.startswith("images/")
        assert path2.endswith(".jpg")
        
        # Paths should be unique
        path3 = storage.generate_storage_path(filename)
        assert path1 != path3
    
    @pytest.mark.asyncio
    async def test_save_creates_directories(self, storage):
        """Test that save creates necessary directories."""
        test_data = b"Directory creation test"
        filename = "nested/deep/file.txt"
        
        # This should work even though nested directories don't exist
        storage_path = await storage.save(test_data, filename)
        
        # File should be retrievable
        retrieved_data = await storage.retrieve(storage_path)
        assert retrieved_data == test_data
    
    @pytest.mark.asyncio
    async def test_multiple_files_same_name(self, storage):
        """Test saving multiple files with same name generates unique paths."""
        test_data1 = b"First file"
        test_data2 = b"Second file"
        filename = "same_name.txt"
        
        # Save two files with same name
        path1 = await storage.save(test_data1, filename)
        path2 = await storage.save(test_data2, filename)
        
        # Paths should be different
        assert path1 != path2
        
        # Both files should be retrievable with correct content
        retrieved1 = await storage.retrieve(path1)
        retrieved2 = await storage.retrieve(path2)
        
        assert retrieved1 == test_data1
        assert retrieved2 == test_data2
    
    @pytest.mark.asyncio
    async def test_save_invalid_file_data(self, storage):
        """Test saving invalid file data raises error."""
        invalid_data = "not bytes or file object"
        filename = "invalid.txt"
        
        with pytest.raises(StorageError, match="Unsupported file_data type"):
            await storage.save(invalid_data, filename)
    
    def test_get_full_path(self, storage):
        """Test getting full filesystem path."""
        storage_path = "test/file.txt"
        full_path = storage.get_full_path(storage_path)
        
        assert isinstance(full_path, Path)
        assert str(full_path).endswith("test/file.txt")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage):
        """Test concurrent storage operations."""
        async def save_file(i):
            data = f"Concurrent test {i}".encode()
            filename = f"concurrent_{i}.txt"
            return await storage.save(data, filename)
        
        # Save multiple files concurrently
        tasks = [save_file(i) for i in range(10)]
        paths = await asyncio.gather(*tasks)
        
        # All paths should be unique
        assert len(set(paths)) == 10
        
        # All files should be retrievable
        for i, path in enumerate(paths):
            data = await storage.retrieve(path)
            expected = f"Concurrent test {i}".encode()
            assert data == expected