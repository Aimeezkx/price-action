"""
Integration test for SRS (Spaced Repetition System) functionality
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db, engine
from app.models.base import BaseModel
from app.models.document import Document, Chapter
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.learning import Card, CardType, SRS
from app.services.srs_service import SRSService


def test_srs_integration():
    """Test complete SRS workflow integration"""
    
    # Create database tables
    BaseModel.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # 1. Create test data hierarchy
        print("Creating test data...")
        
        # Create document
        document = Document(
            filename="test_srs_doc.pdf",
            file_type="pdf",
            status="completed"
        )
        db.add(document)
        db.commit()
        
        # Create chapter
        chapter = Chapter(
            document_id=document.id,
            title="Test Chapter",
            level=1,
            order_index=1,
            page_start=1,
            page_end=10
        )
        db.add(chapter)
        db.commit()
        
        # Create knowledge point
        knowledge = Knowledge(
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            entities=["machine learning", "artificial intelligence", "algorithms"],
            anchors={"page": 1, "chapter": "Test Chapter", "position": 0}
        )
        db.add(knowledge)
        db.commit()
        
        # Create flashcard
        card = Card(
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front="What is machine learning?",
            back="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            difficulty=1.5
        )
        db.add(card)
        db.commit()
        
        print(f"Created card: {card.id}")
        
        # 2. Test SRS service
        srs_service = SRSService(db)
        
        # Create SRS record
        print("Creating SRS record...")
        srs = srs_service.create_srs_record(str(card.id), "test-user")
        
        assert srs.card_id == card.id
        assert srs.user_id == "test-user"
        assert srs.ease_factor == 2.5
        assert srs.interval == 1
        assert srs.repetitions == 0
        print(f"✓ SRS record created: {srs.id}")
        
        # 3. Test card grading workflow
        print("\nTesting card grading workflow...")
        
        # First review - good performance
        print("First review (grade 4)...")
        updated_srs = srs_service.grade_card(str(srs.id), 4)
        
        assert updated_srs.repetitions == 1
        assert updated_srs.interval == 1  # First repetition stays at 1 day
        assert updated_srs.last_grade == 4
        assert updated_srs.last_reviewed is not None
        print(f"✓ After first review: repetitions={updated_srs.repetitions}, interval={updated_srs.interval}")
        
        # Second review - excellent performance
        print("Second review (grade 5)...")
        updated_srs = srs_service.grade_card(str(srs.id), 5)
        
        assert updated_srs.repetitions == 2
        assert updated_srs.interval == 6  # Second repetition goes to 6 days
        assert updated_srs.last_grade == 5
        print(f"✓ After second review: repetitions={updated_srs.repetitions}, interval={updated_srs.interval}")
        
        # Third review - good performance (mature card)
        print("Third review (grade 4)...")
        updated_srs = srs_service.grade_card(str(srs.id), 4)
        
        assert updated_srs.repetitions == 3
        # Should be interval * ease_factor
        expected_interval = int(6 * updated_srs.ease_factor)
        assert updated_srs.interval == expected_interval
        assert updated_srs.last_grade == 4
        print(f"✓ After third review: repetitions={updated_srs.repetitions}, interval={updated_srs.interval}")
        
        # Fourth review - poor performance (should reset)
        print("Fourth review (grade 2 - poor performance)...")
        initial_ease = updated_srs.ease_factor
        updated_srs = srs_service.grade_card(str(srs.id), 2)
        
        assert updated_srs.repetitions == 0  # Reset
        assert updated_srs.interval == 1     # Reset
        assert updated_srs.ease_factor < initial_ease  # Decreased
        assert updated_srs.last_grade == 2
        print(f"✓ After poor performance: repetitions={updated_srs.repetitions}, interval={updated_srs.interval}, ease_factor={updated_srs.ease_factor}")
        
        # 4. Test due card retrieval
        print("\nTesting due card retrieval...")
        
        # Make card overdue
        updated_srs.due_date = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        
        due_cards = srs_service.get_due_cards("test-user")
        assert len(due_cards) == 1
        assert due_cards[0][0].id == updated_srs.id
        assert due_cards[0][1].id == card.id
        print(f"✓ Found {len(due_cards)} due cards")
        
        overdue_cards = srs_service.get_overdue_cards("test-user")
        assert len(overdue_cards) == 1
        print(f"✓ Found {len(overdue_cards)} overdue cards")
        
        # 5. Test statistics
        print("\nTesting statistics...")
        stats = srs_service.get_review_statistics("test-user")
        
        assert stats['total_cards'] == 1
        assert stats['overdue'] == 1
        assert stats['learning'] == 1  # repetitions < 2
        assert stats['mature'] == 0
        print(f"✓ Statistics: {stats}")
        
        # 6. Test card reset
        print("\nTesting card reset...")
        reset_srs = srs_service.reset_card_progress(str(updated_srs.id))
        
        assert reset_srs.repetitions == 0
        assert reset_srs.interval == 1
        assert reset_srs.ease_factor == 2.5
        assert reset_srs.last_reviewed is None
        assert reset_srs.last_grade is None
        print("✓ Card progress reset successfully")
        
        # 7. Test multiple cards scenario
        print("\nTesting multiple cards scenario...")
        
        # Create additional cards
        for i in range(3):
            additional_card = Card(
                knowledge_id=knowledge.id,
                card_type=CardType.CLOZE,
                front=f"Test cloze card {i+1}",
                back=f"Answer {i+1}",
                difficulty=1.0 + i * 0.3
            )
            db.add(additional_card)
            db.commit()
            
            # Create SRS record
            additional_srs = srs_service.create_srs_record(str(additional_card.id), "test-user")
            
            # Set different due dates
            if i == 0:
                additional_srs.due_date = datetime.utcnow() - timedelta(days=2)  # Very overdue
            elif i == 1:
                additional_srs.due_date = datetime.utcnow()  # Due now
            else:
                additional_srs.due_date = datetime.utcnow() + timedelta(days=1)  # Due tomorrow
            
            db.commit()
        
        # Test due cards with multiple cards
        all_due_cards = srs_service.get_due_cards("test-user")
        assert len(all_due_cards) >= 3  # At least 3 due cards
        print(f"✓ Found {len(all_due_cards)} total due cards")
        
        # Test with limit
        limited_due_cards = srs_service.get_due_cards("test-user", limit=2)
        assert len(limited_due_cards) == 2
        print(f"✓ Limited query returned {len(limited_due_cards)} cards")
        
        # Test updated statistics
        final_stats = srs_service.get_review_statistics("test-user")
        assert final_stats['total_cards'] >= 4
        print(f"✓ Final statistics: {final_stats}")
        
        print("\n🎉 All SRS integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_srs_integration()