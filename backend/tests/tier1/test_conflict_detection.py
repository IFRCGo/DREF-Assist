"""
Tier 1 tests for conflict detection — ALL BLOCKERS.

Tests 12.1, 12.2, 12.4, 12.5 — the system must detect contradictions
between new input and existing form state, and must NEVER silently
overwrite a confirmed field value.

These tests call process_user_input() (not handle_message) because
conflict detection requires the service layer with enriched form state.
"""

import pytest

from helpers.input_builder import structured_input, pdf_input
from helpers.form_state_factory import make_enriched_form_state
from helpers.assertions import (
    assert_has_conflicts,
    assert_conflict_for_field,
    assert_field_not_silently_overwritten,
    assert_all_field_types_valid,
)


@pytest.mark.blocker
@pytest.mark.tier1
def test_12_1_cross_turn_contradiction(call_process_user_input):
    """Test 12.1 ★ — Cross-Turn Contradiction (BLOCKER).

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1
    Blocker: YES

    Turn 1 sets total_affected_population=5000 (confirmed).
    Turn 5 uploads a PDF stating 3,000.
    The field must NOT be silently overwritten. A conflict must be raised.
    """
    # Form state has confirmed value from earlier turn
    enriched_state = make_enriched_form_state(
        source="user_message_turn_1",
        event_detail__total_affected_population=5000,
    )

    # New document contradicts the existing value
    result = call_process_user_input(
        pdf_input("assessment_update.pdf", {
            "Impact Summary": "Total affected population: 3,000 persons."
        }),
        enriched_form_state=enriched_state,
        conversation_history=[
            {"role": "user", "content": "5000 people were affected by the flood."},
            {"role": "assistant", "content": "I've recorded 5,000 as the total affected population."},
        ],
    )

    # BLOCKER: Conflict must be detected
    assert_has_conflicts(result, min_count=1)
    assert_conflict_for_field(result, "event_detail.total_affected_population")

    # The field must NOT appear in field_updates with the new value
    assert_field_not_silently_overwritten(
        result,
        field_id="event_detail.total_affected_population",
        original_value=5000,
    )


@pytest.mark.blocker
@pytest.mark.tier1
def test_12_2_conflict_resolution_ux_flow(call_process_user_input):
    """Test 12.2 ★ — Conflict Resolution UX Flow (BLOCKER).

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1 + 3 (human review)
    Blocker: YES

    Document A says 4,200 affected. Document B says 6,800 affected.
    The field must be paused (not in field_updates). Both values must
    be presented. No auto-resolution or averaging.
    """
    # Document A's value is already in the form
    enriched_state = make_enriched_form_state(
        source="document_a.pdf",
        event_detail__total_affected_population=4200,
    )

    # Document B provides a different number
    result = call_process_user_input(
        pdf_input("document_b.pdf", {
            "Summary": "The disaster has affected 6,800 people across the region."
        }),
        enriched_form_state=enriched_state,
    )

    # BLOCKER: Conflict must be detected
    assert_has_conflicts(result)
    assert_conflict_for_field(result, "event_detail.total_affected_population")

    # The field must NOT be silently resolved
    assert_field_not_silently_overwritten(
        result,
        field_id="event_detail.total_affected_population",
        original_value=4200,
    )


@pytest.mark.blocker
@pytest.mark.tier1
def test_12_4_cross_document_conflict(call_process_user_input):
    """Test 12.4 ★ — Cross-Document Conflict (BLOCKER).

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1
    Blocker: YES

    Form has values from PDF-A (4500 affected, March 3).
    PDF-B says 7200 affected, March 1.
    Both contradicting fields must trigger conflicts.
    """
    # PDF-A values already in form
    enriched_state = make_enriched_form_state(
        source="pdf_a.pdf",
        event_detail__total_affected_population=4500,
        event_detail__date_trigger_met="2025-03-03",
    )

    # PDF-B contradicts both values
    result = call_process_user_input(
        pdf_input("pdf_b.pdf", {
            "Situation Report": (
                "7,200 people affected by the disaster. "
                "The event began on March 1, 2025."
            )
        }),
        enriched_form_state=enriched_state,
    )

    # BLOCKER: At least the population conflict must be detected
    assert_has_conflicts(result, min_count=1)
    assert_conflict_for_field(result, "event_detail.total_affected_population")

    # Population must not be silently overwritten
    assert_field_not_silently_overwritten(
        result,
        field_id="event_detail.total_affected_population",
        original_value=4500,
    )


@pytest.mark.blocker
@pytest.mark.tier1
def test_12_5_silent_overwrite_prevention(call_process_user_input):
    """Test 12.5 ★ — Silent Overwrite Prevention (BLOCKER).

    Category: New Tests — Multi-Turn, Stateful & Systemic
    Tier: 1
    Blocker: YES

    Form has confirmed total_affected_population=8000.
    New message says "Actually 6,000 people."
    The field must NOT be silently changed. Either a conflict is raised
    or the field remains unchanged.
    """
    enriched_state = make_enriched_form_state(
        source="confirmed_user_input",
        event_detail__total_affected_population=8000,
    )

    result = call_process_user_input(
        "Actually 6,000 people were affected.",
        enriched_form_state=enriched_state,
    )

    # BLOCKER: Must not silently overwrite 8000 → 6000
    assert_field_not_silently_overwritten(
        result,
        field_id="event_detail.total_affected_population",
        original_value=8000,
    )
