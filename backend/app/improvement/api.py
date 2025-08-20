"""
API endpoints for the continuous improvement system
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from .improvement_engine import ContinuousImprovementEngine
from .models import UserFeedback, Improvement, FeatureRequest


# Request/Response models
class FeedbackRequest(BaseModel):
    feature: str
    rating: int
    comment: str
    category: Optional[str] = None
    severity: Optional[str] = None
    user_id: Optional[str] = None


class FeatureRequestRequest(BaseModel):
    title: str
    description: str
    requested_by: str
    user_votes: int = 1


class ImprovementCompletionRequest(BaseModel):
    improvement_id: str
    implementation_notes: Optional[str] = ""


class AnalysisResponse(BaseModel):
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None


# Initialize improvement engine
improvement_engine = ContinuousImprovementEngine()

# Create router
router = APIRouter(prefix="/api/improvement", tags=["improvement"])


@router.post("/feedback", response_model=Dict[str, str])
async def submit_feedback(feedback_request: FeedbackRequest):
    """Submit user feedback for analysis"""
    try:
        feedback = UserFeedback(
            feature=feedback_request.feature,
            rating=feedback_request.rating,
            comment=feedback_request.comment,
            category=feedback_request.category,
            severity=feedback_request.severity,
            user_id=feedback_request.user_id
        )
        
        feedback_id = await improvement_engine.submit_user_feedback(feedback)
        
        return {
            "feedback_id": feedback_id,
            "status": "submitted",
            "message": "Feedback submitted successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


@router.post("/feature-request", response_model=Dict[str, Any])
async def create_feature_request(request: FeatureRequestRequest):
    """Create a new feature request"""
    try:
        feature_request = await improvement_engine.create_feature_request(
            title=request.title,
            description=request.description,
            requested_by=request.requested_by,
            user_votes=request.user_votes
        )
        
        return {
            "feature_request_id": feature_request.id,
            "priority_score": feature_request.priority_score,
            "status": "created",
            "message": "Feature request created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating feature request: {str(e)}")


@router.post("/run-analysis", response_model=AnalysisResponse)
async def run_continuous_analysis(background_tasks: BackgroundTasks):
    """Trigger continuous improvement analysis"""
    try:
        # Run analysis in background
        background_tasks.add_task(improvement_engine.run_continuous_analysis)
        
        return AnalysisResponse(
            status="started",
            message="Continuous improvement analysis started in background"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")


@router.get("/analysis-results", response_model=Dict[str, Any])
async def get_analysis_results():
    """Get latest analysis results"""
    try:
        results = await improvement_engine.run_continuous_analysis()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analysis results: {str(e)}")


@router.get("/improvements", response_model=List[Dict[str, Any]])
async def get_improvements(limit: int = 20, priority: Optional[str] = None):
    """Get current improvement suggestions"""
    try:
        improvements = await improvement_engine.get_top_improvements(limit)
        
        # Filter by priority if specified
        if priority:
            improvements = [imp for imp in improvements if imp.priority.value == priority]
        
        # Convert to dict format for JSON response
        improvements_data = []
        for imp in improvements:
            improvements_data.append({
                "id": imp.id,
                "title": imp.title,
                "description": imp.description,
                "priority": imp.priority.value,
                "category": imp.category.value,
                "status": imp.status.value,
                "suggested_actions": imp.suggested_actions,
                "estimated_effort": imp.estimated_effort,
                "expected_impact": imp.expected_impact,
                "confidence": imp.confidence,
                "created_at": imp.created_at.isoformat(),
                "updated_at": imp.updated_at.isoformat()
            })
        
        return improvements_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting improvements: {str(e)}")


@router.get("/feature-requests", response_model=List[Dict[str, Any]])
async def get_feature_requests(limit: int = 10):
    """Get current feature requests"""
    try:
        feature_requests = improvement_engine.feature_requests[:limit]
        
        # Convert to dict format
        requests_data = []
        for req in feature_requests:
            requests_data.append({
                "id": req.id,
                "title": req.title,
                "description": req.description,
                "requested_by": req.requested_by,
                "priority_score": req.priority_score,
                "user_votes": req.user_votes,
                "business_value": req.business_value,
                "technical_complexity": req.technical_complexity,
                "estimated_effort": req.estimated_effort,
                "status": req.status,
                "created_at": req.created_at.isoformat()
            })
        
        return requests_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feature requests: {str(e)}")


@router.post("/complete-improvement", response_model=Dict[str, Any])
async def mark_improvement_completed(request: ImprovementCompletionRequest):
    """Mark an improvement as completed"""
    try:
        success = await improvement_engine.mark_improvement_completed(
            request.improvement_id,
            request.implementation_notes
        )
        
        if success:
            return {
                "status": "completed",
                "message": "Improvement marked as completed and impact tracking started"
            }
        else:
            raise HTTPException(status_code=404, detail="Improvement not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing improvement: {str(e)}")


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_improvement_dashboard():
    """Get comprehensive improvement dashboard data"""
    try:
        dashboard_data = await improvement_engine.get_improvement_dashboard()
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")


@router.get("/roi-analysis", response_model=Dict[str, Any])
async def get_roi_analysis():
    """Get ROI analysis for current improvements"""
    try:
        roi_data = await improvement_engine.get_roi_analysis()
        return roi_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ROI analysis: {str(e)}")


@router.get("/impact-report/{improvement_id}", response_model=Dict[str, Any])
async def get_impact_report(improvement_id: str, period_days: int = 30):
    """Get impact report for a specific improvement"""
    try:
        impact_report = await improvement_engine.impact_tracker.generate_impact_report(
            improvement_id, period_days
        )
        
        if 'error' in impact_report:
            raise HTTPException(status_code=404, detail=impact_report['error'])
        
        return impact_report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting impact report: {str(e)}")


@router.get("/roadmap", response_model=Dict[str, Any])
async def get_implementation_roadmap(
    total_capacity_hours: int = 160,
    sprint_capacity_hours: int = 40,
    max_effort_hours: Optional[int] = None
):
    """Get implementation roadmap for improvements and features"""
    try:
        constraints = {
            'total_capacity_hours': total_capacity_hours,
            'sprint_capacity_hours': sprint_capacity_hours
        }
        
        if max_effort_hours:
            constraints['max_effort_hours'] = max_effort_hours
        
        roadmap = await improvement_engine.prioritization_engine.create_implementation_roadmap(
            improvement_engine.improvements[:20],  # Top 20 improvements
            improvement_engine.feature_requests[:10],  # Top 10 features
            constraints
        )
        
        # Convert items to serializable format
        for sprint in roadmap.get('sprints', []):
            for item_data in sprint.get('items', []):
                item = item_data['item']
                if hasattr(item, 'dict'):
                    item_data['item'] = item.dict()
                else:
                    # Convert to dict manually
                    item_data['item'] = {
                        'id': getattr(item, 'id', ''),
                        'title': getattr(item, 'title', ''),
                        'description': getattr(item, 'description', ''),
                        'estimated_effort': getattr(item, 'estimated_effort', 0)
                    }
        
        return roadmap
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting roadmap: {str(e)}")


@router.get("/metrics/code-quality", response_model=Dict[str, Any])
async def get_code_quality_metrics():
    """Get current code quality metrics"""
    try:
        metrics = await improvement_engine.code_analyzer.analyze_project()
        
        # Calculate summary statistics
        if metrics:
            summary = {
                'total_files': len(metrics),
                'average_complexity': sum(m.complexity for m in metrics) / len(metrics),
                'average_maintainability': sum(m.maintainability_index for m in metrics) / len(metrics),
                'average_coverage': sum(m.test_coverage for m in metrics) / len(metrics),
                'total_code_smells': sum(m.code_smells for m in metrics),
                'average_technical_debt': sum(m.technical_debt_ratio for m in metrics) / len(metrics)
            }
        else:
            summary = {
                'total_files': 0,
                'average_complexity': 0,
                'average_maintainability': 0,
                'average_coverage': 0,
                'total_code_smells': 0,
                'average_technical_debt': 0
            }
        
        return {
            'summary': summary,
            'metrics': [m.dict() for m in metrics[:20]]  # Return top 20 for performance
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting code quality metrics: {str(e)}")


@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "continuous_improvement",
        "timestamp": datetime.now().isoformat()
    }