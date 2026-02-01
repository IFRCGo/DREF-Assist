"""
Conflict management module for tracking and resolving field conflicts.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from .detector import Conflict, FieldValue


@dataclass
class ConflictResolution:
    """Represents a resolved conflict."""
    conflict_id: str
    field_name: str
    chosen_value: FieldValue
    rejected_value: FieldValue
    resolved_at: str
    resolved_by_message_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ConflictManager:
    """Manages active conflicts and resolution history."""
    
    def __init__(self):
        self.pending_conflicts: Dict[str, Conflict] = {}  # conflict_id -> Conflict
        self.resolution_history: List[ConflictResolution] = []
    
    def add_conflicts(self, conflicts: List[Conflict]) -> None:
        """Add new conflicts to pending list."""
        for conflict in conflicts:
            self.pending_conflicts[conflict.conflict_id] = conflict
    
    def get_pending_conflicts(self) -> List[Conflict]:
        """Get all pending conflicts."""
        return list(self.pending_conflicts.values())
    
    def get_conflict_by_id(self, conflict_id: str) -> Optional[Conflict]:
        """Get a specific pending conflict by ID."""
        return self.pending_conflicts.get(conflict_id)
    
    def has_pending_conflicts(self) -> bool:
        """Check if there are any pending conflicts."""
        return len(self.pending_conflicts) > 0
    
    def resolve_conflict(
        self,
        conflict_id: str,
        choice: int,  # 1 for existing, 2 for new
        message_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve a conflict with user's choice.
        
        Args:
            conflict_id: ID of the conflict to resolve
            choice: 1 to keep existing value, 2 to use new value
            message_id: Optional message ID for tracking
        
        Returns:
            Field update dict if successful, None if conflict not found or invalid choice
        """
        conflict = self.pending_conflicts.get(conflict_id)
        if not conflict:
            return None
        
        if choice not in [1, 2]:
            return None
        
        # Determine chosen and rejected values
        if choice == 1:
            chosen_value = conflict.existing_value
            rejected_value = conflict.new_value
        else:
            chosen_value = conflict.new_value
            rejected_value = conflict.existing_value
        
        # Record resolution
        resolution = ConflictResolution(
            conflict_id=conflict_id,
            field_name=conflict.field_name,
            chosen_value=chosen_value,
            rejected_value=rejected_value,
            resolved_at=datetime.utcnow().isoformat(),
            resolved_by_message_id=message_id
        )
        self.resolution_history.append(resolution)
        
        # Remove from pending
        del self.pending_conflicts[conflict_id]
        
        # Return field update
        return {
            "field": conflict.field_name,
            "value": chosen_value.value,
            "source": chosen_value.source,
            "timestamp": chosen_value.timestamp
        }
    
    def resolve_all_conflicts(
        self,
        choices: Dict[str, int],  # conflict_id -> choice (1 or 2)
        message_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Resolve multiple conflicts at once.
        
        Args:
            choices: Map of conflict_id to choice (1 or 2)
            message_id: Optional message ID for tracking
        
        Returns:
            List of field updates
        """
        updates = []
        for conflict_id, choice in choices.items():
            update = self.resolve_conflict(conflict_id, choice, message_id)
            if update:
                updates.append(update)
        return updates
    
    def get_resolution_history(
        self,
        field_name: Optional[str] = None
    ) -> List[ConflictResolution]:
        """
        Get conflict resolution history.
        
        Args:
            field_name: Optional filter by field name
        
        Returns:
            List of resolutions
        """
        if field_name:
            return [r for r in self.resolution_history if r.field_name == field_name]
        return self.resolution_history.copy()
    
    def clear_pending_conflicts(self) -> None:
        """Clear all pending conflicts (use with caution)."""
        self.pending_conflicts.clear()
    
    def get_audit_trail(self, field_name: str) -> List[Dict[str, Any]]:
        """
        Get full audit trail for a specific field.
        
        Returns list of all values that field has had, in chronological order.
        """
        trail = []
        for resolution in self.resolution_history:
            if resolution.field_name == field_name:
                trail.append({
                    "value": resolution.chosen_value.value,
                    "source": resolution.chosen_value.source,
                    "timestamp": resolution.chosen_value.timestamp,
                    "resolved_at": resolution.resolved_at,
                    "rejected_alternative": resolution.rejected_value.value
                })
        return trail
    
    def export_state(self) -> Dict[str, Any]:
        """Export current state for persistence."""
        return {
            "pending_conflicts": [c.to_dict() for c in self.pending_conflicts.values()],
            "resolution_history": [r.to_dict() for r in self.resolution_history]
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import state from persistence."""
        # Note: This is a simplified version. Production code would need
        # to reconstruct the dataclass objects from dicts
        self.pending_conflicts.clear()
        self.resolution_history.clear()
        
        # Would need proper deserialization logic here
        # For now, just showing the structure