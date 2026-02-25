"""
DREF Assistant service - orchestrates media processing and LLM interaction.

Stateless design: all state (form state, conversation history) is passed
in with each request. Conflict detection runs per-request using the
enriched form state from the frontend.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Add parent paths for sibling package imports
_backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(_backend_path / "media-processor"))
sys.path.insert(0, str(_backend_path / "llm_handler"))
sys.path.insert(0, str(_backend_path / "conflict_resolver"))

from media_processor import MediaProcessor, ProcessingInput, FileInput, FileType
from media_processor.formatter import format_for_llm
from llm_handler import handle_message
from conflict_resolver.detector import ConflictDetector, FieldValue


def _create_azure_client() -> AzureOpenAI:
    """Create an AzureOpenAI client from environment variables."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


def _extract_plain_form_state(enriched_form_state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract plain values from enriched form state for the LLM.

    Enriched: {"field_id": {"value": X, "source": "...", "timestamp": "..."}}
    Plain:    {"field_id": X}
    """
    plain = {}
    for key, val in enriched_form_state.items():
        if isinstance(val, dict) and "value" in val:
            plain[key] = val["value"]
        else:
            plain[key] = val
    return plain


def _enriched_to_field_values(enriched_form_state: Dict[str, Any]) -> Dict[str, FieldValue]:
    """Convert enriched form state to FieldValue objects for conflict detection."""
    field_values = {}
    for key, val in enriched_form_state.items():
        if isinstance(val, dict) and "value" in val:
            field_values[key] = FieldValue(
                value=val["value"],
                source=val.get("source", "unknown"),
                timestamp=val.get("timestamp", ""),
            )
    return field_values


def _normalize_updates_for_detector(field_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize LLM field_updates (field_id key) to detector format (field key)."""
    return [
        {"field": u.get("field_id", u.get("field")), "value": u.get("value")}
        for u in field_updates
    ]


def process_user_input(
    user_message: str,
    enriched_form_state: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[AzureOpenAI] = None,
) -> Dict[str, Any]:
    """
    Process user input (text + optional media files) and return LLM response.

    Stateless: all state is passed in, nothing is stored between calls.

    Args:
        user_message: The user's text message.
        enriched_form_state: Dictionary mapping field IDs to enriched values:
            {"field_id": {"value": X, "source": "...", "timestamp": "..."}}
        files: Optional list of file dicts, each containing:
            - data: Base64-encoded file content
            - type: File type string ("image", "video", "audio", "pdf", "docx")
            - filename: Original filename
        conversation_history: Optional list of previous message dicts with
            "role" and "content" keys.
        client: Optional AzureOpenAI client instance.

    Returns:
        Dictionary with:
        - classification: str
        - reply: str
        - field_updates: list of field update dicts (with field_id, value, source, timestamp)
        - conflicts: list of conflict dicts (if any)
        - processing_summary: dict (if files provided)
    """
    if client is None:
        client = _create_azure_client()

    # Extract plain values for the LLM (it doesn't need source metadata)
    plain_form_state = _extract_plain_form_state(enriched_form_state)

    llm_input: Any

    processing_summary = None
    source = "user_message"

    if files:
        file_inputs = [
            FileInput(
                data=f["data"],
                type=FileType(f["type"]),
                filename=f["filename"],
            )
            for f in files
        ]

        processor = MediaProcessor()
        processing_result = processor.process(ProcessingInput(files=file_inputs))

        formatted = format_for_llm(processing_result, user_message)
        llm_input = formatted["content"]

        summary = processing_result.processing_summary
        processing_summary = {
            "total_files": summary.total_files,
            "successful": summary.successful,
            "failed": summary.failed,
        }

        source = files[0]["filename"]
        if len(files) > 1:
            source = f"{files[0]['filename']} (+{len(files)-1} more)"
    else:
        llm_input = user_message

    # Call LLM handler
    llm_result = handle_message(
        user_message=llm_input,
        current_form_state=plain_form_state,
        conversation_history=conversation_history,
        client=client,
    )

    # Conflict detection against enriched form state
    field_values = _enriched_to_field_values(enriched_form_state)
    detector = ConflictDetector()
    normalized_updates = _normalize_updates_for_detector(llm_result.get("field_updates", []))

    conflicts, non_conflicting = detector.detect_conflicts(
        current_state=field_values,
        new_updates=normalized_updates,
        source=source,
    )

    # Build response with enriched field updates (add source + timestamp)
    timestamp = datetime.now(timezone.utc).isoformat()
    enriched_updates = [
        {
            "field_id": u["field"],
            "value": u["value"],
            "source": source,
            "timestamp": timestamp,
        }
        for u in non_conflicting
    ]

    response = {
        "classification": llm_result.get("classification"),
        "reply": llm_result.get("reply"),
        "field_updates": enriched_updates,
        "conflicts": [c.to_dict() for c in conflicts] if conflicts else [],
    }

    if processing_summary:
        response["processing_summary"] = processing_summary

    return response
