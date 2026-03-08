"""
Reusable assertion helpers for the DREF Assist LLM test suite.

These encode domain-specific checking logic so test files stay concise
and assertion failures produce clear, actionable messages.
"""

import json
from typing import Any, Optional

from llm_handler.field_schema import VALID_FIELD_IDS, FIELD_TYPES


# ---------------------------------------------------------------------------
# Classification assertions
# ---------------------------------------------------------------------------

def assert_classification(result: dict, expected: str):
    """Assert the response classification matches the expected value."""
    actual = result.get("classification")
    assert actual == expected, (
        f"Expected classification '{expected}', got '{actual}'. "
        f"Reply: {result.get('reply', '')[:200]}"
    )


# ---------------------------------------------------------------------------
# Field update assertions
# ---------------------------------------------------------------------------

def assert_field_present(result: dict, field_id: str, expected_value: Optional[Any] = None):
    """Assert a specific field appears in field_updates with optional value check.

    Works with both handle_message format (field_id key) and
    process_user_input format (also field_id key).
    """
    updates = result.get("field_updates", [])
    matching = [u for u in updates if u.get("field_id") == field_id]
    assert len(matching) > 0, (
        f"Field '{field_id}' not found in field_updates. "
        f"Got: {[u.get('field_id') for u in updates]}"
    )
    if expected_value is not None:
        actual = matching[0].get("value")
        assert actual == expected_value, (
            f"Field '{field_id}' value mismatch: expected {expected_value!r}, got {actual!r}"
        )


def assert_field_absent(result: dict, field_id: str):
    """Assert a specific field does NOT appear in field_updates."""
    updates = result.get("field_updates", [])
    matching = [u for u in updates if u.get("field_id") == field_id]
    assert len(matching) == 0, (
        f"Field '{field_id}' should NOT be in field_updates "
        f"but found with value: {matching[0].get('value')!r}"
    )


def assert_no_field_updates(result: dict):
    """Assert field_updates is empty."""
    updates = result.get("field_updates", [])
    assert len(updates) == 0, (
        f"Expected empty field_updates, got {len(updates)} update(s): "
        f"{[u.get('field_id') for u in updates]}"
    )


def assert_only_valid_field_ids(result: dict):
    """Assert every field_id in field_updates is in the real schema."""
    for update in result.get("field_updates", []):
        fid = update.get("field_id")
        assert fid in VALID_FIELD_IDS, (
            f"Invalid field ID '{fid}' in field_updates. "
            f"Not found in VALID_FIELD_IDS."
        )


# ---------------------------------------------------------------------------
# Type validation assertions
# ---------------------------------------------------------------------------

def assert_field_type_correct(result: dict, field_id: str):
    """Assert the value type for a field matches the schema type."""
    updates = result.get("field_updates", [])
    matching = [u for u in updates if u.get("field_id") == field_id]
    if not matching:
        return  # Field not present — nothing to check

    value = matching[0].get("value")
    expected_type = FIELD_TYPES.get(field_id)

    if expected_type == "number":
        assert isinstance(value, (int, float)), (
            f"{field_id}: expected number type, got {type(value).__name__} ({value!r})"
        )
    elif expected_type == "boolean":
        assert isinstance(value, bool), (
            f"{field_id}: expected bool, got {type(value).__name__} ({value!r})"
        )
    elif expected_type == "text":
        assert isinstance(value, str), (
            f"{field_id}: expected str, got {type(value).__name__} ({value!r})"
        )
    elif expected_type == "date":
        assert isinstance(value, str), (
            f"{field_id}: expected date string, got {type(value).__name__} ({value!r})"
        )
    elif expected_type == "multi_select":
        assert isinstance(value, list), (
            f"{field_id}: expected list, got {type(value).__name__} ({value!r})"
        )
    elif expected_type == "dropdown":
        assert isinstance(value, str), (
            f"{field_id}: expected dropdown string, got {type(value).__name__} ({value!r})"
        )


def assert_all_field_types_valid(result: dict):
    """Assert every field_update has the correct type per the schema."""
    for update in result.get("field_updates", []):
        field_id = update.get("field_id")
        if field_id in FIELD_TYPES:
            assert_field_type_correct(result, field_id)


# ---------------------------------------------------------------------------
# Security / injection assertions
# ---------------------------------------------------------------------------

