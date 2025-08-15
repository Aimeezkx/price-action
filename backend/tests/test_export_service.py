"""
Tests for export service
"""

import pytest
import json
import csv
import io
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.export_service import ExportService
from app.models.document import Document, Chapter, Figure, ProcessingStatus
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, SRS, CardType


class TestExportService:
    """Test export service functionality"""
    
    @pytest.fixture
    def export_service(self, db_session: Session):
        """Create export service instance"""
        return ExportService(db_session)
    
    @pytest.fixture
    def sample_data(self, db_session: Session):
        """Create sample data for testing"""
        # Create document
        document = Document(
            id=uuid4(),
            filename="test_document.pdf",
            file_type="pdf",
            file_path="/test/path.pdf",
            file_size=1024,
            status=ProcessingStatus.COMPLETED,
            doc_metadata={"pages": 10}
        )
        db_session.add(document)
        
        # Create chapter
        chapter = Chapter(
            id=uuid4(),
            document_id=document.id,
            title="Test Chapter",
            level=1,
            order_index=1,
            page_start=1,
            page_end=5,
            content="Test chapter content"
        )
        db_session.add(chapter)
        
        # Create figure
        figure = Figure(
            id=uuid4(),
            chapter_id=chapter.id,
            image_path="/images/test.png",
            caption="Test figure caption",
            page_number=2,
            bbox={"x": 100, "y": 200, "width": 300, "height": 400},
            image_format="png"
        )
        db_session.add(figure)
        
        # Create knowledge point
        knowledge = Knowledge(
            id=uuid4(),
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence.",
            entities=["machine learning", "artificial intelligence"],
            anchors={"page": 2, "chapter": "Test Chapter", "position": 100},
            confidence_score=0.95
        )
        db_session.add(knowledge)
        
        # Create cards
        qa_card = Card(
            id=uuid4(),
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence.",
            difficulty=2.0,
            card_metadata={}
        )
        db_session.add(qa_card)
        
        cloze_card = Card(
            id=uuid4(),
            knowledge_id=knowledge.id,
            card_type=CardType.CLOZE,
            front="{{c1::Machine learning}} is a subset of {{c2::artificial intelligence}}.",
            back="Machine learning is a subset of artificial intelligence.",
            difficulty=2.5,
            card_metadata={"blanks": ["machine learning", "artificial intelligence"]}
        )
        db_session.add(cloze_card)
        
        image_card = Card(
            id=uuid4(),
            knowledge_id=knowledge.id,
            card_type=CardType.IMAGE_HOTSPOT,
            front="/images/test.png",
            back="Test figure caption",
            difficulty=1.5,
            card_metadata={"hotspots": ["region1", "region2"]}
        )
        db_session.add(image_card)
        
        # Create SRS records
        srs1 = SRS(
            id=uuid4(),
            card_id=qa_card.id,
            ease_factor=2.5,
            interval=3,
            repetitions=2,
            due_date=datetime.utcnow() + timedelta(days=3),
            last_reviewed=datetime.utcnow() - timedelta(days=1),
            last_grade=4
        )
        db_session.add(srs1)
        
        srs2 = SRS(
            id=uuid4(),
            card_id=cloze_card.id,
            ease_factor=2.3,
            interval=1,
            repetitions=1,
            due_date=datetime.utcnow() + timedelta(days=1),
            last_reviewed=datetime.utcnow() - timedelta(hours=12),
            last_grade=3
        )
        db_session.add(srs2)
        
        db_session.commit()
        
        return {
            'document': document,
            'chapter': chapter,
            'figure': figure,
            'knowledge': knowledge,
            'cards': [qa_card, cloze_card, image_card],
            'srs_records': [srs1, srs2]
        }
    
    def test_export_anki_csv(self, export_service: ExportService, sample_data):
        """Test Anki CSV export"""
        document_id = sample_data['document'].id
        
        csv_content = export_service.export_anki_csv(document_id=document_id)
        
        # Parse CSV content
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have 3 cards
        assert len(rows) == 3
        
        # Check header
        expected_headers = ['Front', 'Back', 'Tags', 'Type', 'Deck', 'Difficulty', 'Source']
        assert reader.fieldnames == expected_headers
        
        # Check Q&A card
        qa_row = next(row for row in rows if row['Type'] == 'qa')
        assert qa_row['Front'] == "What is machine learning?"
        assert qa_row['Back'] == "Machine learning is a subset of artificial intelligence."
        assert 'type:definition' in qa_row['Tags']
        assert 'difficulty:medium' in qa_row['Tags']
        assert qa_row['Deck'] == "test_document.pdf::Test Chapter"
        assert qa_row['Difficulty'] == '2.0'
        assert 'Page 2' in qa_row['Source']
        
        # Check cloze card
        cloze_row = next(row for row in rows if row['Type'] == 'cloze')
        assert cloze_row['Front'] == "{{c1::Machine learning}} is a subset of {{c2::artificial intelligence}}."
        assert cloze_row['Back'] == "Machine learning is a subset of artificial intelligence."
        assert 'type:definition' in cloze_row['Tags']
        assert 'difficulty:hard' in cloze_row['Tags']
        
        # Check image card
        image_row = next(row for row in rows if row['Type'] == 'image_hotspot')
        assert '[IMAGE: /images/test.png]' in image_row['Front']
        assert 'Click on: region1, region2' in image_row['Front']
        assert image_row['Back'] == "Test figure caption"
        assert 'difficulty:easy' in image_row['Tags']
    
    def test_export_notion_csv(self, export_service: ExportService, sample_data):
        """Test Notion CSV export"""
        document_id = sample_data['document'].id
        
        csv_content = export_service.export_notion_csv(document_id=document_id)
        
        # Parse CSV content
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have 3 cards
        assert len(rows) == 3
        
        # Check header
        expected_headers = [
            'Question', 'Answer', 'Category', 'Difficulty', 'Source Document',
            'Chapter', 'Page', 'Knowledge Type', 'Entities', 'Created Date', 'Last Reviewed'
        ]
        assert reader.fieldnames == expected_headers
        
        # Check Q&A card
        qa_row = next(row for row in rows if 'What is machine learning?' in row['Question'])
        assert qa_row['Answer'] == "Machine learning is a subset of artificial intelligence."
        assert qa_row['Category'] == "Definition"
        assert qa_row['Difficulty'] == "Medium"
        assert qa_row['Source Document'] == "test_document.pdf"
        assert qa_row['Chapter'] == "Test Chapter"
        assert qa_row['Page'] == '2'
        assert qa_row['Knowledge Type'] == "definition"
        assert "machine learning, artificial intelligence" in qa_row['Entities']
        assert qa_row['Last Reviewed']  # Should have a value
        
        # Check cloze card
        cloze_row = next(row for row in rows if 'c1::Machine learning' in row['Question'])
        assert cloze_row['Category'] == "Cloze - Definition"
        assert cloze_row['Difficulty'] == "Hard"
        
        # Check image card
        image_row = next(row for row in rows if '[IMAGE:' in row['Question'])
        assert image_row['Category'] == "Image - Definition"
        assert image_row['Difficulty'] == "Easy"
    
    def test_export_jsonl_backup(self, export_service: ExportService, sample_data):
        """Test JSONL backup export"""
        document_id = sample_data['document'].id
        
        jsonl_content = export_service.export_jsonl_backup(document_id=document_id)
        
        # Parse JSONL content
        lines = jsonl_content.strip().split('\n')
        assert len(lines) == 1  # One document
        
        doc_data = json.loads(lines[0])
        
        # Check document structure
        assert 'document' in doc_data
        assert 'chapters' in doc_data
        assert 'export_metadata' in doc_data
        
        # Check document data
        document_data = doc_data['document']
        assert document_data['filename'] == "test_document.pdf"
        assert document_data['file_type'] == "pdf"
        assert document_data['status'] == "completed"
        
        # Check export metadata
        metadata = doc_data['export_metadata']
        assert metadata['total_chapters'] == 1
        assert metadata['total_figures'] == 1
        assert metadata['total_knowledge'] == 1
        assert metadata['total_cards'] == 3
        assert 'export_date' in metadata
        assert metadata['export_version'] == '1.0'
        
        # Check chapter data
        chapters = doc_data['chapters']
        assert len(chapters) == 1
        
        chapter_data = chapters[0]
        assert chapter_data['title'] == "Test Chapter"
        assert chapter_data['level'] == 1
        assert len(chapter_data['figures']) == 1
        assert len(chapter_data['knowledge_points']) == 1
        
        # Check figure data
        figure_data = chapter_data['figures'][0]
        assert figure_data['image_path'] == "/images/test.png"
        assert figure_data['caption'] == "Test figure caption"
        assert figure_data['page_number'] == 2
        assert figure_data['bbox'] == {"x": 100, "y": 200, "width": 300, "height": 400}
        
        # Check knowledge data
        knowledge_data = chapter_data['knowledge_points'][0]
        assert knowledge_data['kind'] == "definition"
        assert knowledge_data['text'] == "Machine learning is a subset of artificial intelligence."
        assert knowledge_data['entities'] == ["machine learning", "artificial intelligence"]
        assert knowledge_data['anchors'] == {"page": 2, "chapter": "Test Chapter", "position": 100}
        assert knowledge_data['confidence_score'] == 0.95
        assert len(knowledge_data['cards']) == 3
        
        # Check card data
        cards = knowledge_data['cards']
        card_types = [card['card_type'] for card in cards]
        assert 'qa' in card_types
        assert 'cloze' in card_types
        assert 'image_hotspot' in card_types
        
        # Check SRS data
        qa_card = next(card for card in cards if card['card_type'] == 'qa')
        assert len(qa_card['srs_records']) == 1
        
        srs_data = qa_card['srs_records'][0]
        assert srs_data['ease_factor'] == 2.5
        assert srs_data['interval'] == 3
        assert srs_data['repetitions'] == 2
        assert srs_data['last_grade'] == 4
    
    def test_import_jsonl_backup(self, export_service: ExportService, sample_data, db_session: Session):
        """Test JSONL backup import"""
        # First export the data
        document_id = sample_data['document'].id
        jsonl_content = export_service.export_jsonl_backup(document_id=document_id)
        
        # Clear the database
        db_session.query(SRS).delete()
        db_session.query(Card).delete()
        db_session.query(Knowledge).delete()
        db_session.query(Figure).delete()
        db_session.query(Chapter).delete()
        db_session.query(Document).delete()
        db_session.commit()
        
        # Import the data back
        result = export_service.import_jsonl_backup(jsonl_content)
        
        # Check import result
        assert result['imported_documents'] == 1
        assert result['imported_chapters'] == 1
        assert result['imported_figures'] == 1
        assert result['imported_knowledge'] == 1
        assert result['imported_cards'] == 3
        assert len(result['errors']) == 0
        
        # Verify data was imported correctly
        imported_doc = db_session.query(Document).filter(Document.id == document_id).first()
        assert imported_doc is not None
        assert imported_doc.filename == "test_document.pdf"
        
        imported_chapters = db_session.query(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_chapters) == 1
        assert imported_chapters[0].title == "Test Chapter"
        
        imported_figures = db_session.query(Figure).join(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_figures) == 1
        assert imported_figures[0].caption == "Test figure caption"
        
        imported_knowledge = db_session.query(Knowledge).join(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_knowledge) == 1
        assert imported_knowledge[0].text == "Machine learning is a subset of artificial intelligence."
        
        imported_cards = db_session.query(Card).join(Knowledge).join(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_cards) == 3
        
        # Check SRS records were imported
        imported_srs = db_session.query(SRS).join(Card).join(Knowledge).join(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_srs) == 2
    
    def test_export_with_filters(self, export_service: ExportService, sample_data):
        """Test export with chapter filters"""
        chapter_id = sample_data['chapter'].id
        
        csv_content = export_service.export_anki_csv(chapter_ids=[chapter_id])
        
        # Parse CSV content
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have 3 cards from the filtered chapter
        assert len(rows) == 3
        
        # All cards should be from the same chapter
        for row in rows:
            assert "Test Chapter" in row['Deck']
    
    def test_export_empty_data(self, export_service: ExportService):
        """Test export with no data"""
        # Export with non-existent document ID
        fake_id = uuid4()
        
        csv_content = export_service.export_anki_csv(document_id=fake_id)
        
        # Should only have header
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) == 0
    
    def test_difficulty_conversion(self, export_service: ExportService):
        """Test difficulty score conversion"""
        # Test difficulty to tag conversion
        assert export_service._difficulty_to_tag(1.0) == "easy"
        assert export_service._difficulty_to_tag(1.5) == "easy"
        assert export_service._difficulty_to_tag(2.0) == "medium"
        assert export_service._difficulty_to_tag(2.5) == "medium"
        assert export_service._difficulty_to_tag(3.0) == "hard"
        
        # Test difficulty to label conversion
        assert export_service._difficulty_to_label(1.0) == "Easy"
        assert export_service._difficulty_to_label(2.0) == "Medium"
        assert export_service._difficulty_to_label(3.0) == "Hard"
    
    def test_card_content_formatting(self, export_service: ExportService, sample_data):
        """Test card content formatting for different types"""
        cards = sample_data['cards']
        
        # Test Q&A card
        qa_card = next(card for card in cards if card.card_type == CardType.QA)
        front, back = export_service._format_card_content(qa_card)
        assert front == "What is machine learning?"
        assert back == "Machine learning is a subset of artificial intelligence."
        
        # Test cloze card
        cloze_card = next(card for card in cards if card.card_type == CardType.CLOZE)
        front, back = export_service._format_card_content(cloze_card)
        assert front == "{{c1::Machine learning}} is a subset of {{c2::artificial intelligence}}."
        assert back == "Machine learning is a subset of artificial intelligence."
        
        # Test image card
        image_card = next(card for card in cards if card.card_type == CardType.IMAGE_HOTSPOT)
        front, back = export_service._format_card_content(image_card)
        assert "[IMAGE: /images/test.png]" in front
        assert "Click on: region1, region2" in front
        assert back == "Test figure caption"
    
    def test_import_error_handling(self, export_service: ExportService):
        """Test import error handling"""
        # Test invalid JSON
        invalid_jsonl = "invalid json content\n{\"valid\": \"json\"}"
        
        result = export_service.import_jsonl_backup(invalid_jsonl)
        
        assert result['imported_documents'] == 0
        assert len(result['errors']) > 0
        assert "Invalid JSON" in result['errors'][0]
    
    def test_get_card_category(self, export_service: ExportService, sample_data):
        """Test card category generation for Notion export"""
        cards = sample_data['cards']
        
        # Test Q&A card
        qa_card = next(card for card in cards if card.card_type == CardType.QA)
        category = export_service._get_card_category(qa_card)
        assert category == "Definition"
        
        # Test cloze card
        cloze_card = next(card for card in cards if card.card_type == CardType.CLOZE)
        category = export_service._get_card_category(cloze_card)
        assert category == "Cloze - Definition"
        
        # Test image card
        image_card = next(card for card in cards if card.card_type == CardType.IMAGE_HOTSPOT)
        category = export_service._get_card_category(image_card)
        assert category == "Image - Definition"