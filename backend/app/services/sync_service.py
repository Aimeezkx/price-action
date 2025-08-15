"""
Cross-platform data synchronization service
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from uuid import UUID
import json
import hashlib
from dataclasses import dataclass

from app.models.document import Document, Chapter, Figure
from app.models.knowledge import Knowledge
from app.models.learning import Card, SRS
from app.models.base import BaseModel


@dataclass
class SyncChange:
    """Represents a single sync change"""
    id: str
    entity_type: str
    operation: str  # create, update, delete
    data: Dict[str, Any]
    timestamp: datetime
    client_id: str
    version: int = 1


@dataclass
class SyncMetadata:
    """Sync metadata for tracking client state"""
    client_id: str
    platform: str
    last_sync_time: datetime
    sync_version: int
    pending_changes: int


class SyncService:
    """Service for handling cross-platform data synchronization"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.entity_models = {
            "document": Document,
            "chapter": Chapter,
            "figure": Figure,
            "knowledge": Knowledge,
            "card": Card,
            "srs": SRS
        }
    
    async def get_changes_since(
        self, 
        last_sync_time: Optional[datetime],
        client_id: str,
        platform: str
    ) -> List[SyncChange]:
        """Get all changes since the last sync time"""
        changes = []
        
        # If no last sync time, this is a full sync
        if not last_sync_time:
            return await self.get_full_sync_data(client_id, platform)
        
        # Get changes for each entity type
        for entity_type, model_class in self.entity_models.items():
            entity_changes = await self._get_entity_changes_since(
                model_class, entity_type, last_sync_time, client_id
            )
            changes.extend(entity_changes)
        
        # Sort by timestamp
        changes.sort(key=lambda x: x.timestamp)
        
        return changes
    
    async def _get_entity_changes_since(
        self,
        model_class: BaseModel,
        entity_type: str,
        since_time: datetime,
        client_id: str
    ) -> List[SyncChange]:
        """Get changes for a specific entity type since given time"""
        changes = []
        
        # Get updated/created entities
        stmt = select(model_class).where(
            or_(
                model_class.created_at > since_time,
                model_class.updated_at > since_time
            )
        )
        
        result = await self.db.execute(stmt)
        entities = result.scalars().all()
        
        for entity in entities:
            # Determine operation type
            operation = "create" if entity.created_at > since_time else "update"
            
            # Convert entity to dict
            entity_data = await self._entity_to_dict(entity)
            
            change = SyncChange(
                id=str(entity.id),
                entity_type=entity_type,
                operation=operation,
                data=entity_data,
                timestamp=max(entity.created_at, entity.updated_at),
                client_id="server",  # Server-originated change
                version=1
            )
            changes.append(change)
        
        # TODO: Handle deleted entities (would need soft delete tracking)
        
        return changes
    
    async def apply_change(self, change: SyncChange) -> SyncChange:
        """Apply a sync change to the database"""
        model_class = self.entity_models.get(change.entity_type)
        if not model_class:
            raise ValueError(f"Unknown entity type: {change.entity_type}")
        
        if change.operation == "create":
            return await self._apply_create(model_class, change)
        elif change.operation == "update":
            return await self._apply_update(model_class, change)
        elif change.operation == "delete":
            return await self._apply_delete(model_class, change)
        else:
            raise ValueError(f"Unknown operation: {change.operation}")
    
    async def _apply_create(self, model_class: BaseModel, change: SyncChange) -> SyncChange:
        """Apply a create operation"""
        # Check if entity already exists
        stmt = select(model_class).where(model_class.id == UUID(change.id))
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Entity exists, convert to update
            change.operation = "update"
            return await self._apply_update(model_class, change)
        
        # Create new entity
        entity_data = change.data.copy()
        entity_data["id"] = UUID(change.id)
        
        # Handle datetime fields
        entity_data = await self._prepare_entity_data(entity_data, model_class)
        
        entity = model_class(**entity_data)
        self.db.add(entity)
        await self.db.flush()
        
        return change
    
    async def _apply_update(self, model_class: BaseModel, change: SyncChange) -> SyncChange:
        """Apply an update operation"""
        stmt = select(model_class).where(model_class.id == UUID(change.id))
        result = await self.db.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if not entity:
            # Entity doesn't exist, convert to create
            change.operation = "create"
            return await self._apply_create(model_class, change)
        
        # Update entity fields
        entity_data = await self._prepare_entity_data(change.data, model_class)
        
        for key, value in entity_data.items():
            if hasattr(entity, key) and key != "id":
                setattr(entity, key, value)
        
        await self.db.flush()
        
        return change
    
    async def _apply_delete(self, model_class: BaseModel, change: SyncChange) -> SyncChange:
        """Apply a delete operation"""
        stmt = select(model_class).where(model_class.id == UUID(change.id))
        result = await self.db.execute(stmt)
        entity = result.scalar_one_or_none()
        
        if entity:
            await self.db.delete(entity)
            await self.db.flush()
        
        return change
    
    async def _prepare_entity_data(self, data: Dict[str, Any], model_class: BaseModel) -> Dict[str, Any]:
        """Prepare entity data for database insertion/update"""
        prepared_data = data.copy()
        
        # Convert string UUIDs to UUID objects
        for key, value in prepared_data.items():
            if key.endswith("_id") and isinstance(value, str):
                try:
                    prepared_data[key] = UUID(value)
                except ValueError:
                    pass
        
        # Convert datetime strings to datetime objects
        datetime_fields = ["created_at", "updated_at", "due_date", "last_reviewed"]
        for field in datetime_fields:
            if field in prepared_data and isinstance(prepared_data[field], str):
                try:
                    prepared_data[field] = datetime.fromisoformat(
                        prepared_data[field].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
        
        return prepared_data
    
    async def _entity_to_dict(self, entity: BaseModel) -> Dict[str, Any]:
        """Convert entity to dictionary for sync"""
        data = {}
        
        for column in entity.__table__.columns:
            value = getattr(entity, column.name)
            
            # Convert special types to serializable formats
            if isinstance(value, UUID):
                data[column.name] = str(value)
            elif isinstance(value, datetime):
                data[column.name] = value.isoformat()
            elif hasattr(value, "value"):  # Enum
                data[column.name] = value.value
            else:
                data[column.name] = value
        
        return data
    
    async def get_full_sync_data(self, client_id: str, platform: str) -> List[SyncChange]:
        """Get all data for full synchronization"""
        changes = []
        
        for entity_type, model_class in self.entity_models.items():
            stmt = select(model_class).order_by(model_class.created_at)
            result = await self.db.execute(stmt)
            entities = result.scalars().all()
            
            for entity in entities:
                entity_data = await self._entity_to_dict(entity)
                
                change = SyncChange(
                    id=str(entity.id),
                    entity_type=entity_type,
                    operation="create",
                    data=entity_data,
                    timestamp=entity.created_at,
                    client_id="server",
                    version=1
                )
                changes.append(change)
        
        return changes
    
    async def update_sync_metadata(
        self, 
        client_id: str, 
        platform: str, 
        sync_time: datetime
    ) -> None:
        """Update sync metadata for a client"""
        # In a real implementation, this would update a sync_metadata table
        # For now, we'll use a simple in-memory approach or Redis
        pass
    
    async def get_sync_status(self, client_id: str) -> Dict[str, Any]:
        """Get sync status for a client"""
        # This would query sync metadata and pending changes
        return {
            "last_sync_time": datetime.now(timezone.utc).isoformat(),
            "pending_changes": 0,
            "conflicts": 0,
            "consistency_check": True
        }
    
    async def calculate_entity_checksum(self, entity_type: str, client_id: str) -> str:
        """Calculate checksum for entity type to validate consistency"""
        model_class = self.entity_models.get(entity_type)
        if not model_class:
            return ""
        
        # Get all entities of this type
        stmt = select(model_class).order_by(model_class.id)
        result = await self.db.execute(stmt)
        entities = result.scalars().all()
        
        # Create checksum from entity data
        checksum_data = []
        for entity in entities:
            entity_data = await self._entity_to_dict(entity)
            # Remove timestamps for consistency check
            entity_data.pop("created_at", None)
            entity_data.pop("updated_at", None)
            checksum_data.append(json.dumps(entity_data, sort_keys=True))
        
        combined_data = "|".join(checksum_data)
        return hashlib.sha256(combined_data.encode()).hexdigest()
    
    async def reset_sync_metadata(self, client_id: str, platform: str) -> None:
        """Reset sync metadata for full sync"""
        # This would reset the sync metadata table
        pass
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get sync system health status"""
        # Count active entities
        total_documents = await self._count_entities(Document)
        total_cards = await self._count_entities(Card)
        total_srs = await self._count_entities(SRS)
        
        return {
            "overall_healthy": True,
            "active_clients": 1,  # Would track active clients
            "pending_syncs": 0,
            "recent_conflicts": 0,
            "system_load": {
                "documents": total_documents,
                "cards": total_cards,
                "srs_records": total_srs
            },
            "recommendations": []
        }
    
    async def _count_entities(self, model_class: BaseModel) -> int:
        """Count entities of a specific type"""
        stmt = select(func.count(model_class.id))
        result = await self.db.execute(stmt)
        return result.scalar() or 0


class SyncConflictResolver:
    """Service for resolving sync conflicts"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sync_service = SyncService(db)
    
    async def detect_conflict(self, change: SyncChange) -> Optional[Dict[str, Any]]:
        """Detect if a change conflicts with server state"""
        model_class = self.sync_service.entity_models.get(change.entity_type)
        if not model_class:
            return None
        
        # Get current server state
        stmt = select(model_class).where(model_class.id == UUID(change.id))
        result = await self.db.execute(stmt)
        server_entity = result.scalar_one_or_none()
        
        if not server_entity:
            # No conflict if entity doesn't exist on server
            return None
        
        # Check if server entity was modified after client's last sync
        # This is a simplified conflict detection
        server_data = await self.sync_service._entity_to_dict(server_entity)
        
        # Compare key fields for conflicts
        conflicts = []
        for key, client_value in change.data.items():
            server_value = server_data.get(key)
            if server_value != client_value and key not in ["updated_at", "created_at"]:
                conflicts.append({
                    "field": key,
                    "client_value": client_value,
                    "server_value": server_value
                })
        
        if conflicts:
            return {
                "conflict_id": f"{change.entity_type}_{change.id}",
                "entity_type": change.entity_type,
                "entity_id": change.id,
                "conflicts": conflicts,
                "client_change": change,
                "server_data": server_data
            }
        
        return None
    
    async def resolve_conflict(
        self, 
        conflict: Dict[str, Any], 
        resolution: str
    ) -> Optional[SyncChange]:
        """Resolve a sync conflict"""
        if resolution == "client_wins":
            # Apply client change as-is
            return await self.sync_service.apply_change(conflict["client_change"])
        
        elif resolution == "server_wins":
            # Keep server data, return server state as change
            server_change = SyncChange(
                id=conflict["entity_id"],
                entity_type=conflict["entity_type"],
                operation="update",
                data=conflict["server_data"],
                timestamp=datetime.now(timezone.utc),
                client_id="server",
                version=1
            )
            return server_change
        
        elif resolution == "merge":
            # Implement merge logic (simplified)
            merged_data = conflict["server_data"].copy()
            client_change = conflict["client_change"]
            
            # For now, merge by taking non-conflicting client changes
            for key, value in client_change.data.items():
                if not any(c["field"] == key for c in conflict["conflicts"]):
                    merged_data[key] = value
            
            merged_change = SyncChange(
                id=conflict["entity_id"],
                entity_type=conflict["entity_type"],
                operation="update",
                data=merged_data,
                timestamp=datetime.now(timezone.utc),
                client_id="merged",
                version=1
            )
            
            return await self.sync_service.apply_change(merged_change)
        
        return None
    
    async def apply_resolution(self, resolution) -> Optional[SyncChange]:
        """Apply a conflict resolution"""
        # This would look up the stored conflict and apply the resolution
        # For now, return None as conflicts are resolved immediately
        return None