"""
Redis Queue service for background processing
"""

import redis
import logging
from rq import Queue, Worker, Retry
from rq.exceptions import NoSuchJobError
from uuid import UUID
from typing import Optional, Dict, List
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing Redis Queue operations"""
    
    def __init__(self):
        try:
            self.redis_conn = redis.from_url(settings.redis_url)
            # Test connection
            self.redis_conn.ping()
            
            # Create queues with different priorities
            self.queue = Queue('document_processing', connection=self.redis_conn)
            self.priority_queue = Queue('priority_processing', connection=self.redis_conn)
            
            logger.info("QueueService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize QueueService: {e}")
            raise
    
    async def enqueue_document_processing(
        self, 
        document_id: UUID, 
        priority: bool = False,
        retry_attempts: int = 3
    ) -> str:
        """
        Enqueue document for background processing
        
        Requirements: 1.3, 6.1, 6.2, 6.3 - Background processing with RQ
        
        Args:
            document_id: UUID of document to process
            priority: Whether to use priority queue
            retry_attempts: Number of retry attempts on failure
        
        Returns:
            Job ID for tracking
        """
        try:
            from app.workers.document_processor import process_document
            
            # Choose queue based on priority
            queue = self.priority_queue if priority else self.queue
            
            # Configure retry policy
            retry_policy = Retry(max=retry_attempts) if retry_attempts > 0 else None
            
            job = queue.enqueue(
                process_document,
                str(document_id),
                job_timeout='30m',  # 30 minute timeout
                job_id=f"doc_process_{document_id}",
                retry=retry_policy,
                description=f"Process document {document_id}"
            )
            
            logger.info(f"Enqueued document {document_id} for processing (job_id: {job.id})")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to enqueue document {document_id}: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get job status and progress
        
        Requirements: 1.4, 1.5 - Status tracking and progress updates
        """
        try:
            # Try to fetch from both queues
            job = None
            try:
                job = self.queue.job_class.fetch(job_id, connection=self.redis_conn)
            except NoSuchJobError:
                try:
                    job = self.priority_queue.job_class.fetch(job_id, connection=self.redis_conn)
                except NoSuchJobError:
                    pass
            
            if job:
                return {
                    'id': job.id,
                    'status': job.get_status(),
                    'created_at': job.created_at.isoformat() if job.created_at else None,
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'ended_at': job.ended_at.isoformat() if job.ended_at else None,
                    'result': job.result,
                    'exc_info': job.exc_info,
                    'description': job.description,
                    'timeout': job.timeout,
                    'retry_attempts': getattr(job, 'retries_left', 0)
                }
        except Exception as e:
            logger.error(f"Error fetching job status for {job_id}: {e}")
        return None
    
    def get_queue_info(self) -> Dict:
        """
        Get comprehensive queue information
        
        Requirements: 6.2, 6.3 - Queue monitoring and responsiveness
        """
        try:
            return {
                'queues': {
                    'document_processing': {
                        'name': self.queue.name,
                        'length': len(self.queue),
                        'failed_jobs': len(self.queue.failed_job_registry),
                        'scheduled_jobs': len(self.queue.scheduled_job_registry),
                        'started_jobs': len(self.queue.started_job_registry),
                        'finished_jobs': len(self.queue.finished_job_registry)
                    },
                    'priority_processing': {
                        'name': self.priority_queue.name,
                        'length': len(self.priority_queue),
                        'failed_jobs': len(self.priority_queue.failed_job_registry),
                        'scheduled_jobs': len(self.priority_queue.scheduled_job_registry),
                        'started_jobs': len(self.priority_queue.started_job_registry),
                        'finished_jobs': len(self.priority_queue.finished_job_registry)
                    }
                },
                'redis_info': {
                    'connected': True,
                    'memory_usage': self.redis_conn.info().get('used_memory_human', 'unknown')
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting queue info: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def clear_failed_jobs(self, queue_name: str = 'all') -> Dict[str, int]:
        """
        Clear failed jobs from the queue(s)
        
        Args:
            queue_name: 'all', 'document_processing', or 'priority_processing'
        
        Returns:
            Dictionary with counts of cleared jobs per queue
        """
        try:
            results = {}
            
            if queue_name in ['all', 'document_processing']:
                failed_registry = self.queue.failed_job_registry
                count = len(failed_registry)
                # Clear failed jobs by removing them
                for job_id in failed_registry.get_job_ids():
                    failed_registry.remove(job_id)
                results['document_processing'] = count
                logger.info(f"Cleared {count} failed jobs from document_processing queue")
            
            if queue_name in ['all', 'priority_processing']:
                failed_registry = self.priority_queue.failed_job_registry
                count = len(failed_registry)
                # Clear failed jobs by removing them
                for job_id in failed_registry.get_job_ids():
                    failed_registry.remove(job_id)
                results['priority_processing'] = count
                logger.info(f"Cleared {count} failed jobs from priority_processing queue")
            
            return results
            
        except Exception as e:
            logger.error(f"Error clearing failed jobs: {e}")
            return {'error': str(e)}
    
    def get_job_by_document_id(self, document_id: UUID) -> Optional[Dict]:
        """
        Get job information by document ID
        
        Requirements: 1.4, 1.5 - Document-specific job tracking
        """
        job_id = f"doc_process_{document_id}"
        return self.get_job_status(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or running job
        
        Requirements: 5.3, 5.5 - Error handling and recovery
        """
        try:
            # Try to cancel from both queues
            for queue in [self.queue, self.priority_queue]:
                try:
                    job = queue.job_class.fetch(job_id, connection=self.redis_conn)
                    if job:
                        job.cancel()
                        logger.info(f"Cancelled job {job_id}")
                        return True
                except NoSuchJobError:
                    continue
            
            logger.warning(f"Job {job_id} not found for cancellation")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def get_active_workers(self) -> List[Dict]:
        """
        Get information about active workers
        
        Requirements: 6.2, 6.3 - System responsiveness monitoring
        """
        try:
            workers = Worker.all(connection=self.redis_conn)
            return [
                {
                    'name': worker.name,
                    'state': worker.get_state(),
                    'current_job': worker.get_current_job_id(),
                    'queues': [q.name for q in worker.queues],
                    'birth_date': worker.birth_date.isoformat() if worker.birth_date else None,
                    'last_heartbeat': worker.last_heartbeat.isoformat() if worker.last_heartbeat else None
                }
                for worker in workers
            ]
        except Exception as e:
            logger.error(f"Error getting worker info: {e}")
            return []
    
    def health_check(self) -> Dict:
        """
        Perform health check on queue system
        
        Requirements: 6.1, 6.2 - System health and responsiveness
        """
        try:
            # Test Redis connection
            self.redis_conn.ping()
            
            # Get queue stats
            queue_info = self.get_queue_info()
            workers = self.get_active_workers()
            
            # Calculate health metrics
            total_pending = (
                queue_info['queues']['document_processing']['length'] +
                queue_info['queues']['priority_processing']['length']
            )
            
            total_failed = (
                queue_info['queues']['document_processing']['failed_jobs'] +
                queue_info['queues']['priority_processing']['failed_jobs']
            )
            
            active_workers = len([w for w in workers if w['state'] == 'busy'])
            
            return {
                'status': 'healthy',
                'redis_connected': True,
                'total_pending_jobs': total_pending,
                'total_failed_jobs': total_failed,
                'active_workers': active_workers,
                'total_workers': len(workers),
                'queue_info': queue_info,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Queue health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'redis_connected': False,
                'timestamp': datetime.utcnow().isoformat()
            }