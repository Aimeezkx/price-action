"""
Database service for chapter operations.
"""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..models.document import Chapter
from ..services.chapter_service import ExtractedChapter


class ChapterDBService:
    """Service for chapter database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_chapters(self, document_id: UUID, extracted_chapters: List[ExtractedChapter]) -> List[Chapter]:
        """
        Create chapter records in the database.
        
        Args:
            document_id: ID of the parent document
            extracted_chapters: List of extracted chapters
            
        Returns:
            List of created Chapter models
        """
        chapters = []
        
        for extracted in extracted_chapters:
            # Create content text from content blocks
            content_text = ""
            if extracted.content_blocks:
                content_text = "\n\n".join(block.text for block in extracted.content_blocks)
            
            chapter = Chapter(
                document_id=document_id,
                title=extracted.title,
                level=extracted.level,
                order_index=extracted.order_index,
                page_start=extracted.page_start,
                page_end=extracted.page_end,
                content=content_text
            )
            
            self.db.add(chapter)
            chapters.append(chapter)
        
        await self.db.flush()  # Get IDs without committing
        return chapters
    
    async def get_chapters_by_document(self, document_id: UUID) -> List[Chapter]:
        """Get all chapters for a document."""
        stmt = select(Chapter).where(Chapter.document_id == document_id).order_by(Chapter.order_index)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_chapter(self, chapter_id: UUID) -> Chapter:
        """Get a single chapter by ID."""
        stmt = select(Chapter).where(Chapter.id == chapter_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete_chapters_by_document(self, document_id: UUID) -> None:
        """Delete all chapters for a document."""
        stmt = delete(Chapter).where(Chapter.document_id == document_id)
        await self.db.execute(stmt)
    
    async def update_chapter_content(self, chapter_id: UUID, content: str) -> Chapter:
        """Update chapter content."""
        chapter = await self.get_chapter(chapter_id)
        if chapter:
            chapter.content = content
            await self.db.flush()
        return chapter