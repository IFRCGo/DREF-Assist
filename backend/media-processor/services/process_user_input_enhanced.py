"""
Enhanced services module integrating conflict resolution.

This shows how to modify the existing process_user_input() to include
conflict detection and resolution.
"""

from typing import Dict, List, Any, Optional
from conflict_resolver import ConflictResolverService

# Initialize conflict resolver (could be session-scoped in production)
conflict_resolver = ConflictResolverService(field_labels={
    "people_affected": "Number of People Affected",
    "disaster_type": "Type of Disaster",
    "location": "Location",
    "start_date": "Disaster Start Date",
    "budget_requested": "Budget Requested",
    # Add more field labels as needed
})


def process_user_input(
    user_message: str,
    current_form_state: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
    message_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhanced process_user_input with conflict detection.
    
    Args:
        user_message: The user's text input
        current_form_state: Current DREF form state
        files: Optional list of uploaded files
        message_id: Optional message ID for tracking
        session_id: Optional session ID for multi-session support
    
    Returns:
        Response with classification, reply, field_updates, and conflict info:
        {
            "classification": "NEW_INFORMATION" | "MODIFICATION_REQUEST" | "QUESTION" | "OFF_TOPIC",
            "reply": str,
            "field_updates": [...],
            "has_conflicts": bool,
            "conflicts": [...],  # If conflicts detected
            "conflict_prompt": str  # If conflicts detected
        }
    """
    
    # Check if user is resolving a pending conflict
    if conflict_resolver.manager.has_pending_conflicts():
        # Try to parse as conflict resolution
        resolution_result = conflict_resolver.resolve_conflicts(
            user_choice=user_message,
            message_id=message_id
        )
        
        if resolution_result["resolved"]:
            return resolution_result
        # If not a valid resolution choice, fall through to normal processing
    
    # --- EXISTING LLM HANDLER LOGIC (placeholder) ---
    # In production, this would call your actual llm_handler
    llm_response = _call_llm_handler(
        user_message=user_message,
        current_form_state=current_form_state,
        files=files
    )
    # --- END EXISTING LOGIC ---
    
    # Determine source for conflict tracking
    if files and len(files) > 0:
        source = files[0].get("filename", "uploaded_file")
    else:
        source = f"user_message_{message_id}" if message_id else "user_message"
    
    # Process with conflict detection
    enhanced_response = conflict_resolver.process_with_conflict_detection(
        llm_response=llm_response,
        source=source,
        message_id=message_id
    )
    
    return enhanced_response


def _call_llm_handler(
    user_message: str,
    current_form_state: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Placeholder for actual LLM handler call.
    
    In production, this would:
    1. Process files through media-processor
    2. Format for GPT-4o
    3. Get LLM response
    4. Parse and validate field updates
    
    Returns:
        {
            "classification": str,
            "reply": str,
            "field_updates": [
                {"field": "people_affected", "value": 5000},
                {"field": "disaster_type", "value": "Flood"},
                ...
            ]
        }
    """
    # This is where your existing llm_handler code goes
    # For now, returning a mock response
    return {
        "classification": "NEW_INFORMATION",
        "reply": "I've extracted information from your input.",
        "field_updates": [
            {"field": "people_affected", "value": 5000},
            {"field": "disaster_type", "value": "Flood"}
        ]
    }


def get_current_form_state() -> Dict[str, Any]:
    """Get current form state (values only)."""
    return conflict_resolver.get_form_state()


def get_pending_conflicts() -> Dict[str, Any]:
    """Get information about pending conflicts."""
    return conflict_resolver.get_pending_conflicts_summary()


def get_field_history(field_name: str) -> List[Dict[str, Any]]:
    """Get change history for a specific field."""
    return conflict_resolver.get_field_audit_trail(field_name)


# Example usage and testing
if __name__ == "__main__":
    print("=== Conflict Resolution Demo ===\n")
    
    # Simulate first input
    print("1. User uploads report.pdf with '5000 people affected'")
    result1 = process_user_input(
        user_message="Flood in Bangladesh",
        current_form_state={},
        files=[{"filename": "report.pdf", "type": "pdf"}],
        message_id="msg_001"
    )
    print(f"Result: {result1['reply']}")
    print(f"Updates: {result1['field_updates']}")
    print(f"Conflicts: {result1['has_conflicts']}\n")
    
    # Simulate second input with conflicting data
    print("2. User uploads assessment.pdf with '7000 people affected'")
    # Modify the mock to return conflicting value
    result2 = process_user_input(
        user_message="Updated assessment",
        current_form_state=get_current_form_state(),
        files=[{"filename": "assessment.pdf", "type": "pdf"}],
        message_id="msg_002"
    )
    print(f"Conflicts detected: {result2['has_conflicts']}")
    if result2['has_conflicts']:
        print(f"\n{result2['conflict_prompt']}\n")
    
    # Simulate user resolving conflict
    print("3. User chooses second option")
    result3 = process_user_input(
        user_message="2",
        current_form_state=get_current_form_state(),
        message_id="msg_003"
    )
    print(f"Resolution: {result3['reply']}")
    print(f"Final form state: {get_current_form_state()}")