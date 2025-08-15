"""
Integration tests for export functionality
"""

import pytest
import json
import csv
import io
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.core.database import get_db
from app.models.document import Document, Chapter, Figure, ProcessingStatus
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, SRS, CardType


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_data(db_session: Session):
    """Create test data for export integration tests"""
    # Create document
    document = Document(
        id=uuid4(),
        filename="integration_test.pdf",
        file_type="pdf",
        file_path="/test/integration.pdf",
        file_size=2048,
        status=ProcessingStatus.COMPLETED,
        doc_metadata={"pages": 15}
    )
    db_session.add(document)
    
    # Create chapters
    chapter1 = Chapter(
        id=uuid4(),
        document_id=document.id,
        title="Introduction",
        level=1,
        order_index=1,
        page_start=1,
        page_end=3,
        content="Introduction content"
    )
    db_session.add(chapter1)
    
    chapter2 = Chapter(
        id=uuid4(),
        document_id=document.id,
        title="Advanced Topics",
        level=1,
        order_index=2,
        page_start=4,
        page_end=10,
        content="Advanced content"
    )
    db_session.add(chapter2)
    
    # Create figures
    figure1 = Figure(
        id=uuid4(),
        chapter_id=chapter1.id,
        image_path="/images/intro_diagram.png",
        caption="Introduction diagram",
        page_number=2,
        bbox={"x": 50, "y": 100, "width": 400, "height": 300}
    )
    db_session.add(figure1)
    
    # Create knowledge points
    knowledge1 = Knowledge(
        id=uuid4(),
        chapter_id=chapter1.id,
        kind=KnowledgeType.DEFINITION,
        text="Artificial Intelligence (AI) is the simulation of human intelligence in machines.",
        entities=["artificial intelligence", "AI", "machines"],
        anchors={"page": 2, "chapter": "Introduction", "position": 150},
        confidence_score=0.92
    )
    db_session.add(knowledge1)
    
    knowledge2 = Knowledge(
        id=uuid4(),
        chapter_id=chapter2.id,
        kind=KnowledgeType.THEOREM,
        text="The Central Limit Theorem states that the distribution of sample means approaches a normal distribution.",
        entities=["Central Limit Theorem", "normal distribution", "sample means"],
        anchors={"page": 6, "chapter": "Advanced Topics", "position": 200},
        confidence_score=0.88
    )
    db_session.add(knowledge2)
    
    # Create cards
    cards_data = [
        {
            'knowledge': knowledge1,
            'type': CardType.QA,
            'front': "What is Artificial Intelligence?",
            'back': "Artificial Intelligence (AI) is the simulation of human intelligence in machines.",
            'difficulty': 1.8,
            'metadata': {}
        },
        {
            'knowledge': knowledge1,
            'type': CardType.CLOZE,
            'front': "{{c1::Artificial Intelligence}} ({{c2::AI}}) is the simulation of human intelligence in {{c3::machines}}.",
            'back': "Artificial Intelligence (AI) is the simulation of human intelligence in machines.",
            'difficulty': 2.2,
            'metadata': {'blanks': ['Artificial Intelligence', 'AI', 'machines']}
        },
        {
            'knowledge': knowledge2,
            'type': CardType.QA,
            'front': "What does the Central Limit Theorem state?",
            'back': "The Central Limit Theorem states that the distribution of sample means approaches a normal distribution.",
            'difficulty': 3.1,
            'metadata': {}
        },
        {
            'knowledge': knowledge1,
            'type': CardType.IMAGE_HOTSPOT,
            'front': "/images/intro_diagram.png",
            'back': "Introduction diagram",
            'difficulty': 1.5,
            'metadata': {'hotspots': ['ai_section', 'machine_section']}
        }
    ]
    
    cards = []
    for card_data in cards_data:
        card = Card(
            id=uuid4(),
            knowledge_id=card_data['knowledge'].id,
            card_type=card_data['type'],
            front=card_data['front'],
            back=card_data['back'],
            difficulty=card_data['difficulty'],
            card_metadata=card_data['metadata']
        )
        db_session.add(card)
        cards.append(card)
    
    # Create SRS records
    for i, card in enumerate(cards[:2]):  # Only for first 2 cards
        srs = SRS(
            id=uuid4(),
            card_id=card.id,
            ease_factor=2.5 - (i * 0.1),
            interval=i + 1,
            repetitions=i,
            due_date=datetime.utcnow() + timedelta(days=i + 1),
            last_reviewed=datetime.utcnow() - timedelta(hours=12 * (i + 1)),
            last_grade=4 - i
        )
        db_session.add(srs)
    
    db_session.commit()
    
    return {
        'document': document,
        'chapters': [chapter1, chapter2],
        'figures': [figure1],
        'knowledge': [knowledge1, knowledge2],
        'cards': cards
    }


