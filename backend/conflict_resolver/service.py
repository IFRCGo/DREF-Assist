"""
Service layer integration for conflict resolution.
Extends the existing process_user_input() to handle conflicts.
"""

from typing import Dict, List, Any, Optional
from .detector import ConflictDetector, FieldValue
from .manager import ConflictManager


class ConflictResolverService:
    """
    Service that integrates conflict resolution into the user input processing pipeline.
    """
    
    def __init__(self, field_labels: Optional[Dict[str, str]] = None):
        """
        Initialize conflict resolver service
        
        Args:
            field_labels: Human-readable labels for form fields
        """
        self.detector = ConflictDetector(field_labels)
        self.manager = ConflictManager()
        self.form_state: Dict[str, FieldValue] = {}  # field_name -> FieldValue
    
    def process_with_conflict_detection(
        self,
        llm_response: Dict[str, Any],
        source: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process LLM response and detect conflicts with current form state.
        
        This should be called after getting the response from llm_handler.
        
        Args:
            llm_response: Response from LLM handler containing field_updates
                         {"classification": "...", "reply": "...", "field_updates": [...]}
            source: Source of the updates (e.g., filename or "user_message")
            message_id: Optional message ID for tracking
        
        Returns:
            Enhanced response with conflict information:
            {
                "classification": "...",
                "reply": "...",
                "field_updates": [...],  # Only non-conflicting updates
                "has_conflicts": bool,
                "conflicts": [...],  # List of conflicts if any
                "conflict_prompt": str  # User-friendly prompt if conflicts exist
            }
        """
        field_updates = llm_response.get("field_updates", [])
        
        # Detect conflicts
        conflicts, non_conflicting_updates = self.detector.detect_conflicts(
            current_state=self.form_state,
            new_updates=field_updates,
            source=source,
            message_id=message_id
        )
        
        # Add conflicts to manager
        if conflicts:
            self.manager.add_conflicts(conflicts)
        
        # Apply non-conflicting updates to form state
        self._apply_updates(non_conflicting_updates, source, message_id)
        
        # Build response
        response = {
            "classification": llm_response.get("classification"),
            "reply": llm_response.get("reply"),
            "field_updates": non_conflicting_updates,
            "has_conflicts": len(conflicts) > 0,
        }
        
        if conflicts:
            response["conflicts"] = [c.to_dict() for c in conflicts]
            response["conflict_prompt"] = self._generate_conflict_prompt(conflicts)
        
        return response
    
    def resolve_conflicts(
        self,
        user_choice: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user's conflict resolution choices.
        
        Args:
            user_choice: User's message resolving conflicts (e.g., "1", "2", "use first")
            message_id: Optional message ID for tracking
        
        Returns:
            Response with applied updates:
            {
                "resolved": bool,
                "field_updates": [...],
                "reply": str,
                "remaining_conflicts": int
            }
        """
        pending = self.manager.get_pending_conflicts()
        
        if not pending:
            return {
                "resolved": False,
                "field_updates": [],
                "reply": "There are no pending conflicts to resolve.",
                "remaining_conflicts": 0
            }
        
        # Parse user choice
        choice = self._parse_choice(user_choice)
        
        if choice is None:
            return {
                "resolved": False,
                "field_updates": [],
                "reply": "I didn't understand your choice. Please reply with '1' for the first option or '2' for the second option.",
                "remaining_conflicts": len(pending)
            }
        
        # Resolve the first pending conflict
        conflict = pending[0]
        field_update = self.manager.resolve_conflict(
            conflict_id=conflict.conflict_id,
            choice=choice,
            message_id=message_id
        )
        
        if field_update:
            # Apply the resolved update to form state
            self._apply_updates([field_update], field_update["source"], message_id)
            
            remaining = self.manager.get_pending_conflicts()
            
            if remaining:
                # More conflicts to resolve
                reply = f"✓ Updated {conflict.field_label}. You have {len(remaining)} more conflict(s) to resolve:\n\n"
                reply += remaining[0].generate_prompt()
            else:
                # All conflicts resolved
                reply = f"✓ Updated {conflict.field_label}. All conflicts resolved!"
            
            return {
                "resolved": True,
                "field_updates": [field_update],
                "reply": reply,
                "remaining_conflicts": len(remaining)
            }
        
        return {
            "resolved": False,
            "field_updates": [],
            "reply": "Failed to resolve conflict. Please try again.",
            "remaining_conflicts": len(pending)
        }
    
    def get_form_state(self) -> Dict[str, Any]:
        """Get current form state (values only, without metadata)."""
        return {
            field_name: field_value.value
            for field_name, field_value in self.form_state.items()
        }
    
    def get_full_form_state(self) -> Dict[str, FieldValue]:
        """Get current form state with full metadata."""
        return self.form_state.copy()
    
    def get_pending_conflicts_summary(self) -> Dict[str, Any]:
        """Get summary of pending conflicts."""
        conflicts = self.manager.get_pending_conflicts()
        return {
            "count": len(conflicts),
            "conflicts": [c.to_dict() for c in conflicts],
            "prompt": self._generate_conflict_prompt(conflicts) if conflicts else None
        }
    
    def get_field_audit_trail(self, field_name: str) -> List[Dict[str, Any]]:
        """Get audit trail for a specific field."""
        return self.manager.get_audit_trail(field_name)
    
    def _apply_updates(
        self,
        updates: List[Dict[str, Any]],
        source: str,
        message_id: Optional[str]
    ) -> None:
        """Apply field updates to form state."""
        from datetime import datetime
        
        for update in updates:
            field_name = update.get("field")
            value = update.get("value")
            
            # Get timestamp and source from update if provided, otherwise use defaults
            timestamp = update.get("timestamp", datetime.utcnow().isoformat())
            update_source = update.get("source", source)
            
            self.form_state[field_name] = FieldValue(
                value=value,
                source=update_source,
                timestamp=timestamp,
                message_id=message_id
            )
    
    def _generate_conflict_prompt(self, conflicts: List) -> str:
        """Generate user-friendly prompt for conflicts."""
        if len(conflicts) == 1:
            return conflicts[0].generate_prompt()
        else:
            prompt = f"I found {len(conflicts)} conflicts that need your attention. Let's resolve them one at a time.\n\n"
            prompt += conflicts[0].generate_prompt()
            return prompt
    
    @staticmethod
    def _parse_choice(user_input: str) -> Optional[int]:
        """
        Parse user's choice from their message.
        
        Returns 1 or 2, or None if can't parse.
        """
        user_input = user_input.strip().lower()
        
        # Direct number
        if user_input in ["1", "first", "one", "existing", "keep first", "option 1"]:
            return 1
        if user_input in ["2", "second", "two", "new", "keep second", "option 2"]:
            return 2
        
        # More natural language
        if "first" in user_input or "existing" in user_input:
            return 1
        if "second" in user_input or "new" in user_input:
            return 2
        
        return None
    
    def reset(self) -> None:
        """Reset service state (for testing or new sessions)."""
        self.form_state.clear()
        self.manager.clear_pending_conflicts()