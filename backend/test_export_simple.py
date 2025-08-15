"""
Simple integration test for export functionality
"""

import pytest
import json
import csv
import io
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.document import Document, Chapter, Figure, ProcessingStatus
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, SRS, CardType
from app.services.export_service import ExportService


def test_export_service_basic():
    """Test basic export service functionality without database"""
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create test data
        document = Document(
            id=uuid4(),
            filename="test.pdf",
            file_type="pdf",
            file_path="/test.pdf",
            file_size=1024,
            status=ProcessingStatus.COMPLETED,
            doc_metadata={}
        )
        db.add(document)
        
        chapter = Chapter(
            id=uuid4(),
            document_id=document.id,
            title="Test Chapter",
            level=1,
            order_index=1,
            page_start=1,
            page_end=5
        )
        db.add(chapter)
        
        knowledge = Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Test knowledge point",
            entities=["test", "knowledge"],
            anchors={"page": 1},
            confidence_score=0.9
        )
        db.add(knowledge)
        
        card = Card(
            id=uuid4(),
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front="What is test?",
            back="Test knowledge point",
            difficulty=2.0,
            card_metadata={}
        )
        db.add(card)
        
        srs = SRS(
            id=uuid4(),
            card_id=card.id,
            ease_factor=2.5,
            interval=3,
            repetitions=1,
            due_date=datetime.utcnow() + timedelta(days=3),
            last_reviewed=datetime.utcnow(),
            last_grade=4
        )
        db.add(srs)
        
        db.commit()
        
        # Test export service
        export_service = ExportService(db)
        
        # Test Anki CSV export
        anki_csv = export_service.export_anki_csv(document_id=document.id)
        assert len(anki_csv) > 0
        assert "What is test?" in anki_csv
        assert "Test knowledge point" in anki_csv
        
        # Parse CSV to verify structure
        reader = csv.DictReader(io.StringIO(anki_csv))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['Front'] == "What is test?"
        assert rows[0]['Back'] == "Test knowledge point"
        assert rows[0]['Type'] == "qa"
        assert "test.pdf::Test Chapter" in rows[0]['Deck']
        
        # Test Notion CSV export
        notion_csv = export_service.export_notion_csv(document_id=document.id)
        assert len(notion_csv) > 0
        assert "What is test?" in notion_csv
        
        # Test JSONL backup export
        jsonl_backup = export_service.export_jsonl_backup(document_id=document.id)
        assert len(jsonl_backup) > 0
        
        # Parse JSONL to verify structure
        doc_data = json.loads(jsonl_backup.strip())
        assert doc_data['document']['filename'] == "test.pdf"
        assert len(doc_data['chapters']) == 1
        assert doc_data['chapters'][0]['title'] == "Test Chapter"
        assert len(doc_data['chapters'][0]['knowledge_points']) == 1
        assert len(doc_data['chapters'][0]['knowledge_points'][0]['cards']) == 1
        
        # Test import functionality
        # Clear data first
        db.query(SRS).delete()
        db.query(Card).delete()
        db.query(Knowledge).delete()
        db.query(Chapter).delete()
        db.query(Document).delete()
        db.commit()
        
        # Import the data back
        result = export_service.import_jsonl_backup(jsonl_backup)
        assert result['imported_documents'] == 1
        assert result['imported_chapters'] == 1
        assert result['imported_knowledge'] == 1
        assert result['imported_cards'] == 1
        assert len(result['errors']) == 0
        
        # Verify data was imported
        imported_doc = db.query(Document).filter(Document.id == document.id).first()
        assert imported_doc is not None
        assert imported_doc.filename == "test.pdf"
        
        print("✓ All export functionality tests passed!")
        
    finally:
        db.close()


def test_export_utility_functions():
    """Test export service utility functions"""
    # Create a mock database session (not used for these tests)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        export_service = ExportService(db)
        
        # Test difficulty conversion
        assert export_service._difficulty_to_tag(1.0) == "easy"
        assert export_service._difficulty_to_tag(2.0) == "medium"
        assert export_service._difficulty_to_tag(3.0) == "hard"
        
        assert export_service._difficulty_to_label(1.0) == "Easy"
        assert export_service._difficulty_to_label(2.0) == "Medium"
        assert export_service._difficulty_to_label(3.0) == "Hard"
        
        # Test card content formatting
        # Create mock card objects
        class MockKnowledge:
            def __init__(self):
                self.kind = KnowledgeType.DEFINITION
                
        class MockCard:
            def __init__(self, card_type, front, back, metadata=None):
                self.card_type = card_type
                self.front = front
                self.back = back
                self.card_metadata = metadata or {}
                self.knowledge = MockKnowledge()
        
        # Test Q&A card formatting
        qa_card = MockCard(CardType.QA, "What is AI?", "Artificial Intelligence")
        front, back = export_service._format_card_content(qa_card)
        assert front == "What is AI?"
        assert back == "Artificial Intelligence"
        
        # Test cloze card formatting
        cloze_card = MockCard(CardType.CLOZE, "{{c1::AI}} is smart", "AI is smart")
        front, back = export_service._format_card_content(cloze_card)
        assert front == "{{c1::AI}} is smart"
        assert back == "AI is smart"
        
        # Test image card formatting
        image_card = MockCard(
            CardType.IMAGE_HOTSPOT, 
            "/images/test.png", 
            "Test caption",
            {"hotspots": ["region1", "region2"]}
        )
        front, back = export_service._format_card_content(image_card)
        assert "[IMAGE: /images/test.png]" in front
        assert "Click on: region1, region2" in front
        assert back == "Test caption"
        
        # Test card category generation
        category = export_service._get_card_category(qa_card)
        assert category == "Definition"
        
        cloze_category = export_service._get_card_category(cloze_card)
        assert cloze_category == "Cloze - Definition"
        
        image_category = export_service._get_card_category(image_card)
        assert image_category == "Image - Definition"
        
        print("✓ All utility function tests passed!")
        
    finally:
        db.close()


def test_export_error_handling():
    """Test export service error handling"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        export_service = ExportService(db)
        
        # Test export with no data
        anki_csv = export_service.export_anki_csv(document_id=uuid4())
        reader = csv.DictReader(io.StringIO(anki_csv))
        rows = list(reader)
        assert len(rows) == 0  # Should be empty
        
        # Test import with invalid JSON
        invalid_jsonl = "invalid json\n{broken}"
        result = export_service.import_jsonl_backup(invalid_jsonl)
        assert result['imported_documents'] == 0
        assert len(result['errors']) > 0
        
        print("✓ All error handling tests passed!")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_export_service_basic()
    test_export_utility_functions()
    test_export_error_handling()
    print("\n🎉 All export service tests completed successfully!")