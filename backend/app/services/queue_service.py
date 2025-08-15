"""
Redis Queue service for background processing
"""

import redis
from rq import Queue, Worker
from uuid import UUID
from typing import Optional

from app.core.config import settings


class QueueService:
    """Service for managing Redis Queue operations"""
    
    def __init__(self):
        self.redis_conn = redis.from_url(settings.redis_url)
        self.queue = Queue('document_processing', connection=self.redis_conn)
    
    async def enqueue_document_processing(self, document_id: UUID) -> str:
        """
        Enqueue document for background processing
        
        Requirements: 1.3, 1.4 - Background processing with RQ
        """
        from app.workers.document_processor import process_document
        
        job = self.queue.enqueue(
            process_document,
            str(document_id),
            job_timeout='30m',  # 30 minute timeout
            job_id=f"doc_process_{document_id}"
        )
        
        return job.id
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get job status and progress"""
        try:
            job = self.queue.job_class.fetch(job_id, connection=self.redis_conn)
            if job:
                return {
                    'id': job.id,
                    'status': job.get_status(),
                    'created_at': job.created_at,
                    'started_at': job.started_at,
                    'ended_at': job.ended_at,
                    'result': job.result,
                    'exc_info': job.exc_info
                }
        except Exception:
            pass
        return None
    
    def get_queue_info(self) -> dict:
        """Get queue information"""
        return {
            'name': self.queue.name,
            'length': len(self.queue),
            'failed_jobs': len(self.queue.failed_job_registry),
            'scheduled_jobs': len(self.queue.scheduled_job_registry),
            'started_jobs': len(self.queue.started_job_registry)
        }
    
    def clear_failed_jobs(self) -> int:
        """Clear failed jobs from the queue"""
        failed_registry = self.queue.failed_job_registry
        count = len(failed_registry)
        failed_registry.requeue_all()
        return count