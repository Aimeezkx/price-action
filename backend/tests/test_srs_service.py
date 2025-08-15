"""
Tests for SRS (Spaced Repetition System) service
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.srs_service import SRSService
from app.models.learning import SRS, Card, CardType
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Document, Chapter


class TestSRSService:
    """Test SRS service functionality"""
    
    def test_create_srs_record(self, db_session: Session, sample_card):
        """Test creating a new SRS record"""
        service = SRSService(db_session)
        
        srs = service.create_srs_record(str(sample_card.id))
        
        assert srs.card_id == sample_card.id
        assert srs.ease_factor == 2.5
        assert srs.interval == 1
        assert srs.repetitions == 0
        assert srs.last_reviewed is None
        assert srs.last_grade is None
        assert srs.due_date is not None
    
    def test_create_srs_record_with_user(self, db_session: Session, sample_card):
        """Test creating SRS record with user ID"""
        service = SRSService(db_session)
        user_id = "test-user-123"
        
        srs = service.create_srs_record(str(sample_card.id), user_id)
        
        assert srs.user_id == user_id
        assert srs.card_id == sample_card.id
    
    def test_grade_card_invalid_grade(self, db_session: Session, sample_srs):
        """Test grading with invalid grade values"""
        service = SRSService(db_session)
        
        # Test grades outside 0-5 range
        with pytest.raises(ValueError, match="Grade must be between 0 and 5"):
            service.grade_card(str(sample_srs.id), -1)
        
        with pytest.raises(ValueError, match="Grade must be between 0 and 5"):
            service.grade_card(str(sample_srs.id), 6)
    
    def test_grade_card_nonexistent(self, db_session: Session):
        """Test grading non-existent SRS record"""
        service = SRSService(db_session)
        
        with pytest.raises(ValueError, match="SRS record not found"):
            service.grade_card("nonexistent-id", 3)
    
    def test_grade_card_poor_performance(self, db_session: Session, sample_srs):
        """Test grading with poor performance (grade < 3)"""
        service = SRSService(db_session)
        
        # Set up initial state
        sample_srs.repetitions = 5
        sample_srs.interval = 30
        sample_srs.ease_factor = 2.8
        db_session.commit()
        
        # Grade with poor performance
        updated_srs = service.grade_card(str(sample_srs.id), 2)
        
        # Should reset progress
        assert updated_srs.repetitions == 0
        assert updated_srs.interval == 1
        assert updated_srs.ease_factor < 2.8  # Should decrease
        assert updated_srs.last_grade == 2
        assert updated_srs.last_reviewed is not None
    
    def test_grade_card_first_repetition(self, db_session: Session, sample_srs):
        """Test grading first repetition (good performance)"""
        service = SRSService(db_session)
        
        # Initial state (new card)
        assert sample_srs.repetitions == 0
        assert sample_srs.interval == 1
        
        # Grade with good performance
        updated_srs = service.grade_card(str(sample_srs.id), 4)
        
        assert updated_srs.repetitions == 1
        assert updated_srs.interval == 1  # First repetition stays at 1 day
        assert updated_srs.last_grade == 4
        assert updated_srs.due_date > datetime.utcnow()
    
    def test_grade_card_second_repetition(self, db_session: Session, sample_srs):
        """Test grading second repetition"""
        service = SRSService(db_session)
        
        # Set up for second repetition
        sample_srs.repetitions = 1
        sample_srs.interval = 1
        db_session.commit()
        
        # Grade with good performance
        updated_srs = service.grade_card(str(sample_srs.id), 4)
        
        assert updated_srs.repetitions == 2
        assert updated_srs.interval == 6  # Second repetition goes to 6 days
        assert updated_srs.last_grade == 4
    
    def test_grade_card_mature_repetition(self, db_session: Session, sample_srs):
        """Test grading mature card (repetitions > 2)"""
        service = SRSService(db_session)
        
        # Set up mature card
        sample_srs.repetitions = 3
        sample_srs.interval = 6
        sample_srs.ease_factor = 2.5
        db_session.commit()
        
        # Grade with good performance
        updated_srs = service.grade_card(str(sample_srs.id), 4)
        
        assert updated_srs.repetitions == 4
        # Interval should be previous_interval * ease_factor
        expected_interval = int(6 * 2.5)
        assert updated_srs.interval == expected_interval
        assert updated_srs.last_grade == 4
    
    def test_grade_card_perfect_performance(self, db_session: Session, sample_srs):
        """Test grading with perfect performance (grade 5)"""
        service = SRSService(db_session)
        
        initial_ease = sample_srs.ease_factor
        
        # Grade with perfect performance
        updated_srs = service.grade_card(str(sample_srs.id), 5)
        
        # Ease factor should increase or stay same for grade 5
        assert updated_srs.ease_factor >= initial_ease
        assert updated_srs.last_grade == 5
    
    def test_ease_factor_minimum(self, db_session: Session, sample_srs):
        """Test that ease factor doesn't go below 1.3"""
        service = SRSService(db_session)
        
        # Set low ease factor
        sample_srs.ease_factor = 1.4
        db_session.commit()
        
        # Grade with very poor performance multiple times
        for _ in range(5):
            service.grade_card(str(sample_srs.id), 0)
            db_session.refresh(sample_srs)
        
        assert sample_srs.ease_factor >= 1.3
    
    def test_get_due_cards(self, db_session: Session, sample_cards_with_srs):
        """Test getting cards due for review"""
        service = SRSService(db_session)
        
        # Set up cards with different due dates
        srs_records = db_session.query(SRS).all()
        
        # Make some cards overdue
        srs_records[0].due_date = datetime.utcnow() - timedelta(days=1)
        srs_records[1].due_date = datetime.utcnow() - timedelta(hours=1)
        
        # Make some cards due in future
        srs_records[2].due_date = datetime.utcnow() + timedelta(days=1)
        
        db_session.commit()
        
        # Get due cards
        due_cards = service.get_due_cards()
        
        # Should return overdue and due cards, not future cards
        assert len(due_cards) >= 2
        
        # Check that results are (SRS, Card) tuples
        for srs, card in due_cards:
            assert isinstance(srs, SRS)
            assert isinstance(card, Card)
            assert srs.due_date <= datetime.utcnow()
    
    def test_get_due_cards_with_limit(self, db_session: Session, sample_cards_with_srs):
        """Test getting due cards with limit"""
        service = SRSService(db_session)
        
        # Make all cards overdue
        for srs in db_session.query(SRS).all():
            srs.due_date = datetime.utcnow() - timedelta(days=1)
        db_session.commit()
        
        # Get limited number of due cards
        due_cards = service.get_due_cards(limit=2)
        
        assert len(due_cards) == 2
    
    def test_get_overdue_cards(self, db_session: Session, sample_cards_with_srs):
        """Test getting overdue cards"""
        service = SRSService(db_session)
        
        # Set up overdue cards
        srs_records = db_session.query(SRS).all()
        srs_records[0].due_date = datetime.utcnow() - timedelta(days=2)
        srs_records[1].due_date = datetime.utcnow() - timedelta(days=1)
        
        # Set up future cards
        srs_records[2].due_date = datetime.utcnow() + timedelta(days=1)
        
        db_session.commit()
        
        overdue_cards = service.get_overdue_cards()
        
        # Should only return overdue cards
        assert len(overdue_cards) == 2
        
        # Check ordering (most overdue first)
        assert overdue_cards[0][0].due_date < overdue_cards[1][0].due_date
    
    def test_get_cards_due_today(self, db_session: Session, sample_cards_with_srs):
        """Test getting cards due today"""
        service = SRSService(db_session)
        
        today = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # Set up cards with different due dates
        srs_records = db_session.query(SRS).all()
        srs_records[0].due_date = yesterday  # Overdue
        srs_records[1].due_date = today      # Due today
        srs_records[2].due_date = tomorrow   # Due tomorrow
        
        db_session.commit()
        
        today_cards = service.get_cards_due_today()
        
        # Should only return cards due today
        assert len(today_cards) == 1
        assert today_cards[0][0].due_date.date() == today.date()
    
    def test_get_review_statistics_empty(self, db_session: Session):
        """Test getting statistics with no cards"""
        service = SRSService(db_session)
        
        stats = service.get_review_statistics()
        
        assert stats['total_cards'] == 0
        assert stats['due_today'] == 0
        assert stats['overdue'] == 0
        assert stats['learning'] == 0
        assert stats['mature'] == 0
        assert stats['average_ease_factor'] == 0.0
        assert stats['average_interval'] == 0.0
    
    def test_get_review_statistics(self, db_session: Session, sample_cards_with_srs):
        """Test getting review statistics"""
        service = SRSService(db_session)
        
        # Set up different card states
        srs_records = db_session.query(SRS).all()
        
        today = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Overdue card
        srs_records[0].due_date = today - timedelta(days=1)
        srs_records[0].repetitions = 0  # Learning
        
        # Due today card
        srs_records[1].due_date = today
        srs_records[1].repetitions = 1  # Learning
        
        # Mature card
        srs_records[2].due_date = today + timedelta(days=5)
        srs_records[2].repetitions = 3  # Mature
        srs_records[2].ease_factor = 2.8
        srs_records[2].interval = 15
        
        db_session.commit()
        
        stats = service.get_review_statistics()
        
        assert stats['total_cards'] == 3
        assert stats['due_today'] == 1
        assert stats['overdue'] == 1
        assert stats['learning'] == 2  # repetitions < 2
        assert stats['mature'] == 1    # repetitions >= 2
        assert stats['average_ease_factor'] > 0
        assert stats['average_interval'] > 0
    
    def test_get_srs_record(self, db_session: Session, sample_srs, sample_card):
        """Test getting SRS record for a card"""
        service = SRSService(db_session)
        
        srs = service.get_srs_record(str(sample_card.id))
        
        assert srs is not None
        assert srs.id == sample_srs.id
        assert srs.card_id == sample_card.id
    
    def test_get_srs_record_with_user(self, db_session: Session, sample_card):
        """Test getting SRS record with user filter"""
        service = SRSService(db_session)
        
        # Create SRS records for different users
        srs1 = service.create_srs_record(str(sample_card.id), "user1")
        srs2 = service.create_srs_record(str(sample_card.id), "user2")
        
        # Get record for specific user
        user1_srs = service.get_srs_record(str(sample_card.id), "user1")
        user2_srs = service.get_srs_record(str(sample_card.id), "user2")
        
        assert user1_srs.id == srs1.id
        assert user2_srs.id == srs2.id
        assert user1_srs.user_id == "user1"
        assert user2_srs.user_id == "user2"
    
    def test_reset_card_progress(self, db_session: Session, sample_srs):
        """Test resetting card progress"""
        service = SRSService(db_session)
        
        # Set up advanced card state
        sample_srs.repetitions = 5
        sample_srs.interval = 30
        sample_srs.ease_factor = 3.0
        sample_srs.last_reviewed = datetime.utcnow() - timedelta(days=1)
        sample_srs.last_grade = 4
        db_session.commit()
        
        # Reset progress
        reset_srs = service.reset_card_progress(str(sample_srs.id))
        
        # Should be back to initial state
        assert reset_srs.repetitions == 0
        assert reset_srs.interval == 1
        assert reset_srs.ease_factor == 2.5
        assert reset_srs.last_reviewed is None
        assert reset_srs.last_grade is None
        assert reset_srs.due_date <= datetime.utcnow() + timedelta(minutes=1)
    
    def test_reset_nonexistent_card(self, db_session: Session):
        """Test resetting non-existent card"""
        service = SRSService(db_session)
        
        with pytest.raises(ValueError, match="SRS record not found"):
            service.reset_card_progress("nonexistent-id")


# Fixtures for testing

@pytest.fixture
def sample_srs(db_session: Session, sample_card):
    """Create a sample SRS record"""
    srs = SRS(
        card_id=sample_card.id,
        ease_factor=2.5,
        interval=1,
        repetitions=0,
        due_date=datetime.utcnow()
    )
    db_session.add(srs)
    db_session.commit()
    db_session.refresh(srs)
    return srs


@pytest.fixture
def sample_cards_with_srs(db_session: Session, sample_knowledge):
    """Create multiple cards with SRS records"""
    cards = []
    
    # Create multiple cards
    for i in range(3):
        card = Card(
            knowledge_id=sample_knowledge.id,
            card_type=CardType.QA,
            front=f"Question {i+1}?",
            back=f"Answer {i+1}",
            difficulty=1.0 + i * 0.5
        )
        db_session.add(card)
        cards.append(card)
    
    db_session.commit()
    
    # Create SRS records for each card
    for card in cards:
        srs = SRS(
            card_id=card.id,
            ease_factor=2.5,
            interval=1,
            repetitions=0,
            due_date=datetime.utcnow()
        )
        db_session.add(srs)
    
    db_session.commit()
    return cards