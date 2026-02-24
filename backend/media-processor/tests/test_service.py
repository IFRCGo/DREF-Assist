"""
Tests for ConflictResolverService
"""

import pytest
from conflict_resolver.service import ConflictResolverService
from conflict_resolver.detector import FieldValue


class TestConflictResolverService:
    """Test suite for ConflictResolverService."""
    
    @pytest.fixture
    def service(self):
        """Create fresh service."""
        return ConflictResolverService(field_labels={
            "people_affected": "Number of People Affected",
            "disaster_type": "Type of Disaster",
            "location": "Location"
        })
    
    @pytest.fixture
    def mock_llm_response(self):
        """Create mock LLM response."""
        return {
            "classification": "NEW_INFORMATION",
            "reply": "I've extracted the information.",
            "field_updates": [
                {"field": "people_affected", "value": 5000},
                {"field": "disaster_type", "value": "Flood"}
            ]
        }
    
    def test_process_no_conflicts_first_input(self, service, mock_llm_response):
        """Test processing first input with no conflicts."""
        result = service.process_with_conflict_detection(
            llm_response=mock_llm_response,
            source="report.pdf",
            message_id="msg_001"
        )
        
        assert not result["has_conflicts"]
        assert len(result["field_updates"]) == 2
        assert result["classification"] == "NEW_INFORMATION"
        
        # Check form state was updated
        form_state = service.get_form_state()
        assert form_state["people_affected"] == 5000
        assert form_state["disaster_type"] == "Flood"
    
    def test_process_with_conflicts(self, service):
        """Test processing input that creates conflicts."""
        # First input
        first_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Information extracted.",
            "field_updates": [
                {"field": "people_affected", "value": 5000}
            ]
        }
        service.process_with_conflict_detection(
            llm_response=first_response,
            source="report1.pdf",
            message_id="msg_001"
        )
        
        # Second input with conflicting data
        second_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Updated information.",
            "field_updates": [
                {"field": "people_affected", "value": 7000}
            ]
        }
        result = service.process_with_conflict_detection(
            llm_response=second_response,
            source="report2.pdf",
            message_id="msg_002"
        )
        
        assert result["has_conflicts"]
        assert len(result["conflicts"]) == 1
        assert len(result["field_updates"]) == 0  # Conflicting update not applied
        assert "conflict_prompt" in result
        
        # Original value should still be in form state
        form_state = service.get_form_state()
        assert form_state["people_affected"] == 5000
    
    def test_resolve_conflict_valid_choice(self, service):
        """Test resolving a conflict with valid user choice."""
        # Create a conflict
        first_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info extracted.",
            "field_updates": [{"field": "people_affected", "value": 5000}]
        }
        service.process_with_conflict_detection(
            llm_response=first_response,
            source="old.pdf",
            message_id="msg_001"
        )
        
        second_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Updated info.",
            "field_updates": [{"field": "people_affected", "value": 7000}]
        }
        service.process_with_conflict_detection(
            llm_response=second_response,
            source="new.pdf",
            message_id="msg_002"
        )
        
        # Resolve with choice 2 (new value)
        result = service.resolve_conflicts(
            user_choice="2",
            message_id="msg_003"
        )
        
        assert result["resolved"]
        assert len(result["field_updates"]) == 1
        assert result["field_updates"][0]["value"] == 7000
        assert result["remaining_conflicts"] == 0
        
        # Form state should be updated
        form_state = service.get_form_state()
        assert form_state["people_affected"] == 7000
    
    def test_resolve_conflict_natural_language(self, service):
        """Test resolving conflicts with natural language choices."""
        # Create conflict
        first_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "disaster_type", "value": "Flood"}]
        }
        service.process_with_conflict_detection(first_response, "a.pdf", "msg_001")
        
        second_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "disaster_type", "value": "Cyclone"}]
        }
        service.process_with_conflict_detection(second_response, "b.pdf", "msg_002")
        
        # Test various natural language inputs
        test_cases = [
            ("first", 1, "Flood"),
            ("keep first", 1, "Flood"),
            ("existing", 1, "Flood"),
            ("second", 2, "Cyclone"),
            ("new", 2, "Cyclone"),
            ("use second", 2, "Cyclone"),
        ]
        
        for user_input, expected_choice, expected_value in test_cases:
            service.reset()
            service.process_with_conflict_detection(first_response, "a.pdf", "msg_001")
            service.process_with_conflict_detection(second_response, "b.pdf", "msg_002")
            
            result = service.resolve_conflicts(user_input, "msg_003")
            
            assert result["resolved"], f"Failed to parse: {user_input}"
            assert result["field_updates"][0]["value"] == expected_value
    
    def test_resolve_conflict_invalid_choice(self, service):
        """Test resolving with invalid choice."""
        # Create conflict
        first_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "people_affected", "value": 5000}]
        }
        service.process_with_conflict_detection(first_response, "a.pdf", "msg_001")
        
        second_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "people_affected", "value": 7000}]
        }
        service.process_with_conflict_detection(second_response, "b.pdf", "msg_002")
        
        # Try invalid choice
        result = service.resolve_conflicts(
            user_choice="invalid",
            message_id="msg_003"
        )
        
        assert not result["resolved"]
        assert "didn't understand" in result["reply"].lower()
        assert result["remaining_conflicts"] == 1
    
    def test_resolve_no_pending_conflicts(self, service):
        """Test resolving when there are no pending conflicts."""
        result = service.resolve_conflicts(
            user_choice="1",
            message_id="msg_001"
        )
        
        assert not result["resolved"]
        assert "no pending conflicts" in result["reply"].lower()
    
    def test_multiple_conflicts_sequential_resolution(self, service):
        """Test resolving multiple conflicts one at a time."""
        # Create multiple conflicts
        first_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [
                {"field": "people_affected", "value": 5000},
                {"field": "disaster_type", "value": "Flood"}
            ]
        }
        service.process_with_conflict_detection(first_response, "a.pdf", "msg_001")
        
        second_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [
                {"field": "people_affected", "value": 7000},
                {"field": "disaster_type", "value": "Cyclone"}
            ]
        }
        result = service.process_with_conflict_detection(second_response, "b.pdf", "msg_002")
        
        assert result["has_conflicts"]
        assert len(result["conflicts"]) == 2
        
        # Resolve first conflict
        result1 = service.resolve_conflicts("1", "msg_003")
        assert result1["resolved"]
        assert result1["remaining_conflicts"] == 1
        assert "more conflict" in result1["reply"].lower()
        
        # Resolve second conflict
        result2 = service.resolve_conflicts("2", "msg_004")
        assert result2["resolved"]
        assert result2["remaining_conflicts"] == 0
        assert "all conflicts resolved" in result2["reply"].lower()
    
    def test_get_pending_conflicts_summary(self, service):
        """Test getting pending conflicts summary."""
        # No conflicts initially
        summary = service.get_pending_conflicts_summary()
        assert summary["count"] == 0
        assert summary["prompt"] is None
        
        # Create conflict
        first_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "people_affected", "value": 5000}]
        }
        service.process_with_conflict_detection(first_response, "a.pdf", "msg_001")
        
        second_response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "people_affected", "value": 7000}]
        }
        service.process_with_conflict_detection(second_response, "b.pdf", "msg_002")
        
        # Check summary
        summary = service.get_pending_conflicts_summary()
        assert summary["count"] == 1
        assert summary["prompt"] is not None
        assert len(summary["conflicts"]) == 1
    
    def test_get_field_audit_trail(self, service):
        """Test getting audit trail for a field."""
        # Create and resolve conflicts
        responses = [
            ({"field_updates": [{"field": "people_affected", "value": 5000}]}, "a.pdf"),
            ({"field_updates": [{"field": "people_affected", "value": 7000}]}, "b.pdf"),
            ({"field_updates": [{"field": "people_affected", "value": 8000}]}, "c.pdf"),
        ]
        
        for i, (resp, source) in enumerate(responses):
            resp["classification"] = "NEW_INFORMATION"
            resp["reply"] = "Info."
            result = service.process_with_conflict_detection(resp, source, f"msg_{i}")
            if result["has_conflicts"]:
                service.resolve_conflicts("2", f"msg_{i}_resolve")
        
        trail = service.get_field_audit_trail("people_affected")
        assert len(trail) >= 1  # Should have resolution history
    
    def test_form_state_metadata(self, service):
        """Test that form state includes metadata."""
        response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "location", "value": "Bangladesh"}]
        }
        service.process_with_conflict_detection(response, "report.pdf", "msg_001")
        
        full_state = service.get_full_form_state()
        
        assert "location" in full_state
        assert isinstance(full_state["location"], FieldValue)
        assert full_state["location"].value == "Bangladesh"
        assert full_state["location"].source == "report.pdf"
        assert full_state["location"].message_id == "msg_001"
    
    def test_reset_service(self, service):
        """Test resetting service state."""
        response = {
            "classification": "NEW_INFORMATION",
            "reply": "Info.",
            "field_updates": [{"field": "people_affected", "value": 5000}]
        }
        service.process_with_conflict_detection(response, "report.pdf", "msg_001")
        
        assert len(service.get_form_state()) > 0
        
        service.reset()
        
        assert len(service.get_form_state()) == 0
        assert not service.manager.has_pending_conflicts()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])