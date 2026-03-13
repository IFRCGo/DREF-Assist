"""
DREF Assistant service - orchestrates media processing and LLM interaction.

Stateless design: all state (form state, conversation history) is passed
in with each request. Conflict detection runs per-request using the
enriched form state from the frontend.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Add parent paths for sibling package imports
_backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(_backend_path / "media-processor"))
sys.path.insert(0, str(_backend_path / "llm_handler"))
sys.path.insert(0, str(_backend_path / "conflict_resolver"))

from media_processor import MediaProcessor, ProcessingInput, FileInput, FileType
from media_processor.formatter import format_for_llm
from llm_handler import handle_message
from conflict_resolver.detector import ConflictDetector, FieldValue

FIELD_LABELS = {
    "operation_overview.national_society": "National Society",
    "operation_overview.dref_type": "DREF Type",
    "operation_overview.disaster_type": "Disaster Type",
    "operation_overview.disaster_onset": "Onset Type",
    "operation_overview.disaster_category": "Disaster Category",
    "operation_overview.country": "Country",
    "operation_overview.region_province": "Region/Province",
    "operation_overview.dref_title": "DREF Title",
    "operation_overview.emergency_appeal_planned": "Emergency Appeal Planned",
    "event_detail.date_trigger_met": "Date Trigger Met",
    "event_detail.total_affected_population": "Total Affected Population",
    "event_detail.people_in_need": "People in Need",
    "event_detail.estimated_male_affected": "Estimated Male Affected",
    "event_detail.estimated_female_affected": "Estimated Female Affected",
    "event_detail.estimated_girls_under_18": "Estimated Girls (under 18)",
    "event_detail.estimated_boys_under_18": "Estimated Boys (under 18)",
    "event_detail.what_happened": "What Happened",
    # actions_needs
    "actions_needs.ns_actions_started": "NS Actions Started",
    "actions_needs.ns_action_types": "National Society Action Types",
    "actions_needs.ifrc_description": "IFRC Presence/Support",
    "actions_needs.participating_ns": "Participating National Societies",
    "actions_needs.icrc_description": "ICRC Presence/Activities",
    "actions_needs.gov_requested_assistance": "Government Requested Assistance",
    "actions_needs.national_authorities_actions": "National Authorities Actions",
    "actions_needs.un_other_actors": "UN/Other Actors",
    "actions_needs.coordination_mechanisms": "Coordination Mechanisms",
    "actions_needs.identified_gaps": "Identified Gaps",
    # operation
    "operation.overall_objective": "Overall Objective",
    "operation.strategy_rationale": "Strategy Rationale",
    "operation.targeting_description": "Targeting Description",
    "operation.selection_criteria": "Selection Criteria",
    "operation.targeted_women": "Targeted Women",
    "operation.targeted_men": "Targeted Men",
    "operation.targeted_girls": "Targeted Girls (under 18)",
    "operation.targeted_boys": "Targeted Boys (under 18)",
    "operation.targeted_total": "Total Targeted Population",
    "operation.people_with_disability": "People with Disability",
    "operation.urban_population": "Urban Population",
    "operation.rural_population": "Rural Population",
    "operation.people_on_the_move": "People on the Move",
    "operation.has_anti_fraud_policy": "Anti-Fraud Policy",
    "operation.has_psea_policy": "PSEA Policy",
    "operation.has_child_protection_policy": "Child Protection Policy",
    "operation.has_whistleblower_policy": "Whistleblower Policy",
    "operation.has_anti_harassment_policy": "Anti-Harassment Policy",
    "operation.risk_analysis": "Risk Analysis",
    "operation.security_concerns": "Security Concerns",
    "operation.child_safeguarding_assessment": "Child Safeguarding Assessment",
    "operation.requested_amount_chf": "Requested Amount (CHF)",
    "operation.staff_volunteers": "Staff/Volunteers",
    "operation.volunteer_diversity": "Volunteer Diversity",
    "operation.surge_personnel": "Surge Personnel",
    "operation.procurement": "Procurement",
    "operation.monitoring": "Monitoring",
    "operation.communication_strategy": "Communication Strategy",
    # timeframes_contacts
    "timeframes_contacts.ns_application_date": "NS Application Date",
    "timeframes_contacts.operation_timeframe_months": "Operation Timeframe (months)",
    "timeframes_contacts.appeal_code": "Appeal Code",
    "timeframes_contacts.glide_number": "GLIDE Number",
    "timeframes_contacts.ns_contact_name": "NS Contact Name",
    "timeframes_contacts.ns_contact_title": "NS Contact Title",
    "timeframes_contacts.ns_contact_email": "NS Contact Email",
    "timeframes_contacts.ns_contact_phone": "NS Contact Phone",
}


def _create_azure_client() -> AzureOpenAI:
    """Create an AzureOpenAI client from environment variables."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