class TestExportIntegration:
    """Integration tests for export functionality"""
    
    def test_export_anki_csv_endpoint(self, client: TestClient, test_data):
        """Test Anki CSV export endpoint"""
        document_id = test_data['document'].id
        
        response = client.get(f"/export/csv/anki?document_id={document_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert f"anki_export_{document_id}.csv" in response.headers["content-disposition"]
        
        # Parse CSV content
        csv_content = response.text
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have 4 cards
        assert len(rows) == 4
        
        # Check headers
        expected_headers = ['Front', 'Back', 'Tags', 'Type', 'Deck', 'Difficulty', 'Source']
        assert reader.fieldnames == expected_headers
        
        # Verify card data
        ai_qa_card = next(row for row in rows if "What is Artificial Intelligence?" in row['Front'])
        assert ai_qa_card['Back'] == "Artificial Intelligence (AI) is the simulation of human intelligence in machines."
        assert 'type:definition' in ai_qa_card['Tags']
        assert ai_qa_card['Deck'] == "integration_test.pdf::Introduction"
        assert ai_qa_card['Difficulty'] == '1.8'
        assert 'Page 2' in ai_qa_card['Source']
    
    def test_export_notion_csv_endpoint(self, client: TestClient, test_data):
        """Test Notion CSV export endpoint"""
        document_id = test_data['document'].id
        
        response = client.get(f"/export/csv/notion?document_id={document_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert f"notion_export_{document_id}.csv" in response.headers["content-disposition"]
        
        # Parse CSV content
        csv_content = response.text
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have 4 cards
        assert len(rows) == 4
        
        # Check headers
        expected_headers = [
            'Question', 'Answer', 'Category', 'Difficulty', 'Source Document',
            'Chapter', 'Page', 'Knowledge Type', 'Entities', 'Created Date', 'Last Reviewed'
        ]
        assert reader.fieldnames == expected_headers
        
        # Verify card data
        ai_qa_card = next(row for row in rows if "What is Artificial Intelligence?" in row['Question'])
        assert ai_qa_card['Answer'] == "Artificial Intelligence (AI) is the simulation of human intelligence in machines."
        assert ai_qa_card['Category'] == "Definition"
        assert ai_qa_card['Difficulty'] == "Medium"
        assert ai_qa_card['Source Document'] == "integration_test.pdf"
        assert ai_qa_card['Chapter'] == "Introduction"
        assert ai_qa_card['Page'] == '2'
        assert ai_qa_card['Knowledge Type'] == "definition"
        assert "artificial intelligence" in ai_qa_card['Entities']
        assert ai_qa_card['Last Reviewed']  # Should have a timestamp
    
    def test_export_jsonl_backup_endpoint(self, client: TestClient, test_data):
        """Test JSONL backup export endpoint"""
        document_id = test_data['document'].id
        
        response = client.get(f"/export/jsonl/backup?document_id={document_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/jsonl; charset=utf-8"
        assert f"backup_{document_id}.jsonl" in response.headers["content-disposition"]
        
        # Parse JSONL content
        jsonl_content = response.text
        lines = jsonl_content.strip().split('\n')
        assert len(lines) == 1  # One document
        
        doc_data = json.loads(lines[0])
        
        # Verify structure
        assert 'document' in doc_data
        assert 'chapters' in doc_data
        assert 'export_metadata' in doc_data
        
        # Check document data
        document_data = doc_data['document']
        assert document_data['filename'] == "integration_test.pdf"
        assert document_data['file_type'] == "pdf"
        
        # Check metadata
        metadata = doc_data['export_metadata']
        assert metadata['total_chapters'] == 2
        assert metadata['total_figures'] == 1
        assert metadata['total_knowledge'] == 2
        assert metadata['total_cards'] == 4
        
        # Check chapters
        chapters = doc_data['chapters']
        assert len(chapters) == 2
        
        intro_chapter = next(ch for ch in chapters if ch['title'] == "Introduction")
        assert len(intro_chapter['knowledge_points']) == 1
        assert len(intro_chapter['figures']) == 1
        
        advanced_chapter = next(ch for ch in chapters if ch['title'] == "Advanced Topics")
        assert len(advanced_chapter['knowledge_points']) == 1
        assert len(advanced_chapter['figures']) == 0
        
        # Check knowledge points have cards
        for chapter in chapters:
            for knowledge in chapter['knowledge_points']:
                assert len(knowledge['cards']) > 0
                for card in knowledge['cards']:
                    assert 'id' in card
                    assert 'card_type' in card
                    assert 'front' in card
                    assert 'back' in card
    
    def test_import_jsonl_backup_endpoint(self, client: TestClient, test_data, db_session: Session):
        """Test JSONL backup import endpoint"""
        # First export the data
        document_id = test_data['document'].id
        export_response = client.get(f"/export/jsonl/backup?document_id={document_id}")
        jsonl_content = export_response.text
        
        # Clear the test data
        db_session.query(SRS).delete()
        db_session.query(Card).delete()
        db_session.query(Knowledge).delete()
        db_session.query(Figure).delete()
        db_session.query(Chapter).delete()
        db_session.query(Document).delete()
        db_session.commit()
        
        # Create file-like object for upload
        files = {
            'file': ('backup_test.jsonl', io.BytesIO(jsonl_content.encode('utf-8')), 'application/jsonl')
        }
        
        # Import the data
        response = client.post("/export/jsonl/import", files=files)
        
        assert response.status_code == 200
        
        result = response.json()
        assert result['message'] == "Import completed"
        
        summary = result['summary']
        assert summary['imported_documents'] == 1
        assert summary['imported_chapters'] == 2
        assert summary['imported_figures'] == 1
        assert summary['imported_knowledge'] == 2
        assert summary['imported_cards'] == 4
        assert len(summary['errors']) == 0
        
        # Verify data was imported
        imported_doc = db_session.query(Document).filter(Document.id == document_id).first()
        assert imported_doc is not None
        assert imported_doc.filename == "integration_test.pdf"
        
        imported_chapters = db_session.query(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_chapters) == 2
        
        imported_cards = db_session.query(Card).join(Knowledge).join(Chapter).filter(Chapter.document_id == document_id).all()
        assert len(imported_cards) == 4
    
    def test_export_with_chapter_filter(self, client: TestClient, test_data):
        """Test export with chapter ID filter"""
        chapter_id = test_data['chapters'][0].id  # Introduction chapter
        
        response = client.get(f"/export/csv/anki?chapter_ids={chapter_id}")
        
        assert response.status_code == 200
        
        # Parse CSV content
        csv_content = response.text
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have 3 cards from Introduction chapter only
        assert len(rows) == 3
        
        # All cards should be from Introduction chapter
        for row in rows:
            assert "Introduction" in row['Deck']
    
    def test_export_all_documents(self, client: TestClient, test_data):
        """Test export without document filter (all documents)"""
        response = client.get("/export/csv/anki")
        
        assert response.status_code == 200
        assert "anki_export_all.csv" in response.headers["content-disposition"]
        
        # Should contain cards from all documents
        csv_content = response.text
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Should have at least the 4 cards from our test data
        assert len(rows) >= 4
    
    def test_get_export_formats_endpoint(self, client: TestClient):
        """Test export formats information endpoint"""
        response = client.get("/export/formats")
        
        assert response.status_code == 200
        
        data = response.json()
        assert 'formats' in data
        assert 'import_formats' in data
        
        formats = data['formats']
        assert len(formats) == 3
        
        format_names = [fmt['name'] for fmt in formats]
        assert 'anki_csv' in format_names
        assert 'notion_csv' in format_names
        assert 'jsonl_backup' in format_names
        
        # Check format details
        anki_format = next(fmt for fmt in formats if fmt['name'] == 'anki_csv')
        assert anki_format['endpoint'] == '/export/csv/anki'
        assert anki_format['file_extension'] == '.csv'
        assert 'Front' in anki_format['fields']
        
        import_formats = data['import_formats']
        assert len(import_formats) == 1
        assert import_formats[0]['name'] == 'jsonl_backup'
    
    def test_import_invalid_file_type(self, client: TestClient):
        """Test import with invalid file type"""
        files = {
            'file': ('test.txt', io.BytesIO(b'invalid content'), 'text/plain')
        }
        
        response = client.post("/export/jsonl/import", files=files)
        
        assert response.status_code == 400
        assert "File must be a .jsonl file" in response.json()['detail']
    
    def test_import_invalid_json(self, client: TestClient):
        """Test import with invalid JSON content"""
        invalid_content = "invalid json content\n{broken json}"
        
        files = {
            'file': ('test.jsonl', io.BytesIO(invalid_content.encode('utf-8')), 'application/jsonl')
        }
        
        response = client.post("/export/jsonl/import", files=files)
        
        assert response.status_code == 200  # Import completes but with errors
        
        result = response.json()
        summary = result['summary']
        assert summary['imported_documents'] == 0
        assert len(summary['errors']) > 0
        assert "Invalid JSON" in summary['errors'][0]
    
    def test_export_nonexistent_document(self, client: TestClient):
        """Test export with non-existent document ID"""
        fake_id = uuid4()
        
        response = client.get(f"/export/csv/anki?document_id={fake_id}")
        
        assert response.status_code == 200
        
        # Should return empty CSV (only headers)
        csv_content = response.text
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])