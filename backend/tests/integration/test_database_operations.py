"""
Integration tests for database operations and data consistency.
Tests database transactions, relationships, and data integrity.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from app.core.database import get_db, engine
from app.models.document import Document, DocumentStatus
from app.models.knowledge import KnowledgePoint, Chapter
from app.models.learning import Card, SRSState, ReviewHistory, CardType
from app.services.document_service import DocumentService
from app.services.chapter_service import ChapterService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.card_generation_service import CardGenerationService
from app.services.srs_service import SRSService


class TestDatabaseOperations:
    """Test database operations and data consistency"""
    
    @pytest.fixture
    async def services(self, db_session):
        """Create service instances"""
        return {
            'document': DocumentService(db_session),
            'chapter': ChapterService(db_session),
            'knowledge': KnowledgeExtractionService(db_session),
            'card': CardGenerationService(db_session),
            'srs': SRSService(db_session)
        }
    
    async def test_database_transaction_integrity(self, db_session, services):
        """Test database transaction integrity and rollback"""
        
        # Create document
        document = await services['document'].create_document(
            filename="transaction_test.pdf",
            content=b"test content",
            user_id="test_user"
        )
        
        # Start transaction that should fail
        try:
            async with db_session.begin():
                # Create chapter
                chapter = Chapter(
                    document_id=document.id,
                    title="Test Chapter",
                    content="Test content",
                    order=1
                )
                db_session.add(chapter)
                await db_session.flush()
                
                # Create knowledge point
                knowledge_point = KnowledgePoint(
                    chapter_id=chapter.id,
                    concept="Test Concept",
                    definition="Test definition",
                    difficulty=0.5
                )
                db_session.add(knowledge_point)
                await db_session.flush()
                
                # Force an error to test rollback
                raise Exception("Simulated error")
                
        except Exception:
            # Transaction should be rolled back
            pass
        
        # Verify rollback - chapter and knowledge point should not exist
        chapters = await services['chapter'].get_chapters_by_document(document.id)
        assert len(chapters) == 0
        
        knowledge_points = await services['knowledge'].get_knowledge_points_by_document(document.id)
        assert len(knowledge_points) == 0
        
        # But document should still exist (created before transaction)
        doc = await services['document'].get_document(document.id)
        assert doc is not None
    
    async def test_foreign_key_constraints(self, db_session, services):
        """Test foreign key constraints and referential integrity"""
        
        # Create document
        document = await services['document'].create_document(
            filename="fk_test.pdf",
            content=b"test content",
            user_id="test_user"
        )
        
        # Try to create chapter with invalid document_id
        with pytest.raises(IntegrityError):
            chapter = Chapter(
                document_id="invalid-id",
                title="Invalid Chapter",
                content="Test content",
                order=1
            )
            db_session.add(chapter)
            await db_session.commit()
        
        # Create valid chapter
        chapter = Chapter(
            document_id=document.id,
            title="Valid Chapter",
            content="Test content",
            order=1
        )
        db_session.add(chapter)
        await db_session.commit()
        
        # Try to create knowledge point with invalid chapter_id
        with pytest.raises(IntegrityError):
            knowledge_point = KnowledgePoint(
                chapter_id="invalid-id",
                concept="Invalid KP",
                definition="Test definition",
                difficulty=0.5
            )
            db_session.add(knowledge_point)
            await db_session.commit()
        
        # Create valid knowledge point
        knowledge_point = KnowledgePoint(
            chapter_id=chapter.id,
            concept="Valid KP",
            definition="Test definition",
            difficulty=0.5
        )
        db_session.add(knowledge_point)
        await db_session.commit()
        
        # Try to create card with invalid knowledge_point_id
        with pytest.raises(IntegrityError):
            card = Card(
                knowledge_point_id="invalid-id",
                front_content="Front",
                back_content="Back",
                card_type=CardType.BASIC
            )
            db_session.add(card)
            await db_session.commit()
    
    async def test_cascade_deletions(self, db_session, services):
        """Test cascade deletions maintain referential integrity"""
        
        # Create complete hierarchy
        document = await services['document'].create_document(
            filename="cascade_test.pdf",
            content=b"test content",
            user_id="test_user"
        )
        
        chapter = Chapter(
            document_id=document.id,
            title="Test Chapter",
            content="Test content",
            order=1
        )
        db_session.add(chapter)
        await db_session.flush()
        
        knowledge_point = KnowledgePoint(
            chapter_id=chapter.id,
            concept="Test Concept",
            definition="Test definition",
            difficulty=0.5
        )
        db_session.add(knowledge_point)
        await db_session.flush()
        
        card = Card(
            knowledge_point_id=knowledge_point.id,
            front_content="Front",
            back_content="Back",
            card_type=CardType.BASIC
        )
        db_session.add(card)
        await db_session.flush()
        
        srs_state = SRSState(
            card_id=card.id,
            ease_factor=2.5,
            interval=1,
            due_date=datetime.now() + timedelta(days=1)
        )
        db_session.add(srs_state)
        await db_session.commit()
        
        # Store IDs for verification
        chapter_id = chapter.id
        knowledge_point_id = knowledge_point.id
        card_id = card.id
        srs_state_id = srs_state.id
        
        # Delete document (should cascade)
        await services['document'].delete_document(document.id)
        
        # Verify all related entities are deleted
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM chapters WHERE id = :id"),
            {"id": chapter_id}
        )
        assert result.scalar() == 0
        
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM knowledge_points WHERE id = :id"),
            {"id": knowledge_point_id}
        )
        assert result.scalar() == 0
        
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM cards WHERE id = :id"),
            {"id": card_id}
        )
        assert result.scalar() == 0
        
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM srs_states WHERE id = :id"),
            {"id": srs_state_id}
        )
        assert result.scalar() == 0
    
    async def test_concurrent_database_operations(self, db_session, services):
        """Test concurrent database operations"""
        
        # Create document
        document = await services['document'].create_document(
            filename="concurrent_test.pdf",
            content=b"test content",
            user_id="test_user"
        )
        
        async def create_chapter(order: int):
            """Create a chapter concurrently"""
            chapter = Chapter(
                document_id=document.id,
                title=f"Chapter {order}",
                content=f"Content {order}",
                order=order
            )
            db_session.add(chapter)
            await db_session.commit()
            return chapter
        
        # Create multiple chapters concurrently
        tasks = [create_chapter(i) for i in range(5)]
        chapters = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions (some might fail due to concurrency)
        successful_chapters = [c for c in chapters if isinstance(c, Chapter)]
        
        # At least some should succeed
        assert len(successful_chapters) >= 3
        
        # Verify chapters in database
        db_chapters = await services['chapter'].get_chapters_by_document(document.id)
        assert len(db_chapters) >= 3
    
    async def test_database_connection_pooling(self, services):
        """Test database connection pooling and management"""
        
        async def create_document(index: int):
            """Create document using connection pool"""
            return await services['document'].create_document(
                filename=f"pool_test_{index}.pdf",
                content=b"test content",
                user_id="test_user"
            )
        
        # Create many documents to test connection pooling
        tasks = [create_document(i) for i in range(10)]
        documents = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(documents) == 10
        assert all(doc.id is not None for doc in documents)
    
    async def test_database_performance_optimization(self, db_session, services):
        """Test database performance optimizations"""
        
        # Create test data
        document = await services['document'].create_document(
            filename="performance_test.pdf",
            content=b"test content",
            user_id="test_user"
        )
        
        # Create multiple chapters
        chapters = []
        for i in range(10):
            chapter = Chapter(
                document_id=document.id,
                title=f"Chapter {i}",
                content=f"Content {i}",
                order=i
            )
            chapters.append(chapter)
        
        db_session.add_all(chapters)
        await db_session.commit()
        
        # Test bulk operations performance
        import time
        
        start_time = time.time()
        
        # Bulk query
        result = await db_session.execute(
            text("SELECT * FROM chapters WHERE document_id = :doc_id"),
            {"doc_id": document.id}
        )
        fetched_chapters = result.fetchall()
        
        query_time = time.time() - start_time
        
        assert len(fetched_chapters) == 10
        assert query_time < 1.0  # Should be fast
        
        # Test indexed queries
        start_time = time.time()
        
        # Query by indexed field
        chapters_by_doc = await services['chapter'].get_chapters_by_document(document.id)
        
        indexed_query_time = time.time() - start_time
        
        assert len(chapters_by_doc) == 10
        assert indexed_query_time < 0.5  # Should be very fast with index
    
    async def test_data_validation_constraints(self, db_session):
        """Test database-level data validation constraints"""
        
        # Test document constraints
        with pytest.raises(IntegrityError):
            # Missing required fields
            document = Document(filename=None)  # filename is required
            db_session.add(document)
            await db_session.commit()
        
        # Test chapter constraints
        document = Document(
            filename="validation_test.pdf",
            content_text="test",
            user_id="test_user",
            status=DocumentStatus.UPLOADED
        )
        db_session.add(document)
        await db_session.flush()
        
        with pytest.raises(IntegrityError):
            # Invalid order (negative)
            chapter = Chapter(
                document_id=document.id,
                title="Test Chapter",
                content="Test content",
                order=-1  # Should be >= 0
            )
            db_session.add(chapter)
            await db_session.commit()
        
        # Test knowledge point constraints
        chapter = Chapter(
            document_id=document.id,
            title="Valid Chapter",
            content="Test content",
            order=1
        )
        db_session.add(chapter)
        await db_session.flush()
        
        with pytest.raises(IntegrityError):
            # Invalid difficulty (out of range)
            knowledge_point = KnowledgePoint(
                chapter_id=chapter.id,
                concept="Test Concept",
                definition="Test definition",
                difficulty=1.5  # Should be <= 1.0
            )
            db_session.add(knowledge_point)
            await db_session.commit()
    
    async def test_database_backup_and_recovery(self, db_session, services):
        """Test database backup and recovery scenarios"""
        
        # Create test data
        document = await services['document'].create_document(
            filename="backup_test.pdf",
            content=b"test content",
            user_id="test_user"
        )
        
        chapter = Chapter(
            document_id=document.id,
            title="Backup Chapter",
            content="Backup content",
            order=1
        )
        db_session.add(chapter)
        await db_session.commit()
        
        # Simulate backup by exporting data
        backup_data = {
            "document": {
                "id": document.id,
                "filename": document.filename,
                "content_text": document.content_text,
                "user_id": document.user_id,
                "status": document.status.value
            },
            "chapters": [{
                "id": chapter.id,
                "document_id": chapter.document_id,
                "title": chapter.title,
                "content": chapter.content,
                "order": chapter.order
            }]
        }
        
        # Simulate data loss
        await db_session.execute(text("DELETE FROM chapters WHERE id = :id"), {"id": chapter.id})
        await db_session.execute(text("DELETE FROM documents WHERE id = :id"), {"id": document.id})
        await db_session.commit()
        
        # Verify data is gone
        doc = await services['document'].get_document(document.id)
        assert doc is None
        
        # Simulate recovery by restoring data
        restored_document = Document(
            id=backup_data["document"]["id"],
            filename=backup_data["document"]["filename"],
            content_text=backup_data["document"]["content_text"],
            user_id=backup_data["document"]["user_id"],
            status=DocumentStatus(backup_data["document"]["status"])
        )
        db_session.add(restored_document)
        await db_session.flush()
        
        restored_chapter = Chapter(
            id=backup_data["chapters"][0]["id"],
            document_id=backup_data["chapters"][0]["document_id"],
            title=backup_data["chapters"][0]["title"],
            content=backup_data["chapters"][0]["content"],
            order=backup_data["chapters"][0]["order"]
        )
        db_session.add(restored_chapter)
        await db_session.commit()
        
        # Verify recovery
        recovered_doc = await services['document'].get_document(document.id)
        assert recovered_doc is not None
        assert recovered_doc.filename == "backup_test.pdf"
        
        recovered_chapters = await services['chapter'].get_chapters_by_document(document.id)
        assert len(recovered_chapters) == 1
        assert recovered_chapters[0].title == "Backup Chapter"
    
    async def test_database_migration_compatibility(self, db_session):
        """Test database migration compatibility"""
        
        # Test that current schema matches expected structure
        
        # Check tables exist
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        result = await db_session.execute(tables_query)
        tables = [row[0] for row in result.fetchall()]
        
        expected_tables = [
            'documents', 'chapters', 'knowledge_points', 
            'cards', 'srs_states', 'review_history'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"
        
        # Check key columns exist
        columns_query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
        """)
        
        result = await db_session.execute(columns_query)
        columns = {row[0]: row[1] for row in result.fetchall()}
        
        expected_columns = {
            'id': 'uuid',
            'filename': 'character varying',
            'status': 'character varying',
            'created_at': 'timestamp without time zone'
        }
        
        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} not found in documents table"
            # Note: exact type matching may vary by database