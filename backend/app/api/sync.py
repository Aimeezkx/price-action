"""
Cross-platform data synchronization API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import UUID
import json

from app.core.database import get_async_db
from app.models.document import Document, Chapter, Figure
from app.models.knowledge import Knowledge
from app.models.learning import Card, SRS
from app.services.sync_service import SyncService, SyncConflictResolver
from app.utils.logging import SecurityLogger

router = APIRouter(prefix="/api/sync", tags=["sync"])
security_logger = SecurityLogger(__name__)


# Request/Response Models
class SyncRequest(BaseModel):
    """Request model for sync operations"""
    last_sync_time: Optional[datetime] = None
    client_id: str = Field(..., description="Unique client identifier")
    platform: str = Field(..., description="Platform (web/ios)")
    changes: List[Dict[str, Any]] = Field(default_factory=list)


class SyncChange(BaseModel):
    """Model for individual sync changes"""
    id: str
    entity_type: str  # document, chapter, card, srs
    operation: str  # create, update, delete
    data: Dict[str, Any]
    timestamp: datetime
    client_id: str
    version: int = 1


class SyncResponse(BaseModel):
    """Response model for sync operations"""
    success: bool
    sync_time: datetime
    changes: List[SyncChange]
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    next_sync_token: Optional[str] = None
    stats: Dict[str, int] = Field(default_factory=dict)


class ConflictResolution(BaseModel):
    """Model for conflict resolution"""
    conflict_id: str
    resolution: str  # "client_wins", "server_wins", "merge"
    merged_data: Optional[Dict[str, Any]] = None


@router.post("/pull", response_model=SyncResponse)
async def pull_changes(
    sync_request: SyncRequest,
    db: AsyncSession = Depends(get_async_db)
) -> SyncResponse:
    """
    Pull changes from server since last sync
    
    Requirements: 12.5 - Cross-platform data synchronization
    """
    try:
        sync_service = SyncService(db)
        
        # Get changes since last sync
        changes = await sync_service.get_changes_since(
            last_sync_time=sync_request.last_sync_time,
            client_id=sync_request.client_id,
            platform=sync_request.platform
        )
        
        # Log sync activity
        security_logger.log_security_event(
            "sync_pull_request",
            {
                "client_id": sync_request.client_id,
                "platform": sync_request.platform,
                "last_sync": sync_request.last_sync_time.isoformat() if sync_request.last_sync_time else None,
                "changes_count": len(changes)
            },
            "INFO"
        )
        
        return SyncResponse(
            success=True,
            sync_time=datetime.now(timezone.utc),
            changes=changes,
            stats={
                "pulled_changes": len(changes),
                "documents": len([c for c in changes if c.entity_type == "document"]),
                "cards": len([c for c in changes if c.entity_type == "card"]),
                "srs": len([c for c in changes if c.entity_type == "srs"])
            }
        )
        
    except Exception as e:
        security_logger.log_error(e, {
            "operation": "sync_pull",
            "client_id": sync_request.client_id
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pull changes: {str(e)}"
        )


@router.post("/push", response_model=SyncResponse)
async def push_changes(
    sync_request: SyncRequest,
    db: AsyncSession = Depends(get_async_db)
) -> SyncResponse:
    """
    Push changes from client to server
    
    Requirements: 12.5 - Cross-platform data synchronization with conflict resolution
    """
    try:
        sync_service = SyncService(db)
        conflict_resolver = SyncConflictResolver(db)
        
        # Process each change and detect conflicts
        processed_changes = []
        conflicts = []
        
        for change_data in sync_request.changes:
            change = SyncChange(**change_data)
            
            # Check for conflicts
            conflict = await conflict_resolver.detect_conflict(change)
            
            if conflict:
                conflicts.append(conflict)
                # Apply default conflict resolution (server wins for now)
                resolved_change = await conflict_resolver.resolve_conflict(
                    conflict, "server_wins"
                )
                if resolved_change:
                    processed_changes.append(resolved_change)
            else:
                # Apply change directly
                applied_change = await sync_service.apply_change(change)
                processed_changes.append(applied_change)
        
        # Update sync metadata
        await sync_service.update_sync_metadata(
            client_id=sync_request.client_id,
            platform=sync_request.platform,
            sync_time=datetime.now(timezone.utc)
        )
        
        await db.commit()
        
        # Log sync activity
        security_logger.log_security_event(
            "sync_push_request",
            {
                "client_id": sync_request.client_id,
                "platform": sync_request.platform,
                "changes_pushed": len(sync_request.changes),
                "conflicts_detected": len(conflicts),
                "changes_applied": len(processed_changes)
            },
            "INFO"
        )
        
        return SyncResponse(
            success=True,
            sync_time=datetime.now(timezone.utc),
            changes=processed_changes,
            conflicts=conflicts,
            stats={
                "pushed_changes": len(sync_request.changes),
                "applied_changes": len(processed_changes),
                "conflicts": len(conflicts)
            }
        )
        
    except Exception as e:
        await db.rollback()
        security_logger.log_error(e, {
            "operation": "sync_push",
            "client_id": sync_request.client_id
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to push changes: {str(e)}"
        )


@router.post("/resolve-conflicts", response_model=SyncResponse)
async def resolve_conflicts(
    resolutions: List[ConflictResolution],
    client_id: str = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_async_db)
) -> SyncResponse:
    """
    Resolve sync conflicts with user decisions
    
    Requirements: 12.5 - Conflict resolution for concurrent edits
    """
    try:
        conflict_resolver = SyncConflictResolver(db)
        resolved_changes = []
        
        for resolution in resolutions:
            resolved_change = await conflict_resolver.apply_resolution(resolution)
            if resolved_change:
                resolved_changes.append(resolved_change)
        
        await db.commit()
        
        # Log conflict resolution
        security_logger.log_security_event(
            "sync_conflicts_resolved",
            {
                "client_id": client_id,
                "conflicts_resolved": len(resolutions),
                "changes_applied": len(resolved_changes)
            },
            "INFO"
        )
        
        return SyncResponse(
            success=True,
            sync_time=datetime.now(timezone.utc),
            changes=resolved_changes,
            stats={
                "resolved_conflicts": len(resolutions),
                "applied_changes": len(resolved_changes)
            }
        )
        
    except Exception as e:
        await db.rollback()
        security_logger.log_error(e, {
            "operation": "conflict_resolution",
            "client_id": client_id
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve conflicts: {str(e)}"
        )


@router.get("/status")
async def get_sync_status(
    client_id: str = Query(..., description="Client ID"),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get sync status for a client
    
    Requirements: 12.5 - Sync status indicators
    """
    try:
        sync_service = SyncService(db)
        status = await sync_service.get_sync_status(client_id)
        
        return {
            "client_id": client_id,
            "last_sync_time": status.get("last_sync_time"),
            "pending_changes": status.get("pending_changes", 0),
            "sync_conflicts": status.get("conflicts", 0),
            "data_consistency": status.get("consistency_check", True),
            "sync_health": "healthy" if status.get("consistency_check", True) else "needs_attention"
        }
        
    except Exception as e:
        security_logger.log_error(e, {
            "operation": "sync_status",
            "client_id": client_id
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/validate-consistency")
async def validate_data_consistency(
    client_id: str = Query(..., description="Client ID"),
    entity_checksums: Dict[str, str] = {},
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Validate data consistency between client and server
    
    Requirements: 12.5 - Data consistency validation across platforms
    """
    try:
        sync_service = SyncService(db)
        
        # Validate checksums for each entity type
        consistency_results = {}
        inconsistencies = []
        
        for entity_type, client_checksum in entity_checksums.items():
            server_checksum = await sync_service.calculate_entity_checksum(
                entity_type, client_id
            )
            
            is_consistent = client_checksum == server_checksum
            consistency_results[entity_type] = {
                "consistent": is_consistent,
                "client_checksum": client_checksum,
                "server_checksum": server_checksum
            }
            
            if not is_consistent:
                inconsistencies.append({
                    "entity_type": entity_type,
                    "client_checksum": client_checksum,
                    "server_checksum": server_checksum
                })
        
        overall_consistent = len(inconsistencies) == 0
        
        # Log consistency check
        security_logger.log_security_event(
            "sync_consistency_check",
            {
                "client_id": client_id,
                "overall_consistent": overall_consistent,
                "inconsistencies": len(inconsistencies),
                "checked_entities": list(entity_checksums.keys())
            },
            "INFO" if overall_consistent else "WARNING"
        )
        
        return {
            "client_id": client_id,
            "overall_consistent": overall_consistent,
            "entity_results": consistency_results,
            "inconsistencies": inconsistencies,
            "recommendation": "full_sync" if inconsistencies else "continue_normal_sync"
        }
        
    except Exception as e:
        security_logger.log_error(e, {
            "operation": "consistency_validation",
            "client_id": client_id
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate consistency: {str(e)}"
        )


@router.post("/full-sync")
async def perform_full_sync(
    client_id: str = Query(..., description="Client ID"),
    platform: str = Query(..., description="Platform"),
    force: bool = Query(False, description="Force full sync even if not needed"),
    db: AsyncSession = Depends(get_async_db)
) -> SyncResponse:
    """
    Perform full data synchronization
    
    Requirements: 12.5 - Full sync for data consistency recovery
    """
    try:
        sync_service = SyncService(db)
        
        # Get all data for the client
        all_changes = await sync_service.get_full_sync_data(client_id, platform)
        
        # Reset sync metadata
        await sync_service.reset_sync_metadata(client_id, platform)
        
        await db.commit()
        
        # Log full sync
        security_logger.log_security_event(
            "sync_full_sync",
            {
                "client_id": client_id,
                "platform": platform,
                "forced": force,
                "total_changes": len(all_changes)
            },
            "INFO"
        )
        
        return SyncResponse(
            success=True,
            sync_time=datetime.now(timezone.utc),
            changes=all_changes,
            stats={
                "full_sync": True,
                "total_changes": len(all_changes),
                "documents": len([c for c in all_changes if c.entity_type == "document"]),
                "cards": len([c for c in all_changes if c.entity_type == "card"]),
                "srs": len([c for c in all_changes if c.entity_type == "srs"])
            }
        )
        
    except Exception as e:
        await db.rollback()
        security_logger.log_error(e, {
            "operation": "full_sync",
            "client_id": client_id
        })
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform full sync: {str(e)}"
        )


@router.get("/health")
async def sync_health_check(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Check sync system health
    """
    try:
        sync_service = SyncService(db)
        health_status = await sync_service.get_system_health()
        
        return {
            "status": "healthy" if health_status["overall_healthy"] else "degraded",
            "active_clients": health_status["active_clients"],
            "pending_syncs": health_status["pending_syncs"],
            "recent_conflicts": health_status["recent_conflicts"],
            "system_load": health_status["system_load"],
            "recommendations": health_status.get("recommendations", [])
        }
        
    except Exception as e:
        security_logger.log_error(e, {"operation": "sync_health_check"})
        return {
            "status": "error",
            "error": str(e)
        }