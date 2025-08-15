"""
Document processing worker
"""

import asyncio
import logging
from pathlib import Path
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.document import ProcessingStatus
from app.services.document_service import DocumentService
from app.services.chapter_service import ChapterExtractor
from app.services.chapter_db_service import ChapterDBService
from app.parsers.factory import ParserFactory

logger = logging.getLogger(__name__)


def process_document(document_id_str: str) -> dict:
    """
    Background worker function to process a document
    
    This is the main entry point for RQ workers.
    Requirements: 1.4, 1.5 - Background processing and status updates
    """
    document_id = UUID(document_id_str)
    
    # Run async processing in sync context (required by RQ)
    return asyncio.run(_process_document_async(document_id))


async def _process_document_async(document_id: UUID) -> dict:
    """Async document processing implementation"""
    
    logger.info(f"Starting processing for document {document_id}")
    
    # Get database session
    async with get_async_session() as db:
        doc_service = DocumentService(db)
        
        try:
            # Update status to processing
            await doc_service.update_status(document_id, ProcessingStatus.PROCESSING)
            
            # Get document
            document = await doc_service.get_document(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            logger.info(f"Processing document: {document.filename} ({document.file_type})")
            
            # Process document through the pipeline
            result = await _process_document_pipeline(document, db)
            
            # Update status to completed
            await doc_service.update_status(document_id, ProcessingStatus.COMPLETED)
            
            logger.info(f"Successfully processed document {document_id}")
            
            return {
                'document_id': str(document_id),
                'status': 'completed',
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Update status to failed
            try:
                await doc_service.update_status(
                    document_id, 
                    ProcessingStatus.FAILED, 
                    str(e)
                )
            except Exception as update_error:
                logger.error(f"Failed to update document status: {update_error}")
            
            return {
                'document_id': str(document_id),
                'status': 'failed',
                'error': str(e)
            }


async def _process_document_pipeline(document, db: AsyncSession) -> dict:
    """
    Main document processing pipeline.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5 - Chapter structure recognition
    """
    import time
    start_time = time.time()
    
    # Basic file validation
    import os
    if not os.path.exists(document.file_path):
        raise FileNotFoundError(f"Document file not found: {document.file_path}")
    
    file_path = Path(document.file_path)
    
    # Step 1: Parse document content
    logger.info(f"Parsing document: {document.filename}")
    parser_factory = ParserFactory()
    parser = parser_factory.get_parser(file_path)
    
    if not parser:
        raise ValueError(f"No parser available for file type: {document.file_type}")
    
    parsed_content = await parser.parse(file_path)
    logger.info(f"Extracted {len(parsed_content.text_blocks)} text blocks and {len(parsed_content.images)} images")
    
    # Step 2: Extract chapter structure
    logger.info("Extracting chapter structure...")
    chapter_extractor = ChapterExtractor()
    extracted_chapters = await chapter_extractor.extract_chapters(file_path, parsed_content)
    
    logger.info(f"Extracted {len(extracted_chapters)} chapters")
    
    # Step 3: Save chapters to database
    chapter_db_service = ChapterDBService(db)
    
    # Delete existing chapters for this document (in case of reprocessing)
    await chapter_db_service.delete_chapters_by_document(document.id)
    
    # Create new chapters
    chapters = await chapter_db_service.create_chapters(document.id, extracted_chapters)
    
    processing_time = time.time() - start_time
    
    return {
        'filename': document.filename,
        'file_type': document.file_type,
        'file_size': os.path.getsize(document.file_path),
        'processing_time': processing_time,
        'chapters_extracted': len(chapters),
        'text_blocks_processed': len(parsed_content.text_blocks),
        'images_extracted': len(parsed_content.images),
        'knowledge_points': 0,    # Will be implemented in later tasks
        'cards_generated': 0      # Will be implemented in later tasks
    }