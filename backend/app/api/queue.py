"""
Queue management API endpoints
"""

from typing import Dict, List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.document_service import DocumentService
from app.services.queue_service import QueueService

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("/health")
async def get_queue_health() -> Dict:
    """
    Get queue system health status
    
    Requirements: 6.2, 6.3 - System responsiveness monitoring
    """
    try:
        queue_service = QueueService()
        return queue_service.health_check()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Queue health check failed: {str(e)}"
        )


@router.get("/info")
async def get_queue_info() -> Dict:
    """
    Get detailed queue information
    
    Requirements: 6.2, 6.3 - Queue monitoring
    """
    try:
        queue_service = QueueService()
        return queue_service.get_queue_info()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue info: {str(e)}"
        )


@router.get("/workers")
async def get_active_workers() -> List[Dict]:
    """
    Get information about active workers
    
    Requirements: 6.2 - System responsiveness monitoring
    """
    try:
        queue_service = QueueService()
        return queue_service.get_active_workers()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get worker info: {str(e)}"
        )


@router.post("/clear-failed")
async def clear_failed_jobs(queue_name: str = "all") -> Dict[str, int]:
    """
    Clear failed jobs from queue(s)
    
    Requirements: 5.3, 5.5 - Error handling and recovery
    
    Args:
        queue_name: 'all', 'document_processing', or 'priority_processing'
    """
    try:
        queue_service = QueueService()
        return queue_service.clear_failed_jobs(queue_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear failed jobs: {str(e)}"
        )


@router.get("/job/{job_id}")
async def get_job_status(job_id: str) -> Dict:
    """
    Get status of a specific job
    
    Requirements: 1.4, 1.5 - Job status tracking
    """
    try:
        queue_service = QueueService()
        job_status = queue_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return job_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str) -> Dict:
    """
    Cancel a queued or running job
    
    Requirements: 5.3, 5.5 - Error handling and recovery
    """
    try:
        queue_service = QueueService()
        success = queue_service.cancel_job(job_id)
        
        return {
            "job_id": job_id,
            "cancelled": success,
            "message": "Job cancelled successfully" if success else "Job not found or already completed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/document/{document_id}/status")
async def get_document_processing_status(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Get comprehensive processing status for a document
    
    Requirements: 1.4, 1.5 - Document processing status tracking
    """
    try:
        doc_service = DocumentService(db)
        return await doc_service.get_processing_status(document_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.post("/document/{document_id}/retry")
async def retry_document_processing(
    document_id: UUID,
    priority: bool = False,
    db: AsyncSession = Depends(get_async_db)
) -> Dict:
    """
    Retry processing for a failed document
    
    Requirements: 5.3, 5.5 - Error handling and recovery
    
    Args:
        document_id: UUID of document to retry
        priority: Whether to use priority queue
    """
    try:
        doc_service = DocumentService(db)
        job_id = await doc_service.retry_processing(document_id, priority=priority)
        
        return {
            "document_id": str(document_id),
            "job_id": job_id,
            "priority": priority,
            "message": "Document queued for retry processing"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry processing: {str(e)}"
        )