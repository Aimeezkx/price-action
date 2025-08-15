#!/usr/bin/env python3
"""
Example usage of the Review Service

Demonstrates how to use the daily review and scheduling system
for spaced repetition learning.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.database import get_db, init_db
from app.services.review_service import ReviewService, ReviewSessionStatus
from app.services.srs_service import SRSService
from app.models.learning import Card, SRS, CardType
from app.models.knowledge import Knowledge, KnowledgeType
from app.models.document import Document, Chapter


async def setup_sample_data(db):
    """Set up sample learning data"""
    print("Setting up sample learning data...")
    
    # Create a sample document
    doc = Document(
        filename="machine_learning_basics.pdf",
        file_type="pdf",
        status="completed"
    )
    db.add(doc)
    db.flush()
    
    # Create chapters
    chapters = [
        {"title": "Introduction to Machine Learning", "pages": (1, 15)},
        {"title": "Supervised Learning", "pages": (16, 45)},
        {"title": "Unsupervised Learning", "pages": (46, 70)},
        {"title": "Neural Networks", "pages": (71, 100)}
    ]
    
    created_chapters = []
    for i, chapter_data in enumerate(chapters):
        chapter = Chapter(
            document_id=doc.id,
            title=chapter_data["title"],
            level=1,
            order_index=i,
            page_start=chapter_data["pages"][0],
            page_end=chapter_data["pages"][1]
        )
        db.add(chapter)
        db.flush()
        created_chapters.append(chapter)
    
    # Create knowledge points and cards
    sample_knowledge = [
        {
            "chapter": 0,
            "text": "Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
            "entities": ["Machine Learning", "artificial intelligence", "data"],
            "card_front": "What is Machine Learning?",
            "card_back": "Machine Learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed.",
            "difficulty": 1.2
        },
        {
            "chapter": 1,
            "text": "Supervised Learning is a type of machine learning where the algorithm learns from labeled training data to make predictions on new, unseen data.",
            "entities": ["Supervised Learning", "labeled training data", "predictions"],
            "card_front": "What is Supervised Learning?",
            "card_back": "Supervised Learning is a type of machine learning where the algorithm learns from labeled training data to make predictions on new, unseen data.",
            "difficulty": 1.4
        },
        {
            "chapter": 1,
            "text": "Classification is a supervised learning task where the goal is to predict discrete class labels or categories for input data.",
            "entities": ["Classification", "discrete class labels", "categories"],
            "card_front": "What is Classification in machine learning?",
            "card_back": "Classification is a supervised learning task where the goal is to predict discrete class labels or categories for input data.",
            "difficulty": 1.3
        },
        {
            "chapter": 1,
            "text": "Regression is a supervised learning task where the goal is to predict continuous numerical values based on input features.",
            "entities": ["Regression", "continuous numerical values", "input features"],
            "card_front": "What is Regression in machine learning?",
            "card_back": "Regression is a supervised learning task where the goal is to predict continuous numerical values based on input features.",
            "difficulty": 1.3
        },
        {
            "chapter": 2,
            "text": "Unsupervised Learning is a type of machine learning that finds hidden patterns in data without using labeled examples.",
            "entities": ["Unsupervised Learning", "hidden patterns", "unlabeled data"],
            "card_front": "What is Unsupervised Learning?",
            "card_back": "Unsupervised Learning is a type of machine learning that finds hidden patterns in data without using labeled examples.",
            "difficulty": 1.5
        },
        {
            "chapter": 2,
            "text": "Clustering is an unsupervised learning technique that groups similar data points together based on their characteristics.",
            "entities": ["Clustering", "groups", "similar data points"],
            "card_front": "What is Clustering?",
            "card_back": "Clustering is an unsupervised learning technique that groups similar data points together based on their characteristics.",
            "difficulty": 1.4
        },
        {
            "chapter": 3,
            "text": "A Neural Network is a computing system inspired by biological neural networks, consisting of interconnected nodes (neurons) that process information.",
            "entities": ["Neural Network", "biological neural networks", "neurons"],
            "card_front": "What is a Neural Network?",
            "card_back": "A Neural Network is a computing system inspired by biological neural networks, consisting of interconnected nodes (neurons) that process information.",
            "difficulty": 1.6
        },
        {
            "chapter": 3,
            "text": "Deep Learning is a subset of machine learning that uses neural networks with multiple hidden layers to learn complex patterns in data.",
            "entities": ["Deep Learning", "multiple hidden layers", "complex patterns"],
            "card_front": "What is Deep Learning?",
            "card_back": "Deep Learning is a subset of machine learning that uses neural networks with multiple hidden layers to learn complex patterns in data.",
            "difficulty": 1.7
        }
    ]
    
    # Create knowledge points, cards, and SRS records
    now = datetime.utcnow()
    cards_created = []
    
    for i, kp_data in enumerate(sample_knowledge):
        # Create knowledge point
        knowledge = Knowledge(
            chapter_id=created_chapters[kp_data["chapter"]].id,
            kind=KnowledgeType.DEFINITION,
            text=kp_data["text"],
            entities=kp_data["entities"],
            anchors={
                "page": created_chapters[kp_data["chapter"]].page_start + (i % 5),
                "chapter": created_chapters[kp_data["chapter"]].title,
                "position": i
            }
        )
        db.add(knowledge)
        db.flush()
        
        # Create card
        card = Card(
            knowledge_id=knowledge.id,
            card_type=CardType.QA,
            front=kp_data["card_front"],
            back=kp_data["card_back"],
            difficulty=kp_data["difficulty"],
            card_metadata={"source": "example_setup"}
        )
        db.add(card)
        db.flush()
        
        # Create SRS record with varied due dates
        if i < 3:
            # Some overdue cards
            due_date = now - timedelta(days=i+1)
            interval = 1
            repetitions = 0
        elif i < 6:
            # Some due today
            due_date = now - timedelta(hours=i-2)
            interval = 1
            repetitions = 0
        else:
            # Some future cards
            due_date = now + timedelta(days=i-5)
            interval = i-4
            repetitions = 1
        
        srs = SRS(
            card_id=card.id,
            user_id=None,
            ease_factor=2.5,
            interval=interval,
            repetitions=repetitions,
            due_date=due_date
        )
        db.add(srs)
        
        cards_created.append({
            'knowledge': knowledge,
            'card': card,
            'srs': srs
        })
    
    db.commit()
    print(f"✓ Created {len(cards_created)} cards with knowledge points and SRS records")
    return cards_created


async def demonstrate_daily_review_workflow():
    """Demonstrate the complete daily review workflow"""
    print("\n=== Daily Review Workflow Demonstration ===")
    
    # Initialize database and get session
    await init_db()
    db = next(get_db())
    
    try:
        # Set up sample data
        cards_data = await setup_sample_data(db)
        
        # Create review service
        review_service = ReviewService(db)
        
        # 1. Check daily review statistics
        print("\n1. Checking daily review statistics...")
        stats = review_service.get_daily_review_stats()
        
        print(f"   📊 Review Statistics:")
        print(f"   - Total cards in system: {stats['total_cards']}")
        print(f"   - Due today: {stats['due_today']}")
        print(f"   - Overdue: {stats['overdue']}")
        print(f"   - Learning phase: {stats['learning']}")
        print(f"   - Mature cards: {stats['mature']}")
        print(f"   - Review load: {stats['review_load']['current_load']} ({stats['review_load']['load_category']})")
        
        # 2. Get daily review cards
        print("\n2. Getting cards for daily review...")
        daily_cards = review_service.get_daily_review_cards(max_cards=10)
        
        print(f"   📚 Found {len(daily_cards)} cards for review:")
        for i, card in enumerate(daily_cards[:5]):  # Show first 5
            status = "OVERDUE" if card.days_overdue > 0 else "DUE TODAY"
            print(f"   {i+1}. [{status}] {card.front[:50]}...")
            if card.days_overdue > 0:
                print(f"      ⏰ {card.days_overdue} days overdue")
        
        if len(daily_cards) > 5:
            print(f"   ... and {len(daily_cards) - 5} more cards")
        
        # 3. Start a review session
        print("\n3. Starting review session...")
        session = review_service.start_review_session(max_cards=5)
        
        print(f"   🎯 Session started: {session.session_id}")
        print(f"   - Status: {session.status.value}")
        print(f"   - Cards to review: {session.total_cards}")
        
        if session.total_cards == 0:
            print("   ℹ️  No cards available for review")
            return
        
        # 4. Review cards with simulated user interaction
        print("\n4. Reviewing cards...")
        
        # Simulate different grading patterns
        grade_patterns = [5, 4, 3, 4, 5]  # Mix of performance levels
        
        for i in range(min(session.total_cards, len(grade_patterns))):
            # Get current card
            current_card = review_service.get_current_card(session.session_id)
            if not current_card:
                break
            
            print(f"\n   📖 Card {i+1}/{session.total_cards}:")
            print(f"   Q: {current_card.front}")
            print(f"   A: {current_card.back[:100]}...")
            print(f"   Difficulty: {current_card.difficulty:.1f}")
            
            # Simulate user grading
            grade = grade_patterns[i]
            response_time = 3000 + (i * 1000)  # Simulate varying response times
            
            print(f"   👤 User grades: {grade}/5 (response time: {response_time}ms)")
            
            # Grade the card
            result = review_service.grade_current_card(
                session.session_id,
                grade=grade,
                response_time_ms=response_time
            )
            
            if result['success']:
                graded_card = result['graded_card']
                progress = result['session_progress']
                
                print(f"   ✅ Card graded successfully!")
                print(f"   - Next review: {graded_card['new_due_date'][:10]}")
                print(f"   - New interval: {graded_card['new_interval']} days")
                print(f"   - Progress: {progress['completed']}/{progress['total']} ({progress['progress_percent']}%)")
                
                if result['session_complete']:
                    print(f"   🎉 Session completed!")
                    break
            else:
                print(f"   ❌ Grading failed: {result.get('error')}")
        
        # 5. Get final session statistics
        print("\n5. Session summary...")
        final_progress = review_service.get_session_progress(session.session_id)
        
        if final_progress:
            perf = final_progress['performance']
            timing = final_progress['timing']
            
            print(f"   📈 Session Performance:")
            print(f"   - Cards completed: {final_progress['progress']['completed']}")
            print(f"   - Average grade: {perf['average_grade']:.1f}/5")
            print(f"   - Accuracy: {perf['accuracy']:.1f}%")
            print(f"   - Duration: {timing['duration_minutes']} minutes")
            print(f"   - Average response time: {perf['average_response_time_ms']}ms")
            
            # Show grade distribution
            grade_dist = perf['grade_distribution']
            print(f"   - Grade distribution: {dict(grade_dist)}")
        
        # 6. Show updated statistics
        print("\n6. Updated review statistics...")
        updated_stats = review_service.get_daily_review_stats()
        
        print(f"   📊 After Review:")
        print(f"   - Cards reviewed today: {updated_stats['today_performance']['cards_reviewed']}")
        print(f"   - Today's accuracy: {updated_stats['today_performance']['accuracy']:.1f}%")
        print(f"   - Remaining due: {updated_stats['due_today']}")
        print(f"   - Still overdue: {updated_stats['overdue']}")
        
        print("\n✅ Daily review workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


async def demonstrate_concurrent_sessions():
    """Demonstrate concurrent session handling"""
    print("\n=== Concurrent Sessions Demonstration ===")
    
    db = next(get_db())
    
    try:
        review_service = ReviewService(db)
        
        # Start multiple sessions
        print("\n1. Starting multiple concurrent sessions...")
        
        session1 = review_service.start_review_session(max_cards=3)
        session2 = review_service.start_review_session(max_cards=3)
        
        print(f"   Session 1: {session1.session_id} ({session1.total_cards} cards)")
        print(f"   Session 2: {session2.session_id} ({session2.total_cards} cards)")
        
        # Demonstrate independent operation
        print("\n2. Operating sessions independently...")
        
        if session1.total_cards > 0:
            result1 = review_service.grade_current_card(session1.session_id, 4)
            print(f"   ✅ Session 1: Graded card with result: {result1['success']}")
        
        if session2.total_cards > 0:
            result2 = review_service.grade_current_card(session2.session_id, 3)
            print(f"   ✅ Session 2: Graded card with result: {result2['success']}")
        
        # Show session states
        progress1 = review_service.get_session_progress(session1.session_id)
        progress2 = review_service.get_session_progress(session2.session_id)
        
        if progress1:
            print(f"   Session 1 progress: {progress1['progress']['completed']}/{progress1['progress']['total']}")
        if progress2:
            print(f"   Session 2 progress: {progress2['progress']['completed']}/{progress2['progress']['total']}")
        
        # Demonstrate session control
        print("\n3. Demonstrating session control...")
        
        if session1.total_cards > 0:
            review_service.pause_session(session1.session_id)
            print("   ⏸️  Session 1 paused")
            
            review_service.resume_session(session1.session_id)
            print("   ▶️  Session 1 resumed")
        
        review_service.cancel_session(session2.session_id)
        print("   ❌ Session 2 cancelled")
        
        print("\n✅ Concurrent sessions demonstration completed!")
        
    except Exception as e:
        print(f"\n❌ Error during concurrent sessions demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


async def demonstrate_performance_metrics():
    """Demonstrate performance metrics and analytics"""
    print("\n=== Performance Metrics Demonstration ===")
    
    db = next(get_db())
    
    try:
        review_service = ReviewService(db)
        
        # Get comprehensive statistics
        print("\n1. Comprehensive review statistics...")
        stats = review_service.get_daily_review_stats()
        
        print(f"   📊 System Overview:")
        print(f"   - Total cards: {stats['total_cards']}")
        print(f"   - Average ease factor: {stats['average_ease_factor']}")
        print(f"   - Average interval: {stats['average_interval']} days")
        
        print(f"\n   📅 Today's Activity:")
        today_perf = stats['today_performance']
        print(f"   - Cards reviewed: {today_perf['cards_reviewed']}")
        print(f"   - Average grade: {today_perf['average_grade']}")
        print(f"   - Accuracy: {today_perf['accuracy']}%")
        
        print(f"\n   📈 Upcoming Workload:")
        upcoming = stats['upcoming_reviews']
        print(f"   - Next 7 days: {upcoming['next_7_days']} cards")
        
        # Show daily breakdown
        by_day = upcoming['by_day']
        for day, count in by_day.items():
            day_num = day.split('_')[1]
            print(f"   - Day {day_num}: {count} cards")
        
        print(f"\n   ⚖️  Current Load Assessment:")
        load = stats['review_load']
        print(f"   - Current load: {load['current_load']} cards")
        print(f"   - Load category: {load['load_category'].upper()}")
        
        # Provide recommendations based on load
        recommendations = {
            'none': "Perfect! No reviews due. Great time to learn new material.",
            'light': "Light review load. Easy to manage with regular study.",
            'moderate': "Moderate load. Maintain consistent daily reviews.",
            'heavy': "Heavy load. Consider extending daily review time.",
            'overwhelming': "Overwhelming load! Focus on overdue cards first."
        }
        
        rec = recommendations.get(load['load_category'], "Continue regular reviews.")
        print(f"   💡 Recommendation: {rec}")
        
        print("\n✅ Performance metrics demonstration completed!")
        
    except Exception as e:
        print(f"\n❌ Error during performance metrics demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


async def main():
    """Run all demonstrations"""
    print("🎓 Review Service Demonstration")
    print("=" * 50)
    
    try:
        # Run demonstrations
        await demonstrate_daily_review_workflow()
        await demonstrate_concurrent_sessions()
        await demonstrate_performance_metrics()
        
        print("\n" + "=" * 50)
        print("🎉 All demonstrations completed successfully!")
        print("\nThe Review Service provides:")
        print("✅ Optimized daily review card selection")
        print("✅ Complete session management with progress tracking")
        print("✅ Concurrent session handling")
        print("✅ Comprehensive performance metrics")
        print("✅ Robust error handling and edge case management")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())