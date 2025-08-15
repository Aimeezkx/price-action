"""
Image and caption pairing service for document processing.

This service implements the logic to associate images with their captions
using pattern matching and proximity-based algorithms.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..parsers.base import ImageData, TextBlock


@dataclass
class CaptionMatch:
    """Represents a matched caption with confidence score."""
    text: str
    confidence: float
    pattern_type: str
    text_block: TextBlock
    distance: float


@dataclass
class ImageCaptionPair:
    """Represents a paired image and caption."""
    image: ImageData
    caption: Optional[str]
    caption_confidence: float
    caption_source: str  # 'pattern', 'proximity', 'fallback'
    source_text_block: Optional[TextBlock]


class ImageCaptionService:
    """Service for pairing images with their captions."""
    
    def __init__(self):
        """Initialize the image-caption pairing service."""
        # Caption patterns for different languages and formats
        # Order matters - more specific patterns first
        self.caption_patterns = [
            # Chinese patterns - more specific first
            (r'插图\s*(\d+)[\.、:：]\s*(.+)', 'chinese_illustration'),
            (r'图片\s*(\d+)[\.、:：]\s*(.+)', 'chinese_image'),
            (r'图\s*(\d+)[\.、:：]\s*(.+)', 'chinese_figure'),
            
            # English patterns
            (r'Figure\s+(\d+)[\.:]?\s*(.+)', 'english_figure'),
            (r'Fig\.\s*(\d+)[\.\-:\s]+(.+)', 'english_fig_abbrev'),
            (r'Fig\s+(\d+)[\.:]?\s*(.+)', 'english_fig'),
            (r'Image\s+(\d+)[\.:]?\s*(.+)', 'english_image'),
            (r'Illustration\s+(\d+)[\.:]?\s*(.+)', 'english_illustration'),
        ]
        
        # Proximity thresholds (in points/pixels)
        self.max_caption_distance = 150  # Maximum distance to consider
        self.preferred_caption_distance = 80  # Preferred distance for high confidence
        
        # Minimum text length for fallback captions
        self.min_fallback_length = 20
        self.max_fallback_length = 300
    
    def pair_images_with_captions(
        self, 
        images: List[ImageData], 
        text_blocks: List[TextBlock]
    ) -> List[ImageCaptionPair]:
        """
        Pair images with their captions using pattern matching and proximity.
        
        Args:
            images: List of extracted images
            text_blocks: List of extracted text blocks
            
        Returns:
            List of image-caption pairs
        """
        pairs = []
        
        for image in images:
            caption_match = self._find_best_caption(image, text_blocks)
            
            if caption_match:
                pair = ImageCaptionPair(
                    image=image,
                    caption=caption_match.text,
                    caption_confidence=caption_match.confidence,
                    caption_source=caption_match.pattern_type,
                    source_text_block=caption_match.text_block
                )
            else:
                # No caption found
                pair = ImageCaptionPair(
                    image=image,
                    caption=None,
                    caption_confidence=0.0,
                    caption_source='none',
                    source_text_block=None
                )
            
            pairs.append(pair)
        
        return pairs
    
    def _find_best_caption(
        self, 
        image: ImageData, 
        text_blocks: List[TextBlock]
    ) -> Optional[CaptionMatch]:
        """
        Find the best caption for an image using multiple strategies.
        
        Args:
            image: The image to find a caption for
            text_blocks: Available text blocks to search
            
        Returns:
            Best caption match or None if no suitable caption found
        """
        # Filter text blocks to same page as image
        same_page_blocks = [
            block for block in text_blocks 
            if block.page == image.page
        ]
        
        if not same_page_blocks:
            # Fallback to all text blocks if no same-page blocks
            same_page_blocks = text_blocks
        
        # Strategy 1: Pattern-based caption detection
        pattern_matches = self._find_pattern_captions(image, same_page_blocks)
        
        # Strategy 2: Proximity-based caption detection
        proximity_matches = self._find_proximity_captions(image, same_page_blocks)
        
        # Strategy 3: Fallback paragraph selection
        fallback_matches = self._find_fallback_captions(image, same_page_blocks)
        
        # Combine and rank all matches
        all_matches = pattern_matches + proximity_matches + fallback_matches
        
        if not all_matches:
            return None
        
        # Sort by confidence score (descending)
        all_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return all_matches[0]
    
    def _find_pattern_captions(
        self, 
        image: ImageData, 
        text_blocks: List[TextBlock]
    ) -> List[CaptionMatch]:
        """Find captions using pattern matching."""
        matches = []
        
        for block in text_blocks:
            # Only use the first matching pattern to avoid duplicates
            for pattern, pattern_type in self.caption_patterns:
                match = re.search(pattern, block.text, re.IGNORECASE)
                if match:
                    # Extract caption text
                    if len(match.groups()) >= 2:
                        caption_text = match.group(2).strip()
                    else:
                        caption_text = match.group(0).strip()
                    
                    # Calculate distance between image and text block
                    distance = self._calculate_distance(image.bbox, block.bbox)
                    
                    # Only consider if within reasonable distance
                    if distance <= self.max_caption_distance:
                        # Calculate confidence based on pattern type and distance
                        confidence = self._calculate_pattern_confidence(
                            pattern_type, distance, caption_text
                        )
                        
                        matches.append(CaptionMatch(
                            text=caption_text,
                            confidence=confidence,
                            pattern_type=f'pattern_{pattern_type}',
                            text_block=block,
                            distance=distance
                        ))
                    
                    # Break after first match to avoid duplicates
                    break
        
        return matches
    
    def _find_proximity_captions(
        self, 
        image: ImageData, 
        text_blocks: List[TextBlock]
    ) -> List[CaptionMatch]:
        """Find captions based on proximity to image."""
        matches = []
        
        for block in text_blocks:
            distance = self._calculate_distance(image.bbox, block.bbox)
            
            # Only consider blocks within reasonable distance
            if distance <= self.max_caption_distance:
                # Skip very short or very long text
                text_length = len(block.text.strip())
                if text_length < 30 or text_length > self.max_fallback_length:
                    continue
                
                # Calculate confidence based on distance and text characteristics
                confidence = self._calculate_proximity_confidence(distance, block.text)
                
                matches.append(CaptionMatch(
                    text=block.text.strip(),
                    confidence=confidence,
                    pattern_type='proximity',
                    text_block=block,
                    distance=distance
                ))
        
        return matches
    
    def _find_fallback_captions(
        self, 
        image: ImageData, 
        text_blocks: List[TextBlock]
    ) -> List[CaptionMatch]:
        """Find fallback captions from nearby paragraphs."""
        matches = []
        
        # Find the closest text block that could serve as a caption
        closest_blocks = sorted(
            text_blocks,
            key=lambda block: self._calculate_distance(image.bbox, block.bbox)
        )
        
        for i, block in enumerate(closest_blocks[:3]):  # Consider top 3 closest
            distance = self._calculate_distance(image.bbox, block.bbox)
            
            # Skip if too far
            if distance > self.max_caption_distance:
                continue
            
            text = block.text.strip()
            text_length = len(text)
            
            # Skip very short or very long text
            if text_length < self.min_fallback_length or text_length > self.max_fallback_length:
                continue
            
            # Lower confidence for fallback captions
            base_confidence = 0.3 - (i * 0.1)  # Decrease confidence for further blocks
            distance_penalty = min(distance / self.max_caption_distance, 1.0) * 0.2
            confidence = max(base_confidence - distance_penalty, 0.1)
            
            matches.append(CaptionMatch(
                text=text,
                confidence=confidence,
                pattern_type='fallback',
                text_block=block,
                distance=distance
            ))
        
        return matches
    
    def _calculate_distance(self, bbox1: Dict[str, float], bbox2: Dict[str, float]) -> float:
        """
        Calculate distance between two bounding boxes.
        
        Uses center-to-center distance with consideration for vertical proximity
        (captions are often directly below images).
        """
        # Calculate centers
        center1_x = bbox1['x'] + bbox1['width'] / 2
        center1_y = bbox1['y'] + bbox1['height'] / 2
        center2_x = bbox2['x'] + bbox2['width'] / 2
        center2_y = bbox2['y'] + bbox2['height'] / 2
        
        # Calculate Euclidean distance
        dx = center1_x - center2_x
        dy = center1_y - center2_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        # Give preference to text blocks below the image (typical caption position)
        if center2_y > center1_y:  # Text is below image
            distance *= 0.8  # Reduce distance penalty
        
        return distance
    
    def _calculate_pattern_confidence(
        self, 
        pattern_type: str, 
        distance: float, 
        caption_text: str
    ) -> float:
        """Calculate confidence score for pattern-matched captions."""
        # Base confidence by pattern type
        pattern_confidence = {
            'chinese_figure': 0.95,
            'chinese_image': 0.90,
            'chinese_illustration': 0.85,
            'english_figure': 0.95,
            'english_fig_abbrev': 0.90,
            'english_fig': 0.90,
            'english_image': 0.85,
            'english_illustration': 0.85,
            'numbered_caption': 0.70,
        }.get(pattern_type, 0.60)
        
        # Distance penalty
        if distance <= self.preferred_caption_distance:
            distance_factor = 1.0
        else:
            distance_factor = max(0.7, 1.0 - (distance - self.preferred_caption_distance) / self.max_caption_distance)
        
        # Text length bonus (reasonable caption length)
        text_length = len(caption_text)
        if 20 <= text_length <= 100:
            length_factor = 1.0
        elif text_length < 20:
            length_factor = 0.8
        else:
            length_factor = 0.9
        
        return pattern_confidence * distance_factor * length_factor
    
    def _calculate_proximity_confidence(self, distance: float, text: str) -> float:
        """Calculate confidence score for proximity-based captions."""
        # Base confidence for proximity matching
        base_confidence = 0.6
        
        # Distance factor
        if distance <= self.preferred_caption_distance:
            distance_factor = 1.0
        else:
            distance_factor = max(0.3, 1.0 - distance / self.max_caption_distance)
        
        # Text characteristics
        text_length = len(text)
        if 30 <= text_length <= 150:
            length_factor = 1.0
        elif text_length < 30:
            length_factor = 0.7
        else:
            length_factor = 0.8
        
        # Check for descriptive words that suggest it's a caption
        descriptive_words = [
            'shows', 'displays', 'illustrates', 'depicts', 'represents',
            '显示', '展示', '说明', '描述', '表示'
        ]
        
        descriptive_factor = 1.0
        for word in descriptive_words:
            if word.lower() in text.lower():
                descriptive_factor = 1.2
                break
        
        return min(base_confidence * distance_factor * length_factor * descriptive_factor, 0.8)
    
    def validate_caption_pairing(
        self, 
        pairs: List[ImageCaptionPair], 
        min_accuracy_threshold: float = 0.9
    ) -> Dict[str, float]:
        """
        Validate the accuracy of caption pairing.
        
        Args:
            pairs: List of image-caption pairs
            min_accuracy_threshold: Minimum required accuracy
            
        Returns:
            Dictionary with validation metrics
        """
        total_images = len(pairs)
        if total_images == 0:
            return {'accuracy': 0.0, 'coverage': 0.0, 'avg_confidence': 0.0}
        
        # Count successful pairings
        paired_images = sum(1 for pair in pairs if pair.caption is not None)
        high_confidence_pairs = sum(
            1 for pair in pairs 
            if pair.caption is not None and pair.caption_confidence >= 0.7
        )
        
        # Calculate metrics
        coverage = paired_images / total_images
        accuracy = high_confidence_pairs / total_images if total_images > 0 else 0.0
        avg_confidence = sum(pair.caption_confidence for pair in pairs) / total_images
        
        return {
            'accuracy': accuracy,
            'coverage': coverage,
            'avg_confidence': avg_confidence,
            'total_images': total_images,
            'paired_images': paired_images,
            'high_confidence_pairs': high_confidence_pairs,
        }