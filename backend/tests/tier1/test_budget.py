"""
Tier 1 tests for budget field handling.

Test 8.1 — budget categories without specific amounts must not populate
numeric budget fields.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_field_absent,
    assert_all_field_types_valid,
)


@pytest.mark.tier1
def test_8_1_budget_items_without_amounts(call_handle_message):
    """Test 8.1 — Budget Items Without Amounts.

    Category: Budget & Financial Complexity
    Tier: 1 (budget fields null)
    Blocker: No

    Input lists budget categories but provides no specific CHF amounts.
    The budget field must remain null.
    """
    result = call_handle_message(
        structured_input(
            "We need money for food, water, shelter, medical, staff, "
            "transportation, logistics, and contingency."
        ),
        form_state={},
    )

    # No specific amounts given — budget must be null
    assert_field_absent(result, "operation.requested_amount_chf")

    assert_all_field_types_valid(result)
