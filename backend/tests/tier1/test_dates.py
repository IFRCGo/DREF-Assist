"""
Tier 1 tests for date handling.

Test 6.2 — ambiguous date formats must not be populated without clarification.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_field_absent,
    assert_all_field_types_valid,
    assert_reply_mentions_any,
)


@pytest.mark.tier1
def test_6_2_ambiguous_date_format(call_handle_message):
    """Test 6.2 — Ambiguous Date Format.

    Category: Date & Time Ambiguities
    Tier: 1 (date fields null)
    Blocker: No

    Input uses MM/DD vs DD/MM ambiguous format (03/04/2025 could be
    March 4 or April 3). Date fields must remain null until the
    ambiguity is resolved.
    """
    result = call_handle_message(
        structured_input(
            "Disaster occurred on 03/04/2025. "
            "Operations 05/06/2025 to 08/07/2025."
        ),
        form_state={},
    )

    # Date should NOT be populated because the format is ambiguous
    assert_field_absent(result, "event_detail.date_trigger_met")

    # Reply should mention the date ambiguity
    assert_reply_mentions_any(
        result,
        "ambig", "clarif", "format", "which date",
        "march", "april",  # mentioning possible interpretations
    )

    assert_all_field_types_valid(result)
