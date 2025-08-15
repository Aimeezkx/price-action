"""
Test database models
"""

import pytest
from datetime import datetime
import uuid

from app.models import (
    Document, Chapter, Figure, Knowledge, Card, SRS,
    ProcessingStatus, KnowledgeType, CardType
)


def test_model_imports():
    """Test that all models can be imported successfully"""
    # Test that models exist and have expected attributes
    assert hasattr(Document, '__tablename__')
    assert hasattr(Chapter, '__tablename__')
    assert hasattr(Figure, '__tablename__')
    assert hasattr(Knowledge, '__tablename__')
    assert hasattr(Card, '__tablename__')
    assert hasattr(SRS, '__tablename__')


def test_enum_values():
    """Test that enums have expected values"""
    # Test ProcessingStatus enum
    assert ProcessingStatus.PENDING == "pending"
    assert ProcessingStatus.PROCESSING == "processing"
    assert ProcessingStatus.COMPLETED == "completed"
    assert ProcessingStatus.FAILED == "failed"
    
    # Test KnowledgeType enum
    assert KnowledgeType.DEFINITION == "definition"
    assert KnowledgeType.FACT == "fact"
    assert KnowledgeType.THEOREM == "theorem"
    assert KnowledgeType.PROCESS == "process"
    assert KnowledgeType.EXAMPLE == "example"
    assert KnowledgeType.CONCEPT == "concept"
    
    # Test CardType enum
    assert CardType.QA == "qa"
    assert CardType.CLOZE == "cloze"
    assert CardType.IMAGE_HOTSPOT == "image_hotspot"


def test_document_model_structure():
    """Test Document model has expected columns"""
    doc_columns = [col.name for col in Document.__table__.columns]
    expected_columns = [
        'id', 'filename', 'file_type', 'file_path', 'file_size', 
        'status', 'doc_metadata', 'error_message', 'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in doc_columns, f"Column {col} missing from Document model"


def test_chapter_model_structure():
    """Test Chapter model has expected columns"""
    chapter_columns = [col.name for col in Chapter.__table__.columns]
    expected_columns = [
        'id', 'document_id', 'title', 'level', 'order_index',
        'page_start', 'page_end', 'content', 'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in chapter_columns, f"Column {col} missing from Chapter model"


def test_knowledge_model_structure():
    """Test Knowledge model has expected columns"""
    knowledge_columns = [col.name for col in Knowledge.__table__.columns]
    expected_columns = [
        'id', 'chapter_id', 'kind', 'text', 'entities', 'anchors',
        'embedding', 'confidence_score', 'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in knowledge_columns, f"Column {col} missing from Knowledge model"


def test_card_model_structure():
    """Test Card model has expected columns"""
    card_columns = [col.name for col in Card.__table__.columns]
    expected_columns = [
        'id', 'knowledge_id', 'card_type', 'front', 'back',
        'difficulty', 'card_metadata', 'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in card_columns, f"Column {col} missing from Card model"


def test_srs_model_structure():
    """Test SRS model has expected columns"""
    srs_columns = [col.name for col in SRS.__table__.columns]
    expected_columns = [
        'id', 'card_id', 'user_id', 'ease_factor', 'interval',
        'repetitions', 'due_date', 'last_reviewed', 'last_grade',
        'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in srs_columns, f"Column {col} missing from SRS model"


def test_figure_model_structure():
    """Test Figure model has expected columns"""
    figure_columns = [col.name for col in Figure.__table__.columns]
    expected_columns = [
        'id', 'chapter_id', 'image_path', 'caption', 'page_number',
        'bbox', 'image_format', 'created_at', 'updated_at'
    ]
    
    for col in expected_columns:
        assert col in figure_columns, f"Column {col} missing from Figure model"


def test_model_relationships():
    """Test that models have expected relationships"""
    # Test Document relationships
    assert hasattr(Document, 'chapters')
    
    # Test Chapter relationships
    assert hasattr(Chapter, 'document')
    assert hasattr(Chapter, 'figures')
    assert hasattr(Chapter, 'knowledge_points')
    
    # Test Knowledge relationships
    assert hasattr(Knowledge, 'chapter')
    assert hasattr(Knowledge, 'cards')
    
    # Test Card relationships
    assert hasattr(Card, 'knowledge')
    assert hasattr(Card, 'srs_records')
    
    # Test SRS relationships
    assert hasattr(SRS, 'card')
    
    # Test Figure relationships
    assert hasattr(Figure, 'chapter')


def test_model_repr():
    """Test that models have proper string representations"""
    # Test that __repr__ methods exist and don't crash
    doc = Document()
    doc.id = uuid.uuid4()
    doc.filename = "test.pdf"
    doc.status = ProcessingStatus.PENDING
    
    repr_str = repr(doc)
    assert "Document" in repr_str
    assert "test.pdf" in repr_str
    assert "pending" in repr_str


def test_model_defaults():
    """Test that models have proper default values defined in columns"""
    # Test Document column defaults
    status_col = Document.__table__.columns['status']
    assert status_col.default.arg == ProcessingStatus.PENDING
    
    # Test SRS column defaults
    ease_factor_col = SRS.__table__.columns['ease_factor']
    assert ease_factor_col.default.arg == 2.5
    
    interval_col = SRS.__table__.columns['interval']
    assert interval_col.default.arg == 1
    
    repetitions_col = SRS.__table__.columns['repetitions']
    assert repetitions_col.default.arg == 0
    
    # Test Card column defaults
    difficulty_col = Card.__table__.columns['difficulty']
    assert difficulty_col.default.arg == 1.0
    
    # Test Knowledge column defaults
    confidence_col = Knowledge.__table__.columns['confidence_score']
    assert confidence_col.default.arg == 1.0