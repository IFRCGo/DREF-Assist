"""
DREF Assistant service - orchestrates media processing and LLM interaction.

This module provides the main entry point for processing user input that may
contain both text and media files, coordinating the media-processor and
llm_handler modules.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from openai import OpenAI

# Add parent paths for sibling package imports
_backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(_backend_path / "media-processor"))
sys.path.insert(0, str(_backend_path / "llm_handler"))

from media_processor import MediaProcessor, ProcessingInput, FileInput, FileType
from media_processor.formatter import format_for_llm
from llm_handler import handle_message


def process_user_input(
    user_message: str,
    current_form_state: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[OpenAI] = None,
) -> Dict[str, Any]:
    """
    Process user input (text + optional media files) and return LLM response.

    This is the main entry point for the DREF assistant. It:
    1. Processes any attached media files through media-processor
    2. Formats the combined text + media for the LLM
    3. Sends to GPT-4o via llm_handler
    4. Returns validated response with field updates

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

    Returns:
        Dictionary with:
        - classification: str ("NEW_INFORMATION", "MODIFICATION_REQUEST",
                               "QUESTION", "OFF_TOPIC", or "ERROR")
        - reply: str (message to display to the user)
        - field_updates: list of validated field update dicts
        - processing_summary: dict with file processing stats (if files provided)

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
        >>> print(result["reply"])
        >>> print(result["field_updates"])
    """
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
    result = handle_message(
        user_message=llm_input,
        current_form_state=current_form_state,
        conversation_history=conversation_history,
        client=client,
    )

    # Add processing summary if files were processed
    if processing_summary:
        result["processing_summary"] = processing_summary

    return result
