"""
Bug Tracking API

REST API endpoints for bug tracking and issue management functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from ..services.bug_tracking_service import (
    BugTrackingService, TestIssue, IssueSeverity, IssueCategory, 
    IssueStatus, ReproductionStep
)
from ..services.bug_reproduction_service import BugReproductionService
from ..services.bug_fix_verification_service import BugFixVerificationService

router = APIRouter(prefix="/api/bug-tracking", tags=["bug-tracking"])

# Pydantic models for API
class ReproductionStepModel(BaseModel):
    step_number: int
    action: str
    expected_result: str
    actual_result: str
    screenshot_path: Optional[str] = None
    data_used: Optional[Dict[str, Any]] = None

class CreateIssueRequest(BaseModel):
    title: str
    description: str
    test_case: str
    expected_behavior: str
    actual_behavior: str
    environment: Dict[str, str]
    error_trace: Optional[str] = None
    reproduction_steps: Optional[List[ReproductionStepModel]] = None

class UpdateIssueRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    severity: Optional[IssueSeverity] = None
    category: Optional[IssueCategory] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None

class IssueResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: IssueSeverity
    category: IssueCategory
    status: IssueStatus
    test_case: str
    expected_behavior: str
    actual_behavior: str
    environment: Dict[str, str]
    error_trace: Optional[str]
    created_at: datetime
    updated_at: datetime
    assigned_to: Optional[str]
    tags: List[str]
    related_issues: List[str]
    fix_commit: Optional[str]
    verification_test: Optional[str]

class VerifyFixRequest(BaseModel):
    fix_commit: str

class ApproveFixRequest(BaseModel):
    fix_commit: str
    approver: str

# Dependency to get bug tracking service
def get_bug_tracking_service() -> BugTrackingService:
    return BugTrackingService()

def get_reproduction_service() -> BugReproductionService:
    return BugReproductionService()

def get_verification_service() -> BugFixVerificationService:
    return BugFixVerificationService()

@router.post("/issues", response_model=IssueResponse)
async def create_issue(
    request: CreateIssueRequest,
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Create a new issue"""
    try:
        # Convert reproduction steps
        reproduction_steps = []
        if request.reproduction_steps:
            for step_data in request.reproduction_steps:
                step = ReproductionStep(
                    step_number=step_data.step_number,
                    action=step_data.action,
                    expected_result=step_data.expected_result,
                    actual_result=step_data.actual_result,
                    screenshot_path=step_data.screenshot_path,
                    data_used=step_data.data_used
                )
                reproduction_steps.append(step)
        
        issue = service.create_issue(
            title=request.title,
            description=request.description,
            test_case=request.test_case,
            expected_behavior=request.expected_behavior,
            actual_behavior=request.actual_behavior,
            environment=request.environment,
            error_trace=request.error_trace,
            reproduction_steps=reproduction_steps
        )
        
        return IssueResponse(**issue.__dict__)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issues", response_model=List[IssueResponse])
