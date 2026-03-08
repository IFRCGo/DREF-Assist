"""
Tier 1 tests for field mapping correctness.

Tests 11.4 and 12.8 — values must be mapped to the correct fields
and must not be swapped or assigned to non-existent field IDs.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_only_valid_field_ids,
    assert_all_field_types_valid,
    assert_field_type_correct,
)
from llm_handler.field_schema import VALID_FIELD_IDS


@pytest.mark.tier1
def test_11_4_infrastructure_damage_mapping(call_handle_message):
    """Test 11.4 — Infrastructure Damage Categorisation (Field Mapping).

    Category: Form Section Edge Cases
    Tier: 1 (field mapping) + 2
    Blocker: No

    Input: "100 houses damaged total — 30 completely destroyed, 40 severely, 30 minor."

    Note: homes_damaged and homes_destroyed are NOT valid field IDs in the
    schema. These numbers should appear in event_detail.what_happened narrative
    or the reply text, not as discrete field updates to non-existent fields.
    The LLM must never create field_updates for field IDs outside VALID_FIELD_IDS.
    """
    result = call_handle_message(
        structured_input(
            "100 houses damaged total — 30 completely destroyed, "
            "40 severely, 30 minor."
        ),
        form_state={},
    )

    # Every field_id in updates must be a real schema field
    assert_only_valid_field_ids(result)

    # All types must be correct
    assert_all_field_types_valid(result)

    # If what_happened narrative was populated, check it mentions the numbers
    updates = result.get("field_updates", [])
    what_happened = [
        u for u in updates
        if u.get("field_id") == "event_detail.what_happened"
    ]
    if what_happened:
        narrative = str(what_happened[0].get("value", "")).lower()
        assert "100" in narrative or "30" in narrative, (
            "what_happened narrative should mention infrastructure damage figures"
        )


@pytest.mark.tier1
def test_12_8_field_mapping_error(call_handle_message):
    """Test 12.8 ★ — Field Mapping Error.

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1 (field value assertion)
    Blocker: No

    Input: "500 homes damaged, 3,200 people displaced."

    The value 500 (homes) must NOT end up in a population field.
    The value 3200 (people) must NOT end up being misattributed.
    """
    result = call_handle_message(
        structured_input("500 homes damaged, 3,200 people displaced."),
        form_state={},
    )

    # All field IDs must be valid schema fields
    assert_only_valid_field_ids(result)
    assert_all_field_types_valid(result)

    # If population was extracted, it should be 3200 (people), not 500 (homes)
    updates = result.get("field_updates", [])
    pop_updates = [
        u for u in updates
        if u.get("field_id") == "event_detail.total_affected_population"
    ]
    if pop_updates:
        value = pop_updates[0]["value"]
        assert value != 500, (
            f"Population field contains 500 (homes count) instead of 3200 (people). "
            f"Values were swapped."
        )
