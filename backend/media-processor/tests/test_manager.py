"""
Tests for ConflictManager
"""

import pytest
from conflict_resolver.manager import ConflictManager, ConflictResolution
from conflict_resolver.detector import Conflict, FieldValue


class TestConflictManager:
    """Test suite for ConflictManager."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh ConflictManager."""
        return ConflictManager()
    
    @pytest.fixture
    def sample_conflict(self):
        """Create sample conflict."""
        return Conflict(
            field_name="people_affected",
            field_label="Number of People Affected",
            existing_value=FieldValue(5000, "report.pdf", "2025-01-28T10:00:00"),
            new_value=FieldValue(7000, "assessment.pdf", "2025-01-28T11:00:00"),
            conflict_id="conflict_001"
        )
    
    def test_add_conflicts(self, manager, sample_conflict):
        """Test adding conflicts to manager."""
        manager.add_conflicts([sample_conflict])
        
        assert manager.has_pending_conflicts()
        assert len(manager.get_pending_conflicts()) == 1
    
    def test_get_conflict_by_id(self, manager, sample_conflict):
        """Test retrieving conflict by ID."""
        manager.add_conflicts([sample_conflict])
        
        retrieved = manager.get_conflict_by_id("conflict_001")
        
        assert retrieved is not None
        assert retrieved.field_name == "people_affected"
        assert retrieved.conflict_id == "conflict_001"
    
    def test_get_conflict_by_id_not_found(self, manager):
        """Test retrieving non-existent conflict."""
        result = manager.get_conflict_by_id("nonexistent")
        assert result is None
    
    def test_resolve_conflict_choice_1(self, manager, sample_conflict):
        """Test resolving conflict by choosing existing value (1)."""
        manager.add_conflicts([sample_conflict])
        
        update = manager.resolve_conflict(
            conflict_id="conflict_001",
            choice=1,
            message_id="msg_123"
        )
        
        assert update is not None
        assert update["field"] == "people_affected"
        assert update["value"] == 5000  # Existing value
        assert update["source"] == "report.pdf"
        assert not manager.has_pending_conflicts()
    
    def test_resolve_conflict_choice_2(self, manager, sample_conflict):
        """Test resolving conflict by choosing new value (2)."""
        manager.add_conflicts([sample_conflict])
        
        update = manager.resolve_conflict(
            conflict_id="conflict_001",
            choice=2,
            message_id="msg_124"
        )
        
        assert update is not None
        assert update["field"] == "people_affected"
        assert update["value"] == 7000  # New value
        assert update["source"] == "assessment.pdf"
        assert not manager.has_pending_conflicts()
    
    def test_resolve_conflict_invalid_choice(self, manager, sample_conflict):
        """Test resolving with invalid choice."""
        manager.add_conflicts([sample_conflict])
        
        update = manager.resolve_conflict(
            conflict_id="conflict_001",
            choice=3  # Invalid
        )
        
        assert update is None
        assert manager.has_pending_conflicts()  # Conflict still pending
    
    def test_resolve_nonexistent_conflict(self, manager):
        """Test resolving conflict that doesn't exist."""
        update = manager.resolve_conflict(
            conflict_id="nonexistent",
            choice=1
        )
        
        assert update is None
    
    def test_resolution_history(self, manager, sample_conflict):
        """Test that resolutions are recorded in history."""
        manager.add_conflicts([sample_conflict])
        manager.resolve_conflict("conflict_001", choice=2)
        
        history = manager.get_resolution_history()
        
        assert len(history) == 1
        assert history[0].conflict_id == "conflict_001"
        assert history[0].field_name == "people_affected"
        assert history[0].chosen_value.value == 7000
        assert history[0].rejected_value.value == 5000
    
    def test_resolve_multiple_conflicts(self, manager):
        """Test resolving multiple conflicts."""
        conflicts = [
            Conflict(
                field_name="people_affected",
                field_label="Number of People Affected",
                existing_value=FieldValue(5000, "a.pdf", "2025-01-28T10:00:00"),
                new_value=FieldValue(7000, "b.pdf", "2025-01-28T11:00:00"),
                conflict_id="conflict_001"
            ),
            Conflict(
                field_name="disaster_type",
                field_label="Type of Disaster",
                existing_value=FieldValue("Flood", "a.pdf", "2025-01-28T10:00:00"),
                new_value=FieldValue("Cyclone", "b.pdf", "2025-01-28T11:00:00"),
                conflict_id="conflict_002"
            )
        ]
        
        manager.add_conflicts(conflicts)
        
        updates = manager.resolve_all_conflicts({
            "conflict_001": 1,
            "conflict_002": 2
        })
        
        assert len(updates) == 2
        assert updates[0]["value"] == 5000
        assert updates[1]["value"] == "Cyclone"
        assert not manager.has_pending_conflicts()
    
    def test_get_resolution_history_by_field(self, manager):
        """Test filtering resolution history by field."""
        conflicts = [
            Conflict(
                field_name="people_affected",
                field_label="Number of People Affected",
                existing_value=FieldValue(5000, "a.pdf", "2025-01-28T10:00:00"),
                new_value=FieldValue(7000, "b.pdf", "2025-01-28T11:00:00"),
                conflict_id="conflict_001"
            ),
            Conflict(
                field_name="disaster_type",
                field_label="Type of Disaster",
                existing_value=FieldValue("Flood", "a.pdf", "2025-01-28T10:00:00"),
                new_value=FieldValue("Cyclone", "b.pdf", "2025-01-28T11:00:00"),
                conflict_id="conflict_002"
            )
        ]
        
        manager.add_conflicts(conflicts)
        manager.resolve_conflict("conflict_001", choice=1)
        manager.resolve_conflict("conflict_002", choice=2)
        
        people_history = manager.get_resolution_history(field_name="people_affected")
        
        assert len(people_history) == 1
        assert people_history[0].field_name == "people_affected"
    
    def test_audit_trail(self, manager):
        """Test getting audit trail for a field."""
        conflicts = [
            Conflict(
                field_name="people_affected",
                field_label="Number of People Affected",
                existing_value=FieldValue(5000, "a.pdf", "2025-01-28T10:00:00"),
                new_value=FieldValue(7000, "b.pdf", "2025-01-28T11:00:00"),
                conflict_id="conflict_001"
            ),
            Conflict(
                field_name="people_affected",
                field_label="Number of People Affected",
                existing_value=FieldValue(7000, "b.pdf", "2025-01-28T11:00:00"),
                new_value=FieldValue(8000, "c.pdf", "2025-01-28T12:00:00"),
                conflict_id="conflict_002"
            )
        ]
        
        manager.add_conflicts(conflicts)
        manager.resolve_conflict("conflict_001", choice=2)  # Choose 7000
        manager.resolve_conflict("conflict_002", choice=1)  # Keep 7000
        
        trail = manager.get_audit_trail("people_affected")
        
        assert len(trail) == 2
        assert trail[0]["value"] == 7000
        assert trail[0]["rejected_alternative"] == 5000
        assert trail[1]["value"] == 7000
        assert trail[1]["rejected_alternative"] == 8000
    
    def test_clear_pending_conflicts(self, manager, sample_conflict):
        """Test clearing all pending conflicts."""
        manager.add_conflicts([sample_conflict])
        assert manager.has_pending_conflicts()
        
        manager.clear_pending_conflicts()
        
        assert not manager.has_pending_conflicts()
        assert len(manager.get_pending_conflicts()) == 0
    
    def test_export_state(self, manager, sample_conflict):
        """Test exporting manager state."""
        manager.add_conflicts([sample_conflict])
        manager.resolve_conflict("conflict_001", choice=1)
        
        state = manager.export_state()
        
        assert "pending_conflicts" in state
        assert "resolution_history" in state
        assert len(state["resolution_history"]) == 1


