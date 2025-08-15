"""
Spaced Repetition System (SRS) service implementing SM-2 algorithm
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.learning import SRS, Card
from ..core.database import get_db


class SRSService:
    """Service for managing spaced repetition system"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_srs_record(self, card_id: str, user_id: Optional[str] = None) -> SRS:
        """Create a new SRS record for a card"""
        srs = SRS(
            card_id=card_id,
            user_id=user_id,
            ease_factor=2.5,
            interval=1,
            repetitions=0,
            due_date=datetime.utcnow(),
            last_reviewed=None,
            last_grade=None
        )
        
        self.db.add(srs)
        self.db.commit()
        self.db.refresh(srs)
        
        return srs
    
    def grade_card(self, srs_id: str, grade: int) -> SRS:
        """
        Grade a card and update SRS parameters using SM-2 algorithm
        
        Args:
            srs_id: SRS record ID
            grade: Grade from 0-5 scale
                  0-2: Poor performance (reset)
                  3: Minimum passing grade
                  4: Good performance
                  5: Perfect performance
        
        Returns:
            Updated SRS record
        """
        if not (0 <= grade <= 5):
            raise ValueError("Grade must be between 0 and 5")
        
        srs = self.db.query(SRS).filter(SRS.id == srs_id).first()
        if not srs:
            raise ValueError(f"SRS record not found: {srs_id}")
        
        # Update last reviewed and grade
        srs.last_reviewed = datetime.utcnow()
        srs.last_grade = grade
        
        # Apply SM-2 algorithm
        srs = self._apply_sm2_algorithm(srs, grade)
        
        self.db.commit()
        self.db.refresh(srs)
        
        return srs
    
    def _apply_sm2_algorithm(self, srs: SRS, grade: int) -> SRS:
        """
        Apply SM-2 algorithm to update SRS parameters
        
        SM-2 Algorithm:
        1. If grade < 3: reset repetitions to 0, interval to 1
        2. If grade >= 3:
           - If repetitions == 0: interval = 1
           - If repetitions == 1: interval = 6
           - If repetitions > 1: interval = previous_interval * ease_factor
        3. Update ease factor based on grade
        4. Calculate next due date
        """
        
        # Poor performance (quality < 3): reset learning progress
        if grade < 3:
            srs.repetitions = 0
            srs.interval = 1
            srs.ease_factor = max(1.3, srs.ease_factor - 0.2)
        else:
            # Good performance: advance in the schedule
            srs.repetitions += 1
            
            if srs.repetitions == 1:
                srs.interval = 1
            elif srs.repetitions == 2:
                srs.interval = 6
            else:
                srs.interval = int(srs.interval * srs.ease_factor)
            
            # Update ease factor based on performance
            ease_adjustment = 0.1 * (5 - grade) * (0.08 * (5 - grade) + 0.02)
            srs.ease_factor = max(1.3, srs.ease_factor - ease_adjustment)
        
        # Calculate next due date
        srs.due_date = datetime.utcnow() + timedelta(days=srs.interval)
        
        return srs
    
    def get_due_cards(self, user_id: Optional[str] = None, limit: Optional[int] = None) -> List[Tuple[SRS, Card]]:
        """
        Get cards that are due for review
        
        Args:
            user_id: Optional user ID filter
            limit: Optional limit on number of cards
            
        Returns:
            List of (SRS, Card) tuples for due cards
        """
        query = self.db.query(SRS, Card).join(Card)
        
        # Filter by due date (overdue + due today)
        now = datetime.utcnow()
        query = query.filter(SRS.due_date <= now)
        
        # Filter by user if specified
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        # Order by due date (most overdue first)
        query = query.order_by(SRS.due_date.asc())
        
        # Apply limit if specified
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_overdue_cards(self, user_id: Optional[str] = None) -> List[Tuple[SRS, Card]]:
        """Get cards that are overdue for review"""
        query = self.db.query(SRS, Card).join(Card)
        
        # Filter by overdue (due date < today)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(SRS.due_date < today)
        
        # Filter by user if specified
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        # Order by due date (most overdue first)
        query = query.order_by(SRS.due_date.asc())
        
        return query.all()
    
    def get_cards_due_today(self, user_id: Optional[str] = None) -> List[Tuple[SRS, Card]]:
        """Get cards that are due today"""
        query = self.db.query(SRS, Card).join(Card)
        
        # Filter by today's date
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        query = query.filter(
            and_(
                SRS.due_date >= today,
                SRS.due_date < tomorrow
            )
        )
        
        # Filter by user if specified
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        # Order by due date
        query = query.order_by(SRS.due_date.asc())
        
        return query.all()
    
    def get_review_statistics(self, user_id: Optional[str] = None) -> dict:
        """
        Get review statistics for a user
        
        Returns:
            Dictionary with review statistics
        """
        query = self.db.query(SRS)
        
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        all_cards = query.all()
        
        if not all_cards:
            return {
                'total_cards': 0,
                'due_today': 0,
                'overdue': 0,
                'learning': 0,
                'mature': 0,
                'average_ease_factor': 0.0,
                'average_interval': 0.0
            }
        
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        # Count different card states
        due_today = sum(1 for srs in all_cards if today <= srs.due_date < tomorrow)
        overdue = sum(1 for srs in all_cards if srs.due_date < today)
        learning = sum(1 for srs in all_cards if srs.repetitions < 2)
        mature = sum(1 for srs in all_cards if srs.repetitions >= 2)
        
        # Calculate averages
        total_ease = sum(srs.ease_factor for srs in all_cards)
        total_interval = sum(srs.interval for srs in all_cards)
        
        return {
            'total_cards': len(all_cards),
            'due_today': due_today,
            'overdue': overdue,
            'learning': learning,
            'mature': mature,
            'average_ease_factor': round(total_ease / len(all_cards), 2),
            'average_interval': round(total_interval / len(all_cards), 1)
        }
    
    def get_srs_record(self, card_id: str, user_id: Optional[str] = None) -> Optional[SRS]:
        """Get SRS record for a specific card"""
        query = self.db.query(SRS).filter(SRS.card_id == card_id)
        
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        return query.first()
    
    def reset_card_progress(self, srs_id: str) -> SRS:
        """Reset a card's learning progress"""
        srs = self.db.query(SRS).filter(SRS.id == srs_id).first()
        if not srs:
            raise ValueError(f"SRS record not found: {srs_id}")
        
        srs.ease_factor = 2.5
        srs.interval = 1
        srs.repetitions = 0
        srs.due_date = datetime.utcnow()
        srs.last_reviewed = None
        srs.last_grade = None
        
        self.db.commit()
        self.db.refresh(srs)
        
        return srs