def assert_string_absent_from_response(result: dict, forbidden_string: str):
    """Assert a string does not appear anywhere in the full response.

    Checks reply text, classification, and all field values.
    Case-sensitive by default — pass lowered string to check case-insensitively.
    """
    reply = result.get("reply", "")
    classification = result.get("classification", "")
    field_values = [str(u.get("value", "")) for u in result.get("field_updates", [])]
    field_ids = [str(u.get("field_id", "")) for u in result.get("field_updates", [])]

    all_text = " ".join([reply, classification] + field_values + field_ids)

    assert forbidden_string not in all_text, (
        f"Forbidden string '{forbidden_string}' found in response. "
        f"Reply excerpt: {reply[:200]}"
    )


def assert_no_value_equals(result: dict, forbidden_value: Any):
    """Assert no field_update has a specific forbidden value."""
    for update in result.get("field_updates", []):
        actual = update.get("value")
        assert actual != forbidden_value, (
            f"Forbidden value {forbidden_value!r} found in field "
            f"'{update.get('field_id')}'"
        )


# ---------------------------------------------------------------------------
# Conflict detection assertions (for process_user_input results)
# ---------------------------------------------------------------------------

def assert_has_conflicts(result: dict, min_count: int = 1):
    """Assert the response contains at least min_count conflicts.

    Only meaningful for results from process_user_input(), which includes
    a 'conflicts' key. handle_message() does not return conflicts.
    """
    conflicts = result.get("conflicts", [])
    assert len(conflicts) >= min_count, (
        f"Expected at least {min_count} conflict(s), got {len(conflicts)}. "
        f"field_updates present: {[u.get('field_id') for u in result.get('field_updates', [])]}"
    )


def assert_conflict_for_field(result: dict, field_name: str):
    """Assert a conflict exists for a specific field.

    The conflict resolver uses 'field_name' as the key in conflict dicts.
    """
    conflicts = result.get("conflicts", [])
    matching = [c for c in conflicts if c.get("field_name") == field_name]
    assert len(matching) > 0, (
        f"No conflict found for field '{field_name}'. "
        f"Got conflicts for: {[c.get('field_name') for c in conflicts]}"
    )


def assert_field_not_silently_overwritten(
    result: dict, field_id: str, original_value: Any
):
    """Assert a field was not silently overwritten without a conflict.

    This is the critical blocker assertion. It is NOT acceptable for
    field_updates to contain a new value with zero conflicts for that field.

    Either:
    - The field is absent from field_updates (safe — not updated), OR
    - The field is in field_updates with the original value (safe — unchanged), OR
    - The field is in field_updates with a new value AND there's a conflict (safe — flagged)

    A new value in field_updates WITHOUT a conflict = silent overwrite = BLOCKER.
    """
    updates = result.get("field_updates", [])
    conflicts = result.get("conflicts", [])

    field_updates = [u for u in updates if u.get("field_id") == field_id]
    field_conflicts = [c for c in conflicts if c.get("field_name") == field_id]

    if not field_updates:
        return  # Field not in updates — safe

    new_value = field_updates[0].get("value")
    if new_value == original_value:
        return  # Value unchanged — safe

    # Value changed — there MUST be a conflict
    assert len(field_conflicts) > 0, (
        f"BLOCKER: Silent overwrite detected for '{field_id}'. "
        f"Value changed from {original_value!r} to {new_value!r} "
        f"without a conflict being raised."
    )


# ---------------------------------------------------------------------------
# Reply content assertions
# ---------------------------------------------------------------------------

def assert_reply_mentions(result: dict, *substrings: str):
    """Assert the reply text contains all specified substrings (case-insensitive)."""
    reply = result.get("reply", "").lower()
    for s in substrings:
        assert s.lower() in reply, (
            f"Reply does not mention '{s}'. "
            f"Reply: {result.get('reply', '')[:300]}"
        )


def assert_reply_mentions_any(result: dict, *substrings: str):
    """Assert the reply text contains at least one of the specified substrings."""
    reply = result.get("reply", "").lower()
    found = any(s.lower() in reply for s in substrings)
    assert found, (
        f"Reply does not mention any of: {substrings}. "
        f"Reply: {result.get('reply', '')[:300]}"
    )
