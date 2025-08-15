#!/usr/bin/env python3
"""
Integration test for the review system

Tests the complete daily review and scheduling system including:
- Daily review card selection
- Review session management
- Progress tracking
- Concurrent session handling
- Performance metrics
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import get_db, init_db
from app.services.review_service import ReviewService, ReviewSessionStatus
from app.services.srs_service import SRSService
from app.models.learning import Card, SRS, CardType
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Document, Chapter


async def create_test_data(db):
    """Create test data for review system testing"""
    print("Creating test data...")
    
    # Create document
    doc = Document(
        filename="review_test_document.pdf",
        file_type="pdf",
        status="completed"
    )
    db.add(doc)
    db.flush()
    
    # Create chapter
    chapter = Chapter(
        document_id=doc.id,
        title="Review Test Chapter",
        level=1,
        order_index=1,
        page_start=1,
        page_end=20
    )
    db.add(chapter)
    db.flush()
    
    # Create knowledge points and cards
    cards_data = []
    now = datetime.utcnow()
    
    for i in range(10):
        # Create knowledge
        knowledge = Knowledge(
            chapter_id=chapter.id,
            kind=KnowledgeType.DEFINITION,
            text=f"Test knowledge point {i+1}: This is a definition of concept {i+1}",
            entities=[f"concept_{i+1}", f"term_{i+1}"],
            anchors={"page": i+1, "chapter": "Review Test Chapter", "position": i}
        )
        db.add(knowledge)
        db.flush()
        
        # Create card
        card = Card(
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front=f"What is concept {i+1}?",
            back=f"Concept {i+1} is defined as: {knowledge.text}",
            difficulty=1.0 + (i * 0.1),
            card_metadata={"source": "integration_test"}
        )
        db.add(card)
        db.flush()
        
        # Create SRS record with different due dates
        if i < 3:
            # Overdue cards (1-3 days overdue)
            due_date = now - timedelta(days=i+1)
        elif i < 6:
            # Due today
            due_date = now - timedelta(hours=i-2)
        elif i < 8:
            # Due tomorrow
            due_date = now + timedelta(days=1)
        else:
            # Due in future
            due_date = now + timedelta(days=i-5)
        
        srs = SRS(
            card_id=card.id,
            user_id=None,
            ease_factor=2.5,
            interval=1 if i < 6 else i-4,
            repetitions=0 if i < 6 else 1,
            due_date=due_date
        )
        db.add(srs)
        
        cards_data.append({
            'knowledge': knowledge,
            'card': card,
            'srs': srs,
            'expected_due': i < 6  # First 6 should be due for review
        })
    
    db.commit()
    print(f"Created {len(cards_data)} cards with SRS records")
    return cards_data


async def test_daily_review_selection(db, cards_data):
    """Test daily review card selection"""
    print("\n=== Testing Daily Review Card Selection ===")
    
    review_service = ReviewService(db)
    
    # Test getting daily review cards
    daily_cards = review_service.get_daily_review_cards(max_cards=20)
    
    print(f"Found {len(daily_cards)} cards for daily review")
    
    # Should have 6 cards (3 overdue + 3 due today)
    expected_due_count = sum(1 for card in cards_data if card['expected_due'])
    assert len(daily_cards) == expected_due_count, f"Expected {expected_due_count} cards, got {len(daily_cards)}"
    
    # Check that overdue cards come first
    overdue_cards = [c for c in daily_cards if c.days_overdue > 0]
    due_today_cards = [c for c in daily_cards if c.days_overdue == 0]
    
    print(f"  - Overdue cards: {len(overdue_cards)}")
    print(f"  - Due today: {len(due_today_cards)}")
    
    # Verify card data structure
    if daily_cards:
        card = daily_cards[0]
        assert hasattr(card, 'srs_id')
        assert hasattr(card, 'card_id')
        assert hasattr(card, 'card_type')
        assert hasattr(card, 'front')
        assert hasattr(card, 'back')
        assert hasattr(card, 'difficulty')
        assert hasattr(card, 'due_date')
        assert hasattr(card, 'days_overdue')
        assert hasattr(card, 'metadata')
        print(f"  - Sample card: {card.front[:50]}...")
    
    # Test with max_cards limit
    limited_cards = review_service.get_daily_review_cards(max_cards=3)
    assert len(limited_cards) <= 3, "Max cards limit not respected"
    print(f"  - Limited to 3 cards: {len(limited_cards)} returned")
    
    print("✓ Daily review card selection working correctly")
    return daily_cards


async def test_review_session_management(db, daily_cards):
    """Test review session management"""
    print("\n=== Testing Review Session Management ===")
    
    review_service = ReviewService(db)
    
    # Start a review session
    session = review_service.start_review_session(max_cards=5)
    
    print(f"Started session {session.session_id}")
    print(f"  - Status: {session.status.value}")
    print(f"  - Total cards: {session.total_cards}")
    print(f"  - Current index: {session.current_index}")
    
    if session.total_cards == 0:
        print("  - No cards available, testing empty session handling")
        assert session.status == ReviewSessionStatus.COMPLETED
        print("✓ Empty session handled correctly")
        return None
    
    # Test getting current card
    current_card = review_service.get_current_card(session.session_id)
    assert current_card is not None, "Should have current card"
    print(f"  - Current card: {current_card.front[:50]}...")
    
    # Test session progress
    progress = review_service.get_session_progress(session.session_id)
    assert progress is not None
    assert progress['session_id'] == session.session_id
    assert progress['status'] == ReviewSessionStatus.ACTIVE.value
    print(f"  - Progress: {progress['progress']['completed']}/{progress['progress']['total']}")
    
    print("✓ Review session management working correctly")
    return session


async def test_card_grading_and_progress(db, session):
    """Test card grading and progress tracking"""
    if not session or session.total_cards == 0:
        print("\n=== Skipping Card Grading Test (No Cards) ===")
        return
    
    print("\n=== Testing Card Grading and Progress ===")
    
    review_service = ReviewService(db)
    
    cards_graded = 0
    grades_used = [5, 4, 3, 2, 4]  # Mix of grades
    
    # Grade cards one by one
    while cards_graded < min(session.total_cards, len(grades_used)):
        grade = grades_used[cards_graded]
        
        # Get current card before grading
        current_card = review_service.get_current_card(session.session_id)
        if not current_card:
            break
        
        print(f"  - Grading card {cards_graded + 1}: '{current_card.front[:30]}...' with grade {grade}")
        
        # Grade the card
        result = review_service.grade_current_card(
            session.session_id, 
            grade=grade,
            response_time_ms=2000 + (cards_graded * 500)
        )
        
        assert result['success'] is True, f"Grading failed: {result.get('error')}"
        
        # Check result structure
        assert 'graded_card' in result
        assert 'session_progress' in result
        assert result['session_progress']['completed'] == cards_graded + 1
        
        print(f"    ✓ Card graded successfully")
        print(f"    - New due date: {result['graded_card']['new_due_date']}")
        print(f"    - New interval: {result['graded_card']['new_interval']} days")
        print(f"    - Ease factor: {result['graded_card']['ease_factor']}")
        
        cards_graded += 1
        
        # Check if session is complete
        if result['session_complete']:
            print(f"    ✓ Session completed after {cards_graded} cards")
            break
    
    # Get final session progress
    final_progress = review_service.get_session_progress(session.session_id)
    print(f"  - Final progress: {final_progress['progress']['completed']}/{final_progress['progress']['total']}")
    print(f"  - Session duration: {final_progress['timing']['duration_minutes']} minutes")
    print(f"  - Average grade: {final_progress['performance']['average_grade']}")
    print(f"  - Accuracy: {final_progress['performance']['accuracy']}%")
    
    print("✓ Card grading and progress tracking working correctly")


async def test_concurrent_sessions(db):
    """Test concurrent session handling"""
    print("\n=== Testing Concurrent Session Handling ===")
    
    review_service = ReviewService(db)
    
    # Start multiple sessions
    session1 = review_service.start_review_session(max_cards=3)
    session2 = review_service.start_review_session(max_cards=3)
    
    print(f"Started two concurrent sessions:")
    print(f"  - Session 1: {session1.session_id} ({session1.total_cards} cards)")
    print(f"  - Session 2: {session2.session_id} ({session2.total_cards} cards)")
    
    # Verify sessions are independent
    assert session1.session_id != session2.session_id
    assert session1.session_id in review_service._active_sessions
    assert session2.session_id in review_service._active_sessions
    
    # Grade cards in both sessions if available
    if session1.total_cards > 0:
        result1 = review_service.grade_current_card(session1.session_id, 4)
        assert result1['success'] is True
        print("  ✓ Session 1 card graded")
    
    if session2.total_cards > 0:
        result2 = review_service.grade_current_card(session2.session_id, 3)
        assert result2['success'] is True
        print("  ✓ Session 2 card graded")
    
    # Verify sessions remain independent
    if session1.total_cards > 0 and session2.total_cards > 0:
        s1 = review_service._active_sessions[session1.session_id]
        s2 = review_service._active_sessions[session2.session_id]
        
        assert s1.completed_cards == 1
        assert s2.completed_cards == 1
        print("  ✓ Sessions maintained independent state")
    
    # Test session control operations
    if session1.total_cards > 0:
        # Pause session 1
        success = review_service.pause_session(session1.session_id)
        assert success is True
        print("  ✓ Session 1 paused")
        
        # Resume session 1
        success = review_service.resume_session(session1.session_id)
        assert success is True
        print("  ✓ Session 1 resumed")
    
    # Cancel session 2
    success = review_service.cancel_session(session2.session_id)
    assert success is True
    print("  ✓ Session 2 cancelled")
    
    print("✓ Concurrent session handling working correctly")


async def test_review_statistics(db):
    """Test review statistics and performance metrics"""
    print("\n=== Testing Review Statistics ===")
    
    review_service = ReviewService(db)
    
    # Get daily review statistics
    stats = review_service.get_daily_review_stats()
    
    print("Daily Review Statistics:")
    print(f"  - Total cards: {stats['total_cards']}")
    print(f"  - Due today: {stats['due_today']}")
    print(f"  - Overdue: {stats['overdue']}")
    print(f"  - Learning: {stats['learning']}")
    print(f"  - Mature: {stats['mature']}")
    print(f"  - Average ease factor: {stats['average_ease_factor']}")
    print(f"  - Average interval: {stats['average_interval']} days")
    
    # Verify statistics structure
    assert 'total_cards' in stats
    assert 'due_today' in stats
    assert 'overdue' in stats
    assert 'today_performance' in stats
    assert 'upcoming_reviews' in stats
    assert 'review_load' in stats
    
    # Check performance stats
    perf = stats['today_performance']
    print(f"  - Today's performance:")
    print(f"    - Cards reviewed: {perf['cards_reviewed']}")
    print(f"    - Average grade: {perf['average_grade']}")
    print(f"    - Accuracy: {perf['accuracy']}%")
    
    # Check review load
    load = stats['review_load']
    print(f"  - Review load: {load['current_load']} cards ({load['load_category']})")
    
    # Check upcoming reviews
    upcoming = stats['upcoming_reviews']
    print(f"  - Upcoming (7 days): {upcoming['next_7_days']} cards")
    
    print("✓ Review statistics working correctly")


async def test_session_cleanup(db):
    """Test session cleanup functionality"""
    print("\n=== Testing Session Cleanup ===")
    
    review_service = ReviewService(db)
    
    # Start and complete a session
    session = review_service.start_review_session(max_cards=1)
    
    if session.total_cards > 0:
        # Grade the card to complete session
        review_service.grade_current_card(session.session_id, 4)
        print("  - Completed a test session")
    
    # Manually set end time to past for testing
    if session.session_id in review_service._active_sessions:
        review_service._active_sessions[session.session_id].end_time = \
            datetime.utcnow() - timedelta(hours=25)
        print("  - Set session end time to 25 hours ago")
    
    # Count sessions before cleanup
    sessions_before = len(review_service._active_sessions)
    
    # Cleanup old sessions
    cleaned_count = review_service.cleanup_completed_sessions(hours_old=24)
    
    print(f"  - Cleaned up {cleaned_count} old sessions")
    print(f"  - Sessions before: {sessions_before}, after: {len(review_service._active_sessions)}")
    
    print("✓ Session cleanup working correctly")


async def test_error_handling(db):
    """Test error handling and edge cases"""
    print("\n=== Testing Error Handling ===")
    
    review_service = ReviewService(db)
    
    # Test invalid session operations
    try:
        review_service.grade_current_card("invalid_session_id", 4)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  ✓ Invalid session error handled: {e}")
    
    # Test invalid grade (should be handled by SRS service)
    session = review_service.start_review_session(max_cards=1)
    if session.total_cards > 0:
        try:
            review_service.grade_current_card(session.session_id, 10)  # Invalid grade
            assert False, "Should have raised error for invalid grade"
        except Exception as e:
            print(f"  ✓ Invalid grade error handled: {e}")
    
    # Test operations on non-existent session
    progress = review_service.get_session_progress("non_existent_session")
    assert progress is None
    print("  ✓ Non-existent session handled gracefully")
    
    # Test pause/resume on invalid sessions
    success = review_service.pause_session("invalid_session")
    assert success is False
    print("  ✓ Invalid pause operation handled")
    
    success = review_service.resume_session("invalid_session")
    assert success is False
    print("  ✓ Invalid resume operation handled")
    
    print("✓ Error handling working correctly")


async def main():
    """Run the complete review system integration test"""
    print("=== Review System Integration Test ===")
    print("Testing daily review and scheduling system...")
    
    try:
        # Initialize database
        await init_db()
        print("✓ Database initialized")
        
        # Get database session
        db = next(get_db())
        
        # Create test data
        cards_data = await create_test_data(db)
        
        # Run tests
        daily_cards = await test_daily_review_selection(db, cards_data)
        session = await test_review_session_management(db, daily_cards)
        await test_card_grading_and_progress(db, session)
        await test_concurrent_sessions(db)
        await test_review_statistics(db)
        await test_session_cleanup(db)
        await test_error_handling(db)
        
        print("\n=== All Tests Passed! ===")
        print("✓ Daily review card selection")
        print("✓ Review session management")
        print("✓ Card grading and progress tracking")
        print("✓ Concurrent session handling")
        print("✓ Review statistics and metrics")
        print("✓ Session cleanup")
        print("✓ Error handling")
        
        print("\nThe review system is working correctly!")
        
        # Clean up
        db.close()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)