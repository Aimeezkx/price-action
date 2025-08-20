"""
Production Readiness API
REST API endpoints for production readiness validation
"""

try:
    from fastapi import APIRouter, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
except ImportError:
    # Fallback for when FastAPI is not available
    class APIRouter:
        def __init__(self, **kwargs):
            pass
        def post(self, path):
            def decorator(func):
                return func
            return decorator
        def get(self, path):
            def decorator(func):
                return func
            return decorator
        def delete(self, path):
            def decorator(func):
                return func
            return decorator
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
    
    class BackgroundTasks:
        def add_task(self, func, *args, **kwargs):
            pass

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json

from .validator import ProductionReadinessOrchestrator, ProductionReadinessValidator
from .models import (
    ProductionEnvironment, DeploymentConfig, ValidationReport,
    ProductionValidationSuite, ValidationStatus
)

router = APIRouter(prefix="/api/v1/production-readiness", tags=["production-readiness"])

# In-memory storage for validation results (in production, use a database)
validation_results = {}
active_validations = {}


@router.post("/validate")
async def start_production_validation(
    environment_config: Dict[str, Any],
    deployment_config: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Start production readiness validation"""
    try:
        # Validate input configurations
        environment = ProductionEnvironment(**environment_config)
        config = DeploymentConfig(**deployment_config)
        
        # Generate validation ID
        validation_id = f"validation_{int(datetime.now().timestamp())}"
        
        # Store validation as active
        active_validations[validation_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "environment": environment.name,
            "version": config.version
        }
        
        # Start validation in background
        background_tasks.add_task(
            run_validation_background,
            validation_id,
            environment_config,
            deployment_config
        )
        
        return {
            "validation_id": validation_id,
            "status": "started",
            "message": "Production readiness validation started",
            "estimated_duration_minutes": 10
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


@router.get("/validate/{validation_id}")
async def get_validation_status(validation_id: str) -> Dict[str, Any]:
    """Get validation status and results"""
    
    # Check if validation is still running
    if validation_id in active_validations:
        return {
            "validation_id": validation_id,
            "status": "running",
            "details": active_validations[validation_id]
        }
    
    # Check if validation is completed
    if validation_id in validation_results:
        result = validation_results[validation_id]
        return {
            "validation_id": validation_id,
            "status": "completed",
            "report": result
        }
    
    raise HTTPException(status_code=404, detail="Validation not found")


@router.get("/validate/{validation_id}/report")
async def get_validation_report(validation_id: str) -> ValidationReport:
    """Get detailed validation report"""
    
    if validation_id not in validation_results:
        raise HTTPException(status_code=404, detail="Validation report not found")
    
    return validation_results[validation_id]


@router.get("/validate/{validation_id}/summary")
async def get_validation_summary(validation_id: str) -> Dict[str, Any]:
    """Get validation summary"""
    
    if validation_id not in validation_results:
        raise HTTPException(status_code=404, detail="Validation not found")
    
    report = validation_results[validation_id]
    
    return {
        "validation_id": validation_id,
        "environment": report.environment,
        "version": report.version,
        "production_ready": report.production_ready,
        "summary": report.summary,
        "total_checks": len(report.check_results),
        "passed_checks": len([c for c in report.check_results if c["status"] == "passed"]),
        "failed_checks": len([c for c in report.check_results if c["status"] == "failed"]),
        "warning_checks": len([c for c in report.check_results if c["status"] == "warning"]),
        "critical_failures": len([
            c for c in report.check_results 
            if c["status"] == "failed" and c["severity"] == "critical"
        ]),
        "generated_at": report.generated_at.isoformat()
    }


@router.get("/validate")
async def list_validations() -> Dict[str, Any]:
    """List all validations"""
    
    # Combine active and completed validations
    all_validations = []
    
    # Add active validations
    for validation_id, details in active_validations.items():
        all_validations.append({
            "validation_id": validation_id,
            "status": "running",
            "environment": details["environment"],
            "version": details["version"],
            "started_at": details["started_at"]
        })
    
    # Add completed validations
    for validation_id, report in validation_results.items():
        all_validations.append({
            "validation_id": validation_id,
            "status": "completed",
            "environment": report.environment,
            "version": report.version,
            "production_ready": report.production_ready,
            "generated_at": report.generated_at.isoformat()
        })
    
    # Sort by most recent first
    all_validations.sort(key=lambda x: x.get("started_at", x.get("generated_at", "")), reverse=True)
    
    return {
        "validations": all_validations,
        "total_count": len(all_validations),
        "active_count": len(active_validations),
        "completed_count": len(validation_results)
    }


@router.delete("/validate/{validation_id}")
async def delete_validation(validation_id: str) -> Dict[str, Any]:
    """Delete validation results"""
    
    deleted = False
    
    # Remove from active validations
    if validation_id in active_validations:
        del active_validations[validation_id]
        deleted = True
    
    # Remove from completed validations
    if validation_id in validation_results:
        del validation_results[validation_id]
        deleted = True
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Validation not found")
    
    return {
        "validation_id": validation_id,
        "status": "deleted",
        "message": "Validation results deleted successfully"
    }


@router.post("/validate/quick")
async def quick_validation_check(
    environment_config: Dict[str, Any],
    deployment_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Run a quick validation check (subset of full validation)"""
    try:
        # Validate input configurations
        environment = ProductionEnvironment(**environment_config)
        config = DeploymentConfig(**deployment_config)
        
        # Create validator
        validator = ProductionReadinessValidator(environment, config)
        
        # Run only critical deployment checks
        deployment_checks = await validator.deployment_validator.validate_deployment_readiness()
        
        # Filter to only critical checks
        critical_checks = [
            check for check in deployment_checks 
            if check.severity.value in ["critical", "high"]
        ]
        
        # Calculate quick summary
        failed_critical = [c for c in critical_checks if c.status == ValidationStatus.FAILED]
        
        return {
            "quick_validation": True,
            "total_critical_checks": len(critical_checks),
            "failed_critical_checks": len(failed_critical),
            "ready_for_full_validation": len(failed_critical) == 0,
            "critical_issues": [
                {
                    "name": check.name,
                    "description": check.description,
                    "error": check.error_message
                }
                for check in failed_critical
            ],
            "recommendation": (
                "Ready for full validation" if len(failed_critical) == 0 
                else "Fix critical issues before full validation"
            )
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Quick validation failed: {str(e)}")


@router.get("/config/sample")
async def get_sample_configurations() -> Dict[str, Any]:
    """Get sample environment and deployment configurations"""
    
    return {
        "environment_config": ProductionReadinessOrchestrator.create_sample_environment_config(),
        "deployment_config": ProductionReadinessOrchestrator.create_sample_deployment_config(),
        "description": "Sample configurations for production readiness validation"
    }


@router.post("/config/validate")
async def validate_configurations(
    environment_config: Dict[str, Any],
    deployment_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate configuration format without running full validation"""
    
    try:
        # Validate environment configuration
        environment = ProductionEnvironment(**environment_config)
        
        # Validate deployment configuration
        config = DeploymentConfig(**deployment_config)
        
        return {
            "valid": True,
            "environment_name": environment.name,
            "deployment_version": config.version,
            "message": "Configurations are valid"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Configuration validation failed"
        }


async def run_validation_background(
    validation_id: str,
    environment_config: Dict[str, Any],
    deployment_config: Dict[str, Any]
):
    """Run validation in background task"""
    try:
        # Run full validation
        report = await ProductionReadinessOrchestrator.validate_production_readiness(
            environment_config,
            deployment_config
        )
        
        # Store results
        validation_results[validation_id] = report
        
        # Remove from active validations
        if validation_id in active_validations:
            del active_validations[validation_id]
            
    except Exception as e:
        # Store error result
        validation_results[validation_id] = {
            "validation_id": validation_id,
            "status": "error",
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }
        
        # Remove from active validations
        if validation_id in active_validations:
            del active_validations[validation_id]


# Health check endpoint for the production readiness service itself
@router.get("/health")
async def production_readiness_health() -> Dict[str, Any]:
    """Health check for production readiness validation service"""
    
    return {
        "status": "healthy",
        "service": "production-readiness-validation",
        "timestamp": datetime.now().isoformat(),
        "active_validations": len(active_validations),
        "completed_validations": len(validation_results),
        "version": "1.0.0"
    }