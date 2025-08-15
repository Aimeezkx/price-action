"""
Figure service for managing image extraction and caption pairing.

This service coordinates the extraction of images from documents and
their pairing with captions, then stores the results in the database.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

from ..models.document import Figure, Chapter
from ..parsers.base import ImageData, TextBlock
from .image_caption_service import ImageCaptionService, ImageCaptionPair


class FigureService:
    """Service for managing figures (images with captions)."""
    
    def __init__(self, db: Session):
        """Initialize the figure service."""
        self.db = db
        self.image_caption_service = ImageCaptionService()
    
    async def process_figures_for_chapter(
        self,
        chapter: Chapter,
        images: List[ImageData],
        text_blocks: List[TextBlock]
    ) -> List[Figure]:
        """
        Process images and pair them with captions for a chapter.
        
        Args:
            chapter: The chapter to process figures for
            images: List of extracted images
            text_blocks: List of text blocks for caption matching
            
        Returns:
            List of created Figure objects
        """
        # Filter images and text blocks for this chapter's page range
        chapter_images = self._filter_images_for_chapter(images, chapter)
        chapter_text_blocks = self._filter_text_blocks_for_chapter(text_blocks, chapter)
        
        if not chapter_images:
            return []
        
        # Pair images with captions
        image_caption_pairs = self.image_caption_service.pair_images_with_captions(
            chapter_images, chapter_text_blocks
        )
        
        # Create Figure objects and save to database
        figures = []
        for pair in image_caption_pairs:
            figure = self._create_figure_from_pair(chapter, pair)
            figures.append(figure)
        
        # Validate pairing quality
        validation_metrics = self.image_caption_service.validate_caption_pairing(
            image_caption_pairs
        )
        
        # Log validation results (could be stored in chapter metadata)
        chapter.content = chapter.content or ""
        if hasattr(chapter, 'metadata'):
            chapter.metadata = chapter.metadata or {}
            chapter.metadata['figure_pairing_metrics'] = validation_metrics
        
        return figures
    
    def _filter_images_for_chapter(
        self, 
        images: List[ImageData], 
        chapter: Chapter
    ) -> List[ImageData]:
        """Filter images that belong to this chapter."""
        if not chapter.page_start or not chapter.page_end:
            # If no page range specified, include all images
            return images
        
        return [
            img for img in images
            if chapter.page_start <= img.page <= chapter.page_end
        ]
    
    def _filter_text_blocks_for_chapter(
        self, 
        text_blocks: List[TextBlock], 
        chapter: Chapter
    ) -> List[TextBlock]:
        """Filter text blocks that belong to this chapter."""
        if not chapter.page_start or not chapter.page_end:
            # If no page range specified, include all text blocks
            return text_blocks
        
        return [
            block for block in text_blocks
            if chapter.page_start <= block.page <= chapter.page_end
        ]
    
    def _create_figure_from_pair(
        self, 
        chapter: Chapter, 
        pair: ImageCaptionPair
    ) -> Figure:
        """Create a Figure object from an image-caption pair."""
        figure = Figure(
            chapter_id=chapter.id,
            image_path=pair.image.image_path,
            caption=pair.caption,
            page_number=pair.image.page,
            bbox=pair.image.bbox,
            image_format=pair.image.format
        )
        
        # Add the figure to the database session
        self.db.add(figure)
        
        return figure
    
    async def get_figures_for_chapter(self, chapter_id: str) -> List[Figure]:
        """Get all figures for a specific chapter."""
        return self.db.query(Figure).filter(
            Figure.chapter_id == chapter_id
        ).order_by(Figure.page_number).all()
    
    async def get_figure_by_id(self, figure_id: str) -> Optional[Figure]:
        """Get a specific figure by ID."""
        return self.db.query(Figure).filter(Figure.id == figure_id).first()
    
    async def update_figure_caption(
        self, 
        figure_id: str, 
        new_caption: str
    ) -> Optional[Figure]:
        """Update the caption of a figure."""
        figure = await self.get_figure_by_id(figure_id)
        if figure:
            figure.caption = new_caption
            self.db.commit()
        return figure
    
    async def delete_figure(self, figure_id: str) -> bool:
        """Delete a figure."""
        figure = await self.get_figure_by_id(figure_id)
        if figure:
            self.db.delete(figure)
            self.db.commit()
            return True
        return False
    
    def get_pairing_statistics(self, chapter: Chapter) -> Dict[str, Any]:
        """Get statistics about figure-caption pairing for a chapter."""
        figures = self.db.query(Figure).filter(
            Figure.chapter_id == chapter.id
        ).all()
        
        total_figures = len(figures)
        figures_with_captions = sum(1 for fig in figures if fig.caption)
        
        return {
            'total_figures': total_figures,
            'figures_with_captions': figures_with_captions,
            'caption_coverage': figures_with_captions / total_figures if total_figures > 0 else 0.0,
            'figures': [
                {
                    'id': str(fig.id),
                    'page_number': fig.page_number,
                    'has_caption': bool(fig.caption),
                    'caption_length': len(fig.caption) if fig.caption else 0,
                }
                for fig in figures
            ]
        }
    
    async def reprocess_figure_captions(
        self,
        chapter: Chapter,
        text_blocks: List[TextBlock]
    ) -> List[Figure]:
        """
        Reprocess caption pairing for existing figures in a chapter.
        
        This can be useful if the caption pairing algorithm is improved
        or if new text blocks are available.
        """
        # Get existing figures
        figures = await self.get_figures_for_chapter(str(chapter.id))
        
        if not figures:
            return []
        
        # Convert figures back to ImageData for reprocessing
        images = []
        for figure in figures:
            image_data = ImageData(
                image_path=figure.image_path,
                page=figure.page_number,
                bbox=figure.bbox,
                format=figure.image_format or 'PNG'
            )
            images.append(image_data)
        
        # Filter text blocks for this chapter
        chapter_text_blocks = self._filter_text_blocks_for_chapter(text_blocks, chapter)
        
        # Re-pair images with captions
        image_caption_pairs = self.image_caption_service.pair_images_with_captions(
            images, chapter_text_blocks
        )
        
        # Update existing figures with new captions
        for i, pair in enumerate(image_caption_pairs):
            if i < len(figures):
                figures[i].caption = pair.caption
        
        self.db.commit()
        return figures