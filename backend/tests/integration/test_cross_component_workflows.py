"""
Integration tests for cross-component interactions and workflows.
Tests complex workflows that span multiple services and components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
import tempfile
import os

from app.services.document_service import DocumentService
from app.services.chapter_service import ChapterService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.card_generation_service import CardGenerationService
from app.services.srs_service import SRSService
from app.services.search_service import SearchService
from app.services.export_service import ExportService
from app.services.sync_service import SyncService
from app.models.document import DocumentStatus
from app.models.learning import CardType


class TestCrossComponentWorkflows:
    """Test complex workflows spanning multiple components"""
    
    @pytest.fixture
    async def all_services(self, db_session):
        """Create all service instances"""
        return {
            'document': DocumentService(db_session),
            'chapter': ChapterService(db_session),
            'knowledge': KnowledgeExtractionService(db_session),
            'card': CardGenerationService(db_session),
            'srs': SRSService(db_session),
            'search': SearchService(db_session),
            'export': ExportService(db_session),
            'sync': SyncService(db_session)
        }
    
    @pytest.fixture
    def sample_document_content(self):
        """Sample document content for testing"""
        return {
            'filename': 'test_workflow.pdf',
            'content': b'Sample PDF content for workflow testing',
            'user_id': 'test_user'
        }
    
    async def test_complete_learning_workflow(self, all_services, sample_document_content):
        """Test complete learning workflow from document upload to card review"""
        
        services = all_services
        
        # Step 1: Upload and process document
        document = await services['document'].create_document(**sample_document_content)
        assert document.status == DocumentStatus.UPLOADED
        
        # Simulate document processing
        document.content_text = "Machine learning is a subset of artificial intelligence."
        document.status = DocumentStatus.PARSED
        await services['document'].update_document(document)
        
        # Step 2: Extract chapters
        chapters = await services['chapter'].extract_chapters(document.id)
        assert len(chapters) >= 1
        
        chapter = chapters[0]
        chapter.content = "Machine learning is a subset of artificial intelligence that focuses on algorithms."
        await services['chapter'].update_chapter(chapter)
        
        # Step 3: Extract knowledge points
        knowledge_points = await services['knowledge'].extract_knowledge_points(
            chapter.id, chapter.content
        )
        assert len(knowledge_points) >= 1
        
        # Step 4: Generate cards
        all_cards = []
        for kp in knowledge_points:
            cards = await services['card'].generate_cards(kp.id)
            all_cards.extend(cards)
        
        assert len(all_cards) >= 1
        
        # Step 5: Initialize SRS for cards
        srs_states = []
        for card in all_cards:
            srs_state = await services['srs'].initialize_card(card.id)
            srs_states.append(srs_state)
        
        assert len(srs_states) == len(all_cards)
        
        # Step 6: Review cards (simulate study session)
        for i, card in enumerate(all_cards[:3]):  # Review first 3 cards
            grade = 4 if i % 2 == 0 else 3  # Alternate between good and medium grades
            
            review_result = await services['srs'].review_card(
                card.id, 
                grade=grade,
                response_time=5.0
            )
            
            assert review_result.next_due_date > datetime.now()
            assert review_result.new_interval >= 1
        
        # Step 7: Search for content
        search_results = await services['search'].search_text(
            query="machine learning",
            user_id=sample_document_content['user_id']
        )
        
        assert len(search_results) > 0
        assert any("machine learning" in result.content.lower() for result in search_results)
        
        # Step 8: Export data
        export_data = await services['export'].export_to_json([document.id])
        
        assert 'documents' in export_data
        assert 'chapters' in export_data
        assert 'knowledge_points' in export_data
        assert 'cards' in export_data
        
        assert len(export_data['documents']) == 1
        assert export_data['documents'][0]['id'] == str(document.id)
        
        # Step 9: Verify workflow integrity
        final_document = await services['document'].get_document(document.id)
        assert final_document.status == DocumentStatus.PARSED
        
        final_chapters = await services['chapter'].get_chapters_by_document(document.id)
        assert len(final_chapters) == len(chapters)
        
        final_cards = await services['card'].get_cards_by_document(document.id)
        assert len(final_cards) == len(all_cards)
    
    async def test_multi_document_workflow(self, all_services):
        """Test workflow with multiple documents"""
        
        services = all_services
        
        # Create multiple documents
        documents = []
        for i in range(3):
            doc = await services['document'].create_document(
                filename=f'multi_doc_{i}.pdf',
                content=f'Content for document {i} about topic {i}'.encode(),
                user_id='test_user'
            )
            
            # Simulate processing
            doc.content_text = f"Document {i} discusses topic {i} in detail."
            doc.status = DocumentStatus.COMPLETED
            await services['document'].update_document(doc)
            
            documents.append(doc)
        
        # Process each document
        all_chapters = []
        all_knowledge_points = []
        all_cards = []
        
        for doc in documents:
            # Extract chapters
            chapters = await services['chapter'].extract_chapters(doc.id)
            all_chapters.extend(chapters)
            
            # Extract knowledge points
            for chapter in chapters:
                chapter.content = f"Chapter content for {doc.filename}"
                await services['chapter'].update_chapter(chapter)
                
                kps = await services['knowledge'].extract_knowledge_points(
                    chapter.id, chapter.content
                )
                all_knowledge_points.extend(kps)
                
                # Generate cards
                for kp in kps:
                    cards = await services['card'].generate_cards(kp.id)
                    all_cards.extend(cards)
        
        # Cross-document search
        search_results = await services['search'].search_text(
            query="topic",
            user_id="test_user"
        )
        
        # Should find results from multiple documents
        document_ids_in_results = set()
        for result in search_results:
            if hasattr(result, 'document_id'):
                document_ids_in_results.add(result.document_id)
        
        assert len(document_ids_in_results) >= 2  # Results from multiple documents
        
        # Export all documents
        export_data = await services['export'].export_to_json([doc.id for doc in documents])
        
        assert len(export_data['documents']) == 3
        assert len(export_data['chapters']) == len(all_chapters)
        assert len(export_data['cards']) == len(all_cards)
    
    async def test_error_recovery_workflow(self, all_services, sample_document_content):
        """Test workflow error recovery and rollback"""
        
        services = all_services
        
        # Create document
        document = await services['document'].create_document(**sample_document_content)
        
        # Simulate processing error
        document.status = DocumentStatus.ERROR
        document.error_message = "Processing failed"
        await services['document'].update_document(document)
        
        # Attempt recovery
        document.status = DocumentStatus.UPLOADED
        document.error_message = None
        await services['document'].update_document(document)
        
        # Retry processing
        document.content_text = "Recovered content"
        document.status = DocumentStatus.COMPLETED
        await services['document'].update_document(document)
        
        # Verify recovery
        final_document = await services['document'].get_document(document.id)
        assert final_document.status == DocumentStatus.COMPLETED
        assert final_document.error_message is None
    
    async def test_concurrent_user_workflows(self, all_services):
        """Test concurrent workflows for multiple users"""
        
        services = all_services
        
        async def user_workflow(user_id: str, doc_index: int):
            """Simulate a complete user workflow"""
            # Upload document
            document = await services['document'].create_document(
                filename=f'user_{user_id}_doc_{doc_index}.pdf',
                content=f'Content for user {user_id} document {doc_index}'.encode(),
                user_id=user_id
            )
            
            # Process document
            document.content_text = f"User {user_id} content about subject {doc_index}"
            document.status = DocumentStatus.COMPLETED
            await services['document'].update_document(document)
            
            # Extract chapters and knowledge
            chapters = await services['chapter'].extract_chapters(document.id)
            
            cards = []
            for chapter in chapters:
                chapter.content = f"Chapter content for user {user_id}"
                await services['chapter'].update_chapter(chapter)
                
                kps = await services['knowledge'].extract_knowledge_points(
                    chapter.id, chapter.content
                )
                
                for kp in kps:
                    kp_cards = await services['card'].generate_cards(kp.id)
                    cards.extend(kp_cards)
            
            # Review some cards
            for card in cards[:2]:  # Review first 2 cards
                await services['srs'].initialize_card(card.id)
                await services['srs'].review_card(card.id, grade=4, response_time=3.0)
            
            return document, cards
        
        # Run concurrent workflows for multiple users
        user_tasks = []
        for user_id in ['user1', 'user2', 'user3']:
            for doc_index in range(2):  # 2 documents per user
                task = user_workflow(user_id, doc_index)
                user_tasks.append(task)
        
        results = await asyncio.gather(*user_tasks)
        
        # Verify all workflows completed
        assert len(results) == 6  # 3 users × 2 documents
        
        documents, all_cards = zip(*results)
        
        # Verify data isolation between users
        user1_docs = [doc for doc in documents if doc.user_id == 'user1']
        user2_docs = [doc for doc in documents if doc.user_id == 'user2']
        user3_docs = [doc for doc in documents if doc.user_id == 'user3']
        
        assert len(user1_docs) == 2
        assert len(user2_docs) == 2
        assert len(user3_docs) == 2
        
        # Test user-specific search
        user1_results = await services['search'].search_text(
            query="content",
            user_id="user1"
        )
        
        # Should only return results for user1
        for result in user1_results:
            if hasattr(result, 'user_id'):
                assert result.user_id == "user1"
    
    async def test_data_synchronization_workflow(self, all_services, sample_document_content):
        """Test data synchronization across components"""
        
        services = all_services
        
        # Create and process document
        document = await services['document'].create_document(**sample_document_content)
        
        document.content_text = "Synchronized content"
        document.status = DocumentStatus.COMPLETED
        await services['document'].update_document(document)
        
        # Extract chapters
        chapters = await services['chapter'].extract_chapters(document.id)
        chapter = chapters[0]
        chapter.content = "Synchronized chapter content"
        await services['chapter'].update_chapter(chapter)
        
        # Extract knowledge points
        knowledge_points = await services['knowledge'].extract_knowledge_points(
            chapter.id, chapter.content
        )
        
        # Generate cards
        cards = []
        for kp in knowledge_points:
            kp_cards = await services['card'].generate_cards(kp.id)
            cards.extend(kp_cards)
        
        # Test sync service
        sync_status = await services['sync'].sync_user_data(
            user_id=sample_document_content['user_id']
        )
        
        assert sync_status['status'] == 'success'
        assert 'documents_synced' in sync_status
        assert 'cards_synced' in sync_status
        
        # Verify data consistency after sync
        synced_document = await services['document'].get_document(document.id)
        assert synced_document.content_text == "Synchronized content"
        
        synced_chapters = await services['chapter'].get_chapters_by_document(document.id)
        assert len(synced_chapters) == len(chapters)
        
        synced_cards = await services['card'].get_cards_by_document(document.id)
        assert len(synced_cards) == len(cards)
    
    async def test_performance_optimization_workflow(self, all_services):
        """Test workflow performance optimization"""
        
        services = all_services
        
        import time
        
        # Create multiple documents for performance testing
        start_time = time.time()
        
        documents = []
        for i in range(5):
            doc = await services['document'].create_document(
                filename=f'perf_test_{i}.pdf',
                content=f'Performance test content {i}'.encode(),
                user_id='perf_user'
            )
            documents.append(doc)
        
        creation_time = time.time() - start_time
        assert creation_time < 5.0  # Should create 5 documents in under 5 seconds
        
        # Batch process documents
        start_time = time.time()
        
        for doc in documents:
            doc.content_text = f"Processed content for {doc.filename}"
            doc.status = DocumentStatus.COMPLETED
            await services['document'].update_document(doc)
        
        processing_time = time.time() - start_time
        assert processing_time < 10.0  # Should process 5 documents in under 10 seconds
        
        # Batch search across all documents
        start_time = time.time()
        
        search_results = await services['search'].search_text(
            query="content",
            user_id="perf_user"
        )
        
        search_time = time.time() - start_time
        assert search_time < 1.0  # Should search in under 1 second
        assert len(search_results) >= 5  # Should find results from all documents
    
    async def test_workflow_monitoring_and_logging(self, all_services, sample_document_content):
        """Test workflow monitoring and logging"""
        
        services = all_services
        
        # Mock logging to capture workflow events
        logged_events = []
        
        def mock_log(level, message, **kwargs):
            logged_events.append({
                'level': level,
                'message': message,
                'kwargs': kwargs
            })
        
        with patch('app.utils.logging.log', side_effect=mock_log):
            # Execute workflow
            document = await services['document'].create_document(**sample_document_content)
            
            document.content_text = "Monitored content"
            document.status = DocumentStatus.COMPLETED
            await services['document'].update_document(document)
            
            chapters = await services['chapter'].extract_chapters(document.id)
            
            for chapter in chapters:
                chapter.content = "Monitored chapter content"
                await services['chapter'].update_chapter(chapter)
                
                kps = await services['knowledge'].extract_knowledge_points(
                    chapter.id, chapter.content
                )
                
                for kp in kps:
                    cards = await services['card'].generate_cards(kp.id)
                    
                    for card in cards:
                        await services['srs'].initialize_card(card.id)
        
        # Verify logging occurred
        assert len(logged_events) > 0
        
        # Check for key workflow events
        event_messages = [event['message'] for event in logged_events]
        
        # Should log document creation, processing, etc.
        workflow_events = [
            msg for msg in event_messages 
            if any(keyword in msg.lower() for keyword in ['document', 'chapter', 'card', 'created', 'processed'])
        ]
        
        assert len(workflow_events) > 0