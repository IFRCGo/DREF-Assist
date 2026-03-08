"""
Tier 1 tests for numeric format handling and type validation.

Tests 5.1 and 12.3 — the LLM must parse informal numeric formats to
correct types and never return string values for number fields.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_field_type_correct,
    assert_all_field_types_valid,
    assert_field_present,
)


@pytest.mark.tier1
def test_5_1_mixed_numeric_formats_type_check(call_handle_message):
    """Test 5.1 — Mixed Numeric Formats and Currencies (Type Check).

    Category: Numeric Confusion & Units
    Tier: 1 (type check) + 2
    Blocker: No

    Input uses informal numeric notation (5k, 250K, 3.5 thousand) and
    multiple currencies. The Tier 1 assertion checks that all values
    are the correct type. The Tier 2 judge evaluates extraction quality.
    """
    result = call_handle_message(
        structured_input(
            "5k people affected. Budget 250K CHF. 3.5 thousand families. "
            "Need $200,000 USD — about €185,000 or 180,000 CHF."
        ),
        form_state={},
    )

    # Every field_update must have the correct schema type
    assert_all_field_types_valid(result)

    # If population was extracted, it must be a number (not string "5k")
    assert_field_type_correct(result, "event_detail.total_affected_population")

    # If budget was extracted, it must be a number
    assert_field_type_correct(result, "operation.requested_amount_chf")


@pytest.mark.tier1
def test_12_3_field_type_mismatch(call_handle_message):
    """Test 12.3 ★ — Field Type Mismatch.

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1 (type assertion)
    Blocker: No

    User provides a number as words ("around five thousand") for an integer
    field. The LLM must parse it to a numeric value (5000), not leave it
    as a string. If truly unparseable, the field should be absent.
    """
    result = call_handle_message(
        structured_input(
            "Around five thousand people were affected by the flood in Bangladesh."
        ),
        form_state={},
    )

    # If the population field was extracted, it must be an integer/float
    assert_field_type_correct(result, "event_detail.total_affected_population")

    # If present, value should be approximately 5000
    updates = result.get("field_updates", [])
    pop_updates = [
        u for u in updates
        if u.get("field_id") == "event_detail.total_affected_population"
    ]
    if pop_updates:
        value = pop_updates[0]["value"]
        assert isinstance(value, (int, float)), (
            f"Population value must be numeric, got {type(value).__name__}: {value!r}"
        )
        assert value == 5000, (
            f"Expected ~5000 for 'five thousand', got {value}"
        )

    # Disaster type should be extractable
    assert_field_present(result, "operation_overview.disaster_type", "Flood")

    assert_all_field_types_valid(result)
