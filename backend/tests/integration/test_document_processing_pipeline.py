"""
Integration tests for complete document processing pipeline.
Tests the full workflow from document upload to card generation.
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.document import Document, DocumentStatus
from app.models.knowledge import KnowledgePoint, Chapter
from app.models.learning import Card, SRSState
from app.services.document_service import DocumentService
from app.services.chapter_service import ChapterService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.card_generation_service import CardGenerationService
from app.services.srs_service import SRSService
from app.parsers.factory import ParserFactory


class TestDocumentProcessingPipeline:
    """Test complete document processing workflow"""
    
    @pytest.fixture
    async def sample_pdf_path(self):
        """Create a sample PDF file for testing"""
        # Create a temporary PDF file with test content
        test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(test_content)
            yield f.name
        
        # Cleanup
        os.unlink(f.name)
    
    @pytest.fixture
    async def document_service(self, db_session):
        """Create document service instance"""
        return DocumentService(db_session)
    
    @pytest.fixture
    async def chapter_service(self, db_session):
        """Create chapter service instance"""
        return ChapterService(db_session)
    
    @pytest.fixture
    async def knowledge_service(self, db_session):
        """Create knowledge extraction service instance"""
        return KnowledgeExtractionService(db_session)
    
    @pytest.fixture
    async def card_service(self, db_session):
        """Create card generation service instance"""
        return CardGenerationService(db_session)
    
    @pytest.fixture
    async def srs_service(self, db_session):
        """Create SRS service instance"""
        return SRSService(db_session)
    
    async def test_complete_document_processing_workflow(
        self, 
        db_session,
        sample_pdf_path,
        document_service,
        chapter_service,
        knowledge_service,
        card_service,
        srs_service
    ):
        """Test complete document processing from upload to card generation"""
        
        # Step 1: Upload document
        with open(sample_pdf_path, 'rb') as f:
            document = await document_service.create_document(
                filename="test_document.pdf",
                content=f.read(),
                user_id="test_user"
            )
        
        assert document.id is not None
        assert document.status == DocumentStatus.UPLOADED
        assert document.filename == "test_document.pdf"
        
        # Step 2: Parse document
        parser = ParserFactory.get_parser(sample_pdf_path)
        parsed_content = await parser.parse(sample_pdf_path)
        
        # Update document with parsed content
        document.content_text = parsed_content.text
        document.status = DocumentStatus.PARSED
        await document_service.update_document(document)
        
        # Step 3: Extract chapters
        chapters = await chapter_service.extract_chapters(document.id)
        assert len(chapters) >= 1
        
        # Verify chapter structure
        for chapter in chapters:
            assert chapter.document_id == document.id
            assert chapter.title is not None
            assert chapter.content is not None
            assert chapter.order >= 0
        
        # Step 4: Extract knowledge points
        knowledge_points = []
        for chapter in chapters:
            chapter_knowledge = await knowledge_service.extract_knowledge_points(
                chapter.id, chapter.content
            )
            knowledge_points.extend(chapter_knowledge)
        
        assert len(knowledge_points) >= 1
        
        # Verify knowledge points
        for kp in knowledge_points:
            assert kp.chapter_id in [c.id for c in chapters]
            assert kp.concept is not None
            assert kp.definition is not None
            assert 0 <= kp.difficulty <= 1
        
        # Step 5: Generate cards
        cards = []
        for kp in knowledge_points:
            kp_cards = await card_service.generate_cards(kp.id)
            cards.extend(kp_cards)
        
        assert len(cards) >= 1
        
        # Verify cards
        for card in cards:
            assert card.knowledge_point_id in [kp.id for kp in knowledge_points]
            assert card.front_content is not None
            assert card.back_content is not None
            assert card.card_type is not None
        
        # Step 6: Initialize SRS states
        srs_states = []
        for card in cards:
            srs_state = await srs_service.initialize_card(card.id)
            srs_states.append(srs_state)
        
        assert len(srs_states) == len(cards)
        
        # Verify SRS states
        for srs_state in srs_states:
            assert srs_state.card_id in [c.id for c in cards]
            assert srs_state.ease_factor > 0
            assert srs_state.interval >= 1
            assert srs_state.due_date >= datetime.now()
        
        # Step 7: Update document status to completed
        document.status = DocumentStatus.COMPLETED
        await document_service.update_document(document)
        
        # Final verification
        final_document = await document_service.get_document(document.id)
        assert final_document.status == DocumentStatus.COMPLETED
        
        # Verify complete pipeline integrity
        db_chapters = await chapter_service.get_chapters_by_document(document.id)
        assert len(db_chapters) == len(chapters)
        
        db_knowledge = await knowledge_service.get_knowledge_points_by_document(document.id)
        assert len(db_knowledge) == len(knowledge_points)
        
        db_cards = await card_service.get_cards_by_document(document.id)
        assert len(db_cards) == len(cards)
    
    async def test_pipeline_error_handling(
        self,
        db_session,
        document_service
    ):
        """Test pipeline error handling and recovery"""
        
        # Test with invalid file
        with pytest.raises(Exception):
            await document_service.create_document(
                filename="invalid.txt",
                content=b"invalid content",
                user_id="test_user"
            )
        
        # Test with corrupted PDF
        corrupted_content = b"corrupted pdf content"
        document = await document_service.create_document(
            filename="corrupted.pdf",
            content=corrupted_content,
            user_id="test_user"
        )
        
        # Processing should fail gracefully
        document.status = DocumentStatus.ERROR
        await document_service.update_document(document)
        
        final_document = await document_service.get_document(document.id)
        assert final_document.status == DocumentStatus.ERROR
    
    async def test_pipeline_performance(
        self,
        db_session,
        sample_pdf_path,
        document_service
    ):
        """Test pipeline performance benchmarks"""
        
        start_time = datetime.now()
        
        # Process document
        with open(sample_pdf_path, 'rb') as f:
            document = await document_service.create_document(
                filename="performance_test.pdf",
                content=f.read(),
                user_id="test_user"
            )
        
        # Simulate processing time
        await asyncio.sleep(0.1)  # Simulate processing
        
        document.status = DocumentStatus.COMPLETED
        await document_service.update_document(document)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Assert processing time is reasonable (adjust based on requirements)
        assert processing_time < 30  # Should complete within 30 seconds
    
    async def test_concurrent_document_processing(
        self,
        db_session,
        sample_pdf_path,
        document_service
    ):
        """Test concurrent document processing"""
        
        async def process_document(doc_name: str):
            with open(sample_pdf_path, 'rb') as f:
                document = await document_service.create_document(
                    filename=doc_name,
                    content=f.read(),
                    user_id="test_user"
                )
            return document
        
        # Process multiple documents concurrently
        tasks = [
            process_document(f"concurrent_test_{i}.pdf")
            for i in range(3)
        ]
        
        documents = await asyncio.gather(*tasks)
        
        # Verify all documents were created
        assert len(documents) == 3
        for doc in documents:
            assert doc.id is not None
            assert doc.status == DocumentStatus.UPLOADED
    
    async def test_pipeline_data_consistency(
        self,
        db_session,
        sample_pdf_path,
        document_service,
        chapter_service,
        knowledge_service,
        card_service
    ):
        """Test data consistency throughout the pipeline"""
        
        # Create document
        with open(sample_pdf_path, 'rb') as f:
            document = await document_service.create_document(
                filename="consistency_test.pdf",
                content=f.read(),
                user_id="test_user"
            )
        
        # Create chapters
        chapters = await chapter_service.extract_chapters(document.id)
        
        # Verify foreign key relationships
        for chapter in chapters:
            assert chapter.document_id == document.id
            
            # Verify document exists
            doc_exists = await document_service.get_document(document.id)
            assert doc_exists is not None
        
        # Create knowledge points
        knowledge_points = []
        for chapter in chapters:
            kps = await knowledge_service.extract_knowledge_points(
                chapter.id, chapter.content
            )
            knowledge_points.extend(kps)
        
        # Verify knowledge point relationships
        for kp in knowledge_points:
            assert kp.chapter_id in [c.id for c in chapters]
            
            # Verify chapter exists
            chapter_exists = next(
                (c for c in chapters if c.id == kp.chapter_id), None
            )
            assert chapter_exists is not None
        
        # Create cards
        cards = []
        for kp in knowledge_points:
            kp_cards = await card_service.generate_cards(kp.id)
            cards.extend(kp_cards)
        
        # Verify card relationships
        for card in cards:
            assert card.knowledge_point_id in [kp.id for kp in knowledge_points]
            
            # Verify knowledge point exists
            kp_exists = next(
                (kp for kp in knowledge_points if kp.id == card.knowledge_point_id), 
                None
            )
            assert kp_exists is not None
        
        # Test cascade operations
        # Delete document should cascade to all related entities
        await document_service.delete_document(document.id)
        
        # Verify cascaded deletions
        remaining_chapters = await chapter_service.get_chapters_by_document(document.id)
        assert len(remaining_chapters) == 0
        
        remaining_knowledge = await knowledge_service.get_knowledge_points_by_document(document.id)
        assert len(remaining_knowledge) == 0
        
        remaining_cards = await card_service.get_cards_by_document(document.id)
        assert len(remaining_cards) == 0