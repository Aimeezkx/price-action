"""
Document processing worker
"""

import asyncio
import logging
from uuid import UUID

from app.services.document_processing_pipeline import DocumentProcessingPipeline

logger = logging.getLogger(__name__)


def process_document(document_id_str: str) -> dict:
    """
    Background worker function to process a document through the complete pipeline.
    
    This is the main entry point for RQ workers.
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5 - Complete document processing pipeline
    """
    document_id = UUID(document_id_str)
    
    # Run async processing in sync context (required by RQ)
    return asyncio.run(_process_document_async(document_id))


async def _process_document_async(document_id: UUID) -> dict:
    """
    Async document processing implementation using the DocumentProcessingPipeline.
    
    This function orchestrates the complete pipeline:
    1. Document parsing
    2. Chapter extraction
    3. Knowledge point extraction
    4. Entity recognition
    5. Flashcard generation
    """
    
    logger.info(f"Starting complete pipeline processing for document {document_id}")
    
    try:
        # Initialize the processing pipeline
        pipeline = DocumentProcessingPipeline()
        
        # Process the document through the complete pipeline
        result = await pipeline.process_document(document_id)
        
        logger.info(f"Successfully processed document {document_id} through complete pipeline")
        
        return {
            'document_id': str(document_id),
            'status': 'completed',
            'pipeline_result': result
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_id} through pipeline: {str(e)}")
        
        return {
            'document_id': str(document_id),
            'status': 'failed',
            'error': str(e)
        }