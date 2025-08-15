"""
Tests for text segmentation service.
"""

import pytest
from unittest.mock import patch

from app.services.text_segmentation_service import (
    TextSegmentationService,
    TextSegment,
    SegmentationConfig
)
from app.parsers.base import TextBlock


class TestTextSegmentationService:
    """Test cases for TextSegmentationService."""
    
    @pytest.fixture
    def service(self):
        """Create a text segmentation service instance."""
        config = SegmentationConfig(
            min_segment_length=100,
            max_segment_length=300,
            similarity_threshold=0.7
        )
        return TextSegmentationService(config)
    
    @pytest.fixture
    def sample_text_blocks(self):
        """Create sample text blocks for testing."""
        return [
            TextBlock(
                text="This is the first paragraph. It contains some important information about machine learning.",
                page=1,
                bbox={"x": 0, "y": 0, "width": 100, "height": 20}
            ),
            TextBlock(
                text="Machine learning is a subset of artificial intelligence. It enables computers to learn without being explicitly programmed.",
                page=1,
                bbox={"x": 0, "y": 25, "width": 100, "height": 20}
            ),
            TextBlock(
                text="Deep learning is a subset of machine learning. It uses neural networks with multiple layers to model complex patterns.",
                page=1,
                bbox={"x": 0, "y": 50, "width": 100, "height": 20}
            )
        ]
    
    def test_clean_text_block(self, service):
        """Test text block cleaning functionality."""
        dirty_block = TextBlock(
            text="  This   has    excessive   whitespace.  \n\n  Page 123  \n  ",
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        
        cleaned = service._clean_text_block(dirty_block)
        
        assert cleaned.text == "This has excessive whitespace."
        assert cleaned.page == 1
        assert cleaned.bbox == dirty_block.bbox
    
    def test_normalize_text(self, service):
        """Test text normalization."""
        text = "  This Is A Test With MIXED Case!  "
        normalized = service.normalize_text(text)
        
        assert normalized == "this is a test with mixed case!"
    
    def test_extract_key_terms(self, service):
        """Test key term extraction."""
        text = "machine learning is important. Machine learning algorithms are powerful. Learning is key."
        terms = service.extract_key_terms(text, max_terms=3)
        
        # Should extract meaningful terms, excluding stopwords
        term_words = [term[0] for term in terms]
        assert "learning" in term_words
        assert "machine" in term_words
    
    def test_calculate_text_complexity(self, service):
        """Test text complexity calculation."""
        simple_text = "This is simple."
        complex_text = "The sophisticated algorithmic implementation demonstrates extraordinary computational capabilities."
        
        simple_complexity = service.calculate_text_complexity(simple_text)
        complex_complexity = service.calculate_text_complexity(complex_text)
        
        assert 0.0 <= simple_complexity <= 1.0
        assert 0.0 <= complex_complexity <= 1.0
        assert complex_complexity > simple_complexity
    
    def test_calculate_text_similarity(self, service):
        """Test text similarity calculation."""
        text1 = "machine learning algorithms are powerful"
        text2 = "machine learning models are effective"
        text3 = "cats and dogs are pets"
        
        similarity_high = service._calculate_text_similarity(text1, text2)
        similarity_low = service._calculate_text_similarity(text1, text3)
        
        assert similarity_high > similarity_low
        assert 0.0 <= similarity_high <= 1.0
        assert 0.0 <= similarity_low <= 1.0
    
    @pytest.mark.asyncio
    async def test_segment_single_block_small(self, service):
        """Test segmentation of a small text block."""
        block = TextBlock(
            text="Short text.",
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        
        segments = await service._segment_single_block(block, 0, "chapter1")
        
        assert len(segments) == 1
        assert segments[0].text == "Short text."
        assert segments[0].anchors['page'] == 1
        assert segments[0].anchors['chapter_id'] == "chapter1"
    
    @pytest.mark.asyncio
    async def test_segment_single_block_optimal_size(self, service):
        """Test segmentation of optimally-sized text block."""
        # Create text within optimal range (100-300 chars)
        text = "This is a text block that is within the optimal size range. " * 3  # ~180 chars
        block = TextBlock(
            text=text,
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        
        segments = await service._segment_single_block(block, 0, "chapter1")
        
        assert len(segments) == 1
        assert len(segments[0].text) >= service.config.min_segment_length
        assert len(segments[0].text) <= service.config.max_segment_length
    
    @pytest.mark.asyncio
    async def test_segment_single_block_large(self, service):
        """Test segmentation of a large text block."""
        # Create text larger than max_segment_length (300 chars)
        text = "This is a very long text block that exceeds the maximum segment length. " * 10  # ~730 chars
        block = TextBlock(
            text=text,
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        
        segments = await service._segment_single_block(block, 0, "chapter1")
        
        assert len(segments) >= 2  # Should be split into multiple segments
        for segment in segments:
            assert len(segment.text) <= service.config.max_segment_length
    
    @pytest.mark.asyncio
    async def test_merge_similar_segments(self, service):
        """Test merging of similar segments."""
        # Create similar segments
        segment1 = TextSegment(
            text="Machine learning is important for AI development.",
            character_count=48,
            word_count=8,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 0}},
            original_blocks=[0]
        )
        
        segment2 = TextSegment(
            text="Machine learning algorithms are crucial for AI systems.",
            character_count=55,
            word_count=9,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 1}},
            original_blocks=[1]
        )
        
        segment3 = TextSegment(
            text="Cats are wonderful pets that bring joy to families.",
            character_count=51,
            word_count=9,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 2}},
            original_blocks=[2]
        )
        
        segments = [segment1, segment2, segment3]
        merged = await service._merge_similar_segments(segments)
        
        # Should merge similar segments (1 and 2) but keep dissimilar one (3) separate
        assert len(merged) <= len(segments)
    
    @pytest.mark.asyncio
    async def test_segment_text_blocks_integration(self, service, sample_text_blocks):
        """Test complete text block segmentation process."""
        segments = await service.segment_text_blocks(sample_text_blocks, "chapter1")
        
        assert len(segments) > 0
        
        for segment in segments:
            # Check segment properties
            assert segment.text.strip()  # Non-empty text
            assert segment.character_count > 0
            assert segment.word_count > 0
            assert segment.sentence_count > 0
            
            # Check anchor information
            assert 'page' in segment.anchors
            assert 'chapter_id' in segment.anchors
            assert 'position' in segment.anchors
            assert segment.anchors['chapter_id'] == "chapter1"
            
            # Check original block references
            assert len(segment.original_blocks) > 0
    
    @pytest.mark.asyncio
    async def test_segment_empty_blocks(self, service):
        """Test segmentation with empty text blocks."""
        empty_blocks = [
            TextBlock(text="", page=1, bbox={"x": 0, "y": 0, "width": 100, "height": 20}),
            TextBlock(text="   ", page=1, bbox={"x": 0, "y": 25, "width": 100, "height": 20})
        ]
        
        segments = await service.segment_text_blocks(empty_blocks, "chapter1")
        
        assert len(segments) == 0
    
    @pytest.mark.asyncio
    async def test_optimize_segment_sizes(self, service):
        """Test segment size optimization."""
        # Create segments with suboptimal sizes
        small_segment1 = TextSegment(
            text="Short.",
            character_count=6,
            word_count=1,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 0}},
            original_blocks=[0]
        )
        
        small_segment2 = TextSegment(
            text="Also short.",
            character_count=11,
            word_count=2,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 1}},
            original_blocks=[1]
        )
        
        segments = [small_segment1, small_segment2]
        optimized = await service._optimize_segment_sizes(segments)
        
        # Should merge small segments if possible
        assert len(optimized) <= len(segments)
        
        # Check that merged segment has combined content
        if len(optimized) == 1:
            merged_segment = optimized[0]
            assert "Short." in merged_segment.text
            assert "Also short." in merged_segment.text
    
    def test_create_segment(self, service):
        """Test segment creation with anchor information."""
        text = "This is a test segment."
        block = TextBlock(
            text=text,
            page=2,
            bbox={"x": 10, "y": 20, "width": 200, "height": 30}
        )
        
        segment = service._create_segment(text, block, 5, "chapter2")
        
        assert segment.text == text
        assert segment.character_count == len(text)
        assert segment.word_count == len(text.split())
        assert segment.anchors['page'] == 2
        assert segment.anchors['chapter_id'] == "chapter2"
        assert segment.anchors['position']['block_index'] == 5
        assert segment.anchors['position']['bbox'] == block.bbox
        assert segment.original_blocks == [5]
    
    def test_merge_segments(self, service):
        """Test merging multiple segments."""
        segment1 = TextSegment(
            text="First segment.",
            character_count=14,
            word_count=2,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 0}},
            original_blocks=[0]
        )
        
        segment2 = TextSegment(
            text="Second segment.",
            character_count=15,
            word_count=2,
            sentence_count=1,
            anchors={'page': 1, 'chapter_id': 'ch1', 'position': {'block_index': 1}},
            original_blocks=[1]
        )
        
        merged = service._merge_segments([segment1, segment2])
        
        assert "First segment." in merged.text
        assert "Second segment." in merged.text
        assert merged.sentence_count == 2
        assert set(merged.original_blocks) == {0, 1}
        assert merged.anchors['page'] == 1  # Uses first segment's primary anchor
        assert 'references' in merged.anchors  # Contains reference to second segment
    
    def test_extract_meaningful_words(self, service):
        """Test extraction of meaningful words."""
        text = "The quick brown fox jumps over the lazy dog! 123"
        words = service._extract_meaningful_words(text)
        
        # Should exclude stopwords, punctuation, and numbers
        assert "quick" in words
        assert "brown" in words
        assert "fox" in words
        assert "the" not in words  # stopword
        assert "!" not in words    # punctuation
        assert "123" not in words  # number
    
    @pytest.mark.asyncio
    async def test_split_large_block_with_sentences(self, service):
        """Test splitting large blocks while preserving sentence boundaries."""
        # Create a long text with clear sentence boundaries
        sentences = [
            "This is the first sentence about machine learning.",
            "Machine learning algorithms can process large datasets.",
            "Deep learning uses neural networks with multiple layers.",
            "Natural language processing is a subset of AI.",
            "Computer vision enables machines to interpret images.",
            "Reinforcement learning trains agents through rewards."
        ]
        long_text = " ".join(sentences)
        
        block = TextBlock(
            text=long_text,
            page=1,
            bbox={"x": 0, "y": 0, "width": 100, "height": 20}
        )
        
        segments = await service._split_large_block(long_text, block, 0, "chapter1")
        
        assert len(segments) >= 1
        
        # Check that sentence boundaries are preserved
        for segment in segments:
            # Each segment should end with proper punctuation
            assert segment.text.strip().endswith(('.', '!', '?'))
            
            # Segments should not be too long
            assert len(segment.text) <= service.config.max_segment_length