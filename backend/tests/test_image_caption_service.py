"""
Tests for the image-caption pairing service.
"""

import pytest
from unittest.mock import Mock

from app.services.image_caption_service import (
    ImageCaptionService, 
    CaptionMatch, 
    ImageCaptionPair
)
from app.parsers.base import ImageData, TextBlock


class TestImageCaptionService:
    """Test cases for ImageCaptionService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ImageCaptionService()
        
        # Sample image data
        self.sample_image = ImageData(
            image_path="/tmp/test_image.png",
            page=1,
            bbox={"x": 100, "y": 200, "width": 300, "height": 200},
            format="PNG"
        )
        
        # Sample text blocks with various caption patterns
        self.text_blocks = [
            # Chinese figure caption
            TextBlock(
                text="图1：这是一个测试图片的说明文字",
                page=1,
                bbox={"x": 100, "y": 420, "width": 300, "height": 20}
            ),
            # English figure caption
            TextBlock(
                text="Figure 2: This is a test image caption",
                page=1,
                bbox={"x": 100, "y": 450, "width": 300, "height": 20}
            ),
            # Fig abbreviation
            TextBlock(
                text="Fig. 3 - Sample illustration showing the process",
                page=1,
                bbox={"x": 100, "y": 480, "width": 300, "height": 20}
            ),
            # Nearby descriptive text (potential fallback)
            TextBlock(
                text="This diagram shows the relationship between different components in the system.",
                page=1,
                bbox={"x": 100, "y": 510, "width": 300, "height": 20}
            ),
            # Distant text (should not be matched)
            TextBlock(
                text="This is some unrelated text far from the image.",
                page=1,
                bbox={"x": 100, "y": 800, "width": 300, "height": 20}
            ),
            # Different page text (should not be matched unless fallback)
            TextBlock(
                text="Figure on different page",
                page=2,
                bbox={"x": 100, "y": 200, "width": 300, "height": 20}
            )
        ]
    
    def test_pattern_matching_chinese(self):
        """Test Chinese caption pattern matching."""
        # Test with Chinese figure pattern
        chinese_block = TextBlock(
            text="图1：这是一个测试图片",
            page=1,
            bbox={"x": 100, "y": 420, "width": 300, "height": 20}
        )
        
        matches = self.service._find_pattern_captions(
            self.sample_image, [chinese_block]
        )
        
        assert len(matches) == 1
        assert matches[0].text == "这是一个测试图片"
        assert matches[0].pattern_type == "pattern_chinese_figure"
        assert matches[0].confidence > 0.6
    
    def test_pattern_matching_english(self):
        """Test English caption pattern matching."""
        # Test with English figure pattern
        english_block = TextBlock(
            text="Figure 1: This is a test caption",
            page=1,
            bbox={"x": 100, "y": 420, "width": 300, "height": 20}
        )
        
        matches = self.service._find_pattern_captions(
            self.sample_image, [english_block]
        )
        
        assert len(matches) == 1
        assert matches[0].text == "This is a test caption"
        assert matches[0].pattern_type == "pattern_english_figure"
        assert matches[0].confidence > 0.6
    
    def test_pattern_matching_fig_abbreviation(self):
        """Test Fig. abbreviation pattern matching."""
        fig_block = TextBlock(
            text="Fig. 2: Sample illustration",
            page=1,
            bbox={"x": 100, "y": 420, "width": 300, "height": 20}
        )
        
        matches = self.service._find_pattern_captions(
            self.sample_image, [fig_block]
        )
        
        assert len(matches) == 1
        assert matches[0].text == "Sample illustration"
        assert matches[0].pattern_type == "pattern_english_fig_abbrev"
    
    def test_proximity_based_matching(self):
        """Test proximity-based caption matching."""
        # Create a text block close to the image
        close_block = TextBlock(
            text="This is a descriptive text that could serve as a caption for the nearby image.",
            page=1,
            bbox={"x": 100, "y": 420, "width": 300, "height": 20}
        )
        
        matches = self.service._find_proximity_captions(
            self.sample_image, [close_block]
        )
        
        assert len(matches) >= 1
        assert matches[0].pattern_type == "proximity"
        assert 0.1 < matches[0].confidence < 0.8  # Lower than pattern matching
    
    def test_fallback_caption_selection(self):
        """Test fallback caption selection."""
        # Create multiple text blocks at different distances
        blocks = [
            TextBlock(
                text="Closest text to the image that could be a caption.",
                page=1,
                bbox={"x": 100, "y": 420, "width": 300, "height": 20}
            ),
            TextBlock(
                text="Second closest text block.",
                page=1,
                bbox={"x": 100, "y": 450, "width": 300, "height": 20}
            ),
            TextBlock(
                text="Third closest text block.",
                page=1,
                bbox={"x": 100, "y": 480, "width": 300, "height": 20}
            )
        ]
        
        matches = self.service._find_fallback_captions(self.sample_image, blocks)
        
        assert len(matches) >= 1
        # Should have fallback matches
        assert all(match.pattern_type == "fallback" for match in matches)
        if len(matches) > 1:
            # Closest should have highest confidence
            assert matches[0].confidence >= matches[1].confidence
    
    def test_distance_calculation(self):
        """Test distance calculation between bounding boxes."""
        bbox1 = {"x": 100, "y": 200, "width": 300, "height": 200}
        bbox2 = {"x": 100, "y": 420, "width": 300, "height": 20}  # Directly below
        
        distance = self.service._calculate_distance(bbox1, bbox2)
        
        # Should be relatively small since they're aligned vertically
        assert distance < 110
        
        # Test with text below image (should get distance reduction)
        bbox3 = {"x": 100, "y": 100, "width": 300, "height": 20}  # Above image
        distance_above = self.service._calculate_distance(bbox1, bbox3)
        distance_below = self.service._calculate_distance(bbox1, bbox2)
        
        # Text below should have effective shorter distance
        assert distance_below < distance_above
    
    def test_full_pairing_process(self):
        """Test the complete image-caption pairing process."""
        pairs = self.service.pair_images_with_captions(
            [self.sample_image], self.text_blocks
        )
        
        assert len(pairs) == 1
        pair = pairs[0]
        
        assert isinstance(pair, ImageCaptionPair)
        assert pair.image == self.sample_image
        assert pair.caption is not None
        assert pair.caption_confidence > 0.0
        assert pair.caption_source in ['pattern_chinese_figure', 'pattern_english_figure', 'pattern_english_fig_abbrev']
    
    def test_multiple_images_pairing(self):
        """Test pairing multiple images with captions."""
        # Create multiple images
        images = [
            ImageData(
                image_path="/tmp/image1.png",
                page=1,
                bbox={"x": 100, "y": 200, "width": 300, "height": 200},
                format="PNG"
            ),
            ImageData(
                image_path="/tmp/image2.png",
                page=1,
                bbox={"x": 100, "y": 500, "width": 300, "height": 200},
                format="PNG"
            )
        ]
        
        # Create corresponding captions
        text_blocks = [
            TextBlock(
                text="图1：第一个图片的说明",
                page=1,
                bbox={"x": 100, "y": 420, "width": 300, "height": 20}
            ),
            TextBlock(
                text="Figure 2: Caption for the second image",
                page=1,
                bbox={"x": 100, "y": 720, "width": 300, "height": 20}
            )
        ]
        
        pairs = self.service.pair_images_with_captions(images, text_blocks)
        
        assert len(pairs) == 2
        assert all(pair.caption is not None for pair in pairs)
        assert pairs[0].caption == "第一个图片的说明"
        assert pairs[1].caption == "Caption for the second image"
    
    def test_no_caption_found(self):
        """Test behavior when no suitable caption is found."""
        # Create an image with no nearby text
        isolated_image = ImageData(
            image_path="/tmp/isolated.png",
            page=1,
            bbox={"x": 1000, "y": 1000, "width": 300, "height": 200},
            format="PNG"
        )
        
        pairs = self.service.pair_images_with_captions(
            [isolated_image], self.text_blocks
        )
        
        assert len(pairs) == 1
        pair = pairs[0]
        assert pair.caption is None
        assert pair.caption_confidence == 0.0
        assert pair.caption_source == "none"
    
    def test_confidence_scoring(self):
        """Test confidence scoring for different caption types."""
        # Pattern match should have higher confidence than proximity
        pattern_block = TextBlock(
            text="Figure 1: Clear pattern match",
            page=1,
            bbox={"x": 100, "y": 420, "width": 300, "height": 20}
        )
        
        proximity_block = TextBlock(
            text="This is just nearby descriptive text without pattern.",
            page=1,
            bbox={"x": 100, "y": 420, "width": 300, "height": 20}
        )
        
        pattern_matches = self.service._find_pattern_captions(
            self.sample_image, [pattern_block]
        )
        proximity_matches = self.service._find_proximity_captions(
            self.sample_image, [proximity_block]
        )
        
        assert pattern_matches[0].confidence > proximity_matches[0].confidence
    
    def test_validation_metrics(self):
        """Test caption pairing validation metrics."""
        # Create pairs with different confidence levels
        pairs = [
            ImageCaptionPair(
                image=self.sample_image,
                caption="High confidence caption",
                caption_confidence=0.9,
                caption_source="pattern_english_figure",
                source_text_block=self.text_blocks[0]
            ),
            ImageCaptionPair(
                image=self.sample_image,
                caption="Low confidence caption",
                caption_confidence=0.4,
                caption_source="proximity",
                source_text_block=self.text_blocks[1]
            ),
            ImageCaptionPair(
                image=self.sample_image,
                caption=None,
                caption_confidence=0.0,
                caption_source="none",
                source_text_block=None
            )
        ]
        
        metrics = self.service.validate_caption_pairing(pairs)
        
        assert metrics['total_images'] == 3
        assert metrics['paired_images'] == 2
        assert metrics['high_confidence_pairs'] == 1
        assert metrics['coverage'] == 2/3
        assert metrics['accuracy'] == 1/3
        assert 0 < metrics['avg_confidence'] < 1
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Empty inputs
        pairs = self.service.pair_images_with_captions([], [])
        assert pairs == []
        
        # No text blocks
        pairs = self.service.pair_images_with_captions([self.sample_image], [])
        assert len(pairs) == 1
        assert pairs[0].caption is None
        
        # No images
        pairs = self.service.pair_images_with_captions([], self.text_blocks)
        assert pairs == []
        
        # Validation with empty pairs
        metrics = self.service.validate_caption_pairing([])
        assert metrics['accuracy'] == 0.0
        assert metrics['coverage'] == 0.0
    
    def test_different_page_handling(self):
        """Test handling of images and text on different pages."""
        # Image on page 1, caption on page 2
        different_page_image = ImageData(
            image_path="/tmp/page1.png",
            page=1,
            bbox={"x": 100, "y": 200, "width": 300, "height": 200},
            format="PNG"
        )
        
        different_page_text = TextBlock(
            text="Figure 1: Caption on different page",
            page=2,
            bbox={"x": 100, "y": 200, "width": 300, "height": 20}
        )
        
        pairs = self.service.pair_images_with_captions(
            [different_page_image], [different_page_text]
        )
        
        # Should still find caption as fallback
        assert len(pairs) == 1
        # But confidence should be lower due to different page
        if pairs[0].caption:
            assert pairs[0].caption_confidence < 0.9