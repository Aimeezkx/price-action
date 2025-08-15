#!/usr/bin/env python3
"""
Test script for Task 18: Core FastAPI endpoints
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from app.core.database import get_db, get_async_db
from app.models.base import Base
from app.models.document import Document, Chapter, Figure, ProcessingStatus
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, CardType, SRS

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_task18.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_async_db():
    """Override async database dependency for testing"""
    return override_get_db()


# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_async_db] = override_get_db

client = TestClient(app)


def setup_test_data():
    """Create test data"""
    db = TestingSessionLocal()
    
    try:
        # Create test document
        document = Document(
            filename="test_document.pdf",
            file_type="pdf",
            file_path="/tmp/test_document.pdf",
            file_size=1024,
            status=ProcessingStatus.COMPLETED
        )
        db.add(document)
        db.flush()
        
        # Create test chapter
        chapter = Chapter(
            document_id=document.id,
            title="Test Chapter",
            level=1,
            order_index=1,
            page_start=1,
            page_end=10,
            content="This is test chapter content."
        )
        db.add(chapter)
        db.flush()
        
        # Create test figure
        figure = Figure(
            chapter_id=chapter.id,
            image_path="/tmp/test_image.png",
            caption="Test figure caption",
            page_number=5,
            bbox={"x": 100, "y": 100, "width": 200, "height": 150}
        )
        db.add(figure)
        db.flush()
        
        # Create test knowledge point
        knowledge = Knowledge(
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            entities=["machine learning", "artificial intelligence", "algorithms"],
            anchors={"page": 5, "chapter": 1, "position": 100},
            confidence_score=0.9
        )
        db.add(knowledge)
        db.flush()
        
        # Create test card
        card = Card(
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            difficulty=2.5,
            card_metadata={"knowledge_type": "definition"}
        )
        db.add(card)
        db.flush()
        
        # Create SRS record
        srs = SRS(
            card_id=card.id,
            user_id=None
        )
        db.add(srs)
        
        db.commit()
        
        return {
            "document_id": str(document.id),
            "chapter_id": str(chapter.id),
            "figure_id": str(figure.id),
            "knowledge_id": str(knowledge.id),
            "card_id": str(card.id),
            "srs_id": str(srs.id)
        }
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def test_document_endpoints():
    """Test document management endpoints"""
    print("Testing document endpoints...")
    
    test_data = setup_test_data()
    document_id = test_data["document_id"]
    
    # Test GET /doc/{id}
    response = client.get(f"/api/doc/{document_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_document.pdf"
    assert data["status"] == "completed"
    print("✓ GET /doc/{id} works")
    
    # Test GET /doc/{id}/toc
    response = client.get(f"/api/doc/{document_id}/toc")
    assert response.status_code == 200
    data = response.json()
    assert data["total_chapters"] == 1
    assert len(data["chapters"]) == 1
    assert data["chapters"][0]["title"] == "Test Chapter"
    print("✓ GET /doc/{id}/toc works")


def test_chapter_endpoints():
    """Test chapter and content endpoints"""
    print("Testing chapter endpoints...")
    
    test_data = setup_test_data()
    chapter_id = test_data["chapter_id"]
    
    # Test GET /chapter/{id}/fig
    response = client.get(f"/api/chapter/{chapter_id}/fig")
    assert response.status_code == 200
    data = response.json()
    assert data["total_figures"] == 1
    assert len(data["figures"]) == 1
    assert data["figures"][0]["caption"] == "Test figure caption"
    print("✓ GET /chapter/{id}/fig works")
    
    # Test GET /chapter/{id}/k
    response = client.get(f"/api/chapter/{chapter_id}/k")
    assert response.status_code == 200
    data = response.json()
    assert data["total_knowledge_points"] == 1
    assert len(data["knowledge_points"]) == 1
    assert data["knowledge_points"][0]["kind"] == "definition"
    print("✓ GET /chapter/{id}/k works")


def test_card_endpoints():
    """Test card management endpoints"""
    print("Testing card endpoints...")
    
    test_data = setup_test_data()
    chapter_id = test_data["chapter_id"]
    
    # Test GET /cards
    response = client.get("/api/cards")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cards"] >= 1
    assert len(data["cards"]) >= 1
    print("✓ GET /cards works")
    
    # Test GET /cards with filters
    response = client.get(f"/api/cards?chapter_id={chapter_id}&card_type=qa")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cards"] >= 1
    print("✓ GET /cards with filters works")
    
    # Test POST /card/gen
    response = client.post(f"/api/card/gen?chapter_id={chapter_id}&max_cards=5")
    assert response.status_code == 200
    data = response.json()
    assert "generated_cards" in data
    print("✓ POST /card/gen works")


def test_review_endpoints():
    """Test review endpoints"""
    print("Testing review endpoints...")
    
    # Test GET /review/today
    response = client.get("/reviews/review/today")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print("✓ GET /review/today works")


def run_all_tests():
    """Run all endpoint tests"""
    print("Starting Task 18 endpoint tests...\n")
    
    try:
        test_document_endpoints()
        print()
        
        test_chapter_endpoints()
        print()
        
        test_card_endpoints()
        print()
        
        test_review_endpoints()
        print()
        
        print("✅ All Task 18 endpoints are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test database
        if os.path.exists("test_task18.db"):
            os.remove("test_task18.db")


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)