def _extract_plain_form_state(enriched_form_state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract plain values from enriched form state for the LLM.

    Enriched: {"field_id": {"value": X, "source": "...", "timestamp": "..."}}
    Plain:    {"field_id": X}
    """
    plain = {}
    for key, val in enriched_form_state.items():
        if isinstance(val, dict) and "value" in val:
            plain[key] = val["value"]
        else:
            plain[key] = val
    return plain


def _enriched_to_field_values(enriched_form_state: Dict[str, Any]) -> Dict[str, FieldValue]:
    """Convert enriched form state to FieldValue objects for conflict detection."""
    field_values = {}
    for key, val in enriched_form_state.items():
        if isinstance(val, dict) and "value" in val:
            field_values[key] = FieldValue(
                value=val["value"],
                source=val.get("source", "unknown"),
                timestamp=val.get("timestamp", ""),
            )
    return field_values


def _normalize_updates_for_detector(field_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize LLM field_updates (field_id key) to detector format (field key)."""
    return [
        {
            "field": u.get("field_id", u.get("field")),
            "value": u.get("value"),
            "source": u.get("source"),
        }
        for u in field_updates
    ]


def process_user_input(
    user_message: str,
    enriched_form_state: Dict[str, Any],
    files: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[AzureOpenAI] = None,
) -> Dict[str, Any]:
    """
    Process user input (text + optional media files) and return LLM response.

    Stateless: all state is passed in, nothing is stored between calls.

    Args:
        user_message: The user's text message.
        enriched_form_state: Dictionary mapping field IDs to enriched values:
            {"field_id": {"value": X, "source": "...", "timestamp": "..."}}
        files: Optional list of file dicts, each containing:
            - data: Base64-encoded file content
            - type: File type string ("image", "video", "audio", "pdf", "docx")
            - filename: Original filename
        conversation_history: Optional list of previous message dicts with
            "role" and "content" keys.
        client: Optional AzureOpenAI client instance.

    Returns:
        Dictionary with:
        - classification: str
        - reply: str
        - field_updates: list of field update dicts (with field_id, value, source, timestamp)
        - conflicts: list of conflict dicts (if any)
        - processing_summary: dict (if files provided)
    """
    try:
        if client is None:
            client = _create_azure_client()

        # Extract plain values for the LLM (it doesn't need source metadata)
        plain_form_state = _extract_plain_form_state(enriched_form_state)

        llm_input: Any

        processing_summary = None
        source = "user_message"

        if files:
            file_inputs = [
                FileInput(
                    data=f["data"],
                    type=FileType(f["type"]),
                    filename=f["filename"],
                )
                for f in files
            ]

            processor = MediaProcessor()
            processing_result = processor.process(ProcessingInput(files=file_inputs))

            formatted = format_for_llm(processing_result, user_message)
            llm_input = formatted["content"]

            summary = processing_result.processing_summary
            processing_summary = {
                "total_files": summary.total_files,
                "successful": summary.successful,
                "failed": summary.failed,
            }

            source = files[0]["filename"]
            if len(files) > 1:
                source = f"{files[0]['filename']} (+{len(files)-1} more)"
        else:
            llm_input = user_message

        # Call LLM handler
        llm_result = handle_message(
            user_message=llm_input,
            current_form_state=plain_form_state,
            conversation_history=conversation_history,
            client=client,
        )

        # Conflict detection against enriched form state
        field_values = _enriched_to_field_values(enriched_form_state)
        detector = ConflictDetector(field_labels=FIELD_LABELS)
        normalized_updates = _normalize_updates_for_detector(llm_result.get("field_updates", []))

        conflicts, non_conflicting = detector.detect_conflicts(
            current_state=field_values,
            new_updates=normalized_updates,
            source=source,
        )

        # Build response with enriched field updates (add source + timestamp)
        timestamp = datetime.now(timezone.utc).isoformat()
        enriched_updates = [
            {
                "field_id": u["field"],
                "value": u["value"],
                "source": source,
                "timestamp": timestamp,
            }
            for u in non_conflicting
        ]

        response = {
            "classification": llm_result.get("classification"),
            "reply": llm_result.get("reply"),
            "field_updates": enriched_updates,
            "conflicts": [c.to_dict() for c in conflicts] if conflicts else [],
        }

        if processing_summary:
            response["processing_summary"] = processing_summary

        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in process_user_input: {str(e)}")
        raise
