"""
Test Analysis API Endpoints
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse

from .models import TestAnalysisReport, ImprovementSuggestion, ExecutiveSummary
from .analyzer import TestResultAnalyzer, ImprovementSuggestionEngine
from .dashboard import TestDashboard, ReportGenerator


# Initialize components
analyzer = TestResultAnalyzer()
suggestion_engine = ImprovementSuggestionEngine()
dashboard = TestDashboard(analyzer)
report_generator = ReportGenerator(analyzer)

router = APIRouter(prefix="/api/test-analysis", tags=["test-analysis"])


@router.post("/analyze")
async def analyze_test_results(
    test_data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Analyze test results and generate comprehensive report
    """
    try:
        # Analyze test results
        report = await analyzer.analyze_test_results(test_data)
        
        # Update trends in background
        background_tasks.add_task(analyzer.update_trends, report)
        
        # Generate improvement suggestions
        suggestions = await suggestion_engine.generate_suggestions(report)
        
        return {
            "status": "success",
            "report_id": report.id,
            "overall_status": report.overall_status.value,
            "overall_pass_rate": report.overall_pass_rate,
            "total_issues": len(report.issues),
            "critical_issues": report.critical_issues_count,
            "suggestions_count": len(suggestions),
            "report_date": report.report_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    days: int = Query(7, description="Number of days for trend analysis")
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data for visualization
    """
    try:
        dashboard_data = await dashboard.get_dashboard_data(days)
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard data: {str(e)}")


@router.get("/reports/latest")
async def get_latest_report() -> Dict[str, Any]:
    """
    Get the latest test analysis report
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        return latest_report.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load report: {str(e)}")


@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> Dict[str, Any]:
    """
    Get specific test analysis report by ID
    """
    try:
        # This would typically load from database
        # For now, we'll return the latest report if ID matches
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report or latest_report.id != report_id:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return latest_report.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load report: {str(e)}")


@router.get("/reports/html/{report_id}")
async def get_html_report(report_id: str) -> HTMLResponse:
    """
    Get HTML formatted test report
    """
    try:
        # Load report
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report or latest_report.id != report_id:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Generate HTML report
        html_content = await report_generator.generate_html_report(latest_report)
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate HTML report: {str(e)}")


@router.get("/suggestions")
async def get_improvement_suggestions() -> List[Dict[str, Any]]:
    """
    Get improvement suggestions based on latest test results
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        suggestions = await suggestion_engine.generate_suggestions(latest_report)
        
        return [suggestion.dict() for suggestion in suggestions]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.get("/executive-summary")
async def get_executive_summary() -> Dict[str, Any]:
    """
    Get executive summary for stakeholders
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        from .analyzer import ExecutiveSummaryGenerator
        summary_generator = ExecutiveSummaryGenerator()
        summary = await summary_generator.generate_summary(latest_report)
        
        return summary.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate executive summary: {str(e)}")


@router.get("/trends")
async def get_test_trends(
    days: int = Query(30, description="Number of days for trend analysis"),
    category: Optional[str] = Query(None, description="Filter by test category")
) -> Dict[str, Any]:
    """
    Get test trend data for analysis
    """
    try:
        trend_data = await dashboard._get_trend_data(days)
        
        # Filter by category if specified
        if category:
            # This would filter the trend data by category
            # Implementation depends on the specific filtering requirements
            pass
        
        return trend_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load trend data: {str(e)}")


@router.get("/coverage")
async def get_coverage_analysis() -> Dict[str, Any]:
    """
    Get detailed coverage analysis
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        coverage_analysis = dashboard._get_coverage_analysis(latest_report)
        
        return coverage_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load coverage analysis: {str(e)}")


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance metrics and benchmarks
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        performance_metrics = dashboard._get_performance_metrics(latest_report)
        
        return performance_metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load performance metrics: {str(e)}")


@router.get("/issues")
async def get_issues_summary(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category")
) -> Dict[str, Any]:
    """
    Get issues summary with optional filtering
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        issue_summary = dashboard._get_issue_summary(latest_report)
        
        # Apply filters if specified
        if severity or category:
            filtered_issues = []
            for issue_data in issue_summary["recent_issues"]:
                if severity and issue_data["severity"] != severity:
                    continue
                if category and issue_data["category"] != category:
                    continue
                filtered_issues.append(issue_data)
            
            issue_summary["recent_issues"] = filtered_issues
            issue_summary["filtered"] = True
        
        return issue_summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load issues summary: {str(e)}")


@router.post("/reports/generate")
async def generate_report(
    format: str = Query("html", description="Report format: html or json"),
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Generate and save test report in specified format
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            raise HTTPException(status_code=404, detail="No reports found")
        
        if format not in ["html", "json"]:
            raise HTTPException(status_code=400, detail="Format must be 'html' or 'json'")
        
        # Generate report in background if requested
        if background_tasks:
            background_tasks.add_task(report_generator.save_report, latest_report, format)
            return {
                "status": "generating",
                "message": f"Report generation started in background",
                "format": format
            }
        else:
            # Generate synchronously
            report_path = await report_generator.save_report(latest_report, format)
            return {
                "status": "completed",
                "report_path": report_path,
                "format": format
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get overall system health based on latest test results
    """
    try:
        latest_report = await dashboard._get_latest_report()
        
        if not latest_report:
            return {
                "status": "unknown",
                "message": "No test data available",
                "health_score": 0
            }
        
        from .analyzer import ExecutiveSummaryGenerator
        summary_generator = ExecutiveSummaryGenerator()
        summary = await summary_generator.generate_summary(latest_report)
        
        # Determine overall health status
        health_score = summary.overall_health_score
        
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 80:
            status = "good"
        elif health_score >= 70:
            status = "fair"
        elif health_score >= 60:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "pass_rate": summary.overall_pass_rate,
            "critical_issues": summary.critical_issues,
            "high_priority_issues": summary.high_priority_issues,
            "performance_status": summary.performance_status,
            "last_updated": latest_report.report_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


# Add router to main app
def setup_test_analysis_routes(app):
    """Setup test analysis routes in the main FastAPI app"""
    app.include_router(router)