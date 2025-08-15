"""
Daily Review and Scheduling Service

Manages daily review sessions, card selection, progress tracking,
and review statistics for the spaced repetition system.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from uuid import UUID, uuid4
import logging
from dataclasses import dataclass
from enum import Enum

from ..models.learning import SRS, Card
from ..models.knowledge import Knowledge
from ..core.database import get_db
from .srs_service import SRSService

logger = logging.getLogger(__name__)


class ReviewSessionStatus(str, Enum):
    """Review session status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class ReviewCard:
    """Card data for review session"""
    srs_id: str
    card_id: str
    card_type: str
    front: str
    back: str
    difficulty: float
    due_date: datetime
    days_overdue: int
    metadata: dict
    knowledge_text: Optional[str] = None
    chapter_title: Optional[str] = None


@dataclass
class ReviewSession:
    """Review session data"""
    session_id: str
    user_id: Optional[str]
    status: ReviewSessionStatus
    cards: List[ReviewCard]
    current_index: int
    total_cards: int
    completed_cards: int
    start_time: datetime
    end_time: Optional[datetime]
    session_stats: Dict[str, Any]


@dataclass
class ReviewStats:
    """Review statistics"""
    total_reviews: int
    correct_reviews: int
    accuracy: float
    average_grade: float
    time_spent: int  # seconds
    cards_per_minute: float
    grade_distribution: Dict[int, int]


