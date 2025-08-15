"""
Review API endpoints for daily review and scheduling system
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..services.review_service import ReviewService, ReviewCard, ReviewSession
from ..services.srs_service import SRSService

router = APIRouter(prefix="/reviews", tags=["reviews"])


# Request/Response Models
class ReviewCardResponse(BaseModel):
    """Response model for review card"""
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

    class Config:
        from_attributes = True


class ReviewSessionResponse(BaseModel):
    """Response model for review session"""
    session_id: str
    user_id: Optional[str]
    status: str
    total_cards: int
    completed_cards: int
    current_index: int
    start_time: datetime
    end_time: Optional[datetime]


class GradeCardRequest(BaseModel):
    """Request model for grading a card"""
    grade: int = Field(..., ge=0, le=5, description="Grade from 0-5")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")


class GradeCardResponse(BaseModel):
    """Response model for card grading"""
    success: bool
    graded_card: Optional[Dict[str, Any]] = None
    session_progress: Optional[Dict[str, Any]] = None
    next_card: Optional[Dict[str, Any]] = None
    session_complete: bool = False
    error: Optional[str] = None


class ReviewStatsResponse(BaseModel):
    """Response model for review statistics"""
    total_cards: int
    due_today: int
    overdue: int
    learning: int
    mature: int
    average_ease_factor: float
    average_interval: float
    today_performance: Dict[str, Any]
    upcoming_reviews: Dict[str, Any]
    review_load: Dict[str, Any]


@router.get("/review/today", response_model=List[ReviewCardResponse])
async def get_daily_review_cards(
    user_id: Optional[str] = Query(None, description="User ID filter"),
    max_cards: int = Query(50, ge=1, le=100, description="Maximum number of cards"),
    prioritize_overdue: bool = Query(True, description="Prioritize overdue cards"),
    db: Session = Depends(get_db)
):
    """
    Get cards for daily review (overdue + due today)
    
    Returns optimized list of cards for review session.
    """
    try:
        review_service = ReviewService(db)
        cards = review_service.get_daily_review_cards(
            user_id=user_id,
            max_cards=max_cards,
            prioritize_overdue=prioritize_overdue
        )
        
        return [ReviewCardResponse(**card.__dict__) for card in cards]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily review cards: {str(e)}")


@router.post("/session/start", response_model=ReviewSessionResponse)
async def start_review_session(
    user_id: Optional[str] = Query(None, description="User ID"),
    max_cards: int = Query(20, ge=1, le=50, description="Maximum cards in session"),
    db: Session = Depends(get_db)
):
    """
    Start a new review session
    
    Creates a new review session with optimized card selection.
    """
    try:
        review_service = ReviewService(db)
        session = review_service.start_review_session(
            user_id=user_id,
            max_cards=max_cards
        )
        
        return ReviewSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            status=session.status.value,
            total_cards=session.total_cards,
            completed_cards=session.completed_cards,
            current_index=session.current_index,
            start_time=session.start_time,
            end_time=session.end_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start review session: {str(e)}")


@router.get("/session/{session_id}/current", response_model=Optional[ReviewCardResponse])
async def get_current_card(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current card in a review session
    """
    try:
        review_service = ReviewService(db)
        card = review_service.get_current_card(session_id)
        
        if not card:
            return None
        
        return ReviewCardResponse(**card.__dict__)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current card: {str(e)}")


@router.post("/review/grade", response_model=GradeCardResponse)
async def grade_card_in_session(
    session_id: str = Query(..., description="Review session ID"),
    grade_request: GradeCardRequest = ...,
    db: Session = Depends(get_db)
):
    """
    Grade the current card in a review session
    
    Requirements: 8.2 - Card grading and SRS updates
    """
    return await grade_current_card(session_id, grade_request, db)


@router.post("/session/{session_id}/grade", response_model=GradeCardResponse)
async def grade_current_card(
    session_id: str,
    grade_request: GradeCardRequest,
    db: Session = Depends(get_db)
):
    """
    Grade the current card in a review session
    
    Updates SRS parameters and advances to next card.
    """
    try:
        review_service = ReviewService(db)
        result = review_service.grade_current_card(
            session_id=session_id,
            grade=grade_request.grade,
            response_time_ms=grade_request.response_time_ms
        )
        
        return GradeCardResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grade card: {str(e)}")


