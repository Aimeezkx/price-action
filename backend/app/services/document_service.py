"""
Document service for business logic
"""

import os
import aiofiles
from uuid import UUID
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, ProcessingStatus
from app.core.config import settings
from app.utils.file_validation import get_file_type
from app.services.queue_service import QueueService
from app.utils.security import generate_secure_filename
from app.utils.access_control import DataProtection
from app.utils.logging import SecurityLogger


class DocumentService:
    """Service for document operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.queue_service = QueueService()
        self.security_logger = SecurityLogger(__name__)
    
    async def create_document(self, file: UploadFile, safe_filename: Optional[str] = None) -> Document:
        """
        Create document record and save file to storage with security measures
        
        Requirements: 1.1, 1.2, 11.2, 11.3 - Document upload with security
        """
        
        # Ensure upload directory exists
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Get file type and original filename
        file_type = get_file_type(file.filename)
        original_filename = file.filename or "unknown"
        
        # Create document record first to get UUID
        document = Document(
            filename=safe_filename or original_filename,
            file_type=file_type,
            file_path="",  # Will be updated after saving
            file_size=0,   # Will be updated after saving
            status=ProcessingStatus.PENDING
        )
        
        self.db.add(document)
        await self.db.flush()  # Get the ID without committing
        
        # Generate secure filename for storage
        secure_filename = generate_secure_filename(original_filename, str(document.id))
        file_path = upload_dir / secure_filename
        
        # Log processing start
        self.security_logger.log_processing_start(str(document.id), original_filename)
        
        # Save file to disk
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                await f.write(chunk)
                file_size += len(chunk)
        
        # Anonymize metadata if privacy mode is enabled
        metadata = {}
        if hasattr(file, 'headers'):
            metadata = dict(file.headers)
            metadata = DataProtection.anonymize_document_metadata(metadata)
        
        # Update document with file info
        document.file_path = str(file_path)
        document.file_size = file_size
        document.metadata = metadata
        
        await self.db.commit()
        await self.db.refresh(document)
        
        return document
    
    async def queue_for_processing(self, document_id: UUID) -> None:
        """
        Queue document for background processing
        
        Requirements: 1.3, 1.4 - Background processing queue
        """
        await self.queue_service.enqueue_document_processing(document_id)
    
    async def update_status(
        self, 
        document_id: UUID, 
        status: ProcessingStatus, 
        error_message: str = None
    ) -> Document:
        """
        Update document processing status
        
        Requirements: 1.5 - Status tracking and progress updates
        """
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        document.status = status
        if error_message:
            document.error_message = error_message
        
        await self.db.commit()
        await self.db.refresh(document)
        
        return document
    
    async def get_document(self, document_id: UUID) -> Document:
        """Get document by ID"""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete document and its file securely"""
        document = await self.get_document(document_id)
        if not document:
            return False
        
        # Securely delete file from disk
        try:
            if os.path.exists(document.file_path):
                # Use secure deletion if available
                if DataProtection.secure_delete_file(document.file_path):
                    self.security_logger.log_security_event(
                        "document_secure_delete",
                        {"document_id": str(document_id)},
                        "INFO"
                    )
                else:
                    # Fallback to regular deletion
                    os.remove(document.file_path)
        except Exception as e:
            self.security_logger.log_error(e, {"document_id": str(document_id), "operation": "delete"})
        
        # Delete from database
        await self.db.delete(document)
        await self.db.commit()
        
        return True