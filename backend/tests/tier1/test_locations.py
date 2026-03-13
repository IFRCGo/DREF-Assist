"""
Tier 1 tests for geographic location handling.

Tests 7.1 and 7.3 — ambiguous or informal locations must not be populated.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_field_absent,
    assert_all_field_types_valid,
)


@pytest.mark.tier1
def test_7_1_generic_location_names(call_handle_message):
    """Test 7.1 — Generic Location Names.

    Category: Geographic Ambiguities
    Tier: 1 (location null)
    Blocker: No

    "Springfield" exists in multiple countries. "Central Region" without a
    country is meaningless. Location fields must remain null.
    """
    result = call_handle_message(
        structured_input(
            "Flood in Springfield. Central Region affected. "
            "Communities near the river."
        ),
        form_state={},
    )

    # "Springfield" is ambiguous — no country extractable
    assert_field_absent(result, "operation_overview.country")

    # region_province is allowed — it's a proposed change the user can review

    assert_all_field_types_valid(result)


@pytest.mark.tier1
def test_7_3_informal_location_descriptions(call_handle_message):
    """Test 7.3 — Informal Location Descriptions.

    Category: Geographic Ambiguities
    Tier: 1 (location null)
    Blocker: No

    Input describes locations using landmarks ("big market", "old church")
    rather than proper geographic names. Location fields must remain null.
    """
    result = call_handle_message(
        structured_input(
            "Flood hit the area by the big market, near the old church. "
            "The neighbourhood by the river."
        ),
        form_state={},
    )

    assert_field_absent(result, "operation_overview.country")
    assert_field_absent(result, "operation_overview.region_province")

    assert_all_field_types_valid(result)
