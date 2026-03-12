"""
Tier 1 tests for contradiction handling.

Tests 1.1 and 1.3 — within-message contradictions where the LLM handler
must surface conflicting values in its reply rather than silently picking one.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.form_state_factory import make_plain_form_state
from helpers.assertions import (
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
            "Severe flooding has hit Bangladesh affecting 5,000 people, started January 15th. "
            "Actually 7,000 people. Actually started January 12th. Or was it 8,000?"
        ),
        form_state={},
    )

    # Reply must mention at least 2 of the 3 conflicting values (not just the chosen one)
    reply = result.get("reply", "").lower()
    mentioned = set()
    if "5,000" in reply or "5000" in reply:
        mentioned.add("5000")
    if "7,000" in reply or "7000" in reply:
        mentioned.add("7000")
    if "8,000" in reply or "8000" in reply:
        mentioned.add("8000")
    assert len(mentioned) >= 2, (
        f"Reply should mention at least 2 of the 3 conflicting values "
        f"(5000, 7000, 8000) but only mentioned {mentioned}. "
        f"Reply: {result.get('reply', '')[:300]}"
    )

    # All field types must be valid
    assert_all_field_types_valid(result)


@pytest.mark.tier1
def test_1_3_temporal_contradictions(call_handle_message):
    """Test 1.3 — Temporal Contradictions.

    Category: Ambiguous & Contradictory Information
    Tier: 1 (conflict flag) + 2
    Blocker: No

    Input contains multiple contradictory dates for the same event alongside
    unambiguous fields (disaster type, country, affected population).
    The LLM must extract the unambiguous fields and flag the date conflict.
    """
    result = call_handle_message(
        structured_input(
            "A major earthquake has struck Nepal affecting 12,000 people. "
            "The quake occurred on March 5th. Main quake hit March 3rd. "
            "Actually February 28th. Response started March 1st."
        ),
        form_state={},
    )

    # Reply should mention at least some of the conflicting dates
    assert_reply_mentions_any(
        result,
        "march 5", "march 3", "february 28",
        "March 5", "March 3", "February 28",
    )

    assert_all_field_types_valid(result)
