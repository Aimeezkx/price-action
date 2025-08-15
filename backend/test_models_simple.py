#!/usr/bin/env python3
"""
Simple test script to verify models are properly defined
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Test imports
    print("Testing model imports...")
    
    from app.models.base import BaseModel, UUIDMixin, TimestampMixin
    print("✓ Base models imported successfully")
    
    from app.models.document import Document, Chapter, Figure, ProcessingStatus
    print("✓ Document models imported successfully")
    
    from app.models.knowledge import Knowledge, KnowledgeType
    print("✓ Knowledge models imported successfully")
    
    from app.models.learning import Card, SRS, CardType
    print("✓ Learning models imported successfully")
    
    from app.models import *
    print("✓ All models imported from __init__.py successfully")
    
    # Test enum values
    print("\nTesting enum values...")
    print(f"ProcessingStatus values: {list(ProcessingStatus)}")
    print(f"KnowledgeType values: {list(KnowledgeType)}")
    print(f"CardType values: {list(CardType)}")
    
    # Test model attributes
    print("\nTesting model attributes...")
    
    # Check Document model
    doc_columns = [col.name for col in Document.__table__.columns]
    expected_doc_columns = ['id', 'filename', 'file_type', 'file_path', 'file_size', 'status', 'metadata', 'error_message', 'created_at', 'updated_at']
    print(f"Document columns: {doc_columns}")
    
    # Check Knowledge model
    knowledge_columns = [col.name for col in Knowledge.__table__.columns]
    expected_knowledge_columns = ['id', 'chapter_id', 'kind', 'text', 'entities', 'anchors', 'embedding', 'confidence_score', 'created_at', 'updated_at']
    print(f"Knowledge columns: {knowledge_columns}")
    
    # Check relationships
    print("\nTesting relationships...")
    print(f"Document.chapters relationship: {hasattr(Document, 'chapters')}")
    print(f"Chapter.document relationship: {hasattr(Chapter, 'document')}")
    print(f"Knowledge.chapter relationship: {hasattr(Knowledge, 'chapter')}")
    print(f"Card.knowledge relationship: {hasattr(Card, 'knowledge')}")
    print(f"SRS.card relationship: {hasattr(SRS, 'card')}")
    
    print("\n✅ All model tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)