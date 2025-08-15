"""
Tests for chapter database service.
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chapter_db_service import ChapterDBService
from app.services.chapter_service import ExtractedChapter
from app.models.document import Document, Chapter, ProcessingStatus
from app.parsers.base import TextBlock


@pytest.mark.asyncio
async def test_create_chapters(async_session: AsyncSession):
    """Test creating chapters in the database."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=1000,
        status=ProcessingStatus.PENDING
    )
    async_session.add(document)
    await async_session.flush()
    
    # Create extracted chapters
    content_blocks = [
        TextBlock("Chapter 1 content", 1, {"x": 0, "y": 0, "width": 100, "height": 20}),
        TextBlock("More content", 1, {"x": 0, "y": 30, "width": 100, "height": 20}),
    ]
    
    extracted_chapters = [
        ExtractedChapter(
            title="Introduction",
            level=1,
            order_index=0,
            page_start=1,
            page_end=2,
            content_blocks=content_blocks
        ),
        ExtractedChapter(
            title="Methods",
            level=1,
            order_index=1,
            page_start=3,
            page_end=5,
            content_blocks=[]
        )
    ]
    
    # Create chapters using the service
    service = ChapterDBService(async_session)
    chapters = await service.create_chapters(document.id, extracted_chapters)
    
    assert len(chapters) == 2
    
    # Check first chapter
    assert chapters[0].title == "Introduction"
    assert chapters[0].level == 1
    assert chapters[0].order_index == 0
    assert chapters[0].page_start == 1
    assert chapters[0].page_end == 2
    assert chapters[0].document_id == document.id
    assert "Chapter 1 content" in chapters[0].content
    
    # Check second chapter
    assert chapters[1].title == "Methods"
    assert chapters[1].level == 1
    assert chapters[1].order_index == 1
    assert chapters[1].page_start == 3
    assert chapters[1].page_end == 5
    assert chapters[1].document_id == document.id
    assert chapters[1].content == ""  # No content blocks


@pytest.mark.asyncio
async def test_get_chapters_by_document(async_session: AsyncSession):
    """Test retrieving chapters by document ID."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=1000,
        status=ProcessingStatus.PENDING
    )
    async_session.add(document)
    await async_session.flush()
    
    # Create chapters directly
    chapter1 = Chapter(
        document_id=document.id,
        title="Chapter 1",
        level=1,
        order_index=0,
        page_start=1,
        page_end=2,
        content="Chapter 1 content"
    )
    chapter2 = Chapter(
        document_id=document.id,
        title="Chapter 2",
        level=1,
        order_index=1,
        page_start=3,
        page_end=4,
        content="Chapter 2 content"
    )
    
    async_session.add_all([chapter1, chapter2])
    await async_session.flush()
    
    # Retrieve chapters using the service
    service = ChapterDBService(async_session)
    chapters = await service.get_chapters_by_document(document.id)
    
    assert len(chapters) == 2
    assert chapters[0].title == "Chapter 1"  # Should be ordered by order_index
    assert chapters[1].title == "Chapter 2"


@pytest.mark.asyncio
async def test_get_chapter(async_session: AsyncSession):
    """Test retrieving a single chapter by ID."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=1000,
        status=ProcessingStatus.PENDING
    )
    async_session.add(document)
    await async_session.flush()
    
    # Create a chapter
    chapter = Chapter(
        document_id=document.id,
        title="Test Chapter",
        level=1,
        order_index=0,
        page_start=1,
        page_end=2,
        content="Test content"
    )
    async_session.add(chapter)
    await async_session.flush()
    
    # Retrieve chapter using the service
    service = ChapterDBService(async_session)
    retrieved_chapter = await service.get_chapter(chapter.id)
    
    assert retrieved_chapter is not None
    assert retrieved_chapter.id == chapter.id
    assert retrieved_chapter.title == "Test Chapter"
    
    # Test with non-existent ID
    non_existent_chapter = await service.get_chapter(uuid4())
    assert non_existent_chapter is None


@pytest.mark.asyncio
async def test_delete_chapters_by_document(async_session: AsyncSession):
    """Test deleting all chapters for a document."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=1000,
        status=ProcessingStatus.PENDING
    )
    async_session.add(document)
    await async_session.flush()
    
    # Create chapters
    chapter1 = Chapter(
        document_id=document.id,
        title="Chapter 1",
        level=1,
        order_index=0,
        page_start=1,
        page_end=2,
        content="Chapter 1 content"
    )
    chapter2 = Chapter(
        document_id=document.id,
        title="Chapter 2",
        level=1,
        order_index=1,
        page_start=3,
        page_end=4,
        content="Chapter 2 content"
    )
    
    async_session.add_all([chapter1, chapter2])
    await async_session.flush()
    
    # Verify chapters exist
    service = ChapterDBService(async_session)
    chapters_before = await service.get_chapters_by_document(document.id)
    assert len(chapters_before) == 2
    
    # Delete chapters
    await service.delete_chapters_by_document(document.id)
    await async_session.commit()
    
    # Verify chapters are deleted
    chapters_after = await service.get_chapters_by_document(document.id)
    assert len(chapters_after) == 0


@pytest.mark.asyncio
async def test_update_chapter_content(async_session: AsyncSession):
    """Test updating chapter content."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_type="pdf",
        file_path="/tmp/test.pdf",
        file_size=1000,
        status=ProcessingStatus.PENDING
    )
    async_session.add(document)
    await async_session.flush()
    
    # Create a chapter
    chapter = Chapter(
        document_id=document.id,
        title="Test Chapter",
        level=1,
        order_index=0,
        page_start=1,
        page_end=2,
        content="Original content"
    )
    async_session.add(chapter)
    await async_session.flush()
    
    # Update content using the service
    service = ChapterDBService(async_session)
    updated_chapter = await service.update_chapter_content(chapter.id, "Updated content")
    
    assert updated_chapter is not None
    assert updated_chapter.content == "Updated content"
    
    # Test with non-existent chapter
    non_existent_result = await service.update_chapter_content(uuid4(), "New content")
    assert non_existent_result is None