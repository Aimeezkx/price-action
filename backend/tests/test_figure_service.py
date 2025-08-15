"""
Tests for the figure service.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.figure_service import FigureService
from app.models.document import Figure, Chapter
from app.parsers.base import ImageData, TextBlock


class TestFigureService:
    """Test cases for FigureService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.service = FigureService(self.mock_db)
        
        # Sample chapter
        self.sample_chapter = Chapter(
            id="chapter-1",
            title="Test Chapter",
            level=1,
            order_index=1,
            page_start=1,
            page_end=3,
            content="Test chapter content"
        )
        
        # Sample images
        self.sample_images = [
            ImageData(
                image_path="/tmp/image1.png",
                page=1,
                bbox={"x": 100, "y": 200, "width": 300, "height": 200},
                format="PNG"
            ),
            ImageData(
                image_path="/tmp/image2.png",
                page=2,
                bbox={"x": 100, "y": 300, "width": 250, "height": 150},
                format="JPEG"
            ),
            ImageData(
                image_path="/tmp/image3.png",
                page=4,  # Outside chapter range
                bbox={"x": 100, "y": 400, "width": 200, "height": 100},
                format="PNG"
            )
        ]
        
        # Sample text blocks
        self.sample_text_blocks = [
            TextBlock(
                text="Figure 1: First image caption",
                page=1,
                bbox={"x": 100, "y": 420, "width": 300, "height": 20}
            ),
            TextBlock(
                text="图2：第二个图片说明",
                page=2,
                bbox={"x": 100, "y": 470, "width": 250, "height": 20}
            ),
            TextBlock(
                text="Some regular text content",
                page=1,
                bbox={"x": 100, "y": 500, "width": 300, "height": 20}
            ),
            TextBlock(
                text="Figure 3: Outside chapter range",
                page=4,
                bbox={"x": 100, "y": 520, "width": 200, "height": 20}
            )
        ]
    
    def test_filter_images_for_chapter(self):
        """Test filtering images by chapter page range."""
        filtered_images = self.service._filter_images_for_chapter(
            self.sample_images, self.sample_chapter
        )
        
        # Should include images on pages 1 and 2, exclude page 4
        assert len(filtered_images) == 2
        assert filtered_images[0].page == 1
        assert filtered_images[1].page == 2
    
    def test_filter_text_blocks_for_chapter(self):
        """Test filtering text blocks by chapter page range."""
        filtered_blocks = self.service._filter_text_blocks_for_chapter(
            self.sample_text_blocks, self.sample_chapter
        )
        
        # Should include blocks on pages 1 and 2, exclude page 4
        assert len(filtered_blocks) == 3  # Two captions + one regular text
        assert all(1 <= block.page <= 3 for block in filtered_blocks)
    
    def test_filter_with_no_page_range(self):
        """Test filtering when chapter has no page range specified."""
        chapter_no_range = Chapter(
            id="chapter-2",
            title="No Range Chapter",
            level=1,
            order_index=1,
            page_start=None,
            page_end=None
        )
        
        filtered_images = self.service._filter_images_for_chapter(
            self.sample_images, chapter_no_range
        )
        filtered_blocks = self.service._filter_text_blocks_for_chapter(
            self.sample_text_blocks, chapter_no_range
        )
        
        # Should include all images and text blocks
        assert len(filtered_images) == len(self.sample_images)
        assert len(filtered_blocks) == len(self.sample_text_blocks)
    
    @patch('app.services.figure_service.ImageCaptionService')
    @pytest.mark.asyncio
    async def test_process_figures_for_chapter(self, mock_caption_service_class):
        """Test processing figures for a chapter."""
        # Mock the image caption service
        mock_caption_service = Mock()
        mock_caption_service_class.return_value = mock_caption_service
        
        # Mock pairing results
        from app.services.image_caption_service import ImageCaptionPair
        mock_pairs = [
            ImageCaptionPair(
                image=self.sample_images[0],
                caption="First image caption",
                caption_confidence=0.9,
                caption_source="pattern_english_figure",
                source_text_block=self.sample_text_blocks[0]
            ),
            ImageCaptionPair(
                image=self.sample_images[1],
                caption="第二个图片说明",
                caption_confidence=0.85,
                caption_source="pattern_chinese_figure",
                source_text_block=self.sample_text_blocks[1]
            )
        ]
        
        mock_caption_service.pair_images_with_captions.return_value = mock_pairs
        mock_caption_service.validate_caption_pairing.return_value = {
            'accuracy': 0.9,
            'coverage': 1.0,
            'avg_confidence': 0.875
        }
        
        # Create new service instance to use mocked caption service
        service = FigureService(self.mock_db)
        
        figures = await service.process_figures_for_chapter(
            self.sample_chapter, self.sample_images, self.sample_text_blocks
        )
        
        # Should create 2 figures (only images within chapter page range)
        assert len(figures) == 2
        
        # Verify figure properties
        assert figures[0].chapter_id == self.sample_chapter.id
        assert figures[0].image_path == "/tmp/image1.png"
        assert figures[0].caption == "First image caption"
        assert figures[0].page_number == 1
        
        assert figures[1].chapter_id == self.sample_chapter.id
        assert figures[1].image_path == "/tmp/image2.png"
        assert figures[1].caption == "第二个图片说明"
        assert figures[1].page_number == 2
        
        # Verify database operations
        assert self.mock_db.add.call_count == 2
    
    def test_create_figure_from_pair(self):
        """Test creating a Figure object from an image-caption pair."""
        from app.services.image_caption_service import ImageCaptionPair
        
        pair = ImageCaptionPair(
            image=self.sample_images[0],
            caption="Test caption",
            caption_confidence=0.8,
            caption_source="pattern_english_figure",
            source_text_block=self.sample_text_blocks[0]
        )
        
        figure = self.service._create_figure_from_pair(self.sample_chapter, pair)
        
        assert isinstance(figure, Figure)
        assert figure.chapter_id == self.sample_chapter.id
        assert figure.image_path == "/tmp/image1.png"
        assert figure.caption == "Test caption"
        assert figure.page_number == 1
        assert figure.bbox == {"x": 100, "y": 200, "width": 300, "height": 200}
        assert figure.image_format == "PNG"
        
        # Verify figure was added to database session
        self.mock_db.add.assert_called_once_with(figure)
    
    @pytest.mark.asyncio
    async def test_get_figures_for_chapter(self):
        """Test retrieving figures for a chapter."""
        # Mock database query
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.all.return_value = [Mock(spec=Figure), Mock(spec=Figure)]
        
        figures = await self.service.get_figures_for_chapter("chapter-1")
        
        assert len(figures) == 2
        self.mock_db.query.assert_called_once_with(Figure)
        mock_query.filter.assert_called_once()
        mock_filter.order_by.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_figure_by_id(self):
        """Test retrieving a specific figure by ID."""
        mock_figure = Mock(spec=Figure)
        
        mock_query = Mock()
        mock_filter = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_figure
        
        figure = await self.service.get_figure_by_id("figure-1")
        
        assert figure == mock_figure
        self.mock_db.query.assert_called_once_with(Figure)
    
    @pytest.mark.asyncio
    async def test_update_figure_caption(self):
        """Test updating a figure's caption."""
        mock_figure = Mock(spec=Figure)
        mock_figure.caption = "Old caption"
        
        # Mock get_figure_by_id
        with patch.object(self.service, 'get_figure_by_id', return_value=mock_figure):
            updated_figure = await self.service.update_figure_caption(
                "figure-1", "New caption"
            )
        
        assert updated_figure == mock_figure
        assert mock_figure.caption == "New caption"
        self.mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_figure_caption_not_found(self):
        """Test updating caption for non-existent figure."""
        with patch.object(self.service, 'get_figure_by_id', return_value=None):
            result = await self.service.update_figure_caption("nonexistent", "New caption")
        
        assert result is None
        self.mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_figure(self):
        """Test deleting a figure."""
        mock_figure = Mock(spec=Figure)
        
        with patch.object(self.service, 'get_figure_by_id', return_value=mock_figure):
            result = await self.service.delete_figure("figure-1")
        
        assert result is True
        self.mock_db.delete.assert_called_once_with(mock_figure)
        self.mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_figure_not_found(self):
        """Test deleting non-existent figure."""
        with patch.object(self.service, 'get_figure_by_id', return_value=None):
            result = await self.service.delete_figure("nonexistent")
        
        assert result is False
        self.mock_db.delete.assert_not_called()
        self.mock_db.commit.assert_not_called()
    
    def test_get_pairing_statistics(self):
        """Test getting pairing statistics for a chapter."""
        # Mock figures
        mock_figures = [
            Mock(spec=Figure, id="fig-1", page_number=1, caption="Caption 1"),
            Mock(spec=Figure, id="fig-2", page_number=2, caption=None),
            Mock(spec=Figure, id="fig-3", page_number=3, caption="Caption 3"),
        ]
        
        mock_query = Mock()
        mock_filter = Mock()
        
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = mock_figures
        
        stats = self.service.get_pairing_statistics(self.sample_chapter)
        
        assert stats['total_figures'] == 3
        assert stats['figures_with_captions'] == 2
        assert stats['caption_coverage'] == 2/3
        assert len(stats['figures']) == 3
        
        # Check individual figure stats
        assert stats['figures'][0]['has_caption'] is True
        assert stats['figures'][1]['has_caption'] is False
        assert stats['figures'][2]['has_caption'] is True
    
    @pytest.mark.asyncio
    async def test_reprocess_figure_captions(self):
        """Test reprocessing captions for existing figures."""
        # Mock existing figures
        mock_figures = [
            Mock(
                spec=Figure,
                id="fig-1",
                image_path="/tmp/image1.png",
                page_number=1,
                bbox={"x": 100, "y": 200, "width": 300, "height": 200},
                image_format="PNG",
                caption="Old caption 1"
            ),
            Mock(
                spec=Figure,
                id="fig-2",
                image_path="/tmp/image2.png",
                page_number=2,
                bbox={"x": 100, "y": 300, "width": 250, "height": 150},
                image_format="JPEG",
                caption="Old caption 2"
            )
        ]
        
        with patch.object(self.service, 'get_figures_for_chapter', return_value=mock_figures):
            with patch.object(self.service.image_caption_service, 'pair_images_with_captions') as mock_pair:
                from app.services.image_caption_service import ImageCaptionPair
                
                # Mock new pairing results
                mock_pairs = [
                    ImageCaptionPair(
                        image=Mock(),
                        caption="New caption 1",
                        caption_confidence=0.9,
                        caption_source="pattern_english_figure",
                        source_text_block=Mock()
                    ),
                    ImageCaptionPair(
                        image=Mock(),
                        caption="New caption 2",
                        caption_confidence=0.8,
                        caption_source="pattern_chinese_figure",
                        source_text_block=Mock()
                    )
                ]
                mock_pair.return_value = mock_pairs
                
                updated_figures = await self.service.reprocess_figure_captions(
                    self.sample_chapter, self.sample_text_blocks
                )
        
        assert len(updated_figures) == 2
        assert mock_figures[0].caption == "New caption 1"
        assert mock_figures[1].caption == "New caption 2"
        self.mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_figures_no_images(self):
        """Test processing figures when no images are found."""
        figures = await self.service.process_figures_for_chapter(
            self.sample_chapter, [], self.sample_text_blocks
        )
        
        assert figures == []
        self.mock_db.add.assert_not_called()
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Empty chapter page range
        chapter_empty = Chapter(
            id="empty",
            title="Empty",
            level=1,
            order_index=1,
            page_start=5,
            page_end=4  # Invalid range
        )
        
        filtered_images = self.service._filter_images_for_chapter(
            self.sample_images, chapter_empty
        )
        
        # Should return empty list for invalid range
        assert filtered_images == []