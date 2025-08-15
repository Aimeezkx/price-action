#!/usr/bin/env python3
"""
Comprehensive verification script for Task 2: Initialize database schema and core models
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def verify_sqlalchemy_models():
    """Verify SQLAlchemy models are properly implemented"""
    print("=== Verifying SQLAlchemy Models ===")
    
    try:
        # Import all models
        from app.models import (
            Document, Chapter, Figure, Knowledge, Card, SRS,
            ProcessingStatus, KnowledgeType, CardType
        )
        print("✓ All models imported successfully")
        
        # Verify model inheritance
        from app.models.base import BaseModel
        assert issubclass(Document, BaseModel)
        assert issubclass(Chapter, BaseModel)
        assert issubclass(Figure, BaseModel)
        assert issubclass(Knowledge, BaseModel)
        assert issubclass(Card, BaseModel)
        assert issubclass(SRS, BaseModel)
        print("✓ All models inherit from BaseModel")
        
        # Verify enums
        assert len(list(ProcessingStatus)) == 4
        assert len(list(KnowledgeType)) == 6
        assert len(list(CardType)) == 3
        print("✓ All enums have correct values")
        
        # Verify relationships
        assert hasattr(Document, 'chapters')
        assert hasattr(Chapter, 'document')
        assert hasattr(Chapter, 'figures')
        assert hasattr(Chapter, 'knowledge_points')
        assert hasattr(Knowledge, 'chapter')
        assert hasattr(Knowledge, 'cards')
        assert hasattr(Card, 'knowledge')
        assert hasattr(Card, 'srs_records')
        assert hasattr(SRS, 'card')
        assert hasattr(Figure, 'chapter')
        print("✓ All model relationships defined")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy models verification failed: {e}")
        return False

def verify_alembic_migrations():
    """Verify Alembic migrations are properly set up"""
    print("\n=== Verifying Alembic Migrations ===")
    
    try:
        # Check migration files exist
        migration_file = "alembic/versions/001_initial_schema.py"
        assert os.path.exists(migration_file), "Initial migration file not found"
        print("✓ Initial migration file exists")
        
        # Check migration content
        with open(migration_file, 'r') as f:
            content = f.read()
        
        # Verify all tables are created
        required_tables = ['documents', 'chapters', 'figures', 'knowledge', 'cards', 'srs']
        for table in required_tables:
            assert f"create_table('{table}'" in content, f"Table {table} not in migration"
        print("✓ All required tables in migration")
        
        # Verify pgvector extension
        assert "CREATE EXTENSION IF NOT EXISTS vector" in content
        print("✓ pgvector extension in migration")
        
        # Verify vector column
        assert "Vector(384)" in content
        print("✓ Vector column defined in migration")
        
        return True
        
    except Exception as e:
        print(f"❌ Alembic migrations verification failed: {e}")
        return False

def verify_pgvector_support():
    """Verify pgvector extension support"""
    print("\n=== Verifying pgvector Support ===")
    
    try:
        # Check pgvector import
        from pgvector.sqlalchemy import Vector
        print("✓ pgvector.sqlalchemy imported successfully")
        
        # Check Knowledge model has embedding column
        from app.models import Knowledge
        embedding_col = Knowledge.__table__.columns.get('embedding')
        assert embedding_col is not None, "embedding column not found"
        print("✓ Knowledge model has embedding column")
        
        # Verify embedding column type
        from pgvector.sqlalchemy import Vector
        assert isinstance(embedding_col.type, Vector), "embedding column is not Vector type"
        print("✓ embedding column is Vector type")
        
        return True
        
    except Exception as e:
        print(f"❌ pgvector support verification failed: {e}")
        return False

def verify_database_connection():
    """Verify database connection and session management"""
    print("\n=== Verifying Database Connection ===")
    
    try:
        from app.core.database import get_db, Base, engine
        from sqlalchemy.orm import Session
        
        # Test session creation
        db_gen = get_db()
        db = next(db_gen)
        assert isinstance(db, Session), "get_db() doesn't return Session"
        db.close()
        print("✓ Database session creation works")
        
        # Test Base metadata
        assert len(Base.metadata.tables) >= 6, "Not all tables registered with Base"
        print("✓ All models registered with Base metadata")
        
        # Test engine configuration
        assert engine is not None, "Database engine not configured"
        print("✓ Database engine configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection verification failed: {e}")
        return False

def verify_model_columns():
    """Verify all required columns are present in models"""
    print("\n=== Verifying Model Columns ===")
    
    try:
        from app.models import Document, Chapter, Figure, Knowledge, Card, SRS
        
        # Document columns
        doc_cols = [col.name for col in Document.__table__.columns]
        required_doc_cols = ['id', 'filename', 'file_type', 'file_path', 'file_size', 
                           'status', 'doc_metadata', 'error_message', 'created_at', 'updated_at']
        for col in required_doc_cols:
            assert col in doc_cols, f"Document missing column: {col}"
        print("✓ Document model has all required columns")
        
        # Chapter columns
        chapter_cols = [col.name for col in Chapter.__table__.columns]
        required_chapter_cols = ['id', 'document_id', 'title', 'level', 'order_index',
                               'page_start', 'page_end', 'content', 'created_at', 'updated_at']
        for col in required_chapter_cols:
            assert col in chapter_cols, f"Chapter missing column: {col}"
        print("✓ Chapter model has all required columns")
        
        # Knowledge columns
        knowledge_cols = [col.name for col in Knowledge.__table__.columns]
        required_knowledge_cols = ['id', 'chapter_id', 'kind', 'text', 'entities', 
                                 'anchors', 'embedding', 'confidence_score', 'created_at', 'updated_at']
        for col in required_knowledge_cols:
            assert col in knowledge_cols, f"Knowledge missing column: {col}"
        print("✓ Knowledge model has all required columns")
        
        # Card columns
        card_cols = [col.name for col in Card.__table__.columns]
        required_card_cols = ['id', 'knowledge_id', 'card_type', 'front', 'back',
                            'difficulty', 'card_metadata', 'created_at', 'updated_at']
        for col in required_card_cols:
            assert col in card_cols, f"Card missing column: {col}"
        print("✓ Card model has all required columns")
        
        # SRS columns
        srs_cols = [col.name for col in SRS.__table__.columns]
        required_srs_cols = ['id', 'card_id', 'user_id', 'ease_factor', 'interval',
                           'repetitions', 'due_date', 'last_reviewed', 'last_grade', 
                           'created_at', 'updated_at']
        for col in required_srs_cols:
            assert col in srs_cols, f"SRS missing column: {col}"
        print("✓ SRS model has all required columns")
        
        # Figure columns
        figure_cols = [col.name for col in Figure.__table__.columns]
        required_figure_cols = ['id', 'chapter_id', 'image_path', 'caption', 'page_number',
                              'bbox', 'image_format', 'created_at', 'updated_at']
        for col in required_figure_cols:
            assert col in figure_cols, f"Figure missing column: {col}"
        print("✓ Figure model has all required columns")
        
        return True
        
    except Exception as e:
        print(f"❌ Model columns verification failed: {e}")
        return False

def verify_requirements_coverage():
    """Verify that all requirements are covered"""
    print("\n=== Verifying Requirements Coverage ===")
    
    try:
        # Requirement 2.1: Document parsing and content extraction
        from app.models import Document, Chapter, Figure
        print("✓ Requirement 2.1: Document, Chapter, Figure models implemented")
        
        # Requirement 2.2: Image extraction and storage
        from app.models import Figure
        figure_cols = [col.name for col in Figure.__table__.columns]
        assert 'image_path' in figure_cols
        assert 'bbox' in figure_cols
        print("✓ Requirement 2.2: Image storage fields implemented")
        
        # Requirement 2.3: Document structure preservation
        from app.models import Chapter
        chapter_cols = [col.name for col in Chapter.__table__.columns]
        assert 'level' in chapter_cols
        assert 'order_index' in chapter_cols
        assert 'page_start' in chapter_cols
        assert 'page_end' in chapter_cols
        print("✓ Requirement 2.3: Document structure fields implemented")
        
        # Requirement 6.1: Flashcard generation
        from app.models import Card, CardType
        assert CardType.QA in list(CardType)
        assert CardType.CLOZE in list(CardType)
        assert CardType.IMAGE_HOTSPOT in list(CardType)
        print("✓ Requirement 6.1: Card types implemented")
        
        # Requirement 8.1: Spaced repetition system
        from app.models import SRS
        srs_cols = [col.name for col in SRS.__table__.columns]
        assert 'ease_factor' in srs_cols
        assert 'interval' in srs_cols
        assert 'repetitions' in srs_cols
        assert 'due_date' in srs_cols
        print("✓ Requirement 8.1: SRS fields implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements coverage verification failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Verifying Task 2: Initialize database schema and core models")
    print("=" * 70)
    
    verifications = [
        verify_sqlalchemy_models,
        verify_alembic_migrations,
        verify_pgvector_support,
        verify_database_connection,
        verify_model_columns,
        verify_requirements_coverage
    ]
    
    results = []
    for verification in verifications:
        results.append(verification())
    
    print("\n" + "=" * 70)
    if all(results):
        print("✅ Task 2 verification PASSED - All components implemented correctly!")
        print("\nImplemented components:")
        print("• SQLAlchemy models for Document, Chapter, Figure, Knowledge, Card, SRS")
        print("• Alembic migrations for database schema")
        print("• pgvector extension support for vector embeddings")
        print("• Database connection and session management")
        print("• All required columns and relationships")
        print("• Coverage of requirements 2.1, 2.2, 2.3, 6.1, 8.1")
    else:
        print("❌ Task 2 verification FAILED - Some components need attention!")
        sys.exit(1)

if __name__ == "__main__":
    main()