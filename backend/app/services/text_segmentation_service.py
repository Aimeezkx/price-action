"""
Text segmentation and preprocessing service for knowledge extraction.
"""

import re
import string
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from collections import Counter

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

from ..parsers.base import TextBlock


@dataclass
class TextSegment:
    """Represents a segmented text block with metadata."""
    
    text: str
    character_count: int
    word_count: int
    sentence_count: int
    anchors: Dict[str, any]  # {page, chapter, position, bbox}
    original_blocks: List[int]  # Indices of original text blocks
    similarity_score: float = 0.0
    
    def __post_init__(self):
        """Calculate derived metrics."""
        if self.character_count == 0:
            self.character_count = len(self.text)
        if self.word_count == 0:
            self.word_count = len(self.text.split())
        if self.sentence_count == 0:
            self.sentence_count = len(sent_tokenize(self.text))


@dataclass
class SegmentationConfig:
    """Configuration for text segmentation."""
    
    min_segment_length: int = 300
    max_segment_length: int = 600
    overlap_threshold: float = 0.1  # 10% overlap allowed
    similarity_threshold: float = 0.7  # For merging similar segments
    preserve_sentence_boundaries: bool = True
    min_sentence_length: int = 10
    max_sentences_per_segment: int = 10


class TextSegmentationService:
    """Service for segmenting and preprocessing text content."""
    
    def __init__(self, config: Optional[SegmentationConfig] = None):
        """Initialize the text segmentation service."""
        self.config = config or SegmentationConfig()
        self._ensure_nltk_data()
        
        # Initialize stopwords for text cleaning
        try:
            self.stopwords = set(stopwords.words('english'))
        except LookupError:
            self.stopwords = set()
    
    def _ensure_nltk_data(self):
        """Ensure required NLTK data is downloaded."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
    async def segment_text_blocks(
        self, 
        text_blocks: List[TextBlock], 
        chapter_id: Optional[str] = None
    ) -> List[TextSegment]:
        """
        Segment text blocks into knowledge point candidates.
        
        Args:
            text_blocks: List of text blocks to segment
            chapter_id: Optional chapter ID for anchor information
            
        Returns:
            List of text segments ready for knowledge extraction
        """
        if not text_blocks:
            return []
        
        # Step 1: Clean and normalize text blocks
        cleaned_blocks = [self._clean_text_block(block) for block in text_blocks]
        
        # Step 2: Create initial segments
        initial_segments = []
        for i, block in enumerate(cleaned_blocks):
            if not block.text.strip():
                continue
                
            block_segments = await self._segment_single_block(block, i, chapter_id)
            initial_segments.extend(block_segments)
        
        # Step 3: Merge similar segments
        merged_segments = await self._merge_similar_segments(initial_segments)
        
        # Step 4: Ensure optimal segment sizes
        final_segments = await self._optimize_segment_sizes(merged_segments)
        
        return final_segments
    
    def _clean_text_block(self, block: TextBlock) -> TextBlock:
        """Clean and normalize a text block."""
        text = block.text
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*Page\s+\d+\s*', '', text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        
        # Normalize quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"[''']", "'", text)
        
        # Remove control characters but preserve line breaks
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Create new block with cleaned text
        return TextBlock(
            text=text,
            page=block.page,
            bbox=block.bbox,
            font_info=block.font_info
        )
    
    async def _segment_single_block(
        self, 
        block: TextBlock, 
        block_index: int, 
        chapter_id: Optional[str]
    ) -> List[TextSegment]:
        """Segment a single text block into smaller segments."""
        text = block.text.strip()
        if not text:
            return []
        
        # If the block is already within size limits, return as single segment
        if (self.config.min_segment_length <= len(text) <= self.config.max_segment_length):
            return [self._create_segment(text, block, block_index, chapter_id)]
        
        # If block is too small, return as is (will be merged later)
        if len(text) < self.config.min_segment_length:
            return [self._create_segment(text, block, block_index, chapter_id)]
        
        # Block is too large, need to split
        return await self._split_large_block(text, block, block_index, chapter_id)
    
    async def _split_large_block(
        self, 
        text: str, 
        block: TextBlock, 
        block_index: int, 
        chapter_id: Optional[str]
    ) -> List[TextSegment]:
        """Split a large text block into smaller segments."""
        segments = []
        
        if self.config.preserve_sentence_boundaries:
            # Split by sentences and group them
            sentences = sent_tokenize(text)
            current_segment = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < self.config.min_sentence_length:
                    continue
                
                # Check if adding this sentence would exceed max length
                potential_segment = current_segment + " " + sentence if current_segment else sentence
                
                if len(potential_segment) <= self.config.max_segment_length:
                    current_segment = potential_segment
                else:
                    # Save current segment if it meets minimum length
                    if len(current_segment) >= self.config.min_segment_length:
                        segments.append(self._create_segment(current_segment, block, block_index, chapter_id))
                    
                    # Start new segment with current sentence
                    current_segment = sentence
            
            # Add remaining segment
            if len(current_segment) >= self.config.min_segment_length:
                segments.append(self._create_segment(current_segment, block, block_index, chapter_id))
        
        else:
            # Simple character-based splitting
            start = 0
            while start < len(text):
                end = min(start + self.config.max_segment_length, len(text))
                
                # Try to break at word boundary
                if end < len(text):
                    # Look for space within last 50 characters
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start + self.config.min_segment_length:
                        end = space_pos
                
                segment_text = text[start:end].strip()
                if len(segment_text) >= self.config.min_segment_length:
                    segments.append(self._create_segment(segment_text, block, block_index, chapter_id))
                
                start = end
        
        return segments
    
    def _create_segment(
        self, 
        text: str, 
        block: TextBlock, 
        block_index: int, 
        chapter_id: Optional[str]
    ) -> TextSegment:
        """Create a text segment with anchor information."""
        anchors = {
            'page': block.page,
            'chapter_id': chapter_id,
            'position': {
                'block_index': block_index,
                'bbox': block.bbox
            }
        }
        
        return TextSegment(
            text=text,
            character_count=len(text),
            word_count=len(text.split()),
            sentence_count=len(sent_tokenize(text)),
            anchors=anchors,
            original_blocks=[block_index]
        )
    
    async def _merge_similar_segments(self, segments: List[TextSegment]) -> List[TextSegment]:
        """Merge segments that are similar in content."""
        if len(segments) <= 1:
            return segments
        
        merged = []
        used_indices = set()
        
        for i, segment in enumerate(segments):
            if i in used_indices:
                continue
            
            # Find similar segments to merge with
            similar_segments = [segment]
            similar_indices = {i}
            
            for j, other_segment in enumerate(segments[i+1:], i+1):
                if j in used_indices:
                    continue
                
                similarity = self._calculate_text_similarity(segment.text, other_segment.text)
                
                if similarity >= self.config.similarity_threshold:
                    # Check if merging would create a segment within size limits
                    combined_length = sum(len(s.text) for s in similar_segments) + len(other_segment.text)
                    
                    if combined_length <= self.config.max_segment_length:
                        similar_segments.append(other_segment)
                        similar_indices.add(j)
            
            # Merge similar segments
            if len(similar_segments) > 1:
                merged_segment = self._merge_segments(similar_segments)
                merged.append(merged_segment)
            else:
                merged.append(segment)
            
            used_indices.update(similar_indices)
        
        return merged
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text segments."""
        # Simple word-based similarity
        words1 = set(self._extract_meaningful_words(text1))
        words2 = set(self._extract_meaningful_words(text2))
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """Extract meaningful words from text (excluding stopwords and punctuation)."""
        words = word_tokenize(text.lower())
        meaningful_words = []
        
        for word in words:
            # Skip punctuation, numbers, and stopwords
            if (word not in string.punctuation and 
                not word.isdigit() and 
                word not in self.stopwords and 
                len(word) > 2):
                meaningful_words.append(word)
        
        return meaningful_words
    
    def _merge_segments(self, segments: List[TextSegment]) -> TextSegment:
        """Merge multiple segments into one."""
        if len(segments) == 1:
            return segments[0]
        
        # Combine text with proper spacing
        combined_text = " ".join(segment.text.strip() for segment in segments)
        
        # Combine anchors (use first segment's primary anchor, add others as references)
        primary_anchors = segments[0].anchors.copy()
        
        # Add reference anchors from other segments
        reference_anchors = []
        for segment in segments[1:]:
            reference_anchors.append(segment.anchors)
        
        if reference_anchors:
            primary_anchors['references'] = reference_anchors
        
        # Combine original block indices
        original_blocks = []
        for segment in segments:
            original_blocks.extend(segment.original_blocks)
        
        return TextSegment(
            text=combined_text,
            character_count=len(combined_text),
            word_count=len(combined_text.split()),
            sentence_count=sum(segment.sentence_count for segment in segments),
            anchors=primary_anchors,
            original_blocks=list(set(original_blocks)),  # Remove duplicates
            similarity_score=1.0  # Merged segments are considered highly similar
        )
    
    async def _optimize_segment_sizes(self, segments: List[TextSegment]) -> List[TextSegment]:
        """Optimize segment sizes to meet length requirements."""
        optimized = []
        
        i = 0
        while i < len(segments):
            segment = segments[i]
            
            # If segment is too small, try to merge with next segment
            if (len(segment.text) < self.config.min_segment_length and 
                i + 1 < len(segments)):
                
                next_segment = segments[i + 1]
                combined_length = len(segment.text) + len(next_segment.text)
                
                if combined_length <= self.config.max_segment_length:
                    # Merge with next segment
                    merged = self._merge_segments([segment, next_segment])
                    optimized.append(merged)
                    i += 2  # Skip next segment as it's been merged
                    continue
            
            # If segment is still too small and can't be merged, keep it anyway
            # (better to have small segments than lose content)
            optimized.append(segment)
            i += 1
        
        return optimized
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent processing."""
        # Convert to lowercase for normalization
        normalized = text.lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove special characters but keep basic punctuation
        normalized = re.sub(r'[^\w\s.,!?;:()\-"]', '', normalized)
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def extract_key_terms(self, text: str, max_terms: int = 10) -> List[Tuple[str, int]]:
        """Extract key terms from text based on frequency."""
        words = self._extract_meaningful_words(text)
        
        if not words:
            return []
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Return most common terms
        return word_counts.most_common(max_terms)
    
    def calculate_text_complexity(self, text: str) -> float:
        """Calculate text complexity score (0.0 to 1.0)."""
        if not text.strip():
            return 0.0
        
        # Factors for complexity calculation
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        if not sentences or not words:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        sentence_complexity = min(1.0, avg_sentence_length / 20.0)  # Normalize to 20 words
        
        # Vocabulary complexity (unique words ratio)
        unique_words = set(word.lower() for word in words if word.isalpha())
        vocab_complexity = len(unique_words) / len(words) if words else 0.0
        
        # Punctuation complexity
        punctuation_count = sum(1 for char in text if char in string.punctuation)
        punct_complexity = min(1.0, punctuation_count / len(text))
        
        # Combined complexity score
        complexity = (
            sentence_complexity * 0.5 +
            vocab_complexity * 0.3 +
            punct_complexity * 0.2
        )
        
        return min(1.0, complexity) 
   
    async def segment_text(
        self, 
        text: str, 
        chapter_id: Optional[str] = None,
        page: int = 1
    ) -> List[TextSegment]:
        """
        Convenience method to segment plain text content.
        
        Args:
            text: Plain text content to segment
            chapter_id: Optional chapter ID for anchor information
            page: Page number for the text (default: 1)
            
        Returns:
            List of text segments
        """
        if not text or not text.strip():
            return []
        
        # Create a TextBlock from the plain text
        # Use a default bbox that covers the whole page
        text_block = TextBlock(
            text=text.strip(),
            page=page,
            bbox={"x": 0, "y": 0, "width": 100, "height": 100}
        )
        
        # Use the existing segment_text_blocks method
        return await self.segment_text_blocks([text_block], chapter_id)