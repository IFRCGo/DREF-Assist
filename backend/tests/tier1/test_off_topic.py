"""
Tier 1 tests for off-topic message handling.

Test 12.11 — off-topic messages must be classified as OFF_TOPIC
with zero field updates.
"""

import pytest

from helpers.input_builder import structured_input
from helpers.assertions import (
    assert_classification,
    assert_no_field_updates,
)


@pytest.mark.tier1
def test_12_11_off_topic_handling(call_handle_message):
    """Test 12.11 ★ — Off-Topic Handling.

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1
    Blocker: No

    Input is completely unrelated to DREF applications (Python scripting,
    pasta recipes). Must be classified as OFF_TOPIC with no field updates.
    """
    result = call_handle_message(
        structured_input(
            "Can you help me write a Python script to scrape weather data? "
            "Also what's a good pasta recipe?"
        ),
        form_state={},
    )

    assert_classification(result, "OFF_TOPIC")
    assert_no_field_updates(result)
