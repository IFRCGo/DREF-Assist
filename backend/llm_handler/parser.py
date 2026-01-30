"""
LLM response parsing and validation.

This module handles extracting JSON from GPT-4o responses and validating
the structure and field updates against the schema.
"""

import json
import re
from typing import Dict, Any, List

from .field_schema import validate_field_updates


# Valid classification types from the specification
VALID_CLASSIFICATIONS = frozenset({
    "NEW_INFORMATION",
    "MODIFICATION_REQUEST",
    "QUESTION",
    "OFF_TOPIC",
})

# Fallback response when parsing fails
ERROR_RESPONSE: Dict[str, Any] = {
    "classification": "ERROR",
    "reply": "I had trouble processing that. Could you try again?",
    "field_updates": [],
}


def parse_llm_response(raw_response: str) -> Dict[str, Any]:
    """
    Extracts JSON from the raw LLM response string.

    Handles responses that may be wrapped in markdown code blocks.
    Returns a safe fallback on parse failure.

    Args:
        raw_response: Raw string output from GPT-4o.

    Returns:
        Parsed JSON as a dictionary, or ERROR_RESPONSE on failure.
    """
    if not raw_response or not raw_response.strip():
        return ERROR_RESPONSE.copy()

    text = raw_response.strip()

    # Handle markdown code block wrapping (```json ... ``` or ``` ... ```)
    if text.startswith("```"):
        # Remove opening fence with optional language specifier
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        # Remove closing fence
        text = re.sub(r"\n?```\s*$", "", text)
        text = text.strip()

    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            return ERROR_RESPONSE.copy()
        return parsed
    except json.JSONDecodeError:
        return ERROR_RESPONSE.copy()


def process_llm_response(raw_response: str) -> Dict[str, Any]:
    """
    Parses and validates the complete LLM response.

    This is the main entry point for response processing. It:
    1. Extracts JSON from the raw response
    2. Validates the classification field
    3. Validates all field updates against the schema
    4. Returns a structured, validated response

    Args:
        raw_response: Raw string output from GPT-4o.

    Returns:
        Dictionary with:
        - classification: str (one of VALID_CLASSIFICATIONS or "ERROR")
        - reply: str (message for the user)
        - field_updates: list (validated field updates only)
    """
    parsed = parse_llm_response(raw_response)

    classification = parsed.get("classification", "ERROR")
    if classification not in VALID_CLASSIFICATIONS:
        classification = "ERROR"

    reply = parsed.get("reply", "")
    if not isinstance(reply, str):
        reply = str(reply) if reply is not None else ""

    raw_updates = parsed.get("field_updates", [])
    if not isinstance(raw_updates, list):
        raw_updates = []

    validated_updates = validate_field_updates(raw_updates)

    return {
        "classification": classification,
        "reply": reply,
        "field_updates": validated_updates,
    }
