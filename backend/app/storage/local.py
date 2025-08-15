"""Local filesystem storage implementation."""

import aiofiles
import os
from pathlib import Path
from typing import BinaryIO, Optional, Union
from urllib.parse import urljoin

from .base import Storage, StorageError


class LocalStorage(Storage):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: str = "storage", base_url: str = "/files/"):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory for file storage
            base_url: Base URL for serving files
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip('/') + '/'
        
        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save(
        self, 
        file_data: Union[bytes, BinaryIO], 
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """Save file to local filesystem."""
        try:
            # Generate unique storage path
            storage_path = self.generate_storage_path(filename)
            full_path = self.base_path / storage_path
            
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file data
            if isinstance(file_data, bytes):
                async with aiofiles.open(full_path, 'wb') as f:
                    await f.write(file_data)
            else:
                # Handle file-like object
                if hasattr(file_data, 'read'):
                    content = file_data.read()
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    async with aiofiles.open(full_path, 'wb') as f:
                        await f.write(content)
                else:
                    raise StorageError(f"Unsupported file_data type: {type(file_data)}")
            
            return storage_path
            
        except Exception as e:
            raise StorageError(f"Failed to save file {filename}: {str(e)}")
    
    async def retrieve(self, storage_path: str) -> bytes:
        """Retrieve file from local filesystem."""
        try:
            full_path = self.base_path / storage_path
            
            if not full_path.exists():
                raise StorageError(f"File not found: {storage_path}")
            
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
                
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to retrieve file {storage_path}: {str(e)}")
    
    async def delete(self, storage_path: str) -> bool:
        """Delete file from local filesystem."""
        try:
            full_path = self.base_path / storage_path
            
            if not full_path.exists():
                return False
            
            full_path.unlink()
            
            # Clean up empty directories
            try:
                parent = full_path.parent
                if parent != self.base_path and not any(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                # Directory not empty or other error, ignore
                pass
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to delete file {storage_path}: {str(e)}")
    
    async def exists(self, storage_path: str) -> bool:
        """Check if file exists in local filesystem."""
        full_path = self.base_path / storage_path
        return full_path.exists() and full_path.is_file()
    
    async def get_url(self, storage_path: str) -> str:
        """Get URL for accessing the file."""
        if not await self.exists(storage_path):
            raise StorageError(f"File not found: {storage_path}")
        
        return urljoin(self.base_url, storage_path)
    
    def get_full_path(self, storage_path: str) -> Path:
        """Get full filesystem path for a storage path."""
        return self.base_path / storage_path