class ReviewService:
    """Service for managing daily reviews and scheduling"""
    
    def __init__(self, db: Session):
        self.db = db
        self.srs_service = SRSService(db)
        self._active_sessions: Dict[str, ReviewSession] = {}
    
    def get_daily_review_cards(
        self, 
        user_id: Optional[str] = None,
        max_cards: int = 50,
        prioritize_overdue: bool = True
    ) -> List[ReviewCard]:
        """
        Get cards for daily review (overdue + due today)
        
        Args:
            user_id: Optional user ID filter
            max_cards: Maximum number of cards to return
            prioritize_overdue: Whether to prioritize overdue cards
            
        Returns:
            List of ReviewCard objects optimized for review
        """
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Build base query
        query = (
            self.db.query(SRS, Card, Knowledge)
            .join(Card, SRS.card_id == Card.id)
            .join(Knowledge, Card.knowledge_id == Knowledge.id)
            .filter(SRS.due_date <= now)
        )
        
        # Filter by user if specified
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        # Get all due cards
        due_cards = query.all()
        
        if not due_cards:
            return []
        
        # Convert to ReviewCard objects
        review_cards = []
        for srs, card, knowledge in due_cards:
            days_overdue = max(0, (now.date() - srs.due_date.date()).days)
            
            review_card = ReviewCard(
                srs_id=str(srs.id),
                card_id=str(card.id),
                card_type=card.card_type.value,
                front=card.front,
                back=card.back,
                difficulty=card.difficulty,
                due_date=srs.due_date,
                days_overdue=days_overdue,
                metadata=card.card_metadata or {},
                knowledge_text=knowledge.text,
                chapter_title=getattr(knowledge.chapter, 'title', None) if hasattr(knowledge, 'chapter') else None
            )
            review_cards.append(review_card)
        
        # Optimize card order
        review_cards = self._optimize_review_queue(review_cards, prioritize_overdue)
        
        # Limit to max_cards
        return review_cards[:max_cards]
    
    def _optimize_review_queue(
        self, 
        cards: List[ReviewCard], 
        prioritize_overdue: bool = True
    ) -> List[ReviewCard]:
        """
        Optimize the order of cards for review
        
        Optimization strategy:
        1. Prioritize overdue cards (most overdue first)
        2. Interleave different card types to maintain engagement
        3. Space out cards from the same chapter
        4. Consider difficulty progression
        """
        if not cards:
            return cards
        
        # Separate overdue and due today
        overdue_cards = [c for c in cards if c.days_overdue > 0]
        due_today = [c for c in cards if c.days_overdue == 0]
        
        # Sort overdue by days overdue (descending)
        overdue_cards.sort(key=lambda c: c.days_overdue, reverse=True)
        
        # Sort due today by difficulty (easier first for warm-up)
        due_today.sort(key=lambda c: c.difficulty)
        
        if prioritize_overdue:
            # Start with most overdue, then interleave with due today
            optimized = []
            overdue_idx = 0
            due_idx = 0
            
            # Add overdue cards first (2:1 ratio with due today)
            while overdue_idx < len(overdue_cards) or due_idx < len(due_today):
                # Add 2 overdue cards
                for _ in range(2):
                    if overdue_idx < len(overdue_cards):
                        optimized.append(overdue_cards[overdue_idx])
                        overdue_idx += 1
                
                # Add 1 due today card
                if due_idx < len(due_today):
                    optimized.append(due_today[due_idx])
                    due_idx += 1
            
            return optimized
        else:
            # Simple concatenation: overdue first, then due today
            return overdue_cards + due_today
    
    def start_review_session(
        self, 
        user_id: Optional[str] = None,
        max_cards: int = 20
    ) -> ReviewSession:
        """
        Start a new review session
        
        Args:
            user_id: Optional user ID
            max_cards: Maximum number of cards in session
            
        Returns:
            ReviewSession object
        """
        # Get cards for review
        cards = self.get_daily_review_cards(user_id, max_cards)
        
        if not cards:
            # Create empty session
            session = ReviewSession(
                session_id=str(uuid4()),
                user_id=user_id,
                status=ReviewSessionStatus.COMPLETED,
                cards=[],
                current_index=0,
                total_cards=0,
                completed_cards=0,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                session_stats={}
            )
        else:
            # Create active session
            session = ReviewSession(
                session_id=str(uuid4()),
                user_id=user_id,
                status=ReviewSessionStatus.ACTIVE,
                cards=cards,
                current_index=0,
                total_cards=len(cards),
                completed_cards=0,
                start_time=datetime.utcnow(),
                end_time=None,
                session_stats={
                    'grades': [],
                    'response_times': [],
                    'card_types_reviewed': {},
                    'chapters_reviewed': set()
                }
            )
        
        # Store session in memory for concurrent access
        self._active_sessions[session.session_id] = session
        
        logger.info(f"Started review session {session.session_id} with {len(cards)} cards")
        return session
    
    def get_current_card(self, session_id: str) -> Optional[ReviewCard]:
        """Get the current card in a review session"""
        session = self._active_sessions.get(session_id)
        if not session or session.status != ReviewSessionStatus.ACTIVE:
            return None
        
        if session.current_index >= len(session.cards):
            return None
        
        return session.cards[session.current_index]
    
    def grade_current_card(
        self, 
        session_id: str, 
        grade: int,
        response_time_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Grade the current card in a review session
        
        Args:
            session_id: Review session ID
            grade: Grade from 0-5
            response_time_ms: Optional response time in milliseconds
            
        Returns:
            Dictionary with grading result and next card info
        """
        session = self._active_sessions.get(session_id)
        if not session or session.status != ReviewSessionStatus.ACTIVE:
            raise ValueError(f"Invalid or inactive session: {session_id}")
        
        if session.current_index >= len(session.cards):
            raise ValueError("No more cards in session")
        
        current_card = session.cards[session.current_index]
        
        # Grade the card using SRS service
        try:
            updated_srs = self.srs_service.grade_card(current_card.srs_id, grade)
            
            # Update session statistics
            session.session_stats['grades'].append(grade)
            if response_time_ms:
                session.session_stats['response_times'].append(response_time_ms)
            
            # Track card types and chapters
            card_type = current_card.card_type
            session.session_stats['card_types_reviewed'][card_type] = \
                session.session_stats['card_types_reviewed'].get(card_type, 0) + 1
            
            if current_card.chapter_title:
                session.session_stats['chapters_reviewed'].add(current_card.chapter_title)
            
            # Move to next card
            session.current_index += 1
            session.completed_cards += 1
            
            # Check if session is complete
            if session.current_index >= len(session.cards):
                session.status = ReviewSessionStatus.COMPLETED
                session.end_time = datetime.utcnow()
                logger.info(f"Completed review session {session_id}")
            
            # Prepare response
            result = {
                'success': True,
                'graded_card': {
                    'card_id': current_card.card_id,
                    'grade': grade,
                    'new_due_date': updated_srs.due_date.isoformat(),
                    'new_interval': updated_srs.interval,
                    'ease_factor': updated_srs.ease_factor
                },
                'session_progress': {
                    'completed': session.completed_cards,
                    'total': session.total_cards,
                    'remaining': session.total_cards - session.completed_cards,
                    'progress_percent': round((session.completed_cards / session.total_cards) * 100, 1)
                },
                'next_card': None,
                'session_complete': session.status == ReviewSessionStatus.COMPLETED
            }
            
            # Add next card info if available
            if session.current_index < len(session.cards):
                next_card = session.cards[session.current_index]
                result['next_card'] = {
                    'card_id': next_card.card_id,
                    'card_type': next_card.card_type,
                    'front': next_card.front,
                    'difficulty': next_card.difficulty,
                    'days_overdue': next_card.days_overdue
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error grading card in session {session_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a review session"""
        session = self._active_sessions.get(session_id)
        if not session:
            return None
        
        # Calculate session statistics
        grades = session.session_stats.get('grades', [])
        response_times = session.session_stats.get('response_times', [])
        
        stats = {
            'session_id': session_id,
            'status': session.status.value,
            'progress': {
                'completed': session.completed_cards,
                'total': session.total_cards,
                'remaining': session.total_cards - session.completed_cards,
                'progress_percent': round((session.completed_cards / session.total_cards) * 100, 1) if session.total_cards > 0 else 100
            },
            'timing': {
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration_minutes': self._calculate_session_duration(session)
            },
            'performance': {
                'average_grade': round(sum(grades) / len(grades), 2) if grades else 0,
                'accuracy': round(sum(1 for g in grades if g >= 3) / len(grades) * 100, 1) if grades else 0,
                'grade_distribution': {str(i): grades.count(i) for i in range(6)},
                'average_response_time_ms': round(sum(response_times) / len(response_times)) if response_times else 0
            },
            'content': {
                'card_types_reviewed': session.session_stats.get('card_types_reviewed', {}),
                'chapters_reviewed': list(session.session_stats.get('chapters_reviewed', set()))
            }
        }
        
        return stats
    
    def _calculate_session_duration(self, session: ReviewSession) -> float:
        """Calculate session duration in minutes"""
        end_time = session.end_time or datetime.utcnow()
        duration = end_time - session.start_time
        return round(duration.total_seconds() / 60, 1)
    
    def pause_session(self, session_id: str) -> bool:
        """Pause a review session"""
        session = self._active_sessions.get(session_id)
        if not session or session.status != ReviewSessionStatus.ACTIVE:
            return False
        
        session.status = ReviewSessionStatus.PAUSED
        logger.info(f"Paused review session {session_id}")
        return True
    
    def resume_session(self, session_id: str) -> bool:
        """Resume a paused review session"""
        session = self._active_sessions.get(session_id)
        if not session or session.status != ReviewSessionStatus.PAUSED:
            return False
        
        session.status = ReviewSessionStatus.ACTIVE
        logger.info(f"Resumed review session {session_id}")
        return True
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel a review session"""
        session = self._active_sessions.get(session_id)
        if not session:
            return False
        
        session.status = ReviewSessionStatus.CANCELLED
        session.end_time = datetime.utcnow()
        logger.info(f"Cancelled review session {session_id}")
        return True
    
    def get_daily_review_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive daily review statistics
        
        Returns:
            Dictionary with daily review statistics
        """
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get basic SRS statistics
        srs_stats = self.srs_service.get_review_statistics(user_id)
        
        # Get additional review-specific statistics
        query = self.db.query(SRS)
        if user_id:
            query = query.filter(SRS.user_id == user_id)
        
        # Cards reviewed today
        reviewed_today = query.filter(
            and_(
                SRS.last_reviewed >= today,
                SRS.last_reviewed < today + timedelta(days=1)
            )
        ).all()
        
        # Calculate review performance
        today_grades = [srs.last_grade for srs in reviewed_today if srs.last_grade is not None]
        
        # Upcoming reviews (next 7 days)
        upcoming_query = query.filter(
            and_(
                SRS.due_date > now,
                SRS.due_date <= now + timedelta(days=7)
            )
        )
        upcoming_by_day = {}
        for i in range(1, 8):
            day_start = now + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_count = upcoming_query.filter(
                and_(SRS.due_date >= day_start, SRS.due_date < day_end)
            ).count()
            upcoming_by_day[f"day_{i}"] = day_count
        
        # Combine all statistics
        daily_stats = {
            **srs_stats,
            'today_performance': {
                'cards_reviewed': len(reviewed_today),
                'average_grade': round(sum(today_grades) / len(today_grades), 2) if today_grades else 0,
                'accuracy': round(sum(1 for g in today_grades if g >= 3) / len(today_grades) * 100, 1) if today_grades else 0,
                'grade_distribution': {str(i): today_grades.count(i) for i in range(6)}
            },
            'upcoming_reviews': {
                'next_7_days': sum(upcoming_by_day.values()),
                'by_day': upcoming_by_day
            },
            'review_load': {
                'current_load': srs_stats['due_today'] + srs_stats['overdue'],
                'load_category': self._categorize_review_load(srs_stats['due_today'] + srs_stats['overdue'])
            }
        }
        
        return daily_stats
    
    def _categorize_review_load(self, total_due: int) -> str:
        """Categorize the current review load"""
        if total_due == 0:
            return "none"
        elif total_due <= 10:
            return "light"
        elif total_due <= 30:
            return "moderate"
        elif total_due <= 60:
            return "heavy"
        else:
            return "overwhelming"
    
    def cleanup_completed_sessions(self, hours_old: int = 24) -> int:
        """
        Clean up completed sessions older than specified hours
        
        Args:
            hours_old: Remove sessions completed more than this many hours ago
            
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        
        sessions_to_remove = []
        for session_id, session in self._active_sessions.items():
            if (session.status in [ReviewSessionStatus.COMPLETED, ReviewSessionStatus.CANCELLED] and
                session.end_time and session.end_time < cutoff_time):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self._active_sessions[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old review sessions")
        return len(sessions_to_remove)