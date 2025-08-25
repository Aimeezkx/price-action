"""
Document upload and management API endpoints
"""

import os
import aiofiles
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.models.document import Document, ProcessingStatus, Chapter, Figure
from app.models.knowledge import Knowledge
from app.models.learning import Card, CardType, SRS
from app.core.config import settings
from app.services.document_service import DocumentService
from app.services.card_generation_service import CardGenerationService
from app.schemas.document import DocumentResponse, DocumentCreate
from app.utils.file_validation import validate_file
from app.utils.security import SecurityValidator, generate_secure_filename
from app.utils.access_control import AccessController, require_rate_limit, check_rate_limit
from app.utils.security import get_client_ip
from app.utils.logging import SecurityLogger
from app.utils.privacy_service import privacy_manager

router = APIRouter(prefix="/api", tags=["documents"])
security_logger = SecurityLogger(__name__)


@router.post("/ingest", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
) -> DocumentResponse:
    """
    Upload and queue a document for processing with comprehensive error handling
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.4, 11.1, 11.2, 11.3
    Task 5: Add comprehensive error handling to upload endpoint
    """
    # Get client IP for logging
    client_ip = get_client_ip(request)
    temp_file_path = None
    document = None
    
    try:
        # === RATE LIMITING CHECK ===
        if check_rate_limit(client_ip, "upload"):
            security_logger.log_security_event(
                "upload_rate_limit_exceeded",
                {
                    "client_ip": client_ip,
                    "filename": getattr(file, 'filename', 'unknown'),
                    "user_agent": request.headers.get("User-Agent", "")
                },
                "MEDIUM"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Upload rate limit exceeded. Please try again later.",
                    "retry_after": 3600  # 1 hour
                }
            )
        
        # === BASIC FILE VALIDATION ===
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "no_file_provided",
                    "message": "No file was provided in the request."
                }
            )
        
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "no_filename",
                    "message": "File must have a filename."
                }
            )
        
        # Check file size early if available
        if hasattr(file, 'size') and file.size is not None:
            if file.size == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "empty_file",
                        "message": "File is empty. Please upload a file with content."
                    }
                )
            
            if file.size > settings.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error": "file_too_large",
                        "message": f"File size ({file.size:,} bytes) exceeds maximum allowed size ({settings.max_file_size:,} bytes).",
                        "max_size_bytes": settings.max_file_size,
                        "file_size_bytes": file.size
                    }
                )
        
        # === INITIAL SECURITY VALIDATION ===
        try:
            security_validator = SecurityValidator()
            initial_validation = security_validator.validate_upload_file(file)
            
            if not initial_validation['is_secure']:
                security_logger.log_security_event(
                    "file_validation_failed",
                    {
                        "filename": file.filename,
                        "issues": initial_validation['issues'],
                        "client_ip": client_ip
                    },
                    "HIGH"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "file_validation_failed",
                        "message": "File failed security validation.",
                        "issues": initial_validation['issues'],
                        "allowed_extensions": list(security_validator.allowed_extensions),
                        "max_file_size": security_validator.max_file_size
                    }
                )
            
            # Log warnings if any
            if initial_validation.get('warnings'):
                security_logger.log_security_event(
                    "file_validation_warnings",
                    {
                        "filename": file.filename,
                        "warnings": initial_validation['warnings'],
                        "client_ip": client_ip
                    },
                    "INFO"
                )
        
        except Exception as e:
            security_logger.log_security_event(
                "file_validation_error",
                {
                    "filename": file.filename,
                    "error": str(e),
                    "client_ip": client_ip
                },
                "ERROR"
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "validation_system_error",
                    "message": "File validation system encountered an error. Please try again."
                }
            )
        
        # === GENERATE SECURE FILENAME ===
        try:
            safe_filename = generate_secure_filename(file.filename)
            file_type = Path(file.filename).suffix.lower()
        except Exception as e:
            security_logger.log_security_event(
                "filename_generation_error",
                {
                    "original_filename": file.filename,
                    "error": str(e),
                    "client_ip": client_ip
                },
                "ERROR"
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_filename",
                    "message": "Unable to process filename. Please use a simpler filename with standard characters."
                }
            )
        
        # === COMPREHENSIVE FILE VALIDATION ===
        try:
            import tempfile
            import aiofiles
            
            # Create temporary file for validation
            temp_fd, temp_file_path = tempfile.mkstemp(suffix=file_type)
            os.close(temp_fd)  # Close the file descriptor
            
            # Save uploaded content to temporary file
            try:
                file_content = await file.read()
                if not file_content:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "empty_file_content",
                            "message": "File appears to be empty or could not be read."
                        }
                    )
                
                async with aiofiles.open(temp_file_path, 'wb') as temp_file:
                    await temp_file.write(file_content)
                
                # Reset file pointer for later use
                await file.seek(0)
                
            except Exception as e:
                security_logger.log_security_event(
                    "file_read_error",
                    {
                        "filename": file.filename,
                        "error": str(e),
                        "client_ip": client_ip
                    },
                    "ERROR"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "file_read_failed",
                        "message": "Unable to read uploaded file. The file may be corrupted or in an unsupported format."
                    }
                )
            
            # Perform comprehensive file validation
            try:
                from app.utils.file_validation import validate_file_upload
                comprehensive_validation = validate_file_upload(Path(temp_file_path))
                
                if not comprehensive_validation.is_valid:
                    security_logger.log_security_event(
                        "comprehensive_validation_failed",
                        {
                            "filename": file.filename,
                            "error_message": comprehensive_validation.error_message,
                            "warnings": comprehensive_validation.warnings,
                            "client_ip": client_ip
                        },
                        "HIGH"
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error": "file_security_validation_failed",
                            "message": comprehensive_validation.error_message,
                            "warnings": comprehensive_validation.warnings,
                            "help": "Please ensure your file is not corrupted and does not contain malicious content."
                        }
                    )
                
                # Log warnings if any
                if comprehensive_validation.warnings:
                    security_logger.log_security_event(
                        "comprehensive_validation_warnings",
                        {
                            "filename": file.filename,
                            "warnings": comprehensive_validation.warnings,
                            "client_ip": client_ip
                        },
                        "INFO"
                    )
            
            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as e:
                security_logger.log_security_event(
                    "comprehensive_validation_error",
                    {
                        "filename": file.filename,
                        "error": str(e),
                        "client_ip": client_ip
                    },
                    "ERROR"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "validation_system_error",
                        "message": "File validation system encountered an error. Please try again."
                    }
                )
        
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            security_logger.log_security_event(
                "temp_file_creation_error",
                {
                    "filename": file.filename,
                    "error": str(e),
                    "client_ip": client_ip
                },
                "ERROR"
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "temporary_file_error",
                    "message": "Unable to process file for validation. Server may be experiencing storage issues."
                }
            )
        
        finally:
            # Clean up temporary file
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                except Exception as cleanup_error:
                    security_logger.log_security_event(
                        "temp_file_cleanup_error",
                        {
                            "temp_file_path": temp_file_path,
                            "error": str(cleanup_error),
                            "client_ip": client_ip
                        },
                        "WARNING"
                    )
        
        # === DATABASE OPERATIONS ===
        try:
            # Test database connection
            from sqlalchemy import text
            
            # Handle both async and sync sessions
            if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
                if hasattr(db.execute, '__await__'):
                    await db.execute(text("SELECT 1"))
                else:
                    db.execute(text("SELECT 1"))
            else:
                db.execute(text("SELECT 1"))
            
            # Create document service
            doc_service = DocumentService(db)
            
            # Create document record and save file with secure filename
            document = await doc_service.create_document(file, safe_filename)
            
        except Exception as db_error:
            error_type = type(db_error).__name__
            
            # Handle specific database errors
            if "connection" in str(db_error).lower() or "timeout" in str(db_error).lower():
                security_logger.log_security_event(
                    "database_connection_error",
                    {
                        "filename": file.filename,
                        "error": str(db_error),
                        "error_type": error_type,
                        "client_ip": client_ip
                    },
                    "HIGH"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "database_unavailable",
                        "message": "Database is temporarily unavailable. Please try again in a few moments.",
                        "retry_after": 60
                    }
                )
            
            elif "disk" in str(db_error).lower() or "space" in str(db_error).lower():
                security_logger.log_security_event(
                    "database_storage_error",
                    {
                        "filename": file.filename,
                        "error": str(db_error),
                        "error_type": error_type,
                        "client_ip": client_ip
                    },
                    "CRITICAL"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                    detail={
                        "error": "insufficient_storage",
                        "message": "Server storage is full. Please contact support or try again later."
                    }
                )
            
            elif "constraint" in str(db_error).lower() or "unique" in str(db_error).lower():
                security_logger.log_security_event(
                    "database_constraint_error",
                    {
                        "filename": file.filename,
                        "error": str(db_error),
                        "error_type": error_type,
                        "client_ip": client_ip
                    },
                    "MEDIUM"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "document_conflict",
                        "message": "A document with similar properties already exists. Please check your uploads."
                    }
                )
            
            else:
                security_logger.log_security_event(
                    "database_general_error",
                    {
                        "filename": file.filename,
                        "error": str(db_error),
                        "error_type": error_type,
                        "client_ip": client_ip
                    },
                    "HIGH"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "database_error",
                        "message": "Database operation failed. Please try again."
                    }
                )
        
        # === STORAGE OPERATIONS ===
        try:
            # Check storage space before processing
            upload_dir = Path(settings.upload_dir)
            
            # Check if upload directory exists and is writable
            if not upload_dir.exists():
                try:
                    upload_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    security_logger.log_security_event(
                        "storage_permission_error",
                        {
                            "upload_dir": str(upload_dir),
                            "operation": "create_directory",
                            "client_ip": client_ip
                        },
                        "CRITICAL"
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={
                            "error": "storage_permission_denied",
                            "message": "Server does not have permission to create upload directory. Please contact support."
                        }
                    )
            
            # Check available disk space
            try:
                import shutil
                total, used, free = shutil.disk_usage(upload_dir)
                
                # Require at least 1GB free space or 2x file size, whichever is larger
                required_space = max(1024 * 1024 * 1024, (file.size or 0) * 2)
                
                if free < required_space:
                    security_logger.log_security_event(
                        "insufficient_disk_space",
                        {
                            "free_space": free,
                            "required_space": required_space,
                            "file_size": file.size,
                            "upload_dir": str(upload_dir),
                            "client_ip": client_ip
                        },
                        "CRITICAL"
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                        detail={
                            "error": "insufficient_disk_space",
                            "message": "Server does not have enough disk space to store the file.",
                            "available_space": free,
                            "required_space": required_space
                        }
                    )
            
            except Exception as space_check_error:
                # Log but don't fail upload for disk space check errors
                security_logger.log_security_event(
                    "disk_space_check_error",
                    {
                        "error": str(space_check_error),
                        "upload_dir": str(upload_dir),
                        "client_ip": client_ip
                    },
                    "WARNING"
                )
        
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as storage_error:
            security_logger.log_security_event(
                "storage_preparation_error",
                {
                    "filename": file.filename,
                    "error": str(storage_error),
                    "client_ip": client_ip
                },
                "HIGH"
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "storage_preparation_failed",
                    "message": "Unable to prepare storage for file upload. Please try again."
                }
            )
        
        # === QUEUE FOR PROCESSING ===
        try:
            await doc_service.queue_for_processing(document.id)
            
        except Exception as queue_error:
            # Log error but don't fail the upload - document is saved
            security_logger.log_security_event(
                "queue_processing_error",
                {
                    "document_id": str(document.id),
                    "filename": file.filename,
                    "error": str(queue_error),
                    "client_ip": client_ip
                },
                "MEDIUM"
            )
            
            # Update document status to indicate queue failure
            try:
                await doc_service.update_status(
                    document.id, 
                    ProcessingStatus.FAILED, 
                    f"Failed to queue for processing: {str(queue_error)}"
                )
            except Exception:
                pass  # Don't fail if status update fails
        
        # === SUCCESS LOGGING ===
        security_logger.log_security_event(
            "document_upload_success",
            {
                "document_id": str(document.id),
                "filename": file.filename,
                "file_type": file_type,
                "file_size": getattr(file, 'size', 0),
                "client_ip": client_ip,
                "secure_filename": safe_filename
            },
            "INFO"
        )
        
        security_logger.log_file_upload(
            filename=file.filename,
            user_id=client_ip,  # Using IP as user identifier for now
            success=True
        )
        
        return DocumentResponse.model_validate(document)
    
    except HTTPException:
        # Log failed upload attempt for HTTP exceptions
        security_logger.log_file_upload(
            filename=getattr(file, 'filename', 'unknown'),
            user_id=client_ip,
            success=False,
            reason=f"HTTP {getattr(HTTPException, 'status_code', 'unknown')}"
        )
        raise  # Re-raise HTTP exceptions as-is
    
    except Exception as unexpected_error:
        # Handle any unexpected errors
        error_type = type(unexpected_error).__name__
        
        security_logger.log_security_event(
            "unexpected_upload_error",
            {
                "filename": getattr(file, 'filename', 'unknown'),
                "error": str(unexpected_error),
                "error_type": error_type,
                "client_ip": client_ip,
                "document_id": str(document.id) if document else None
            },
            "CRITICAL"
        )
        
        security_logger.log_file_upload(
            filename=getattr(file, 'filename', 'unknown'),
            user_id=client_ip,
            success=False,
            reason=f"Unexpected error: {error_type}"
        )
        
        # Clean up document if it was created but processing failed
        if document:
            try:
                doc_service = DocumentService(db)
                await doc_service.delete_document(document.id)
            except Exception:
                pass  # Don't fail if cleanup fails
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "unexpected_server_error",
                "message": "An unexpected error occurred while processing your upload. Please try again.",
                "error_id": f"{error_type}_{int(datetime.utcnow().timestamp())}"
            }
        )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
) -> List[DocumentResponse]:
    """List all documents with their processing status"""
    
    try:
        stmt = select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        # Return empty list if there's an error
        return []


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> DocumentResponse:
    """Get document by ID"""
    
    stmt = select(Document).where(Document.id == document_id)
    
    # Handle both async and sync sessions
    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
        if hasattr(db.execute, '__await__'):
            result = await db.execute(stmt)
        else:
            result = db.execute(stmt)
    else:
        result = db.execute(stmt)
    
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.get("/doc/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> DocumentResponse:
    """
    Get document by ID
    
    Requirements: 1.1, 1.2 - Document management endpoints
    """
    
    stmt = select(Document).where(Document.id == document_id)
    
    # Handle both async and sync sessions
    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
        if hasattr(db.execute, '__await__'):
            result = await db.execute(stmt)
        else:
            result = db.execute(stmt)
    else:
        result = db.execute(stmt)
    
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get comprehensive document processing status and progress
    
    Requirements: 1.4, 1.5, 4.2 - Status tracking, progress updates, and UI integration
    """
    try:
        doc_service = DocumentService(db)
        status_info = await doc_service.get_processing_status(document_id)
        
        if "error" in status_info:
            if status_info["error"] == "Document not found":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error retrieving status: {status_info['error']}"
                )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        security_logger.log_security_event(
            "status_endpoint_error",
            {
                "document_id": str(document_id),
                "error": str(e)
            },
            "ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving document status"
        )


@router.post("/documents/{document_id}/status")
async def update_document_status(
    document_id: UUID,
    status_update: dict,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Update document processing status (for internal use by processing workers)
    
    Requirements: 1.4, 1.5 - Status tracking and progress updates
    """
    try:
        doc_service = DocumentService(db)
        
        # Extract update parameters
        new_status = status_update.get("status")
        error_message = status_update.get("error_message")
        progress_data = status_update.get("progress_data")
        
        # Validate status if provided
        if new_status:
            try:
                status_enum = ProcessingStatus(new_status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {new_status}"
                )
        else:
            status_enum = None
        
        # Update document status
        document = await doc_service.update_status(
            document_id, 
            status_enum, 
            error_message, 
            progress_data
        )
        
        return {
            "document_id": str(document.id),
            "status": document.status.value,
            "updated_at": document.updated_at.isoformat(),
            "message": "Status updated successfully"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        security_logger.log_security_event(
            "status_update_error",
            {
                "document_id": str(document_id),
                "status_update": status_update,
                "error": str(e)
            },
            "ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating document status"
        )


@router.post("/documents/status/batch")
async def get_multiple_document_status(
    document_ids: List[UUID],
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get processing status for multiple documents efficiently
    
    Requirements: 4.2 - UI integration for document lists
    """
    try:
        if not document_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No document IDs provided"
            )
        
        if len(document_ids) > 100:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many document IDs (max 100)"
            )
        
        doc_service = DocumentService(db)
        status_dict = await doc_service.get_multiple_processing_status(document_ids)
        
        if "error" in status_dict:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving batch status: {status_dict['error']}"
            )
        
        return {
            "documents": status_dict,
            "count": len(status_dict)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        security_logger.log_security_event(
            "batch_status_error",
            {
                "document_ids": [str(id) for id in document_ids],
                "error": str(e)
            },
            "ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving batch document status"
        )


@router.post("/documents/{document_id}/retry")
async def retry_document_processing(
    document_id: UUID,
    priority: bool = False,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Retry processing for a failed document
    
    Requirements: 5.3, 5.5 - Error handling and recovery
    """
    try:
        doc_service = DocumentService(db)
        
        # Check if document exists and can be retried
        document = await doc_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Only allow retry for failed or completed documents
        if document.status not in [ProcessingStatus.FAILED, ProcessingStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot retry document with status: {document.status.value}"
            )
        
        # Retry processing
        job_id = await doc_service.retry_processing(document_id, priority=priority)
        
        return {
            "document_id": str(document_id),
            "job_id": job_id,
            "status": "queued_for_retry",
            "priority": priority,
            "message": "Document queued for retry processing"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        security_logger.log_security_event(
            "retry_processing_error",
            {
                "document_id": str(document_id),
                "priority": priority,
                "error": str(e)
            },
            "ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrying document processing"
        )


@router.get("/processing/overview")
async def get_processing_overview(
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get overview of all document processing status
    
    Requirements: 4.2, 6.2 - UI integration and system monitoring
    """
    try:
        # Get counts by status
        from sqlalchemy import func
        
        status_counts_stmt = (
            select(Document.status, func.count(Document.id))
            .group_by(Document.status)
        )
        
        if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
            if hasattr(db.execute, '__await__'):
                result = await db.execute(status_counts_stmt)
            else:
                result = db.execute(status_counts_stmt)
        
        status_counts = {}
        for status, count in result.fetchall():
            status_counts[status.value if status else "unknown"] = count
        
        # Get recent documents (last 24 hours)
        from datetime import timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        
        recent_docs_stmt = (
            select(Document)
            .where(Document.created_at >= recent_cutoff)
            .order_by(Document.created_at.desc())
            .limit(10)
        )
        
        if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
            if hasattr(db.execute, '__await__'):
                recent_result = await db.execute(recent_docs_stmt)
            else:
                recent_result = db.execute(recent_docs_stmt)
        
        recent_docs = recent_result.scalars().all()
        
        # Get queue health
        doc_service = DocumentService(db)
        queue_health = doc_service.get_queue_health()
        
        return {
            "status_counts": status_counts,
            "recent_documents": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "status": doc.status.value if doc.status else "unknown",
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                }
                for doc in recent_docs
            ],
            "queue_health": queue_health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        security_logger.log_security_event(
            "processing_overview_error",
            {
                "error": str(e)
            },
            "ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving processing overview"
        )


@router.get("/doc/{document_id}/toc")
async def get_document_table_of_contents(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get document table of contents (chapter structure)
    
    Requirements: 3.3 - Chapter structure and table of contents
    """
    
    # Verify document exists
    doc_stmt = select(Document).where(Document.id == document_id)
    
    # Handle both async and sync sessions
    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
        if hasattr(db.execute, '__await__'):
            doc_result = await db.execute(doc_stmt)
        else:
            doc_result = db.execute(doc_stmt)
    else:
        doc_result = db.execute(doc_stmt)
    
    document = doc_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get chapters with their structure
    chapters_stmt = (
        select(Chapter)
        .where(Chapter.document_id == document_id)
        .order_by(Chapter.order_index)
    )
    
    # Handle both async and sync sessions
    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
        if hasattr(db.execute, '__await__'):
            chapters_result = await db.execute(chapters_stmt)
        else:
            chapters_result = db.execute(chapters_stmt)
    else:
        chapters_result = db.execute(chapters_stmt)
    
    chapters = chapters_result.scalars().all()
    
    # Build hierarchical table of contents
    toc = {
        "document_id": document_id,
        "document_title": document.filename,
        "total_chapters": len(chapters),
        "chapters": []
    }
    
    for chapter in chapters:
        chapter_info = {
            "id": str(chapter.id),
            "title": chapter.title,
            "level": chapter.level,
            "order_index": chapter.order_index,
            "page_start": chapter.page_start,
            "page_end": chapter.page_end,
            "has_content": bool(chapter.content)
        }
        toc["chapters"].append(chapter_info)
    
    return toc


@router.get("/chapter/{chapter_id}/fig")
async def get_chapter_figures(
    chapter_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get figures/images for a specific chapter
    
    Requirements: 4.5 - Image and caption pairing display
    """
    
    # Verify chapter exists
    chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
    
    # Handle both async and sync sessions
    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
        if hasattr(db.execute, '__await__'):
            chapter_result = await db.execute(chapter_stmt)
        else:
            chapter_result = db.execute(chapter_stmt)
    else:
        chapter_result = db.execute(chapter_stmt)
    
    chapter = chapter_result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Get figures for this chapter
    figures_stmt = (
        select(Figure)
        .where(Figure.chapter_id == chapter_id)
        .order_by(Figure.page_number, Figure.id)
    )
    
    # Handle both async and sync sessions
    if hasattr(db, 'execute') and callable(getattr(db, 'execute')):
        if hasattr(db.execute, '__await__'):
            figures_result = await db.execute(figures_stmt)
        else:
            figures_result = db.execute(figures_stmt)
    else:
        figures_result = db.execute(figures_stmt)
    
    figures = figures_result.scalars().all()
    figures = figures_result.scalars().all()
    
    # Format response
    response = {
        "chapter_id": str(chapter_id),
        "chapter_title": chapter.title,
        "total_figures": len(figures),
        "figures": []
    }
    
    for figure in figures:
        figure_info = {
            "id": str(figure.id),
            "image_path": figure.image_path,
            "caption": figure.caption,
            "page_number": figure.page_number,
            "bbox": figure.bbox,
            "image_format": figure.image_format
        }
        response["figures"].append(figure_info)
    
    return response


@router.get("/chapter/{chapter_id}/k")
async def get_chapter_knowledge_points(
    chapter_id: UUID,
    knowledge_type: Optional[str] = Query(None, description="Filter by knowledge type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of knowledge points"),
    offset: int = Query(0, ge=0, description="Number of knowledge points to skip"),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get knowledge points for a specific chapter
    
    Requirements: 5.4 - Knowledge point display with anchors
    """
    
    # Verify chapter exists
    chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
    chapter_result = await db.execute(chapter_stmt)
    chapter = chapter_result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Build knowledge query
    knowledge_stmt = select(Knowledge).where(Knowledge.chapter_id == chapter_id)
    
    # Apply knowledge type filter if provided
    if knowledge_type:
        try:
            from app.models.knowledge import KnowledgeType
            knowledge_enum = KnowledgeType(knowledge_type.lower())
            knowledge_stmt = knowledge_stmt.where(Knowledge.kind == knowledge_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid knowledge type: {knowledge_type}"
            )
    
    # Apply pagination
    knowledge_stmt = knowledge_stmt.offset(offset).limit(limit).order_by(Knowledge.created_at)
    
    knowledge_result = await db.execute(knowledge_stmt)
    knowledge_points = knowledge_result.scalars().all()
    
    # Format response
    response = {
        "chapter_id": str(chapter_id),
        "chapter_title": chapter.title,
        "total_knowledge_points": len(knowledge_points),
        "knowledge_points": []
    }
    
    for kp in knowledge_points:
        kp_info = {
            "id": str(kp.id),
            "kind": kp.kind.value,
            "text": kp.text,
            "entities": kp.entities or [],
            "anchors": kp.anchors or {},
            "confidence_score": kp.confidence_score,
            "created_at": kp.created_at.isoformat()
        }
        response["knowledge_points"].append(kp_info)
    
    return response


@router.post("/card/gen")
async def generate_cards_for_chapter(
    chapter_id: UUID = Query(..., description="Chapter ID to generate cards for"),
    card_types: Optional[List[str]] = Query(None, description="Card types to generate (qa, cloze, image_hotspot)"),
    max_cards: int = Query(50, ge=1, le=200, description="Maximum number of cards to generate"),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Generate flashcards for a specific chapter
    
    Requirements: 6.4 - Card generation with traceability
    """
    
    # Verify chapter exists
    chapter_stmt = select(Chapter).where(Chapter.id == chapter_id)
    chapter_result = await db.execute(chapter_stmt)
    chapter = chapter_result.scalar_one_or_none()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    try:
        # Get knowledge points for this chapter
        knowledge_stmt = select(Knowledge).where(Knowledge.chapter_id == chapter_id)
        knowledge_result = await db.execute(knowledge_stmt)
        knowledge_points = knowledge_result.scalars().all()
        
        if not knowledge_points:
            return {
                "chapter_id": str(chapter_id),
                "message": "No knowledge points found for this chapter",
                "generated_cards": 0,
                "cards": []
            }
        
        # Get figures for image hotspot cards
        figures_stmt = select(Figure).where(Figure.chapter_id == chapter_id)
        figures_result = await db.execute(figures_stmt)
        figures = figures_result.scalars().all()
        
        # Initialize card generation service
        card_service = CardGenerationService()
        
        # Generate cards
        generated_cards = await card_service.generate_cards_from_knowledge(
            knowledge_points=knowledge_points[:max_cards//2],  # Limit knowledge points to control card count
            figures=figures if not card_types or "image_hotspot" in card_types else None
        )
        
        # Filter by requested card types if specified
        if card_types:
            valid_types = {CardType.QA.value, CardType.CLOZE.value, CardType.IMAGE_HOTSPOT.value}
            requested_types = set(card_types) & valid_types
            if requested_types:
                generated_cards = [
                    card for card in generated_cards 
                    if card.card_type.value in requested_types
                ]
        
        # Limit to max_cards
        generated_cards = generated_cards[:max_cards]
        
        # Save cards to database
        saved_cards = []
        for gen_card in generated_cards:
            # Create Card model
            card = Card(
                knowledge_id=UUID(gen_card.knowledge_id),
                card_type=gen_card.card_type,
                front=gen_card.front,
                back=gen_card.back,
                difficulty=gen_card.difficulty,
                card_metadata=gen_card.metadata
            )
            
            db.add(card)
            await db.flush()  # Get the card ID
            
            # Create SRS record for the card
            srs = SRS(
                card_id=card.id,
                user_id=None  # No user system yet
            )
            db.add(srs)
            
            saved_cards.append({
                "id": str(card.id),
                "card_type": card.card_type.value,
                "front": card.front[:100] + "..." if len(card.front) > 100 else card.front,
                "back": card.back[:100] + "..." if len(card.back) > 100 else card.back,
                "difficulty": card.difficulty,
                "knowledge_id": str(card.knowledge_id),
                "metadata": card.card_metadata
            })
        
        await db.commit()
        
        return {
            "chapter_id": str(chapter_id),
            "chapter_title": chapter.title,
            "generated_cards": len(saved_cards),
            "cards": saved_cards
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cards: {str(e)}"
        )


@router.get("/cards")
async def get_cards(
    document_id: Optional[UUID] = Query(None, description="Filter by document ID"),
    chapter_id: Optional[UUID] = Query(None, description="Filter by chapter ID"),
    card_type: Optional[str] = Query(None, description="Filter by card type"),
    difficulty_min: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum difficulty"),
    difficulty_max: Optional[float] = Query(None, ge=0.0, le=5.0, description="Maximum difficulty"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of cards"),
    offset: int = Query(0, ge=0, description="Number of cards to skip"),
    db: AsyncSession = Depends(get_async_db)
) -> dict:
    """
    Get flashcards with filtering options
    
    Requirements: 6.4 - Card management and retrieval
    """
    
    # Build base query
    cards_stmt = (
        select(Card, Knowledge, Chapter)
        .join(Knowledge, Card.knowledge_id == Knowledge.id)
        .join(Chapter, Knowledge.chapter_id == Chapter.id)
    )
    
    # Apply filters
    if document_id:
        cards_stmt = cards_stmt.join(Document, Chapter.document_id == Document.id).where(Document.id == document_id)
    
    if chapter_id:
        cards_stmt = cards_stmt.where(Chapter.id == chapter_id)
    
    if card_type:
        try:
            card_type_enum = CardType(card_type.lower())
            cards_stmt = cards_stmt.where(Card.card_type == card_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid card type: {card_type}"
            )
    
    if difficulty_min is not None:
        cards_stmt = cards_stmt.where(Card.difficulty >= difficulty_min)
    
    if difficulty_max is not None:
        cards_stmt = cards_stmt.where(Card.difficulty <= difficulty_max)
    
    # Apply pagination and ordering
    cards_stmt = cards_stmt.offset(offset).limit(limit).order_by(Card.created_at.desc())
    
    # Execute query
    cards_result = await db.execute(cards_stmt)
    results = cards_result.all()
    
    # Format response
    cards_data = []
    for card, knowledge, chapter in results:
        card_info = {
            "id": str(card.id),
            "card_type": card.card_type.value,
            "front": card.front,
            "back": card.back,
            "difficulty": card.difficulty,
            "metadata": card.card_metadata or {},
            "knowledge": {
                "id": str(knowledge.id),
                "kind": knowledge.kind.value,
                "text": knowledge.text[:200] + "..." if len(knowledge.text) > 200 else knowledge.text,
                "entities": knowledge.entities or []
            },
            "chapter": {
                "id": str(chapter.id),
                "title": chapter.title,
                "document_id": str(chapter.document_id)
            },
            "created_at": card.created_at.isoformat()
        }
        cards_data.append(card_info)
    
    return {
        "total_cards": len(cards_data),
        "filters_applied": {
            "document_id": str(document_id) if document_id else None,
            "chapter_id": str(chapter_id) if chapter_id else None,
            "card_type": card_type,
            "difficulty_range": [difficulty_min, difficulty_max]
        },
        "cards": cards_data
    }


@router.get("/privacy/status")
async def get_privacy_status() -> dict:
    """
    Get current privacy and security configuration status
    
    Requirements: 11.1, 11.2, 11.3, 11.4, 11.5
    """
    status = privacy_manager.get_privacy_status()
    warnings = privacy_manager.validate_privacy_settings()
    
    return {
        "privacy_configuration": status,
        "warnings": warnings,
        "security_features": {
            "file_validation": True,
            "rate_limiting": True,
            "secure_logging": settings.anonymize_logs,
            "malware_scanning": settings.enable_file_scanning
        }
    }


@router.post("/privacy/toggle")
async def toggle_privacy_mode(
    request: Request,
    enable: bool = Query(..., description="Enable or disable privacy mode")
) -> dict:
    """
    Toggle privacy mode (admin endpoint)
    
    Requirements: 11.1 - Privacy mode toggle
    """
    # In a real application, this would require admin authentication
    # For now, we'll just log the change
    
    client_ip = get_client_ip(request)
    
    # Update settings (in a real app, this would update persistent config)
    old_mode = settings.privacy_mode
    settings.privacy_mode = enable
    
    # Log the change
    security_logger.log_security_event(
        "privacy_mode_changed",
        {
            "old_mode": old_mode,
            "new_mode": enable,
            "client_ip": client_ip
        },
        "WARNING"
    )
    
    return {
        "privacy_mode": settings.privacy_mode,
        "message": f"Privacy mode {'enabled' if enable else 'disabled'}",
        "warnings": privacy_manager.validate_privacy_settings()
    }