"""
DREF Assistant service - orchestrates media processing and LLM interaction.

This module provides the main entry point for processing user input that may
contain both text and media files, coordinating the media-processor and
llm_handler modules.

NOW INCLUDES CONFLICT RESOLUTION for handling conflicting field values from multiple documents.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from openai import OpenAI

# Add parent paths for sibling package imports
_backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(_backend_path / "media-processor"))
sys.path.insert(0, str(_backend_path / "llm_handler"))
sys.path.insert(0, str(_backend_path / "conflict_resolver"))  # NEW: Add conflict resolver path

from media_processor import MediaProcessor, ProcessingInput, FileInput, FileType
from media_processor.formatter import format_for_llm
from llm_handler import handle_message
from conflict_resolver import ConflictResolverService  # NEW: Import conflict resolver


# NEW: Initialize conflict resolver (session-scoped)
# In production, you might want to create one per user session instead of module-level
conflict_resolver = ConflictResolverService(field_labels={
    "people_affected": "Number of People Affected",
    "disaster_type": "Type of Disaster",
    "location": "Affected Location",
    "start_date": "Disaster Start Date",
    "end_date": "Disaster End Date",
    "budget_requested": "Budget Requested (CHF)",
    "disaster_description": "Disaster Description",
    "needs_assessment": "Needs Assessment",
    "target_beneficiaries": "Target Beneficiaries",
    "planned_intervention": "Planned Intervention",
    # TODO: Add all your DREF form field labels here
})


def process_user_input(
    user_message: str,
    current_form_state: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[OpenAI] = None,
    message_id: Optional[str] = None,  # NEW: Optional message ID for tracking
) -> Dict[str, Any]:
    """
    Process user input (text + optional media files) and return LLM response.

    This is the main entry point for the DREF assistant. It:
    1. Checks if user is resolving a pending conflict (NEW)
    2. Processes any attached media files through media-processor
    3. Formats the combined text + media for the LLM
    4. Sends to GPT-4o via llm_handler
    5. Detects conflicts in field updates (NEW)
    6. Returns validated response with field updates and conflict info (NEW)

    Args:
        user_message: The user's text message.
        current_form_state: Dictionary mapping field IDs to current values.
        files: Optional list of file dicts, each containing:
            - data: Base64-encoded file content
            - type: File type string ("image", "video", "audio", "pdf", "docx")
            - filename: Original filename
        conversation_history: Optional list of previous message dicts with
            "role" and "content" keys.
        client: Optional OpenAI client instance for dependency injection.
        message_id: Optional message ID for tracking conflicts (NEW).

    Returns:
        Dictionary with:
        - classification: str ("NEW_INFORMATION", "MODIFICATION_REQUEST",
                               "QUESTION", "OFF_TOPIC", or "ERROR")
        - reply: str (message to display to the user)
        - field_updates: list of validated field update dicts
        - processing_summary: dict with file processing stats (if files provided)
        - has_conflicts: bool (if conflicts detected) (NEW)
        - conflicts: list of conflict dicts (if conflicts detected) (NEW)
        - conflict_prompt: str (user-facing conflict message) (NEW)

    Example:
        >>> result = process_user_input(
        ...     user_message="Analyze this flood report",
        ...     current_form_state={},
        ...     files=[{
        ...         "data": "base64encodedpdf...",
        ...         "type": "pdf",
        ...         "filename": "flood_report.pdf"
        ...     }]
        ... )
        >>> if result.get("has_conflicts"):
        ...     print(result["conflict_prompt"])  # Show to user
        >>> else:
        ...     print(result["field_updates"])  # Apply updates
    """
    
    # ========================================================================
    # NEW: CONFLICT RESOLUTION CHECK
    # If there are pending conflicts, check if user is trying to resolve them
    # ========================================================================
    if conflict_resolver.manager.has_pending_conflicts():
        # User might be responding with "1" or "2" to resolve a conflict
        resolution_result = conflict_resolver.resolve_conflicts(
            user_choice=user_message,
            message_id=message_id
        )
        
        if resolution_result["resolved"]:
            # User successfully resolved a conflict
            return resolution_result
        # If not resolved (invalid choice or user wants to do something else),
        # continue with normal processing below
    
    # ========================================================================
    # EXISTING CODE: Media Processing and LLM Handling
    # ========================================================================
    llm_input: Any  # Either str or List[Dict] for multimodal

    if files:
        # Convert file dicts to FileInput models
        file_inputs = [
            FileInput(
                data=f["data"],
                type=FileType(f["type"]),
                filename=f["filename"],
            )
            for f in files
        ]

        # Process media files
        processor = MediaProcessor()
        processing_result = processor.process(ProcessingInput(files=file_inputs))

        # Format for LLM (combines user message + processed media)
        formatted = format_for_llm(processing_result, user_message)
        llm_input = formatted["content"]

        # Get processing summary for response
        summary = processing_result.processing_summary
        processing_summary = {
            "total_files": summary.total_files,
            "successful": summary.successful,
            "failed": summary.failed,
        }
    else:
        # Text-only input
        llm_input = user_message
        processing_summary = None

    # Call LLM handler
    llm_result = handle_message(
        user_message=llm_input,
        current_form_state=current_form_state,
        conversation_history=conversation_history,
        client=client,
    )

    # Add processing summary if files were processed
    if processing_summary:
        llm_result["processing_summary"] = processing_summary

    # ========================================================================
    # NEW: CONFLICT DETECTION
    # Check if any field updates conflict with existing form state
    # ========================================================================
    
    # Determine source for conflict tracking
    if files and len(files) > 0:
        # Use first filename as source (or combine multiple filenames)
        source = files[0]["filename"]
        if len(files) > 1:
            source = f"{files[0]['filename']} (+{len(files)-1} more)"
    else:
        source = f"user_message_{message_id}" if message_id else "user_message"
    
    # Process with conflict detection
    enhanced_result = conflict_resolver.process_with_conflict_detection(
        llm_response=llm_result,
        source=source,
        message_id=message_id
    )
    
    return enhanced_result


# NEW: Helper functions for conflict management (optional, but useful)

def get_pending_conflicts() -> Dict[str, Any]:
    """
    Get information about pending conflicts.
    
    Returns:
        Dictionary with:
        - count: int (number of pending conflicts)
        - conflicts: list of conflict dicts
        - prompt: str (user-facing prompt for first conflict)
    """
    return conflict_resolver.get_pending_conflicts_summary()


def get_field_history(field_name: str) -> List[Dict[str, Any]]:
    """
    Get change history for a specific field.
    
    Args:
        field_name: Name of the field to get history for
    
    Returns:
        List of change records with chosen/rejected values and timestamps
    """
    return conflict_resolver.get_field_audit_trail(field_name)


def get_current_form_state() -> Dict[str, Any]:
    """
    Get current form state with all field values.
    
    Returns:
        Dictionary mapping field names to their current values
    """
    return conflict_resolver.get_form_state()


def reset_conflict_state():
    """
    Reset conflict resolver state (for new sessions or testing).
    WARNING: This clears all pending conflicts and form state.
    """
    conflict_resolver.reset()