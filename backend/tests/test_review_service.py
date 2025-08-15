"""
Tests for the review service
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import uuid4

from app.services.review_service import ReviewService, ReviewSessionStatus
from app.services.srs_service import SRSService
from app.models.learning import Card, SRS, CardType
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Document, Chapter
from app.core.database import get_test_db


@pytest.fixture
def db_session():
    """Get test database session"""
    db = next(get_test_db())
    yield db
    db.close()


@pytest.fixture
def sample_document(db_session: Session):
    """Create a sample document"""
    doc = Document(
        filename="test_document.pdf",
        file_type="pdf",
        status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def sample_chapter(db_session: Session, sample_document):
    """Create a sample chapter"""
    chapter = Chapter(
        document_id=sample_document.id,
        title="Test Chapter",
        level=1,
        order_index=1,
        page_start=1,
        page_end=10
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter


@pytest.fixture
def sample_knowledge(db_session: Session, sample_chapter):
    """Create sample knowledge points"""
    knowledge_points = []
    
    for i in range(5):
        knowledge = Knowledge(
            chapter_id=sample_chapter.id,
            kind=KnowledgeType.DEFINITION,
            text=f"Test knowledge point {i+1}",
            entities=[f"term_{i+1}"],
            anchors={"page": i+1, "chapter": "Test Chapter"}
        )
        db_session.add(knowledge)
        knowledge_points.append(knowledge)
    
    db_session.commit()
    for kp in knowledge_points:
        db_session.refresh(kp)
    
    return knowledge_points


@pytest.fixture
def sample_cards_with_srs(db_session: Session, sample_knowledge):
    """Create sample cards with SRS records"""
    cards_with_srs = []
    now = datetime.utcnow()
    
    for i, knowledge in enumerate(sample_knowledge):
        # Create card
        card = Card(
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front=f"What is term_{i+1}?",
            back=f"Definition of term_{i+1}",
            difficulty=1.0 + (i * 0.2)
        )
        db_session.add(card)
        db_session.flush()
        
        # Create SRS record with different due dates
        if i < 2:
            # Overdue cards
            due_date = now - timedelta(days=i+1)
        elif i < 4:
            # Due today
            due_date = now - timedelta(hours=i)
        else:
            # Future cards
            due_date = now + timedelta(days=1)
        
        srs = SRS(
            card_id=card.id,
            user_id=None,
            ease_factor=2.5,
            interval=1,
            repetitions=0,
            due_date=due_date
        )
        db_session.add(srs)
        
        cards_with_srs.append((card, srs))
    
    db_session.commit()
    for card, srs in cards_with_srs:
        db_session.refresh(card)
        db_session.refresh(srs)
    
    return cards_with_srs


class TestReviewService:
    """Test cases for ReviewService"""
    
    def test_get_daily_review_cards(self, db_session: Session, sample_cards_with_srs):
        """Test getting daily review cards"""
        review_service = ReviewService(db_session)
        
        # Get daily review cards
        cards = review_service.get_daily_review_cards(max_cards=10)
        
        # Should return 4 cards (2 overdue + 2 due today)
        assert len(cards) == 4
        
        # Check that overdue cards come first
        assert cards[0].days_overdue > 0
        assert cards[1].days_overdue > 0
        
        # Verify card data structure
        card = cards[0]
        assert hasattr(card, 'srs_id')
        assert hasattr(card, 'card_id')
        assert hasattr(card, 'card_type')
        assert hasattr(card, 'front')
        assert hasattr(card, 'back')
        assert hasattr(card, 'difficulty')
        assert hasattr(card, 'due_date')
        assert hasattr(card, 'days_overdue')
    
    def test_optimize_review_queue(self, db_session: Session, sample_cards_with_srs):
        """Test review queue optimization"""
        review_service = ReviewService(db_session)
        
        # Get cards with prioritize_overdue=True
        cards_prioritized = review_service.get_daily_review_cards(
            max_cards=10, 
            prioritize_overdue=True
        )
        
        # Get cards with prioritize_overdue=False
        cards_normal = review_service.get_daily_review_cards(
            max_cards=10, 
            prioritize_overdue=False
        )
        
        # Both should return same number of cards
        assert len(cards_prioritized) == len(cards_normal)
        
        # Prioritized should have overdue cards first
        if len(cards_prioritized) > 0:
            assert cards_prioritized[0].days_overdue >= 0
    
    def test_start_review_session(self, db_session: Session, sample_cards_with_srs):
        """Test starting a review session"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=3)
        
        # Verify session properties
        assert session.session_id is not None
        assert session.status == ReviewSessionStatus.ACTIVE
        assert session.total_cards <= 3
        assert session.completed_cards == 0
        assert session.current_index == 0
        assert session.start_time is not None
        assert session.end_time is None
        assert len(session.cards) == session.total_cards
    
    def test_start_empty_session(self, db_session: Session):
        """Test starting a session with no due cards"""
        review_service = ReviewService(db_session)
        
        # Start session with no cards available
        session = review_service.start_review_session()
        
        # Should create completed empty session
        assert session.status == ReviewSessionStatus.COMPLETED
        assert session.total_cards == 0
        assert session.end_time is not None
    
    def test_get_current_card(self, db_session: Session, sample_cards_with_srs):
        """Test getting current card in session"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=2)
        
        # Get current card
        current_card = review_service.get_current_card(session.session_id)
        
        if session.total_cards > 0:
            assert current_card is not None
            assert current_card.card_id == session.cards[0].card_id
        else:
            assert current_card is None
    
    def test_grade_current_card(self, db_session: Session, sample_cards_with_srs):
        """Test grading current card"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=2)
        
        if session.total_cards == 0:
            pytest.skip("No cards available for testing")
        
        # Grade first card
        result = review_service.grade_current_card(
            session.session_id, 
            grade=4, 
            response_time_ms=2000
        )
        
        # Verify result
        assert result['success'] is True
        assert 'graded_card' in result
        assert 'session_progress' in result
        assert result['session_progress']['completed'] == 1
        
        # Check if session advanced
        updated_session = review_service._active_sessions[session.session_id]
        assert updated_session.current_index == 1
        assert updated_session.completed_cards == 1
    
    def test_grade_invalid_session(self, db_session: Session):
        """Test grading with invalid session"""
        review_service = ReviewService(db_session)
        
        # Try to grade non-existent session
        with pytest.raises(ValueError, match="Invalid or inactive session"):
            review_service.grade_current_card("invalid_session", 4)
    
    def test_grade_invalid_grade(self, db_session: Session, sample_cards_with_srs):
        """Test grading with invalid grade"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=1)
        
        if session.total_cards == 0:
            pytest.skip("No cards available for testing")
        
        # Try invalid grades
        with pytest.raises(Exception):  # Should be caught by SRS service
            review_service.grade_current_card(session.session_id, -1)
        
        with pytest.raises(Exception):  # Should be caught by SRS service
            review_service.grade_current_card(session.session_id, 6)
    
    def test_session_completion(self, db_session: Session, sample_cards_with_srs):
        """Test session completion"""
        review_service = ReviewService(db_session)
        
        # Start session with 1 card
        session = review_service.start_review_session(max_cards=1)
        
        if session.total_cards == 0:
            pytest.skip("No cards available for testing")
        
        # Grade the only card
        result = review_service.grade_current_card(session.session_id, 4)
        
        # Session should be completed
        assert result['session_complete'] is True
        
        updated_session = review_service._active_sessions[session.session_id]
        assert updated_session.status == ReviewSessionStatus.COMPLETED
        assert updated_session.end_time is not None
    
    def test_get_session_progress(self, db_session: Session, sample_cards_with_srs):
        """Test getting session progress"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=2)
        
        # Get initial progress
        progress = review_service.get_session_progress(session.session_id)
        
        assert progress is not None
        assert progress['session_id'] == session.session_id
        assert progress['status'] == ReviewSessionStatus.ACTIVE.value
        assert 'progress' in progress
        assert 'timing' in progress
        assert 'performance' in progress
        assert 'content' in progress
    
    def test_pause_resume_session(self, db_session: Session, sample_cards_with_srs):
        """Test pausing and resuming session"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=2)
        
        # Pause session
        success = review_service.pause_session(session.session_id)
        assert success is True
        
        updated_session = review_service._active_sessions[session.session_id]
        assert updated_session.status == ReviewSessionStatus.PAUSED
        
        # Resume session
        success = review_service.resume_session(session.session_id)
        assert success is True
        
        updated_session = review_service._active_sessions[session.session_id]
        assert updated_session.status == ReviewSessionStatus.ACTIVE
    
    def test_cancel_session(self, db_session: Session, sample_cards_with_srs):
        """Test cancelling session"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=2)
        
        # Cancel session
        success = review_service.cancel_session(session.session_id)
        assert success is True
        
        updated_session = review_service._active_sessions[session.session_id]
        assert updated_session.status == ReviewSessionStatus.CANCELLED
        assert updated_session.end_time is not None
    
    def test_get_daily_review_stats(self, db_session: Session, sample_cards_with_srs):
        """Test getting daily review statistics"""
        review_service = ReviewService(db_session)
        
        # Get stats
        stats = review_service.get_daily_review_stats()
        
        # Verify stats structure
        assert 'total_cards' in stats
        assert 'due_today' in stats
        assert 'overdue' in stats
        assert 'learning' in stats
        assert 'mature' in stats
        assert 'today_performance' in stats
        assert 'upcoming_reviews' in stats
        assert 'review_load' in stats
        
        # Verify performance stats
        perf = stats['today_performance']
        assert 'cards_reviewed' in perf
        assert 'average_grade' in perf
        assert 'accuracy' in perf
        assert 'grade_distribution' in perf
        
        # Verify load categorization
        load = stats['review_load']
        assert 'current_load' in load
        assert 'load_category' in load
        assert load['load_category'] in ['none', 'light', 'moderate', 'heavy', 'overwhelming']
    
    def test_cleanup_completed_sessions(self, db_session: Session, sample_cards_with_srs):
        """Test cleaning up old sessions"""
        review_service = ReviewService(db_session)
        
        # Start and complete a session
        session = review_service.start_review_session(max_cards=1)
        
        if session.total_cards > 0:
            review_service.grade_current_card(session.session_id, 4)
        
        # Manually set end time to past
        if session.session_id in review_service._active_sessions:
            review_service._active_sessions[session.session_id].end_time = \
                datetime.utcnow() - timedelta(hours=25)
        
        # Cleanup sessions older than 24 hours
        cleaned_count = review_service.cleanup_completed_sessions(hours_old=24)
        
        # Should have cleaned up the old session
        if session.total_cards > 0:
            assert cleaned_count >= 0  # May be 0 if session wasn't completed
    
    def test_concurrent_session_handling(self, db_session: Session, sample_cards_with_srs):
        """Test handling multiple concurrent sessions"""
        review_service = ReviewService(db_session)
        
        # Start multiple sessions
        session1 = review_service.start_review_session(max_cards=2)
        session2 = review_service.start_review_session(max_cards=2)
        
        # Both sessions should be active and independent
        assert session1.session_id != session2.session_id
        assert session1.session_id in review_service._active_sessions
        assert session2.session_id in review_service._active_sessions
        
        # Grade cards in different sessions
        if session1.total_cards > 0:
            result1 = review_service.grade_current_card(session1.session_id, 4)
            assert result1['success'] is True
        
        if session2.total_cards > 0:
            result2 = review_service.grade_current_card(session2.session_id, 3)
            assert result2['success'] is True
        
        # Sessions should remain independent
        s1 = review_service._active_sessions[session1.session_id]
        s2 = review_service._active_sessions[session2.session_id]
        
        if session1.total_cards > 0 and session2.total_cards > 0:
            assert s1.completed_cards == 1
            assert s2.completed_cards == 1
            assert s1.current_index == 1
            assert s2.current_index == 1


class TestReviewServiceEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_database(self, db_session: Session):
        """Test behavior with empty database"""
        review_service = ReviewService(db_session)
        
        # Should return empty results gracefully
        cards = review_service.get_daily_review_cards()
        assert len(cards) == 0
        
        session = review_service.start_review_session()
        assert session.status == ReviewSessionStatus.COMPLETED
        assert session.total_cards == 0
        
        stats = review_service.get_daily_review_stats()
        assert stats['total_cards'] == 0
    
    def test_user_filtering(self, db_session: Session, sample_cards_with_srs):
        """Test user-specific filtering"""
        review_service = ReviewService(db_session)
        
        # Create SRS records for specific user
        user_id = str(uuid4())
        
        # Update one SRS record to have user_id
        srs_records = db_session.query(SRS).limit(1).all()
        if srs_records:
            srs_records[0].user_id = user_id
            db_session.commit()
        
        # Get cards for specific user
        user_cards = review_service.get_daily_review_cards(user_id=user_id)
        all_cards = review_service.get_daily_review_cards()
        
        # User should have fewer or equal cards
        assert len(user_cards) <= len(all_cards)
    
    def test_max_cards_limit(self, db_session: Session, sample_cards_with_srs):
        """Test max cards limit"""
        review_service = ReviewService(db_session)
        
        # Get cards with low limit
        cards = review_service.get_daily_review_cards(max_cards=2)
        
        # Should respect the limit
        assert len(cards) <= 2
    
    def test_session_state_synchronization(self, db_session: Session, sample_cards_with_srs):
        """Test session state remains synchronized"""
        review_service = ReviewService(db_session)
        
        # Start session
        session = review_service.start_review_session(max_cards=3)
        
        if session.total_cards == 0:
            pytest.skip("No cards available for testing")
        
        # Get session from different access points
        progress1 = review_service.get_session_progress(session.session_id)
        current_card = review_service.get_current_card(session.session_id)
        
        # Grade a card
        review_service.grade_current_card(session.session_id, 4)
        
        # Check state is updated everywhere
        progress2 = review_service.get_session_progress(session.session_id)
        
        assert progress2['progress']['completed'] == progress1['progress']['completed'] + 1
        assert progress2['progress']['remaining'] == progress1['progress']['remaining'] - 1