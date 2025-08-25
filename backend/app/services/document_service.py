"""
Document service for business logic
"""

import os
import aiofiles
from uuid import UUID
from pathlib import Path
from typing import Optional
from datetime import datetime
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
        Task 4: Create document records in database during upload
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
            status=ProcessingStatus.PENDING,  # Set initial status to PENDING as required
            doc_metadata={}  # Initialize metadata
        )
        
        self.db.add(document)
        
        # Handle both async and sync sessions for flush
        if hasattr(self.db, 'flush') and callable(getattr(self.db, 'flush')):
            if hasattr(self.db.flush, '__await__'):
                await self.db.flush()  # Get the ID without committing
            else:
                self.db.flush()  # Get the ID without committing
        
        # Generate secure filename for storage using document ID
        secure_filename = f"{document.id}_{generate_secure_filename(original_filename)}"
        file_path = upload_dir / secure_filename
        
        # Log processing start
        self.security_logger.log_security_event(
            "document_processing_start",
            {
                "document_id": str(document.id),
                "filename": original_filename,
                "file_type": file_type
            },
            "INFO"
        )
        
        # Save file to disk
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                await f.write(chunk)
                file_size += len(chunk)
        
        # Prepare metadata with file information
        metadata = {
            "original_filename": original_filename,
            "upload_timestamp": document.created_at.isoformat(),
            "content_type": getattr(file, 'content_type', None)
        }
        
        # Add headers if available and anonymize if privacy mode is enabled
        if hasattr(file, 'headers'):
            headers = dict(file.headers)
            if settings.privacy_mode:
                data_protection = DataProtection()
                headers = data_protection.anonymize_data(headers)
            metadata["headers"] = headers
        
        # Update document with file info and metadata
        document.file_path = str(file_path)
        document.file_size = file_size
        document.doc_metadata = metadata
        
        # Commit the transaction
        if hasattr(self.db, 'commit') and callable(getattr(self.db, 'commit')):
            if hasattr(self.db.commit, '__await__'):
                await self.db.commit()
                await self.db.refresh(document)
            else:
                self.db.commit()
                self.db.refresh(document)
        
        return document
    
    async def queue_for_processing(self, document_id: UUID, priority: bool = False) -> str:
        """
        Queue document for background processing
        
        Requirements: 1.3, 6.1, 6.2, 6.3 - Background processing queue
        
        Args:
            document_id: UUID of document to process
            priority: Whether to use priority queue for urgent processing
        
        Returns:
            Job ID for tracking processing status
        """
        try:
            # Update document status to queued
            await self.update_status(document_id, ProcessingStatus.PENDING)
            
            # Enqueue for processing
            job_id = await self.queue_service.enqueue_document_processing(
                document_id, 
                priority=priority
            )
            
            self.security_logger.log_security_event(
                "document_queued_for_processing",
                {
                    "document_id": str(document_id),
                    "job_id": job_id,
                    "priority": priority
                },
                "INFO"
            )
            
            return job_id
            
        except Exception as e:
            self.security_logger.log_security_event(
                "document_queue_error",
                {
                    "document_id": str(document_id),
                    "error": str(e)
                },
                "ERROR"
            )
            
            # Update document status to failed
            await self.update_status(
                document_id, 
                ProcessingStatus.FAILED, 
                f"Failed to queue for processing: {str(e)}"
            )
            raise
    
    async def update_status(
        self, 
        document_id: UUID, 
        status: ProcessingStatus, 
        error_message: str = None,
        progress_data: dict = None
    ) -> Document:
        """
        Update document processing status with optional progress data
        
        Requirements: 1.4, 1.5 - Status tracking and progress updates
        """
        stmt = select(Document).where(Document.id == document_id)
        
        # Handle both async and sync sessions
        if hasattr(self.db, 'execute') and callable(getattr(self.db, 'execute')):
            if hasattr(self.db.execute, '__await__'):
                result = await self.db.execute(stmt)
            else:
                result = self.db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Store old status for logging
        old_status = document.status.value if document.status else "unknown"
        
        # Update status if provided
        if status is not None:
            document.status = status
        
        # Update error message if provided
        if error_message:
            document.error_message = error_message
        
        # Update progress metadata
        if progress_data:
            current_metadata = document.doc_metadata or {}
            if 'processing_progress' not in current_metadata:
                current_metadata['processing_progress'] = {}
            
            current_metadata['processing_progress'].update(progress_data)
            document.doc_metadata = current_metadata
        
        # Log status change (only if status was actually updated or progress data was provided)
        if status is not None or progress_data:
            self.security_logger.log_security_event(
                "document_status_updated",
                {
                    "document_id": str(document_id),
                    "old_status": old_status,
                    "new_status": status.value if status else old_status,
                    "error_message": error_message,
                    "progress_data": progress_data
                },
                "INFO"
            )
        
        # Handle both async and sync sessions
        if hasattr(self.db, 'commit') and callable(getattr(self.db, 'commit')):
            if hasattr(self.db.commit, '__await__'):
                await self.db.commit()
                await self.db.refresh(document)
            else:
                self.db.commit()
                self.db.refresh(document)
        
        return document
    
    async def update_processing_progress(
        self,
        document_id: UUID,
        current_step: str,
        current_step_number: int,
        total_steps: int,
        step_details: dict = None
    ) -> Document:
        """
        Update processing progress with detailed step information
        
        Requirements: 1.4, 1.5 - Processing progress tracking
        """
        progress_data = {
            "current_step": current_step,
            "current_step_number": current_step_number,
            "total_steps": total_steps,
            "progress_percentage": round((current_step_number / total_steps) * 100, 2),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        if step_details:
            progress_data["step_details"] = step_details
        
        return await self.update_status(document_id, None, None, progress_data)
    
    async def update_processing_stats(
        self,
        document_id: UUID,
        stats: dict
    ) -> Document:
        """
        Update processing statistics (pages processed, cards generated, etc.)
        
        Requirements: 1.4, 1.5 - Processing statistics tracking
        """
        stats_data = {
            "stats": stats,
            "stats_updated": datetime.utcnow().isoformat()
        }
        
        return await self.update_status(document_id, None, None, stats_data)
    
    async def get_document(self, document_id: UUID) -> Document:
        """Get document by ID"""
        stmt = select(Document).where(Document.id == document_id)
        
        # Handle both async and sync sessions
        if hasattr(self.db, 'execute') and callable(getattr(self.db, 'execute')):
            if hasattr(self.db.execute, '__await__'):
                result = await self.db.execute(stmt)
            else:
                result = self.db.execute(stmt)
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
                data_protection = DataProtection()
                if hasattr(data_protection, 'secure_delete_file') and data_protection.secure_delete_file(document.file_path):
                    self.security_logger.log_security_event(
                        "document_secure_delete",
                        {"document_id": str(document_id)},
                        "INFO"
                    )
                else:
                    # Fallback to regular deletion
                    os.remove(document.file_path)
        except Exception as e:
            self.security_logger.log_security_event(
                "document_delete_error",
                {"document_id": str(document_id), "operation": "delete", "error": str(e)},
                "ERROR"
            )
        
        # Delete from database
        # Handle both async and sync sessions
        if hasattr(self.db, 'delete') and callable(getattr(self.db, 'delete')):
            if hasattr(self.db.delete, '__await__'):
                await self.db.delete(document)
                await self.db.commit()
            else:
                self.db.delete(document)
                self.db.commit()
        
        return True
    
    async def get_processing_status(self, document_id: UUID) -> dict:
        """
        Get comprehensive processing status including queue information and progress
        
        Requirements: 1.4, 1.5, 4.2 - Status tracking, progress updates, and UI integration
        """
        try:
            # Get document from database
            document = await self.get_document(document_id)
            if not document:
                return {"error": "Document not found"}
            
            # Get job status from queue
            job_status = self.queue_service.get_job_by_document_id(document_id)
            
            # Extract progress information from metadata
            progress_info = {}
            if document.doc_metadata and 'processing_progress' in document.doc_metadata:
                progress_data = document.doc_metadata['processing_progress']
                progress_info = {
                    "current_step": progress_data.get("current_step"),
                    "current_step_number": progress_data.get("current_step_number", 0),
                    "total_steps": progress_data.get("total_steps", 0),
                    "progress_percentage": progress_data.get("progress_percentage", 0),
                    "step_details": progress_data.get("step_details", {}),
                    "last_updated": progress_data.get("last_updated")
                }
            
            # Extract processing statistics
            stats_info = {}
            if document.doc_metadata and 'stats' in document.doc_metadata:
                stats_info = document.doc_metadata['stats']
            
            # Determine if processing is active
            is_processing = document.status in [
                ProcessingStatus.PROCESSING,
                ProcessingStatus.PARSING,
                ProcessingStatus.EXTRACTING,
                ProcessingStatus.GENERATING_CARDS
            ]
            
            # Calculate estimated completion time if processing
            estimated_completion = None
            if is_processing and progress_info.get("progress_percentage", 0) > 0:
                # Simple estimation based on progress percentage
                # This could be enhanced with historical data
                progress_pct = progress_info["progress_percentage"]
                if progress_pct > 0:
                    # Estimate 2-5 minutes total processing time based on file size
                    file_size_mb = (document.file_size or 0) / (1024 * 1024)
                    estimated_total_minutes = max(2, min(5, file_size_mb * 0.5))
                    remaining_minutes = estimated_total_minutes * (100 - progress_pct) / 100
                    estimated_completion = f"{remaining_minutes:.1f} minutes"
            
            return {
                "document_id": str(document_id),
                "filename": document.filename,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "status": document.status.value if document.status else "unknown",
                "error_message": document.error_message,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                "is_processing": is_processing,
                "progress": progress_info,
                "statistics": stats_info,
                "estimated_completion": estimated_completion,
                "job_status": job_status,
                "queue_position": self._get_queue_position(document_id) if job_status and job_status.get('status') == 'queued' else None
            }
            
        except Exception as e:
            self.security_logger.log_security_event(
                "processing_status_error",
                {
                    "document_id": str(document_id),
                    "error": str(e)
                },
                "ERROR"
            )
            return {"error": str(e)}
    
    def _get_queue_position(self, document_id: UUID) -> Optional[int]:
        """Get position of document in processing queue"""
        try:
            job_id = f"doc_process_{document_id}"
            
            # Check both queues
            for queue in [self.queue_service.priority_queue, self.queue_service.queue]:
                job_ids = queue.job_ids
                if job_id in job_ids:
                    return job_ids.index(job_id) + 1
            
            return None
            
        except Exception:
            return None
    
    async def retry_processing(self, document_id: UUID, priority: bool = False) -> str:
        """
        Retry processing for a failed document
        
        Requirements: 5.3, 5.5 - Error handling and recovery
        """
        try:
            document = await self.get_document(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Cancel any existing job
            job_id = f"doc_process_{document_id}"
            self.queue_service.cancel_job(job_id)
            
            # Reset document status
            await self.update_status(document_id, ProcessingStatus.PENDING)
            
            # Re-queue for processing
            new_job_id = await self.queue_for_processing(document_id, priority=priority)
            
            self.security_logger.log_security_event(
                "document_processing_retry",
                {
                    "document_id": str(document_id),
                    "old_job_id": job_id,
                    "new_job_id": new_job_id,
                    "priority": priority
                },
                "INFO"
            )
            
            return new_job_id
            
        except Exception as e:
            self.security_logger.log_security_event(
                "document_retry_error",
                {
                    "document_id": str(document_id),
                    "error": str(e)
                },
                "ERROR"
            )
            raise
    
    async def get_multiple_processing_status(self, document_ids: list[UUID]) -> dict:
        """
        Get processing status for multiple documents efficiently
        
        Requirements: 4.2 - UI integration for document lists
        """
        try:
            # Get all documents in one query
            stmt = select(Document).where(Document.id.in_(document_ids))
            
            if hasattr(self.db, 'execute') and callable(getattr(self.db, 'execute')):
                if hasattr(self.db.execute, '__await__'):
                    result = await self.db.execute(stmt)
                else:
                    result = self.db.execute(stmt)
            documents = result.scalars().all()
            
            # Build status dictionary
            status_dict = {}
            for doc in documents:
                # Extract basic progress info
                progress_pct = 0
                current_step = None
                if doc.doc_metadata and 'processing_progress' in doc.doc_metadata:
                    progress_data = doc.doc_metadata['processing_progress']
                    progress_pct = progress_data.get("progress_percentage", 0)
                    current_step = progress_data.get("current_step")
                
                status_dict[str(doc.id)] = {
                    "status": doc.status.value if doc.status else "unknown",
                    "progress_percentage": progress_pct,
                    "current_step": current_step,
                    "error_message": doc.error_message,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                }
            
            return status_dict
            
        except Exception as e:
            self.security_logger.log_security_event(
                "multiple_status_error",
                {
                    "document_ids": [str(id) for id in document_ids],
                    "error": str(e)
                },
                "ERROR"
            )
            return {"error": str(e)}
    
    def get_queue_health(self) -> dict:
        """
        Get queue system health information
        
        Requirements: 6.2, 6.3 - System responsiveness monitoring
        """
        return self.queue_service.health_check()