"""
Tier 1 tests for missing/partial information handling.

Tests 2.1 and 2.3 — the LLM must NOT fabricate field values when
information is vague, missing, or insufficient. Fields must remain null.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_field_absent,
    assert_all_field_types_valid,
)


@pytest.mark.tier1
def test_2_1_partial_information(call_handle_message):
    """Test 2.1 — Partial Information.

    Category: Missing Critical Information
    Tier: 1 (null field assertion)
    Blocker: No

    Input is extremely vague — no specific disaster type, country, numbers,
    or dates. All fields must remain null. No fabricated values.
    """
    result = call_handle_message(
        structured_input(
            "There was a disaster in the northern region. "
            "Many people were affected. We need help urgently."
        ),
        form_state={},
    )

    # No country extractable — "the northern region" is not a country
    assert_field_absent(result, "operation_overview.country")

    # "Many people" is not a number
    assert_field_absent(result, "event_detail.total_affected_population")

    # "A disaster" is too vague for the disaster_type dropdown
    assert_field_absent(result, "operation_overview.disaster_type")

    # No budget info at all
    assert_field_absent(result, "operation.requested_amount_chf")

    # No date info
    assert_field_absent(result, "event_detail.date_trigger_met")

    assert_all_field_types_valid(result)


@pytest.mark.tier1
def test_2_3_missing_budget_information(call_handle_message):
    """Test 2.3 — Missing Budget Information.

    Category: Missing Critical Information
    Tier: 1 (budget fields null)
    Blocker: No

    Input mentions need for funding and supplies but gives no specific
    CHF amounts. Budget fields must remain null.
    """
    result = call_handle_message(
        structured_input(
            "We need funding for food, water, shelter, and medical supplies "
            "for 3 months. We need significant resources."
        ),
        form_state={},
    )

    # "Significant resources" is not a number — budget must be null
    assert_field_absent(result, "operation.requested_amount_chf")

    assert_all_field_types_valid(result)
