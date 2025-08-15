#!/usr/bin/env python3
"""
RQ Worker startup script
"""

import sys
import logging
from rq import Worker
import redis

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Start RQ worker"""
    
    logger.info("Starting RQ worker...")
    
    # Connect to Redis
    try:
        redis_conn = redis.from_url(settings.redis_url)
        redis_conn.ping()  # Test connection
        logger.info(f"Connected to Redis at {settings.redis_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    
    # Create worker
    worker = Worker(
        ['document_processing'],  # Queue names to listen to
        connection=redis_conn,
        name='document-worker'
    )
    
    logger.info("Worker started. Listening for jobs...")
    
    try:
        # Start worker (this blocks)
        worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)
    finally:
        logger.info("Worker stopped")


if __name__ == '__main__':
    main()