async def list_issues(
    status: Optional[IssueStatus] = Query(None),
    category: Optional[IssueCategory] = Query(None),
    severity: Optional[IssueSeverity] = Query(None),
    limit: Optional[int] = Query(None),
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """List issues with optional filtering"""
    try:
        issues = service.list_issues(
            status=status,
            category=category,
            severity=severity,
            limit=limit
        )
        
        return [IssueResponse(**issue.__dict__) for issue in issues]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: str,
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Get issue by ID"""
    try:
        issue = service.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return IssueResponse(**issue.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/issues/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: str,
    request: UpdateIssueRequest,
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Update an existing issue"""
    try:
        # Filter out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        issue = service.update_issue(issue_id, **updates)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return IssueResponse(**issue.__dict__)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issues/{issue_id}/mark-fixed")
async def mark_issue_fixed(
    issue_id: str,
    request: VerifyFixRequest,
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Mark issue as fixed and generate regression test"""
    try:
        issue = service.mark_issue_fixed(issue_id, request.fix_commit)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return {
            "message": "Issue marked as fixed",
            "issue_id": issue_id,
            "fix_commit": request.fix_commit,
            "regression_test": issue.verification_test
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issues/{issue_id}/generate-regression-test")
async def generate_regression_test(
    issue_id: str,
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Generate regression test for an issue"""
    try:
        test_code = service.generate_regression_test(issue_id)
        if not test_code:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return {
            "message": "Regression test generated",
            "issue_id": issue_id,
            "test_code": test_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-from-logs")
async def detect_issues_from_logs(
    log_entries: List[str],
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Detect issues from log entries"""
    try:
        issues = service.detect_issues_from_logs(log_entries)
        
        return {
            "message": f"Detected {len(issues)} potential issues",
            "issues": [IssueResponse(**issue.__dict__) for issue in issues]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-from-test-failures")
async def detect_issues_from_test_failures(
    test_results: Dict[str, Any],
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Detect issues from test failure results"""
    try:
        issues = service.detect_issues_from_test_failures(test_results)
        
        return {
            "message": f"Detected {len(issues)} issues from test failures",
            "issues": [IssueResponse(**issue.__dict__) for issue in issues]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_issue_statistics(
    service: BugTrackingService = Depends(get_bug_tracking_service)
):
    """Get issue statistics"""
    try:
        stats = service.get_issue_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reproduction endpoints
@router.post("/issues/{issue_id}/reproduction-documentation")
async def create_reproduction_documentation(
    issue_id: str,
    bug_service: BugTrackingService = Depends(get_bug_tracking_service),
    repro_service: BugReproductionService = Depends(get_reproduction_service)
):
    """Generate reproduction documentation for an issue"""
    try:
        issue = bug_service.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        documentation = repro_service.document_reproduction_steps(issue)
        
        return {
            "message": "Reproduction documentation created",
            "issue_id": issue_id,
            "documentation": documentation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issues/{issue_id}/reproduction-script")
async def create_reproduction_script(
    issue_id: str,
    script_type: str = Query("pytest", description="Type of script: pytest, playwright, api, manual"),
    bug_service: BugTrackingService = Depends(get_bug_tracking_service),
    repro_service: BugReproductionService = Depends(get_reproduction_service)
):
    """Create reproduction script for an issue"""
    try:
        issue = bug_service.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        script = repro_service.create_reproduction_script(issue, script_type)
        
        return {
            "message": "Reproduction script created",
            "script_id": script.script_id,
            "script_type": script.script_type,
            "script_content": script.script_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reproduction-scripts/{script_id}/run")
async def run_reproduction_script(
    script_id: str,
    repro_service: BugReproductionService = Depends(get_reproduction_service)
):
    """Run a reproduction script"""
    try:
        result = repro_service.run_reproduction_script(script_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issues/{issue_id}/verify-fix")
async def verify_issue_fix(
    issue_id: str,
    repro_service: BugReproductionService = Depends(get_reproduction_service)
):
    """Verify that an issue has been fixed"""
    try:
        result = repro_service.verify_fix(issue_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fix verification endpoints
@router.post("/issues/{issue_id}/verify-fix-comprehensive")
async def verify_fix_comprehensive(
    issue_id: str,
    request: VerifyFixRequest,
    bug_service: BugTrackingService = Depends(get_bug_tracking_service),
    verification_service: BugFixVerificationService = Depends(get_verification_service)
):
    """Comprehensive fix verification"""
    try:
        issue = bug_service.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        result = verification_service.verify_fix(issue, request.fix_commit)
        
        return {
            "message": "Fix verification completed",
            "verification_result": {
                "issue_id": result.issue_id,
                "fix_commit": result.fix_commit,
                "verification_status": result.verification_status,
                "tests_passed": result.tests_passed,
                "reproduction_scripts_passed": result.reproduction_scripts_passed,
                "regression_tests_passed": result.regression_tests_passed,
                "performance_impact": result.performance_impact,
                "code_quality_score": result.code_quality_score,
                "recommendations": result.recommendations
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/issues/{issue_id}/verification-history")
async def get_verification_history(
    issue_id: str,
    verification_service: BugFixVerificationService = Depends(get_verification_service)
):
    """Get verification history for an issue"""
    try:
        history = verification_service.get_verification_history(issue_id)
        
        return {
            "issue_id": issue_id,
            "verification_count": len(history),
            "history": [
                {
                    "fix_commit": result.fix_commit,
                    "verification_time": result.verification_time.isoformat(),
                    "verification_status": result.verification_status,
                    "tests_passed": result.tests_passed,
                    "reproduction_scripts_passed": result.reproduction_scripts_passed,
                    "regression_tests_passed": result.regression_tests_passed
                }
                for result in history
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issues/{issue_id}/approve-fix")
async def approve_fix(
    issue_id: str,
    request: ApproveFixRequest,
    verification_service: BugFixVerificationService = Depends(get_verification_service)
):
    """Approve a fix after verification"""
    try:
        result = verification_service.approve_fix(
            issue_id, 
            request.fix_commit, 
            request.approver
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))