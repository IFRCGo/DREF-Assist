"""Tests for conflict detection, including within-batch conflict detection."""

from conflict_resolver.detector import ConflictDetector, FieldValue, Conflict


FIELD_LABELS = {
    "event_detail.total_affected_population": "Total Affected Population",
    "event_detail.what_happened": "What Happened",
    "operation_overview.disaster_type": "Disaster Type",
    "operation_overview.country": "Country",
}


class TestWithinBatchConflicts:
    """Tests for within-batch conflict detection (multiple updates for same field)."""

    def _make_detector(self):
        return ConflictDetector(field_labels=FIELD_LABELS)

    def test_single_update_per_field_no_batch_conflict(self):
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.total_affected_population", "value": 5000},
            {"field": "operation_overview.disaster_type", "value": "Flood"},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="report.pdf"
        )

        assert len(conflicts) == 0
        assert len(non_conflicting) == 2

    def test_within_batch_conflict_different_values(self):
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.total_affected_population", "value": 500},
            {"field": "event_detail.total_affected_population", "value": 1000},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="report.pdf"
        )

        assert len(conflicts) == 1
        assert conflicts[0].field_name == "event_detail.total_affected_population"
        assert conflicts[0].existing_value.value == 500
        assert conflicts[0].new_value.value == 1000
        assert conflicts[0].conflict_id.startswith("batch_")
        # Neither value should be in non_conflicting since they conflict
        assert len(non_conflicting) == 0

    def test_within_batch_no_conflict_same_values(self):
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.total_affected_population", "value": 5000},
            {"field": "event_detail.total_affected_population", "value": 5000},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="report.pdf"
        )

        assert len(conflicts) == 0
        # Deduplicated to one update
        assert len(non_conflicting) == 1
        assert non_conflicting[0]["value"] == 5000

    def test_within_batch_three_updates_same_field(self):
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.total_affected_population", "value": 500},
            {"field": "event_detail.total_affected_population", "value": 1000},
            {"field": "event_detail.total_affected_population", "value": 2000},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="report.pdf"
        )

        # Should produce 2 conflicts: (500 vs 1000) and (500 vs 2000)
        assert len(conflicts) == 2
        assert conflicts[0].existing_value.value == 500
        assert conflicts[0].new_value.value == 1000
        assert conflicts[1].existing_value.value == 500
        assert conflicts[1].new_value.value == 2000
        assert len(non_conflicting) == 0

    def test_within_batch_conflict_text_fields(self):
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.what_happened", "value": "A flood destroyed 500 homes."},
            {"field": "event_detail.what_happened", "value": "An earthquake struck the region."},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="reports"
        )

        assert len(conflicts) == 1
        assert conflicts[0].field_name == "event_detail.what_happened"
        assert len(non_conflicting) == 0

    def test_within_batch_conflict_plus_state_conflict(self):
        """Within-batch conflict for one field, state conflict for another."""
        detector = self._make_detector()
        updates = [
            # Two updates for same field (within-batch conflict)
            {"field": "event_detail.total_affected_population", "value": 500},
            {"field": "event_detail.total_affected_population", "value": 1000},
            # One update that conflicts with current state
            {"field": "operation_overview.disaster_type", "value": "Earthquake"},
        ]
        current_state = {
            "operation_overview.disaster_type": FieldValue(
                value="Flood", source="previous.pdf", timestamp="2024-01-01T00:00:00"
            )
        }

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state=current_state, new_updates=updates, source="report.pdf"
        )

        # 1 batch conflict + 1 state conflict = 2 total
        assert len(conflicts) == 2
        batch_conflicts = [c for c in conflicts if c.conflict_id.startswith("batch_")]
        state_conflicts = [c for c in conflicts if not c.conflict_id.startswith("batch_")]
        assert len(batch_conflicts) == 1
        assert len(state_conflicts) == 1
        assert state_conflicts[0].field_name == "operation_overview.disaster_type"
        assert len(non_conflicting) == 0

    def test_within_batch_conflict_mixed_with_non_conflicting(self):
        """Batch conflict for one field, non-conflicting update for another."""
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.total_affected_population", "value": 500},
            {"field": "event_detail.total_affected_population", "value": 1000},
            {"field": "operation_overview.country", "value": "Bangladesh"},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="report.pdf"
        )

        assert len(conflicts) == 1
        assert conflicts[0].field_name == "event_detail.total_affected_population"
        assert len(non_conflicting) == 1
        assert non_conflicting[0]["field"] == "operation_overview.country"

    def test_within_batch_string_normalization(self):
        """Same string values with different casing/whitespace should not conflict."""
        detector = self._make_detector()
        updates = [
            {"field": "event_detail.what_happened", "value": "A flood occurred in the region."},
            {"field": "event_detail.what_happened", "value": "a flood occurred in the region."},
        ]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="report.pdf"
        )

        assert len(conflicts) == 0
        assert len(non_conflicting) == 1


class TestExistingConflictDetection:
    """Tests for original conflict detection against current state (regression tests)."""

    def _make_detector(self):
        return ConflictDetector(field_labels=FIELD_LABELS)

    def test_no_conflict_when_state_empty(self):
        detector = self._make_detector()
        updates = [{"field": "operation_overview.country", "value": "Bangladesh"}]

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state={}, new_updates=updates, source="user_message"
        )

        assert len(conflicts) == 0
        assert len(non_conflicting) == 1

    def test_conflict_when_value_differs(self):
        detector = self._make_detector()
        updates = [{"field": "event_detail.total_affected_population", "value": 7500}]
        current_state = {
            "event_detail.total_affected_population": FieldValue(
                value=5000, source="old_report.pdf", timestamp="2024-01-01T00:00:00"
            )
        }

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state=current_state, new_updates=updates, source="new_report.pdf"
        )

        assert len(conflicts) == 1
        assert conflicts[0].field_name == "event_detail.total_affected_population"
        assert conflicts[0].existing_value.value == 5000
        assert conflicts[0].new_value.value == 7500
        assert len(non_conflicting) == 0

    def test_no_conflict_when_value_same(self):
        detector = self._make_detector()
        updates = [{"field": "event_detail.total_affected_population", "value": 5000}]
        current_state = {
            "event_detail.total_affected_population": FieldValue(
                value=5000, source="old.pdf", timestamp="2024-01-01T00:00:00"
            )
        }

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state=current_state, new_updates=updates, source="new.pdf"
        )

        assert len(conflicts) == 0
        assert len(non_conflicting) == 1

    def test_overwrite_fields_never_conflict(self):
        detector = self._make_detector()
        updates = [{"field": "last_modified", "value": "2024-06-01"}]
        current_state = {
            "last_modified": FieldValue(
                value="2024-01-01", source="system", timestamp="2024-01-01T00:00:00"
            )
        }

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state=current_state, new_updates=updates, source="system"
        )

        assert len(conflicts) == 0
        assert len(non_conflicting) == 1

    def test_numeric_tolerance(self):
        detector = self._make_detector()
        updates = [{"field": "event_detail.total_affected_population", "value": 5000.0}]
        current_state = {
            "event_detail.total_affected_population": FieldValue(
                value=5000, source="old.pdf", timestamp="2024-01-01T00:00:00"
            )
        }

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state=current_state, new_updates=updates, source="new.pdf"
        )

        assert len(conflicts) == 0
        assert len(non_conflicting) == 1
