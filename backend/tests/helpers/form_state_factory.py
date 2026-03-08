"""
Form state factory for the DREF Assist LLM test suite.

Builds form state objects that exactly match the real DREF form schema
defined in backend/llm_handler/field_schema.py. Uses double-underscore
convention for keyword arguments, converting to dot-notation field IDs.

Field ID typos are caught at construction time via validation against
VALID_FIELD_IDS, preventing false passes from misnamed fields.
"""

from datetime import datetime, timezone
from typing import Any

from llm_handler.field_schema import VALID_FIELD_IDS


def _convert_key(key: str) -> str:
    """Convert double-underscore key to dot-notation field ID and validate.

    Args:
        key: Keyword argument name using __ separator (e.g., "event_detail__total_affected_population")

    Returns:
        Dot-notation field ID (e.g., "event_detail.total_affected_population")

    Raises:
        ValueError: If the resulting field ID is not in VALID_FIELD_IDS
    """
    # Split on double underscore to get tab and field
    # e.g., "event_detail__total_affected_population" -> "event_detail.total_affected_population"
    # Handle the case where field names themselves have single underscores
    parts = key.split("__", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Key '{key}' must use double-underscore to separate tab from field. "
            f"Example: 'event_detail__total_affected_population'"
        )
    field_id = f"{parts[0]}.{parts[1]}"
    if field_id not in VALID_FIELD_IDS:
        raise ValueError(
            f"Unknown field ID: '{field_id}' (from key '{key}'). "
            f"Check VALID_FIELD_IDS in field_schema.py for valid field names."
        )
    return field_id


def make_plain_form_state(**fields: Any) -> dict:
    """Create a plain form state dict for use with handle_message().

    Args:
        **fields: Keyword arguments using double-underscore notation.
            Each key is validated against the real field schema.

    Returns:
        Dict mapping dot-notation field IDs to values.

    Example:
        state = make_plain_form_state(
            operation_overview__country="Bangladesh",
            event_detail__total_affected_population=5000,
            operation_overview__disaster_type="Flood",
        )
        # Returns: {
        #     "operation_overview.country": "Bangladesh",
        #     "event_detail.total_affected_population": 5000,
        #     "operation_overview.disaster_type": "Flood",
        # }
    """
    result = {}
    for key, value in fields.items():
        field_id = _convert_key(key)
        result[field_id] = value
    return result


def make_enriched_form_state(source: str = "previous_input", **fields: Any) -> dict:
    """Create an enriched form state dict for use with process_user_input().

    The enriched format wraps each value with source and timestamp metadata,
    matching the format expected by the conflict resolver.

    Args:
        source: The source label for all fields (e.g., "report.pdf", "user_message")
        **fields: Keyword arguments using double-underscore notation.

    Returns:
        Dict mapping dot-notation field IDs to enriched value dicts.

    Example:
        state = make_enriched_form_state(
            source="assessment.pdf",
            event_detail__total_affected_population=5000,
        )
        # Returns: {
        #     "event_detail.total_affected_population": {
        #         "value": 5000,
        #         "source": "assessment.pdf",
        #         "timestamp": "2025-03-08T12:00:00+00:00",
        #     }
        # }
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    result = {}
    for key, value in fields.items():
        field_id = _convert_key(key)
        result[field_id] = {
            "value": value,
            "source": source,
            "timestamp": timestamp,
        }
    return result


def enrich_field(value: Any, source: str = "test", timestamp: str = None) -> dict:
    """Enrich a single field value for manual enriched form state construction.

    Useful when you need to build enriched state with different sources
    per field, which make_enriched_form_state doesn't support.

    Args:
        value: The field value
        source: Source label
        timestamp: Optional ISO timestamp (defaults to now)

    Returns:
        Enriched value dict with value, source, and timestamp.
    """
    return {
        "value": value,
        "source": source,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
