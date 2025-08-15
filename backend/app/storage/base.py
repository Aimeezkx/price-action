"""Abstract base class for storage implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Union
import uuid


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class Storage(ABC):
    """Abstract storage interface for file and image management."""
    
    @abstractmethod
    async def save(
        self, 
        file_data: Union[bytes, BinaryIO], 
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Save file data to storage.
        
        Args:
            file_data: File content as bytes or file-like object
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            str: Storage path/key for the saved file
            
        Raises:
            StorageError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def retrieve(self, storage_path: str) -> bytes:
        """
        Retrieve file data from storage.
        
        Args:
            storage_path: Storage path/key returned by save()
            
        Returns:
            bytes: File content
            
        Raises:
            StorageError: If file not found or retrieval fails
        """
        pass
    
    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            storage_path: Storage path/key returned by save()
            
        Returns:
            bool: True if file was deleted, False if not found
            
        Raises:
            StorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            storage_path: Storage path/key to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_url(self, storage_path: str) -> str:
        """
        Get URL for accessing the file.
        
        Args:
            storage_path: Storage path/key
            
        Returns:
            str: URL for accessing the file
            
        Raises:
            StorageError: If file not found
        """
        pass
    
    def generate_storage_path(self, filename: str, prefix: str = "") -> str:
        """
        Generate a unique storage path for a file.
        
        Args:
            filename: Original filename
            prefix: Optional prefix for the path
            
        Returns:
            str: Unique storage path
        """
        file_path = Path(filename)
        extension = file_path.suffix
        unique_id = str(uuid.uuid4())
        
        if prefix:
            return f"{prefix}/{unique_id}{extension}"
        return f"{unique_id}{extension}"