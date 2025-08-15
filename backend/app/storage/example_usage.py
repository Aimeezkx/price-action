"""Example usage of the storage abstraction layer."""

import asyncio
from pathlib import Path
from typing import Optional

from app.storage.local import LocalStorage
from app.storage.base import StorageError


class DocumentStorageService:
    """Service class demonstrating storage usage for document processing."""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage = LocalStorage(
            base_path=storage_path,
            base_url="/api/files/"
        )
    
    async def store_uploaded_document(
        self, 
        file_data: bytes, 
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """Store an uploaded document and return storage path."""
        try:
            # Use documents prefix for organization
            storage_path = self.storage.generate_storage_path(filename, "documents")
            
            # Save with generated path to ensure uniqueness
            actual_path = await self.storage.save(file_data, storage_path, content_type)
            return actual_path
            
        except StorageError as e:
            raise ValueError(f"Failed to store document: {e}")
    
    async def store_extracted_image(
        self, 
        image_data: bytes, 
        original_filename: str,
        document_id: str,
        page_number: int
    ) -> str:
        """Store an image extracted from a document."""
        try:
            # Create organized path for extracted images
            file_ext = Path(original_filename).suffix or ".png"
            image_filename = f"doc_{document_id}_page_{page_number}{file_ext}"
            
            storage_path = self.storage.generate_storage_path(
                image_filename, 
                f"images/{document_id}"
            )
            
            actual_path = await self.storage.save(
                image_data, 
                storage_path, 
                "image/png"
            )
            return actual_path
            
        except StorageError as e:
            raise ValueError(f"Failed to store extracted image: {e}")
    
    async def get_document_url(self, storage_path: str) -> str:
        """Get public URL for accessing a stored document."""
        try:
            return await self.storage.get_url(storage_path)
        except StorageError as e:
            raise ValueError(f"Document not found: {e}")
    
    async def cleanup_document_files(self, document_id: str) -> int:
        """Clean up all files associated with a document."""
        # This is a simplified example - in practice, you'd track
        # file paths in the database and iterate through them
        deleted_count = 0
        
        # Example cleanup logic (would be more sophisticated in practice)
        try:
            # Delete main document
            doc_path = f"documents/{document_id}.pdf"
            if await self.storage.delete(doc_path):
                deleted_count += 1
            
            # Delete associated images (simplified example)
            for page in range(1, 11):  # Assume max 10 pages
                img_path = f"images/{document_id}/doc_{document_id}_page_{page}.png"
                if await self.storage.delete(img_path):
                    deleted_count += 1
                    
        except StorageError:
            pass  # Continue cleanup even if some files fail
        
        return deleted_count


async def example_usage():
    """Demonstrate storage service usage."""
    service = DocumentStorageService("example_storage")
    
    # Example 1: Store uploaded document
    doc_data = b"Sample PDF content"
    doc_path = await service.store_uploaded_document(
        doc_data, 
        "research_paper.pdf", 
        "application/pdf"
    )
    print(f"Document stored at: {doc_path}")
    
    # Example 2: Store extracted image
    img_data = b"Sample image data"
    img_path = await service.store_extracted_image(
        img_data,
        "figure1.png",
        "doc123",
        1
    )
    print(f"Image stored at: {img_path}")
    
    # Example 3: Get URLs for access
    doc_url = await service.get_document_url(doc_path)
    img_url = await service.get_document_url(img_path)
    
    print(f"Document URL: {doc_url}")
    print(f"Image URL: {img_url}")
    
    # Example 4: Cleanup
    deleted = await service.cleanup_document_files("doc123")
    print(f"Cleaned up {deleted} files")


if __name__ == "__main__":
    asyncio.run(example_usage())