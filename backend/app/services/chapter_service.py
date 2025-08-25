"""
Chapter extraction and structure recognition service.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

import fitz  # PyMuPDF

from ..parsers.base import ParsedContent, TextBlock
from ..models.document import Chapter
from ..core.database import get_async_session


@dataclass
class ChapterCandidate:
    """Represents a potential chapter heading."""
    
    title: str
    level: int
    page: int
    order_index: int
    bbox: Optional[Dict[str, float]] = None
    font_info: Optional[Dict[str, any]] = None
    confidence: float = 0.0


@dataclass
class ExtractedChapter:
    """Represents an extracted chapter with content."""
    
    title: str
    level: int
    order_index: int
    page_start: int
    page_end: Optional[int] = None
    content_blocks: List[TextBlock] = None
    
    def __post_init__(self):
        if self.content_blocks is None:
            self.content_blocks = []


class ChapterExtractor:
    """Service for extracting chapter structure from documents."""
    
    def __init__(self):
        """Initialize chapter extractor with default patterns."""
        # Common chapter heading patterns
        self.chapter_patterns = [
            r'^第\s*[一二三四五六七八九十\d]+\s*章',  # Chinese: 第一章, 第1章
            r'^Chapter\s+\d+',  # English: Chapter 1
            r'^CHAPTER\s+\d+',  # English uppercase
            r'^\d+\.\s*[A-Z]',  # Numbered sections: 1. Introduction
            r'^\d+\s+[A-Z]',    # Numbered without dot: 1 Introduction
            r'^[IVX]+\.\s*[A-Z]',  # Roman numerals: I. Introduction
            r'^#+\s+',          # Markdown headers: # Header, ## Subheader
        ]
        
        # Section/subsection patterns
        self.section_patterns = [
            r'^\d+\.\d+\s*[A-Z]',  # 1.1 Subsection
            r'^\d+\.\d+\.\d+\s*[A-Z]',  # 1.1.1 Sub-subsection
            r'^##\s+',          # Markdown level 2 headers
            r'^###\s+',         # Markdown level 3 headers
        ]
        
        # Minimum font size difference for heading detection
        self.min_font_size_diff = 2.0
        
        # Minimum confidence threshold for heuristic detection
        self.min_confidence = 0.6
    
    async def extract_chapters(self, file_path: Path, parsed_content: ParsedContent) -> List[ExtractedChapter]:
        """
        Extract chapters from any supported document format.
        
        Args:
            file_path: Path to the document file
            parsed_content: Already parsed content from the document
            
        Returns:
            List of extracted chapters
        """
        try:
            # For PDF documents, try bookmark extraction first
            if file_path.suffix.lower() == '.pdf':
                chapters = await self._extract_from_bookmarks(file_path)
                
                if chapters:
                    # Assign content blocks to bookmark-based chapters
                    chapters = self._assign_content_to_chapters(chapters, parsed_content.text_blocks)
                    return chapters
            
            # For all documents (including PDFs without bookmarks), use heuristic extraction
            chapters = await self._extract_from_heuristics(parsed_content.text_blocks)
            
            if chapters:
                return chapters
            
            # Final fallback: single chapter with all content
            return self._create_single_chapter(parsed_content.text_blocks)
            
        except Exception as e:
            # On any error, fall back to single chapter
            return self._create_single_chapter(parsed_content.text_blocks)
    
    async def _extract_from_bookmarks(self, file_path: Path) -> List[ExtractedChapter]:
        """Extract chapters from PDF bookmarks/outlines."""
        chapters = []
        
        try:
            doc = fitz.open(str(file_path))
            toc = doc.get_toc()  # Get table of contents
            
            if not toc:
                return []
            
            for i, (level, title, page) in enumerate(toc):
                # Clean up title
                title = title.strip()
                if not title:
                    continue
                
                chapter = ExtractedChapter(
                    title=title,
                    level=level,
                    order_index=i,
                    page_start=page,
                )
                chapters.append(chapter)
            
            # Set page_end for each chapter
            for i in range(len(chapters)):
                if i + 1 < len(chapters):
                    chapters[i].page_end = chapters[i + 1].page_start - 1
                else:
                    chapters[i].page_end = len(doc)
            
            doc.close()
            
        except Exception:
            return []
        
        return chapters
    
    async def _extract_from_heuristics(self, text_blocks: List[TextBlock]) -> List[ExtractedChapter]:
        """Extract chapters using heuristic methods."""
        # Find potential chapter headings
        candidates = self._find_heading_candidates(text_blocks)
        
        if not candidates:
            return []
        
        # Filter and rank candidates
        filtered_candidates = self._filter_candidates(candidates)
        
        if not filtered_candidates:
            return []
        
        # Convert candidates to chapters
        chapters = self._candidates_to_chapters(filtered_candidates, text_blocks)
        
        return chapters
    
    def _find_heading_candidates(self, text_blocks: List[TextBlock]) -> List[ChapterCandidate]:
        """Find potential chapter heading candidates."""
        candidates = []
        
        # Calculate average font size for comparison
        font_sizes = []
        for block in text_blocks:
            if block.font_info and 'size' in block.font_info:
                font_sizes.append(block.font_info['size'])
        
        if not font_sizes:
            return []
        
        avg_font_size = sum(font_sizes) / len(font_sizes)
        max_font_size = max(font_sizes)
        
        for i, block in enumerate(text_blocks):
            text = block.text.strip()
            if not text:
                continue
            
            # Check pattern matching
            pattern_confidence = self._check_patterns(text)
            
            # Check font size (larger fonts are more likely to be headings)
            font_confidence = 0.0
            if block.font_info and 'size' in block.font_info:
                font_size = block.font_info['size']
                if font_size > avg_font_size + self.min_font_size_diff:
                    font_confidence = min(1.0, (font_size - avg_font_size) / (max_font_size - avg_font_size))
            
            # Check position (headings are often at the beginning of pages)
            position_confidence = 0.0
            if block.bbox:
                # Higher confidence for text near the top of the page
                y_position = block.bbox['y']
                if y_position < 200:  # Assuming page height > 200
                    position_confidence = 0.3
            
            # Check text length (headings are usually shorter)
            length_confidence = 0.0
            if len(text) < 100:  # Short text more likely to be heading
                length_confidence = 0.2
            
            # Combine confidences with higher weight on patterns
            total_confidence = (
                pattern_confidence * 0.6 +
                font_confidence * 0.25 +
                position_confidence * 0.1 +
                length_confidence * 0.05
            )
            
            # Lower the threshold for testing and debugging
            effective_min_confidence = min(self.min_confidence, 0.4)
            
            if total_confidence >= effective_min_confidence:
                # Determine heading level
                level = self._determine_heading_level(text, block.font_info)
                
                candidate = ChapterCandidate(
                    title=text,
                    level=level,
                    page=block.page,
                    order_index=i,
                    bbox=block.bbox,
                    font_info=block.font_info,
                    confidence=total_confidence
                )
                candidates.append(candidate)
        
        return candidates
    
    def _check_patterns(self, text: str) -> float:
        """Check if text matches chapter heading patterns."""
        # Check chapter patterns (higher confidence)
        for pattern in self.chapter_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 0.9
        
        # Check section patterns (lower confidence)
        for pattern in self.section_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 0.7
        
        # Check for common chapter words
        chapter_words = ['chapter', 'section', 'introduction', 'conclusion', 'methods', 'results', 'discussion']
        text_lower = text.lower()
        for word in chapter_words:
            if word in text_lower and len(text.split()) <= 8:
                return 0.6
        
        # Exclude list items and sentences
        if (text.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) and 
            (':' in text or len(text) > 50)):
            return 0.0  # This looks like a list item, not a heading
        
        # Exclude sentences (text ending with periods and being long)
        if text.endswith('.') and len(text) > 50:
            return 0.0
        
        # Check if text looks like a heading (starts with capital, short)
        if (len(text) > 0 and text[0].isupper() and 
            len(text.split()) <= 10 and 
            not text.endswith('.') and
            not text.endswith(',') and
            not text.endswith(':') and
            len(text) < 100):
            return 0.4
        
        return 0.0
    
    def _determine_heading_level(self, text: str, font_info: Optional[Dict]) -> int:
        """Determine the hierarchical level of a heading."""
        # Check for Markdown headers first
        if text.startswith('#'):
            hash_count = len(text) - len(text.lstrip('#'))
            return min(hash_count, 6)  # Markdown supports up to 6 levels
        
        # Check for numbered sections
        if re.match(r'^\d+\.\d+\.\d+', text):
            return 3  # Sub-subsection
        elif re.match(r'^\d+\.\d+', text):
            return 2  # Subsection
        elif re.match(r'^\d+\.', text):
            return 1  # Main section
        
        # Check for chapter patterns
        for pattern in self.chapter_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return 1  # Main chapter
        
        # Use font size information if available
        if font_info and 'size' in font_info:
            font_size = font_info['size']
            # Larger fonts typically indicate higher-level headings
            if font_size >= 18:
                return 1
            elif font_size >= 14:
                return 2
            else:
                return 3
        
        # Default to level 1
        return 1
    
    def _filter_candidates(self, candidates: List[ChapterCandidate]) -> List[ChapterCandidate]:
        """Filter and rank chapter candidates."""
        if not candidates:
            return []
        
        # Sort by confidence (descending) and then by order
        candidates.sort(key=lambda x: (-x.confidence, x.order_index))
        
        # Remove candidates with low confidence
        min_confidence_threshold = 0.5
        high_confidence_candidates = [c for c in candidates if c.confidence >= min_confidence_threshold]
        
        # Remove candidates that are too close to each other
        filtered = []
        for candidate in high_confidence_candidates:
            # Check if this candidate is too similar to existing ones
            is_duplicate = False
            for existing in filtered:
                if (abs(existing.page - candidate.page) <= 1 and
                    self._text_similarity(existing.title, candidate.title) > 0.8):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(candidate)
        
        return filtered
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _candidates_to_chapters(self, candidates: List[ChapterCandidate], text_blocks: List[TextBlock]) -> List[ExtractedChapter]:
        """Convert candidates to chapters and assign content."""
        chapters = []
        
        # Sort candidates by page and order
        candidates.sort(key=lambda x: (x.page, x.order_index))
        
        for i, candidate in enumerate(candidates):
            # Determine page range
            page_start = candidate.page
            page_end = None
            
            # Find next chapter to determine end page
            for j in range(i + 1, len(candidates)):
                if candidates[j].level <= candidate.level:
                    page_end = candidates[j].page - 1
                    break
            
            # If no end found, use last page with content
            if page_end is None:
                last_page = max(block.page for block in text_blocks) if text_blocks else page_start
                page_end = last_page
            
            chapter = ExtractedChapter(
                title=candidate.title,
                level=candidate.level,
                order_index=i,
                page_start=page_start,
                page_end=page_end
            )
            chapters.append(chapter)
        
        # Assign content blocks to chapters
        chapters = self._assign_content_to_chapters(chapters, text_blocks)
        
        return chapters
    
    def _assign_content_to_chapters(self, chapters: List[ExtractedChapter], text_blocks: List[TextBlock]) -> List[ExtractedChapter]:
        """Assign text blocks to appropriate chapters."""
        if not chapters:
            return chapters
        
        # Sort chapters by page start for proper assignment
        chapters.sort(key=lambda x: (x.page_start, x.order_index))
        
        for block in text_blocks:
            # Skip blocks that are chapter titles themselves
            block_is_chapter_title = any(
                block.text.strip() == chapter.title.strip() 
                for chapter in chapters
            )
            if block_is_chapter_title:
                continue
            
            # Find the appropriate chapter for this block
            assigned = False
            
            for i, chapter in enumerate(chapters):
                # Check if block falls within this chapter's page range
                if chapter.page_start <= block.page <= (chapter.page_end or float('inf')):
                    # If there's a next chapter, make sure we don't go past its start
                    if i + 1 < len(chapters):
                        next_chapter = chapters[i + 1]
                        if block.page >= next_chapter.page_start:
                            continue  # This block belongs to the next chapter
                    
                    chapter.content_blocks.append(block)
                    assigned = True
                    break
            
            # If not assigned to any chapter, add to the last one
            if not assigned and chapters:
                chapters[-1].content_blocks.append(block)
        
        return chapters
    
    def _create_single_chapter(self, text_blocks: List[TextBlock]) -> List[ExtractedChapter]:
        """Create a single default chapter containing all content."""
        if not text_blocks:
            return []
        
        first_page = min(block.page for block in text_blocks)
        last_page = max(block.page for block in text_blocks)
        
        chapter = ExtractedChapter(
            title="Document Content",
            level=1,
            order_index=0,
            page_start=first_page,
            page_end=last_page,
            content_blocks=text_blocks.copy()
        )
        
        return [chapter]


class ChapterService:
    """Service for chapter operations and database integration."""
    
    def __init__(self):
        """Initialize chapter service."""
        self.extractor = ChapterExtractor()
    
    async def extract_chapters_from_content(
        self, 
        document_id: UUID, 
        parsed_content: ParsedContent
    ) -> List[Chapter]:
        """
        Extract chapters from parsed content and save to database.
        
        Args:
            document_id: UUID of the document
            parsed_content: Parsed document content
            
        Returns:
            List of saved Chapter model instances
        """
        try:
            # Use a dummy file path for extraction (we already have parsed content)
            dummy_path = Path("dummy.pdf")  # The extractor will use heuristics
            
            # Extract chapters using the extractor
            extracted_chapters = await self.extractor._extract_from_heuristics(parsed_content.text_blocks)
            
            # If no chapters found, create a single default chapter
            if not extracted_chapters:
                extracted_chapters = self.extractor._create_single_chapter(parsed_content.text_blocks)
            
            # Save chapters to database
            saved_chapters = []
            async with get_async_session() as session:
                for ext_chapter in extracted_chapters:
                    # Combine content blocks into a single text
                    content_text = "\n\n".join(block.text for block in ext_chapter.content_blocks)
                    
                    chapter = Chapter(
                        document_id=document_id,
                        title=ext_chapter.title,
                        level=ext_chapter.level,
                        order_index=ext_chapter.order_index,
                        page_start=ext_chapter.page_start,
                        page_end=ext_chapter.page_end,
                        content=content_text
                    )
                    
                    session.add(chapter)
                    saved_chapters.append(chapter)
                
                await session.commit()
                
                # Refresh all chapters to get their IDs
                for chapter in saved_chapters:
                    await session.refresh(chapter)
            
            return saved_chapters
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting chapters for document {document_id}: {e}")
            raise