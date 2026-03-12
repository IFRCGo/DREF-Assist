"""
Tier 1 tests for contradiction handling.

Tests 1.1 and 1.3 — within-message contradictions where the LLM handler
must surface conflicting values in its reply rather than silently picking one.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.form_state_factory import make_plain_form_state
from helpers.assertions import (
    assert_field_present,
    assert_reply_mentions_any,
    assert_all_field_types_valid,
)


@pytest.mark.tier1
def test_1_1_direct_within_message_contradiction(call_handle_message):
    """Test 1.1 — Direct Within-Message Contradiction.

    Category: Ambiguous & Contradictory Information
    Tier: 1 (contradiction flag assertion) + 2 (extraction quality)
    Blocker: No

    Input contains self-contradicting affected population figures (5000, 7000, 8000)
    and contradicting start dates (Jan 15, Jan 12). The LLM must surface the
    contradiction in its reply rather than silently picking one value.
    """
    result = call_handle_message(
        structured_input(
            "Flood in Bangladesh affecting 5,000 people, started January 15th. "
            "Actually 7,000 people. Actually started January 12th. Or was it 8,000?"
        ),
        form_state={},
    )

    # Must extract unambiguous fields correctly
    assert_field_present(result, "operation_overview.disaster_type", "Flood")
    assert_field_present(result, "operation_overview.country")

    # Reply must mention the contradicting values so the surveyor sees both
    assert_reply_mentions_any(result, "5,000", "5000")
    assert_reply_mentions_any(result, "7,000", "7000", "8,000", "8000")

    # All field types must be valid
    assert_all_field_types_valid(result)


@pytest.mark.tier1
def test_1_3_temporal_contradictions(call_handle_message):
    """Test 1.3 — Temporal Contradictions.

    Category: Ambiguous & Contradictory Information
    Tier: 1 (conflict flag) + 2
    Blocker: No

    Input contains multiple contradictory dates for the same event.
    The LLM must detect the inconsistency and not silently pick one date.
    """
    result = call_handle_message(
        structured_input(
            "Earthquake occurred last week on March 5th. Main quake hit March 3rd. "
            "Actually February 28th. Response started March 1st."
        ),
        form_state={},
    )

    # Earthquake should be extracted as the disaster type
    assert_field_present(result, "operation_overview.disaster_type", "Earthquake")

    # Reply should mention at least some of the conflicting dates
    assert_reply_mentions_any(
        result,
        "march 5", "march 3", "february 28",
        "March 5", "March 3", "February 28",
    )

    assert_all_field_types_valid(result)
