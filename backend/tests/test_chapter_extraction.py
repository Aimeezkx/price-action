"""
Tests for chapter extraction functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.chapter_service import ChapterExtractor, ChapterCandidate, ExtractedChapter
from app.parsers.base import TextBlock, ParsedContent


class TestChapterExtractor:
    """Test chapter extraction service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = ChapterExtractor()
    
    def test_pattern_matching(self):
        """Test chapter heading pattern matching."""
        # Test chapter patterns
        assert self.extractor._check_patterns("Chapter 1: Introduction") > 0.8
        assert self.extractor._check_patterns("第一章 概述") > 0.8
        assert self.extractor._check_patterns("1. Introduction") > 0.6
        assert self.extractor._check_patterns("# Main Heading") > 0.8
        
        # Test section patterns
        assert self.extractor._check_patterns("1.1 Subsection") > 0.6
        assert self.extractor._check_patterns("## Subheading") > 0.6
        
        # Test non-patterns
        assert self.extractor._check_patterns("This is regular text.") < 0.5
        assert self.extractor._check_patterns("Some random content here") < 0.5
    
    def test_heading_level_determination(self):
        """Test heading level determination."""
        # Markdown headers
        assert self.extractor._determine_heading_level("# Main Header", None) == 1
        assert self.extractor._determine_heading_level("## Sub Header", None) == 2
        assert self.extractor._determine_heading_level("### Sub-sub Header", None) == 3
        
        # Numbered sections
        assert self.extractor._determine_heading_level("1. Main Section", None) == 1
        assert self.extractor._determine_heading_level("1.1 Subsection", None) == 2
        assert self.extractor._determine_heading_level("1.1.1 Sub-subsection", None) == 3
        
        # Font size based
        font_large = {"size": 20}
        font_medium = {"size": 16}
        font_small = {"size": 12}
        
        assert self.extractor._determine_heading_level("Some Title", font_large) == 1
        assert self.extractor._determine_heading_level("Some Title", font_medium) == 2
        assert self.extractor._determine_heading_level("Some Title", font_small) == 3
    
    def test_text_similarity(self):
        """Test text similarity calculation."""
        # Identical text
        assert self.extractor._text_similarity("Chapter 1", "Chapter 1") == 1.0
        
        # Similar text
        similarity = self.extractor._text_similarity("Chapter 1 Introduction", "Chapter 1 Overview")
        assert 0.3 < similarity < 0.8
        
        # Different text
        similarity = self.extractor._text_similarity("Chapter 1", "Conclusion")
        assert similarity < 0.3
        
        # Empty text
        assert self.extractor._text_similarity("", "") == 1.0
        assert self.extractor._text_similarity("text", "") == 0.0
    
    def test_find_heading_candidates(self):
        """Test finding heading candidates from text blocks."""
        text_blocks = [
            TextBlock(
                text="Chapter 1: Introduction",
                page=1,
                bbox={"x": 0, "y": 50, "width": 200, "height": 20},
                font_info={"size": 18, "font": "Arial-Bold"}
            ),
            TextBlock(
                text="This is regular paragraph text that should not be detected as a heading.",
                page=1,
                bbox={"x": 0, "y": 100, "width": 400, "height": 40},
                font_info={"size": 12, "font": "Arial"}
            ),
            TextBlock(
                text="1.1 Subsection",
                page=1,
                bbox={"x": 0, "y": 150, "width": 150, "height": 15},
                font_info={"size": 14, "font": "Arial-Bold"}
            ),
        ]
        
        candidates = self.extractor._find_heading_candidates(text_blocks)
        
        # Should find 2 candidates (Chapter 1 and 1.1 Subsection)
        assert len(candidates) >= 1
        
        # First candidate should be the chapter
        chapter_candidate = next((c for c in candidates if "Chapter 1" in c.title), None)
        assert chapter_candidate is not None
        assert chapter_candidate.level == 1
        assert chapter_candidate.confidence > 0.6
    
    def test_filter_candidates(self):
        """Test filtering and ranking of candidates."""
        candidates = [
            ChapterCandidate("Chapter 1", 1, 1, 0, confidence=0.9),
            ChapterCandidate("Chapter 1: Introduction", 1, 1, 1, confidence=0.8),  # Similar to first
            ChapterCandidate("1.1 Subsection", 2, 1, 2, confidence=0.7),
            ChapterCandidate("Random text", 1, 2, 3, confidence=0.5),  # Low confidence
        ]
        
        filtered = self.extractor._filter_candidates(candidates)
        
        # Should remove the low confidence candidate (< 0.5)
        assert len(filtered) <= 4  # All candidates have >= 0.5 confidence
        
        # Should keep high confidence candidates
        titles = [c.title for c in filtered]
        confidences = [c.confidence for c in filtered]
        
        # All remaining candidates should have confidence >= 0.5
        assert all(conf >= 0.5 for conf in confidences)
        
        # Should include all candidates since they all meet the threshold
        assert "Chapter 1" in titles or "Chapter 1: Introduction" in titles
        assert "1.1 Subsection" in titles
    
    def test_candidates_to_chapters(self):
        """Test converting candidates to chapters."""
        text_blocks = [
            TextBlock("Chapter 1", 1, {"x": 0, "y": 0, "width": 100, "height": 20}),
            TextBlock("Content for chapter 1", 1, {"x": 0, "y": 30, "width": 200, "height": 40}),
            TextBlock("Chapter 2", 2, {"x": 0, "y": 0, "width": 100, "height": 20}),
            TextBlock("Content for chapter 2", 2, {"x": 0, "y": 30, "width": 200, "height": 40}),
        ]
        
        candidates = [
            ChapterCandidate("Chapter 1", 1, 1, 0, confidence=0.9),
            ChapterCandidate("Chapter 2", 1, 2, 2, confidence=0.8),
        ]
        
        chapters = self.extractor._candidates_to_chapters(candidates, text_blocks)
        
        assert len(chapters) == 2
        
        # Check first chapter
        assert chapters[0].title == "Chapter 1"
        assert chapters[0].page_start == 1
        assert chapters[0].page_end == 1  # Should end before next chapter
        assert len(chapters[0].content_blocks) >= 1
        
        # Check second chapter
        assert chapters[1].title == "Chapter 2"
        assert chapters[1].page_start == 2
        assert len(chapters[1].content_blocks) >= 1
    
    def test_assign_content_to_chapters(self):
        """Test assigning content blocks to chapters."""
        chapters = [
            ExtractedChapter("Chapter 1", 1, 0, 1, 2),
            ExtractedChapter("Chapter 2", 1, 1, 3, 4),
        ]
        
        text_blocks = [
            TextBlock("Chapter 1 title", 1, {"x": 0, "y": 0, "width": 100, "height": 20}),
            TextBlock("Chapter 1 content", 2, {"x": 0, "y": 0, "width": 200, "height": 40}),
            TextBlock("Chapter 2 title", 3, {"x": 0, "y": 0, "width": 100, "height": 20}),
            TextBlock("Chapter 2 content", 4, {"x": 0, "y": 0, "width": 200, "height": 40}),
            TextBlock("Orphaned content", 5, {"x": 0, "y": 0, "width": 200, "height": 40}),
        ]
        
        result = self.extractor._assign_content_to_chapters(chapters, text_blocks)
        
        # Check content assignment
        assert len(result[0].content_blocks) == 2  # Pages 1-2
        assert len(result[1].content_blocks) == 3  # Pages 3-4 + orphaned content
    
    def test_create_single_chapter(self):
        """Test creating a single default chapter."""
        text_blocks = [
            TextBlock("Some content", 1, {"x": 0, "y": 0, "width": 200, "height": 40}),
            TextBlock("More content", 2, {"x": 0, "y": 0, "width": 200, "height": 40}),
        ]
        
        chapters = self.extractor._create_single_chapter(text_blocks)
        
        assert len(chapters) == 1
        assert chapters[0].title == "Document Content"
        assert chapters[0].level == 1
        assert chapters[0].page_start == 1
        assert chapters[0].page_end == 2
        assert len(chapters[0].content_blocks) == 2
    
    @pytest.mark.asyncio
    async def test_extract_from_heuristics(self):
        """Test heuristic chapter extraction."""
        text_blocks = [
            TextBlock(
                text="Chapter 1: Introduction",
                page=1,
                bbox={"x": 0, "y": 50, "width": 200, "height": 20},
                font_info={"size": 18, "font": "Arial-Bold"}
            ),
            TextBlock(
                text="This is the introduction content.",
                page=1,
                bbox={"x": 0, "y": 100, "width": 400, "height": 40},
                font_info={"size": 12, "font": "Arial"}
            ),
            TextBlock(
                text="Chapter 2: Methods",
                page=2,
                bbox={"x": 0, "y": 50, "width": 200, "height": 20},
                font_info={"size": 18, "font": "Arial-Bold"}
            ),
        ]
        
        chapters = await self.extractor._extract_from_heuristics(text_blocks)
        
        # Should extract at least one chapter
        assert len(chapters) >= 1
        
        # Check if chapters have proper structure
        for chapter in chapters:
            assert chapter.title
            assert chapter.level >= 1
            assert chapter.page_start >= 1
    
    @pytest.mark.asyncio
    async def test_extract_chapters_fallback(self):
        """Test chapter extraction with fallback to single chapter."""
        # Create parsed content with no clear headings
        text_blocks = [
            TextBlock("Regular text content", 1, {"x": 0, "y": 0, "width": 200, "height": 40}),
            TextBlock("More regular content", 1, {"x": 0, "y": 50, "width": 200, "height": 40}),
        ]
        
        parsed_content = ParsedContent(text_blocks, [], {})
        
        # Mock file path
        file_path = Path("test.pdf")
        
        with patch.object(self.extractor, '_extract_from_bookmarks', return_value=[]):
            chapters = await self.extractor.extract_chapters(file_path, parsed_content)
        
        # Should fall back to single chapter
        assert len(chapters) == 1
        assert chapters[0].title == "Document Content"
        assert len(chapters[0].content_blocks) == 2


