"""
Conflict detection module for DREF form field updates.
Compares new field values against existing state to identify conflicts.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class FieldValue:
    """Represents a field value with its source metadata."""
    value: Any
    source: str  # e.g., "report.pdf", "user_message_123", "voice_note.wav"
    timestamp: str
    message_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Conflict:
    """Represents a conflict between two field values."""
    field_name: str
    field_label: str  # Human-readable field name
    existing_value: FieldValue
    new_value: FieldValue
    conflict_id: str

    def to_dict(self) -> Dict:
        return {
            "field_name": self.field_name,
            "field_label": self.field_label,
            "existing_value": self.existing_value.to_dict(),
            "new_value": self.new_value.to_dict(),
            "conflict_id": self.conflict_id
        }

    def generate_prompt(self) -> str:
        """Generate user-friendly prompt for this conflict."""
        return (
            f"I found conflicting information for '{self.field_label}':\n\n"
            f"• {self.existing_value.source} says: {self._format_value(self.existing_value.value)}\n"
            f"  (from {self._format_timestamp(self.existing_value.timestamp)})\n\n"
            f"• {self.new_value.source} says: {self._format_value(self.new_value.value)}\n"
            f"  (from {self._format_timestamp(self.new_value.timestamp)})\n\n"
            f"Which value should I use? Reply with '1' for the first option or '2' for the second option."
        )

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format value for display."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value)

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            return timestamp


class ConflictDetector:
    """Detects conflicts between new field updates and existing form state."""

    # Fields that should always be overwritten without conflict detection
    OVERWRITE_FIELDS = {
        "last_modified",
        "last_modified_by",
        "version"
    }

    # Tolerance for numeric comparisons (e.g., 5000 vs 5000.0)
    NUMERIC_TOLERANCE = 0.01

    def __init__(self, field_labels: Optional[Dict[str, str]] = None):
        """
        Initialize conflict detector.

        Args:
            field_labels: Mapping of field names to human-readable labels
                         e.g., {"people_affected": "Number of People Affected"}
        """
        self.field_labels = field_labels or {}

    def detect_conflicts(
        self,
        current_state: Dict[str, FieldValue],
        new_updates: List[Dict[str, Any]],
        source: str,
        message_id: Optional[str] = None
    ) -> tuple[List[Conflict], List[Dict[str, Any]]]:
        """
        Detect conflicts between current form state and new field updates.

        Also detects within-batch conflicts when multiple updates in the same
        batch target the same field with different values.

        Args:
            current_state: Current form state with FieldValue objects
            new_updates: List of field updates from LLM handler
                        [{"field": "people_affected", "value": 7000}, ...]
            source: Source of new updates (e.g., "assessment.pdf")
            message_id: Optional message ID for tracking

        Returns:
            Tuple of (conflicts, non_conflicting_updates)
        """
        conflicts = []
        non_conflicting_updates = []
        timestamp = datetime.utcnow().isoformat()

        # Phase 1: Detect within-batch conflicts (multiple updates for same field)
        batch_groups: Dict[str, List[Dict[str, Any]]] = {}
        for update in new_updates:
            field_name = update.get("field")
            if field_name not in batch_groups:
                batch_groups[field_name] = []
            batch_groups[field_name].append(update)

        deduplicated_updates: List[Dict[str, Any]] = []
        for field_name, group in batch_groups.items():
            if len(group) == 1:
                deduplicated_updates.append(group[0])
                continue

            # Multiple updates for the same field — check if they all agree
            reference_value = group[0].get("value")
            all_agree = True
            for other in group[1:]:
                if self._values_conflict(reference_value, other.get("value")):
                    all_agree = False
                    break

            if all_agree:
                # All values agree — keep one
                deduplicated_updates.append(group[0])
            else:
                # Values conflict within the batch — create conflicts
                for i in range(1, len(group)):
                    conflict = Conflict(
                        field_name=field_name,
                        field_label=self.field_labels.get(field_name, field_name),
                        existing_value=FieldValue(
                            value=group[0].get("value"),
                            source=group[0].get("source", source),
                            timestamp=timestamp,
                            message_id=message_id,
                        ),
                        new_value=FieldValue(
                            value=group[i].get("value"),
                            source=group[i].get("source", source),
                            timestamp=timestamp,
                            message_id=message_id,
                        ),
                        conflict_id=f"batch_{field_name}_{i}_{timestamp.replace(':', '-')}"
                    )
                    conflicts.append(conflict)

        # Phase 2: Detect conflicts against current state (using deduplicated updates)
        for update in deduplicated_updates:
            field_name = update.get("field")
            new_value = update.get("value")

            # Skip if field should always be overwritten
            if field_name in self.OVERWRITE_FIELDS:
                non_conflicting_updates.append(update)
                continue

            # Check if field exists in current state
            if field_name not in current_state:
                # No conflict - field is new
                non_conflicting_updates.append(update)
                continue

            existing_field_value = current_state[field_name]
            existing_value = existing_field_value.value

            # Check if values conflict
            if self._values_conflict(existing_value, new_value):
                conflict = Conflict(
                    field_name=field_name,
                    field_label=self.field_labels.get(field_name, field_name),
                    existing_value=existing_field_value,
                    new_value=FieldValue(
                        value=new_value,
                        source=source,
                        timestamp=timestamp,
                        message_id=message_id
                    ),
                    conflict_id=f"{field_name}_{timestamp.replace(':', '-')}"
                )
                conflicts.append(conflict)
            else:
                # Values are the same - no conflict
                non_conflicting_updates.append(update)

        return conflicts, non_conflicting_updates

    def _values_conflict(self, existing: Any, new: Any) -> bool:
        """
        Determine if two values conflict.

        Returns True if values are meaningfully different.
        """
        # Handle None/empty cases
        # Check if BOTH are empty first (includes None, "", [])
        if self._is_empty(existing) and self._is_empty(new):
            return False

        # If the existing value is empty, getting a new value is an UPDATE, not a conflict
        if self._is_empty(existing):
            return False

        # If the new value is empty but we have an existing value, technically it could be
        # a deletion request or missing data payload. Let's treat it as a conflict to be safe.
        if self._is_empty(new):
            return True

        # Type mismatch is a conflict (except numeric types)
        if not self._types_compatible(existing, new):
            return True

        # Numeric comparison with tolerance
        if isinstance(existing, (int, float)) and isinstance(new, (int, float)):
            return abs(float(existing) - float(new)) > self.NUMERIC_TOLERANCE

        # List comparison (order-independent for simple cases)
        if isinstance(existing, list) and isinstance(new, list):
            return sorted(str(x) for x in existing) != sorted(str(x) for x in new)

        # Boolean comparison
        if isinstance(existing, bool) and isinstance(new, bool):
            return existing != new

        # String comparison (case-insensitive, whitespace-normalized)
        if isinstance(existing, str) and isinstance(new, str):
            return self._normalize_string(existing) != self._normalize_string(new)

        # Default: direct comparison
        return existing != new

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """Check if value is empty (None, empty string, empty list)."""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        if isinstance(value, list):
            return len(value) == 0
        return False

    @staticmethod
    def _types_compatible(val1: Any, val2: Any) -> bool:
        """Check if two values have compatible types."""
        # Numeric types are compatible with each other
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return True
        # Otherwise, types must match exactly
        return type(val1) == type(val2)

    @staticmethod
    def _normalize_string(s: str) -> str:
        """Normalize string for comparison."""
        return " ".join(s.strip().lower().split())
