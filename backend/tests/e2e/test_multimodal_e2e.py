"""End-to-end tests for multimodal input processing through the full pipeline.

These tests send synthetic documents through the full pipeline including LLM
and verify field extraction accuracy. Requires Azure OpenAI credentials.

Run: cd backend && .venv/bin/python -m pytest tests/e2e/test_multimodal_e2e.py -v -m e2e
"""
import pytest
import sys
import os

# Add backend paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "media-processor"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "llm_handler"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "conflict_resolver"))

from services.assistant import process_user_input
from tests.e2e.fixtures import (
    FLOOD_REPORT_FIELDS,
    CONFLICTING_REPORT_FIELDS,
    generate_flood_report_pdf,
    generate_flood_report_docx,
    generate_conflicting_assessment_docx,
    generate_test_image_png,
)


pytestmark = pytest.mark.e2e


def _extract_field_map(response: dict) -> dict[str, str]:
    """Convert field_updates list to {field_id: value} dict."""
    return {u["field_id"]: str(u["value"]) for u in response.get("field_updates", [])}


def _assert_field_extracted(field_map: dict, field_id: str, expected_substring: str):
    """Assert a field was extracted and contains expected value."""
    assert field_id in field_map, f"Field {field_id} not found in updates: {list(field_map.keys())}"
    actual = str(field_map[field_id]).lower()
    assert expected_substring.lower() in actual, (
        f"Field {field_id}: expected '{expected_substring}' in '{field_map[field_id]}'"
    )


class TestSingleDocumentPDF:
    """Test PDF processing through the full pipeline."""

    def test_pdf_field_extraction(self):
        b64, filename = generate_flood_report_pdf()
        response = process_user_input(
            user_message="Please extract all relevant DREF information from this document.",
            enriched_form_state={},
            files=[{"data": b64, "type": "pdf", "filename": filename}],
        )

        assert response["classification"] in ("NEW_INFORMATION", "MODIFICATION_REQUEST")
        assert len(response.get("field_updates", [])) > 0, "No field updates extracted from PDF"
        assert response.get("processing_summary", {}).get("successful") == 1

        field_map = _extract_field_map(response)
        _assert_field_extracted(field_map, "operation_overview.country", "sudan")
        _assert_field_extracted(field_map, "operation_overview.disaster_type", "flood")


class TestSingleDocumentDOCX:
    """Test DOCX processing through the full pipeline."""

    def test_docx_field_extraction(self):
        b64, filename = generate_flood_report_docx()
        response = process_user_input(
            user_message="Please extract all relevant DREF information from this document.",
            enriched_form_state={},
            files=[{"data": b64, "type": "docx", "filename": filename}],
        )

        assert response["classification"] in ("NEW_INFORMATION", "MODIFICATION_REQUEST")
        assert len(response.get("field_updates", [])) > 0, "No field updates extracted from DOCX"
        assert response.get("processing_summary", {}).get("successful") == 1

        field_map = _extract_field_map(response)
        _assert_field_extracted(field_map, "operation_overview.country", "sudan")
        _assert_field_extracted(field_map, "operation_overview.disaster_type", "flood")


class TestSingleImage:
    """Test image processing through the full pipeline."""

    def test_image_accepted_and_processed(self):
        b64, filename = generate_test_image_png()
        response = process_user_input(
            user_message="This is a photo from the disaster area. Extract any information you can.",
            enriched_form_state={},
            files=[{"data": b64, "type": "image", "filename": filename}],
        )

        assert response["classification"] is not None
        assert response["reply"] is not None
        assert response.get("processing_summary", {}).get("successful") == 1


class TestMultiDocumentBatch:
    """Test batch submission of multiple documents."""

    def test_pdf_and_docx_together(self):
        pdf_b64, pdf_name = generate_flood_report_pdf()
        docx_b64, docx_name = generate_flood_report_docx()

        response = process_user_input(
            user_message="Extract all DREF information from both documents.",
            enriched_form_state={},
            files=[
                {"data": pdf_b64, "type": "pdf", "filename": pdf_name},
                {"data": docx_b64, "type": "docx", "filename": docx_name},
            ],
        )

        assert response.get("processing_summary", {}).get("total_files") == 2
        assert response.get("processing_summary", {}).get("successful") == 2
        assert len(response.get("field_updates", [])) > 0

    def test_pdf_plus_image(self):
        pdf_b64, pdf_name = generate_flood_report_pdf()
        img_b64, img_name = generate_test_image_png()

        response = process_user_input(
            user_message="Here is a situation report and a photo from the field.",
            enriched_form_state={},
            files=[
                {"data": pdf_b64, "type": "pdf", "filename": pdf_name},
                {"data": img_b64, "type": "image", "filename": img_name},
            ],
        )

        assert response.get("processing_summary", {}).get("total_files") == 2
        assert response.get("processing_summary", {}).get("successful") == 2


class TestConflictingDocuments:
    """Test that conflicting data across documents is detected."""

    def test_conflicting_docx_against_existing_state(self):
        """Send a DOCX with different numbers when form already has values."""
        docx_b64, docx_name = generate_conflicting_assessment_docx()

        enriched_form_state = {
            "event_detail.total_affected_population": {
                "value": "12500",
                "source": "flood_situation_report.docx",
                "timestamp": "2026-03-09T00:00:00Z",
            },
        }

        response = process_user_input(
            user_message="Here is the needs assessment. Please extract all information.",
            enriched_form_state=enriched_form_state,
            files=[{"data": docx_b64, "type": "docx", "filename": docx_name}],
        )

        # Should detect conflict for total_affected_population (12500 vs 15000)
        conflicts = response.get("conflicts", [])
        conflict_fields = [c["field_name"] for c in conflicts]
        assert "event_detail.total_affected_population" in conflict_fields, (
            f"Expected conflict for total_affected_population. Got conflicts: {conflict_fields}. "
            f"Updates: {response.get('field_updates', [])}"
        )

    def test_within_batch_cross_document_conflicts(self):
        """Two documents with conflicting data in a SINGLE prompt, empty form state."""
        docx1_b64, docx1_name = generate_flood_report_docx()
        docx2_b64, docx2_name = generate_conflicting_assessment_docx()

        response = process_user_input(
            user_message="Extract all DREF information from both documents. Note any differences.",
            enriched_form_state={},
            files=[
                {"data": docx1_b64, "type": "docx", "filename": docx1_name},
                {"data": docx2_b64, "type": "docx", "filename": docx2_name},
            ],
        )

        assert response.get("processing_summary", {}).get("successful") == 2

        # Should detect within-batch conflicts for fields with different values
        conflicts = response.get("conflicts", [])
        conflict_fields = [c["field_name"] for c in conflicts]
        assert "event_detail.total_affected_population" in conflict_fields, (
            f"Expected within-batch conflict for total_affected_population. "
            f"Conflicts: {conflict_fields}. Updates: {response.get('field_updates', [])}"
        )

        # Verify per-document source attribution in conflicts
        pop_conflict = next(c for c in conflicts if c["field_name"] == "event_detail.total_affected_population")
        sources = {pop_conflict["existing_value"]["source"], pop_conflict["new_value"]["source"]}
        assert docx1_name in sources or docx2_name in sources, (
            f"Conflict sources should reference document filenames. Got: {sources}"
        )
