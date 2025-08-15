"""
Example usage of SRS (Spaced Repetition System) service
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.document import Document, Chapter
from ..models.knowledge import Knowledge, KnowledgeType
from ..models.learning import Card, CardType, SRS
from .srs_service import SRSService


def demonstrate_srs_workflow():
    """Demonstrate complete SRS workflow"""
    
    print("=== SRS Service Example ===\n")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create SRS service
        srs_service = SRSService(db)
        
        # Find or create a sample card
        card = db.query(Card).first()
        if not card:
            print("No cards found. Please run card generation first.")
            return
        
        print(f"Using card: {card.front[:50]}...")
        
        # 1. Create SRS record
        print("\n1. Creating SRS record...")
        
        # Check if SRS record already exists
        existing_srs = srs_service.get_srs_record(str(card.id))
        if existing_srs:
            print(f"   SRS record already exists: {existing_srs.id}")
            srs = existing_srs
        else:
            srs = srs_service.create_srs_record(str(card.id), "demo-user")
            print(f"   Created new SRS record: {srs.id}")
        
        print(f"   Initial state:")
        print(f"   - Ease factor: {srs.ease_factor}")
        print(f"   - Interval: {srs.interval} days")
        print(f"   - Repetitions: {srs.repetitions}")
        print(f"   - Due date: {srs.due_date}")
        
        # 2. Simulate learning progression
        print("\n2. Simulating learning progression...")
        
        grades = [4, 5, 3, 4, 2, 4, 5]  # Mix of good and poor performance
        grade_names = {0: "Blackout", 1: "Incorrect", 2: "Incorrect (easy)", 
                      3: "Correct (difficult)", 4: "Correct", 5: "Perfect"}
        
        for i, grade in enumerate(grades):
            print(f"\n   Review {i+1}: Grade {grade} ({grade_names[grade]})")
            
            # Grade the card
            updated_srs = srs_service.grade_card(str(srs.id), grade)
            
            print(f"   After review:")
            print(f"   - Ease factor: {updated_srs.ease_factor:.2f}")
            print(f"   - Interval: {updated_srs.interval} days")
            print(f"   - Repetitions: {updated_srs.repetitions}")
            print(f"   - Next due: {updated_srs.due_date.strftime('%Y-%m-%d %H:%M')}")
            
            if grade < 3:
                print("   ⚠️  Poor performance - progress reset!")
            elif updated_srs.repetitions >= 2:
                print("   🎓 Card is now mature")
            else:
                print("   📚 Card is still learning")
        
        # 3. Demonstrate due card retrieval
        print("\n3. Due card retrieval...")
        
        # Make the card overdue for demonstration
        updated_srs.due_date = datetime.utcnow() - timedelta(hours=2)
        db.commit()
        
        due_cards = srs_service.get_due_cards("demo-user")
        print(f"   Found {len(due_cards)} due cards")
        
        overdue_cards = srs_service.get_overdue_cards("demo-user")
        print(f"   Found {len(overdue_cards)} overdue cards")
        
        cards_due_today = srs_service.get_cards_due_today("demo-user")
        print(f"   Found {len(cards_due_today)} cards due today")
        
        # 4. Show statistics
        print("\n4. Review statistics...")
        
        stats = srs_service.get_review_statistics("demo-user")
        print(f"   Total cards: {stats['total_cards']}")
        print(f"   Due today: {stats['due_today']}")
        print(f"   Overdue: {stats['overdue']}")
        print(f"   Learning: {stats['learning']}")
        print(f"   Mature: {stats['mature']}")
        print(f"   Average ease factor: {stats['average_ease_factor']}")
        print(f"   Average interval: {stats['average_interval']} days")
        
        # 5. Demonstrate card reset
        print("\n5. Card reset demonstration...")
        
        print(f"   Before reset: repetitions={updated_srs.repetitions}, interval={updated_srs.interval}")
        
        reset_srs = srs_service.reset_card_progress(str(updated_srs.id))
        
        print(f"   After reset: repetitions={reset_srs.repetitions}, interval={reset_srs.interval}")
        print("   Card has been reset to initial learning state")
        
        print("\n=== SRS Workflow Complete ===")
        
    except Exception as e:
        print(f"Error in SRS demonstration: {e}")
        raise
    finally:
        db.close()


def demonstrate_sm2_algorithm():
    """Demonstrate SM-2 algorithm behavior with different grades"""
    
    print("\n=== SM-2 Algorithm Demonstration ===\n")
    
    db = next(get_db())
    
    try:
        srs_service = SRSService(db)
        
        # Find a card to use
        card = db.query(Card).first()
        if not card:
            print("No cards found for demonstration.")
            return
        
        # Create fresh SRS record
        srs = srs_service.create_srs_record(str(card.id), "sm2-demo-user")
        
        print("Testing SM-2 algorithm with different grade sequences:\n")
        
        # Test sequence 1: Perfect performance
        print("Sequence 1: Perfect performance (all 5s)")
        test_srs = srs
        for i in range(5):
            test_srs = srs_service.grade_card(str(test_srs.id), 5)
            print(f"  Review {i+1}: Grade 5 → Interval: {test_srs.interval} days, Ease: {test_srs.ease_factor:.2f}")
        
        # Reset for next test
        srs_service.reset_card_progress(str(test_srs.id))
        
        print("\nSequence 2: Good performance (all 4s)")
        for i in range(5):
            test_srs = srs_service.grade_card(str(test_srs.id), 4)
            print(f"  Review {i+1}: Grade 4 → Interval: {test_srs.interval} days, Ease: {test_srs.ease_factor:.2f}")
        
        # Reset for next test
        srs_service.reset_card_progress(str(test_srs.id))
        
        print("\nSequence 3: Mixed performance with failure")
        grades = [4, 5, 2, 4, 4]  # Failure on 3rd review
        for i, grade in enumerate(grades):
            test_srs = srs_service.grade_card(str(test_srs.id), grade)
            status = "RESET" if grade < 3 else "OK"
            print(f"  Review {i+1}: Grade {grade} → Interval: {test_srs.interval} days, Ease: {test_srs.ease_factor:.2f} [{status}]")
        
        print("\n=== SM-2 Algorithm Demonstration Complete ===")
        
    except Exception as e:
        print(f"Error in SM-2 demonstration: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    demonstrate_srs_workflow()
    demonstrate_sm2_algorithm()