@router.get("/session/{session_id}/progress")
async def get_session_progress(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get progress information for a review session
    """
    try:
        review_service = ReviewService(db)
        progress = review_service.get_session_progress(session_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session progress: {str(e)}")


@router.post("/session/{session_id}/pause")
async def pause_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Pause a review session
    """
    try:
        review_service = ReviewService(db)
        success = review_service.pause_session(session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot pause session")
        
        return {"success": True, "message": "Session paused"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause session: {str(e)}")


@router.post("/session/{session_id}/resume")
async def resume_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Resume a paused review session
    """
    try:
        review_service = ReviewService(db)
        success = review_service.resume_session(session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot resume session")
        
        return {"success": True, "message": "Session resumed"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume session: {str(e)}")


@router.post("/session/{session_id}/cancel")
async def cancel_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a review session
    """
    try:
        review_service = ReviewService(db)
        success = review_service.cancel_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel session: {str(e)}")


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_daily_review_stats(
    user_id: Optional[str] = Query(None, description="User ID filter"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive daily review statistics
    
    Returns statistics about due cards, performance, and upcoming reviews.
    """
    try:
        review_service = ReviewService(db)
        stats = review_service.get_daily_review_stats(user_id)
        
        return ReviewStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get review stats: {str(e)}")


@router.get("/stats/performance")
async def get_performance_metrics(
    user_id: Optional[str] = Query(None, description="User ID filter"),
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get detailed performance metrics over time
    """
    try:
        # This would require additional implementation for historical tracking
        # For now, return current day performance
        review_service = ReviewService(db)
        stats = review_service.get_daily_review_stats(user_id)
        
        return {
            "period_days": days,
            "current_performance": stats["today_performance"],
            "trend_analysis": {
                "accuracy_trend": "stable",  # Would need historical data
                "volume_trend": "stable",
                "difficulty_trend": "stable"
            },
            "recommendations": [
                "Continue regular review schedule" if stats["review_load"]["current_load"] <= 30 
                else "Consider increasing daily review time"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_sessions(
    hours_old: int = Query(24, ge=1, le=168, description="Remove sessions older than this many hours"),
    db: Session = Depends(get_db)
):
    """
    Clean up old completed review sessions
    
    Removes completed sessions from memory to free up resources.
    """
    try:
        review_service = ReviewService(db)
        cleaned_count = review_service.cleanup_completed_sessions(hours_old)
        
        return {
            "success": True,
            "cleaned_sessions": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old sessions"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup sessions: {str(e)}")


# Legacy SRS endpoints for backward compatibility
@router.post("/grade/{srs_id}")
async def grade_card_direct(
    srs_id: str,
    grade_request: GradeCardRequest,
    db: Session = Depends(get_db)
):
    """
    Grade a card directly (without session management)
    
    This is a legacy endpoint for direct card grading.
    """
    try:
        srs_service = SRSService(db)
        updated_srs = srs_service.grade_card(srs_id, grade_request.grade)
        
        return {
            "success": True,
            "srs_id": str(updated_srs.id),
            "new_due_date": updated_srs.due_date.isoformat(),
            "new_interval": updated_srs.interval,
            "ease_factor": updated_srs.ease_factor,
            "repetitions": updated_srs.repetitions
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to grade card: {str(e)}")


@router.get("/due")
async def get_due_cards(
    user_id: Optional[str] = Query(None, description="User ID filter"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of cards"),
    db: Session = Depends(get_db)
):
    """
    Get due cards (legacy endpoint)
    
    Use /reviews/today for the optimized daily review cards.
    """
    try:
        srs_service = SRSService(db)
        due_cards = srs_service.get_due_cards(user_id, limit)
        
        result = []
        for srs, card in due_cards:
            result.append({
                "srs_id": str(srs.id),
                "card_id": str(card.id),
                "card_type": card.card_type.value,
                "front": card.front,
                "back": card.back,
                "difficulty": card.difficulty,
                "due_date": srs.due_date.isoformat(),
                "ease_factor": srs.ease_factor,
                "interval": srs.interval,
                "repetitions": srs.repetitions
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get due cards: {str(e)}")