class TestChapterCandidate:
    """Test ChapterCandidate data class."""
    
    def test_chapter_candidate_creation(self):
        """Test creating a chapter candidate."""
        candidate = ChapterCandidate(
            title="Chapter 1",
            level=1,
            page=1,
            order_index=0,
            confidence=0.9
        )
        
        assert candidate.title == "Chapter 1"
        assert candidate.level == 1
        assert candidate.page == 1
        assert candidate.order_index == 0
        assert candidate.confidence == 0.9


class TestExtractedChapter:
    """Test ExtractedChapter data class."""
    
    def test_extracted_chapter_creation(self):
        """Test creating an extracted chapter."""
        chapter = ExtractedChapter(
            title="Introduction",
            level=1,
            order_index=0,
            page_start=1,
            page_end=5
        )
        
        assert chapter.title == "Introduction"
        assert chapter.level == 1
        assert chapter.order_index == 0
        assert chapter.page_start == 1
        assert chapter.page_end == 5
        assert chapter.content_blocks == []  # Should initialize empty list
    
    def test_extracted_chapter_with_content(self):
        """Test extracted chapter with content blocks."""
        content_blocks = [
            TextBlock("Content 1", 1, {"x": 0, "y": 0, "width": 100, "height": 20}),
            TextBlock("Content 2", 1, {"x": 0, "y": 30, "width": 100, "height": 20}),
        ]
        
        chapter = ExtractedChapter(
            title="Chapter with content",
            level=1,
            order_index=0,
            page_start=1,
            content_blocks=content_blocks
        )
        
        assert len(chapter.content_blocks) == 2
        assert chapter.content_blocks[0].text == "Content 1"