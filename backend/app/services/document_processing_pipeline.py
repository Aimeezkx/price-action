"""
Document Processing Pipeline Service

This service orchestrates the complete pipeline from document parsing to flashcard generation.
It connects all the existing services (parsers, knowledge extraction, card generation) into
a cohesive processing workflow.

Requirements addressed:
- 2.1: Document content extraction and parsing
- 2.2: Text segmentation and structure extraction  
- 2.3: Knowledge point extraction and classification
- 2.4: Entity recognition and extraction
- 2.5: Automatic flashcard generation
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.document import Document, ProcessingStatus, Chapter, Figure
from ..models.knowledge import Knowledge
from ..models.learning import Card
from ..parsers.factory import get_parser_for_file
from ..services.text_segmentation_service import TextSegmentationService
from ..services.knowledge_extraction_service import KnowledgeExtractionService
from ..services.card_generation_service import CardGenerationService
from ..services.chapter_service import ChapterService
from ..core.database import get_async_session
from ..utils.logging import SecurityLogger

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for processing pipeline errors."""
    pass


class DocumentProcessingPipeline:
    """
    Service for orchestrating the complete document processing pipeline.
    
    This service coordinates:
    1. Document parsing (PDF, DOCX, TXT, MD)
    2. Chapter and structure extraction
    3. Text segmentation
    4. Knowledge point extraction
    5. Entity recognition
    6. Flashcard generation
    7. Status tracking and error handling
    """
    
    def __init__(self):
        """Initialize the processing pipeline with required services."""
        self.text_segmentation = TextSegmentationService()
        self.knowledge_extraction = KnowledgeExtractionService()
        self.card_generation = CardGenerationService()
        self.chapter_service = ChapterService()
        self.security_logger = SecurityLogger(__name__)
        
        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "chapters_created": 0,
            "knowledge_points_extracted": 0,
            "cards_generated": 0,
            "processing_errors": 0
        }
    
    async def process_document(self, document_id: UUID) -> Dict[str, Any]:
        """
        Process a complete document through the entire pipeline.
        
        Args:
            document_id: UUID of the document to process
            
        Returns:
            Dictionary containing processing results and statistics
            
        Raises:
            ProcessingError: If any step in the pipeline fails
        """
        processing_start = datetime.utcnow()
        
        try:
            # Log processing start
            self.security_logger.log_security_event(
                "document_processing_start",
                {"document_id": str(document_id)},
                "INFO"
            )
            
            async with get_async_session() as session:
                # Step 1: Load document from database
                document = await self._load_document(session, document_id)
                if not document:
                    raise ProcessingError(f"Document {document_id} not found")
                
                # Step 2: Update status to processing
                await self._update_document_status(
                    session, document, ProcessingStatus.PROCESSING,
                    {"current_step": "parsing", "started_at": processing_start.isoformat()}
                )
                
                # Step 3: Parse document content
                parsed_content = await self._parse_document(document)
                
                # Step 4: Extract chapters and structure
                await self._update_processing_metadata(
                    session, document, {"current_step": "extracting_chapters"}
                )
                chapters = await self._extract_chapters(session, document, parsed_content)
                
                # Step 5: Process each chapter
                all_knowledge_points = []
                all_cards = []
                
                for chapter in chapters:
                    try:
                        # Extract knowledge points from chapter
                        await self._update_processing_metadata(
                            session, document, 
                            {"current_step": f"processing_chapter_{chapter.title[:30]}"}
                        )
                        
                        knowledge_points = await self._process_chapter(session, chapter)
                        all_knowledge_points.extend(knowledge_points)
                        
                        # Generate cards from knowledge points
                        chapter_figures = [fig for fig in parsed_content.images 
                                         if self._figure_belongs_to_chapter(fig, chapter)]
                        
                        cards = await self._generate_cards_for_chapter(
                            session, knowledge_points, chapter_figures
                        )
                        all_cards.extend(cards)
                        
                    except Exception as e:
                        logger.error(f"Error processing chapter {chapter.id}: {e}")
                        # Continue with other chapters
                        continue
                
                # Step 6: Update final status
                processing_end = datetime.utcnow()
                processing_duration = (processing_end - processing_start).total_seconds()
                
                final_metadata = {
                    "current_step": "completed",
                    "started_at": processing_start.isoformat(),
                    "completed_at": processing_end.isoformat(),
                    "processing_duration_seconds": processing_duration,
                    "chapters_created": len(chapters),
                    "knowledge_points_extracted": len(all_knowledge_points),
                    "cards_generated": len(all_cards),
                    "figures_processed": len(parsed_content.images)
                }
                
                await self._update_document_status(
                    session, document, ProcessingStatus.COMPLETED, final_metadata
                )
                
                # Update global statistics
                self.stats["documents_processed"] += 1
                self.stats["chapters_created"] += len(chapters)
                self.stats["knowledge_points_extracted"] += len(all_knowledge_points)
                self.stats["cards_generated"] += len(all_cards)
                
                # Log successful completion
                self.security_logger.log_security_event(
                    "document_processing_completed",
                    {
                        "document_id": str(document_id),
                        "processing_duration": processing_duration,
                        "chapters": len(chapters),
                        "knowledge_points": len(all_knowledge_points),
                        "cards": len(all_cards)
                    },
                    "INFO"
                )
                
                return {
                    "success": True,
                    "document_id": str(document_id),
                    "processing_duration": processing_duration,
                    "chapters_created": len(chapters),
                    "knowledge_points_extracted": len(all_knowledge_points),
                    "cards_generated": len(all_cards),
                    "figures_processed": len(parsed_content.images)
                }
                
        except Exception as e:
            # Handle processing errors
            await self._handle_processing_error(document_id, e)
            raise ProcessingError(f"Document processing failed: {str(e)}") from e
    
    async def _load_document(self, session: AsyncSession, document_id: UUID) -> Optional[Document]:
        """Load document from database."""
        try:
            from sqlalchemy import select
            stmt = select(Document).where(Document.id == document_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error loading document {document_id}: {e}")
            return None
    
    async def _update_document_status(
        self, 
        session: AsyncSession, 
        document: Document, 
        status: ProcessingStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update document status and processing metadata."""
        try:
            document.status = status
            
            if metadata:
                # Merge with existing metadata
                current_metadata = document.doc_metadata or {}
                current_metadata.update(metadata)
                document.doc_metadata = current_metadata
            
            await session.commit()
            await session.refresh(document)
            
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            await session.rollback()
            raise
    
    async def _update_processing_metadata(
        self,
        session: AsyncSession,
        document: Document,
        metadata: Dict[str, Any]
    ) -> None:
        """Update processing metadata without changing status."""
        try:
            current_metadata = document.doc_metadata or {}
            current_metadata.update(metadata)
            document.doc_metadata = current_metadata
            
            await session.commit()
            await session.refresh(document)
            
        except Exception as e:
            logger.error(f"Error updating processing metadata: {e}")
            # Don't raise - this is non-critical
    
    async def _parse_document(self, document: Document):
        """Parse document content using appropriate parser."""
        try:
            file_path = Path(document.file_path)
            
            # Validate file exists
            if not file_path.exists():
                raise ProcessingError(f"Document file not found: {file_path}")
            
            # Get appropriate parser based on file extension
            parser = get_parser_for_file(file_path)
            if not parser:
                # Try to provide helpful error message with supported formats
                from ..parsers.factory import get_supported_extensions
                supported_exts = get_supported_extensions()
                raise ProcessingError(
                    f"No parser available for file type '{file_path.suffix}'. "
                    f"Supported formats: {', '.join(supported_exts)}"
                )
            
            logger.info(f"Using {parser.name} to parse document {document.id}")
            
            # Parse the document with timeout protection
            try:
                parsed_content = await asyncio.wait_for(
                    parser.parse(file_path), 
                    timeout=300  # 5 minute timeout for parsing
                )
            except asyncio.TimeoutError:
                raise ProcessingError(
                    f"Document parsing timed out after 5 minutes. "
                    f"File may be too large or corrupted."
                )
            
            # Validate parsed content
            if not parsed_content:
                raise ProcessingError("Parser returned empty content")
            
            if not parsed_content.text_blocks:
                logger.warning(f"No text content extracted from document {document.id}")
                # This might be okay for image-only documents, so don't fail
            
            logger.info(
                f"Successfully parsed document {document.id} using {parser.name}: "
                f"{len(parsed_content.text_blocks)} text blocks, "
                f"{len(parsed_content.images)} images"
            )
            
            return parsed_content
            
        except ProcessingError:
            # Re-raise ProcessingError as-is
            raise
        except FileNotFoundError as e:
            logger.error(f"File not found for document {document.id}: {e}")
            raise ProcessingError(f"Document file not found: {str(e)}") from e
        except PermissionError as e:
            logger.error(f"Permission denied accessing document {document.id}: {e}")
            raise ProcessingError(f"Permission denied accessing document file: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error parsing document {document.id}: {e}")
            raise ProcessingError(f"Document parsing failed: {str(e)}") from e
    
    async def _extract_chapters(
        self, 
        session: AsyncSession, 
        document: Document, 
        parsed_content
    ) -> List[Chapter]:
        """Extract chapters and document structure."""
        try:
            # Use chapter service to extract chapters
            chapters = await self.chapter_service.extract_chapters_from_content(
                document.id, parsed_content
            )
            
            # Save figures to database
            await self._save_figures(session, parsed_content.images, chapters)
            
            logger.info(f"Extracted {len(chapters)} chapters from document {document.id}")
            return chapters
            
        except Exception as e:
            logger.error(f"Error extracting chapters from document {document.id}: {e}")
            raise ProcessingError(f"Chapter extraction failed: {str(e)}") from e
    
    async def _save_figures(
        self, 
        session: AsyncSession, 
        images: List, 
        chapters: List[Chapter]
    ) -> None:
        """Save extracted figures to database."""
        try:
            for image in images:
                # Find the chapter this image belongs to
                chapter = self._find_chapter_for_image(image, chapters)
                if chapter:
                    figure = Figure(
                        chapter_id=chapter.id,
                        image_path=image.image_path,
                        caption=getattr(image, 'caption', None),
                        page_number=image.page,
                        bbox=image.bbox,
                        image_format=image.format
                    )
                    session.add(figure)
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error saving figures: {e}")
            await session.rollback()
            # Don't raise - figures are not critical for processing
    
    def _find_chapter_for_image(self, image, chapters: List[Chapter]) -> Optional[Chapter]:
        """Find which chapter an image belongs to based on page number."""
        if not chapters:
            return None
        
        # Sort chapters by page start
        sorted_chapters = sorted(
            [ch for ch in chapters if ch.page_start is not None], 
            key=lambda x: x.page_start
        )
        
        # Find chapter that contains this page
        for i, chapter in enumerate(sorted_chapters):
            if chapter.page_start <= image.page:
                # Check if this is the last chapter or if image is before next chapter
                if i == len(sorted_chapters) - 1:
                    return chapter
                elif image.page < sorted_chapters[i + 1].page_start:
                    return chapter
        
        # Default to first chapter if no match found
        return chapters[0] if chapters else None
    
    async def _process_chapter(
        self, 
        session: AsyncSession, 
        chapter: Chapter
    ) -> List[Knowledge]:
        """Process a single chapter to extract knowledge points."""
        try:
            if not chapter.content:
                logger.warning(f"Chapter {chapter.id} has no content to process")
                return []
            
            # Step 1: Segment the chapter text
            segments = await self.text_segmentation.segment_text(
                chapter.content, 
                str(chapter.id),
                chapter.page_start or 1
            )
            
            if not segments:
                logger.warning(f"No segments extracted from chapter {chapter.id}")
                return []
            
            # Step 2: Extract knowledge points from segments
            knowledge_points = await self.knowledge_extraction.extract_knowledge_from_segments(
                segments, str(chapter.id)
            )
            
            # Step 3: Save knowledge points to database
            saved_knowledge = []
            for kp in knowledge_points:
                try:
                    knowledge = Knowledge(
                        chapter_id=chapter.id,
                        kind=kp.kind,
                        text=kp.text,
                        entities=kp.entities,
                        anchors=kp.anchors,
                        confidence_score=kp.confidence
                    )
                    session.add(knowledge)
                    saved_knowledge.append(knowledge)
                except Exception as e:
                    logger.error(f"Error saving knowledge point: {e}")
                    continue
            
            await session.commit()
            
            logger.info(
                f"Processed chapter {chapter.id}: "
                f"{len(segments)} segments, {len(saved_knowledge)} knowledge points"
            )
            
            return saved_knowledge
            
        except Exception as e:
            logger.error(f"Error processing chapter {chapter.id}: {e}")
            await session.rollback()
            raise ProcessingError(f"Chapter processing failed: {str(e)}") from e
    
    async def _generate_cards_for_chapter(
        self,
        session: AsyncSession,
        knowledge_points: List[Knowledge],
        figures: List
    ) -> List[Card]:
        """Generate flashcards for a chapter's knowledge points."""
        try:
            if not knowledge_points:
                return []
            
            # Generate cards using the card generation service
            generated_cards = await self.card_generation.generate_cards_from_knowledge(
                knowledge_points, figures
            )
            
            # Save cards to database
            saved_cards = []
            for gen_card in generated_cards:
                try:
                    card = Card(
                        knowledge_id=UUID(gen_card.knowledge_id),
                        card_type=gen_card.card_type,
                        front=gen_card.front,
                        back=gen_card.back,
                        difficulty=gen_card.difficulty,
                        metadata=gen_card.metadata
                    )
                    session.add(card)
                    saved_cards.append(card)
                except Exception as e:
                    logger.error(f"Error saving card: {e}")
                    continue
            
            await session.commit()
            
            logger.info(
                f"Generated {len(saved_cards)} cards from {len(knowledge_points)} knowledge points"
            )
            
            return saved_cards
            
        except Exception as e:
            logger.error(f"Error generating cards: {e}")
            await session.rollback()
            raise ProcessingError(f"Card generation failed: {str(e)}") from e
    
    def _figure_belongs_to_chapter(self, figure, chapter: Chapter) -> bool:
        """Check if a figure belongs to a specific chapter."""
        if not chapter.page_start or not chapter.page_end:
            return True  # Default to including if page info not available
        
        return chapter.page_start <= figure.page <= chapter.page_end
    
    async def _handle_processing_error(self, document_id: UUID, error: Exception) -> None:
        """Handle processing errors by updating document status."""
        try:
            async with get_async_session() as session:
                document = await self._load_document(session, document_id)
                if document:
                    error_metadata = {
                        "current_step": "failed",
                        "error_message": str(error),
                        "error_type": type(error).__name__,
                        "failed_at": datetime.utcnow().isoformat()
                    }
                    
                    await self._update_document_status(
                        session, document, ProcessingStatus.FAILED, error_metadata
                    )
            
            # Update error statistics
            self.stats["processing_errors"] += 1
            
            # Log error
            self.security_logger.log_security_event(
                "document_processing_failed",
                {
                    "document_id": str(document_id),
                    "error": str(error),
                    "error_type": type(error).__name__
                },
                "ERROR"
            )
            
        except Exception as e:
            logger.error(f"Error handling processing error for document {document_id}: {e}")
    
    async def retry_failed_document(self, document_id: UUID) -> Dict[str, Any]:
        """
        Retry processing for a failed document.
        
        Args:
            document_id: UUID of the document to retry
            
        Returns:
            Processing results
        """
        try:
            async with get_async_session() as session:
                document = await self._load_document(session, document_id)
                if not document:
                    raise ProcessingError(f"Document {document_id} not found")
                
                if document.status != ProcessingStatus.FAILED:
                    raise ProcessingError(
                        f"Document {document_id} is not in failed status (current: {document.status})"
                    )
                
                # Reset status to pending
                await self._update_document_status(
                    session, document, ProcessingStatus.PENDING,
                    {"retry_attempted_at": datetime.utcnow().isoformat()}
                )
            
            # Process the document
            return await self.process_document(document_id)
            
        except Exception as e:
            logger.error(f"Error retrying document {document_id}: {e}")
            raise ProcessingError(f"Document retry failed: {str(e)}") from e
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing pipeline statistics."""
        return {
            "statistics": self.stats.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_document_processing_status(self, document_id: UUID) -> Dict[str, Any]:
        """
        Get detailed processing status for a document.
        
        Args:
            document_id: UUID of the document
            
        Returns:
            Detailed status information
        """
        try:
            async with get_async_session() as session:
                document = await self._load_document(session, document_id)
                if not document:
                    return {"error": "Document not found"}
                
                # Get related counts
                from sqlalchemy import select, func
                
                # Count chapters
                chapter_stmt = select(func.count(Chapter.id)).where(Chapter.document_id == document_id)
                chapter_result = await session.execute(chapter_stmt)
                chapter_count = chapter_result.scalar() or 0
                
                # Count knowledge points
                knowledge_stmt = select(func.count(Knowledge.id)).join(Chapter).where(
                    Chapter.document_id == document_id
                )
                knowledge_result = await session.execute(knowledge_stmt)
                knowledge_count = knowledge_result.scalar() or 0
                
                # Count cards
                card_stmt = select(func.count(Card.id)).join(Knowledge).join(Chapter).where(
                    Chapter.document_id == document_id
                )
                card_result = await session.execute(card_stmt)
                card_count = card_result.scalar() or 0
                
                return {
                    "document_id": str(document_id),
                    "filename": document.filename,
                    "status": document.status.value,
                    "error_message": document.error_message,
                    "processing_metadata": document.doc_metadata or {},
                    "chapters_created": chapter_count,
                    "knowledge_points_extracted": knowledge_count,
                    "cards_generated": card_count,
                    "created_at": document.created_at.isoformat() if document.created_at else None,
                    "updated_at": document.updated_at.isoformat() if document.updated_at else None
                }
                
        except Exception as e:
            logger.error(f"Error getting processing status for document {document_id}: {e}")
            return {"error": str(e)}