class TestConflictResolution:
    """Test suite for ConflictResolution dataclass."""
    
    def test_resolution_creation(self):
        """Test creating ConflictResolution."""
        resolution = ConflictResolution(
            conflict_id="conflict_001",
            field_name="people_affected",
            chosen_value=FieldValue(7000, "new.pdf", "2025-01-28T11:00:00"),
            rejected_value=FieldValue(5000, "old.pdf", "2025-01-28T10:00:00"),
            resolved_at="2025-01-28T11:30:00",
            resolved_by_message_id="msg_123"
        )
        
        assert resolution.conflict_id == "conflict_001"
        assert resolution.chosen_value.value == 7000
        assert resolution.rejected_value.value == 5000
    
    def test_resolution_to_dict(self):
        """Test ConflictResolution serialization."""
        resolution = ConflictResolution(
            conflict_id="conflict_001",
            field_name="disaster_type",
            chosen_value=FieldValue("Flood", "a.pdf", "2025-01-28T10:00:00"),
            rejected_value=FieldValue("Cyclone", "b.pdf", "2025-01-28T11:00:00"),
            resolved_at="2025-01-28T11:30:00"
        )
        
        d = resolution.to_dict()
        
        assert d["conflict_id"] == "conflict_001"
        assert d["field_name"] == "disaster_type"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])