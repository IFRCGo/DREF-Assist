"""
DREF Assist FastAPI Application.

Stateless API that orchestrates media processing, LLM interaction,
conflict detection, and DREF evaluation.
"""

import json
import base64
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import AzureOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Ensure sibling packages are importable
_backend_path = Path(__file__).parent
sys.path.insert(0, str(_backend_path))
sys.path.insert(0, str(_backend_path / "media-processor"))
sys.path.insert(0, str(_backend_path / "llm_handler"))
sys.path.insert(0, str(_backend_path / "conflict_resolver"))
sys.path.insert(0, str(_backend_path / "dref_evaluation"))

from services.assistant import process_user_input_stream, FIELD_LABELS
from dref_evaluation.evaluator import DrefEvaluator, RubricLoader

app = FastAPI(title="DREF Assist API")

# --- Frontend → Rubric field name mapping ---
# The prototype frontend uses namespaced field IDs (e.g. "event_detail.what_happened")
# while the evaluation rubric uses Django model field names (e.g. "event_description").
# This map translates frontend keys to rubric keys so the evaluator can find field values.
FRONTEND_TO_RUBRIC_FIELD_MAP: Dict[str, str] = {
    # Operation Overview
    "operation_overview.region_province": "district",
    "operation_overview.disaster_category": "disaster_category",
    "operation_overview.disaster_type": "disaster_type",
    "operation_overview.country": "country",
    "operation_overview.national_society": "national_society",
    "operation_overview.dref_type": "type_of_dref",
    "operation_overview.disaster_onset": "type_of_onset",
    "operation_overview.dref_title": "title",
    "operation_overview.emergency_appeal_planned": "emergency_appeal_planned",
    # Event Detail
    "event_detail.what_happened": "event_description",
    "event_detail.date_trigger_met": "event_date",
    "event_detail.total_affected_population": "num_affected",
    "event_detail.estimated_male_affected": "men",
    "event_detail.estimated_female_affected": "women",
    "event_detail.estimated_girls_under_18": "girls",
    "event_detail.estimated_boys_under_18": "boys",
    # Actions & Needs
    "actions_needs.coordination_mechanisms": "is_there_major_coordination_mechanism",
    "actions_needs.ifrc_description": "ifrc",
    "actions_needs.icrc_description": "icrc",
    "actions_needs.participating_ns": "partner_national_society",
    "actions_needs.national_authorities_actions": "national_authorities",
    "actions_needs.un_other_actors": "un_or_other_actor_actions",
    "actions_needs.identified_gaps": "identified_gaps",
    "actions_needs.ns_action_types": "national_society_actions",
    "actions_needs.gov_requested_assistance": "government_requested_assistance_date",
    # Operation
    "operation.overall_objective": "operation_objective",
    "operation.strategy_rationale": "response_strategy",
    "operation.targeted_total": "total_targeted_population",
    "operation.selection_criteria": "selection_criteria",
    "operation.targeting_description": "people_assisted",
    "operation.staff_volunteers": "human_resource",
    "operation.security_concerns": "safety_concerns",
    "operation.risk_analysis": "risk_security",
    "operation.surge_personnel": "is_surge_personnel_deployed",
    "operation.monitoring": "pmer",
    "operation.communication_strategy": "communication",
    "operation.requested_amount_chf": "amount_requested",
    "operation.child_safeguarding_assessment": "has_child_safeguarding_risk_analysis_assessment",
    "operation.has_anti_fraud_policy": "has_anti_fraud_corruption_policy",
    # Timeframes & Contacts
    "timeframes_contacts.operation_timeframe_months": "operation_timeframe",
    "timeframes_contacts.ns_application_date": "ns_request_date",
    "timeframes_contacts.ns_contact_name": "national_society_contact_name",
    "timeframes_contacts.ns_contact_email": "national_society_contact_email",
    "timeframes_contacts.ns_contact_phone": "national_society_contact_phone_number",
    "timeframes_contacts.appeal_code": "appeal_code",
    "timeframes_contacts.glide_number": "glide_code",
}

# Rubric fields that have no corresponding frontend form input.
# Criteria referencing these fields are filtered out of evaluation responses
# since users cannot fill them in through the current prototype frontend.
_UNSUPPORTED_RUBRIC_FIELDS: set = {
    "budget_file",
    "event_map",
    "event_scope",
    "images",
    "source_information",
    "needs_identified",
    "planned_interventions",
    "num_assisted",
    "ifrc_appeal_manager_name",
    "lessons_learned",
    "anticipatory_actions",
    "major_coordination_mechanism",
    "surge_personnel_deployed",
    "logistic_capacity_of_ns",
}

# Reverse mapping: rubric field name → frontend field ID
# Used to rewrite improvement prompts with names the chat LLM understands.
_RUBRIC_TO_FRONTEND_ID: Dict[str, str] = {
    rubric: frontend for frontend, rubric in FRONTEND_TO_RUBRIC_FIELD_MAP.items()
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---

class EvaluateRequest(BaseModel):
    form_state: Dict[str, Any]

class EvaluateSectionRequest(BaseModel):
    form_state: Dict[str, Any]
    section: str


# --- File type mapping ---

MIME_TO_FILE_TYPE = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "image/gif": "image",
    "video/mp4": "video",
    "video/quicktime": "video",
    "video/x-msvideo": "video",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
    "audio/mp4": "audio",
    "audio/ogg": "audio",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

EXT_TO_FILE_TYPE = {
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image", ".gif": "image",
    ".mp4": "video", ".mov": "video", ".avi": "video",
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio", ".ogg": "audio",
    ".pdf": "pdf",
    ".docx": "docx",
}


def _detect_file_type(filename: str, content_type: Optional[str]) -> str:
    """Detect file type from MIME type or extension."""
    if content_type and content_type in MIME_TO_FILE_TYPE:
        return MIME_TO_FILE_TYPE[content_type]
    ext = Path(filename).suffix.lower()
    return EXT_TO_FILE_TYPE.get(ext, "pdf")


def _extract_plain_values(enriched: Dict[str, Any]) -> Dict[str, Any]:
    """Extract plain values from enriched form state for the evaluator."""
    plain = {}
    for key, val in enriched.items():
        if isinstance(val, dict) and "value" in val:
            plain[key] = val["value"]
        else:
            plain[key] = val
    return plain


def _map_frontend_to_rubric(plain_state: Dict[str, Any]) -> Dict[str, Any]:
    """Translate frontend field names to rubric field names for the evaluator.

    Copies values using FRONTEND_TO_RUBRIC_FIELD_MAP and coerces types
    to match what the evaluator expects (e.g. wrapping strings in lists
    for M2M fields).
    """
    rubric = RubricLoader()
    field_types = rubric.rubric.get("field_type_mapping", {})

    mapped: Dict[str, Any] = {}
    for key, val in plain_state.items():
        rubric_key = FRONTEND_TO_RUBRIC_FIELD_MAP.get(key)
        if rubric_key:
            mapped[rubric_key] = _coerce_value(val, field_types.get(rubric_key, "text"), rubric_key)
        # Always keep the original key too (evaluator ignores unknown keys)
        mapped[key] = val
    return mapped


# Frontend label → Django integer choice mappings for select fields
_CHOICE_LABEL_TO_INT: Dict[str, Dict[str, int]] = {
    "disaster_category": {"Yellow": 0, "Orange": 1, "Red": 2},
    "type_of_onset": {"Sudden": 0, "Slow": 1},
    "type_of_dref": {"Imminent Crisis": 0, "Response": 1, "Protracted Crisis": 2},
}


def _coerce_value(val: Any, field_type: str, rubric_key: str = "") -> Any:
    """Coerce a frontend value to the type the evaluator expects."""
    if val is None:
        return val

    # M2M fields: evaluator expects a list
    if field_type in ("many_to_many", "many_to_many_file"):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val.strip():
            return [val]
        return []

    # Integer fields
    if field_type in ("integer", "integer_choice"):
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, str):
            # Try known label→int mappings first (e.g. "Orange" → 1)
            label_map = _CHOICE_LABEL_TO_INT.get(rubric_key, {})
            if val in label_map:
                return label_map[val]
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        return val

    # Boolean fields
    if field_type == "boolean":
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "yes", "1")
        return bool(val)

    return val


# --- Evaluation post-processing ---

def _rewrite_improvement_prompt(rubric_field: str, criterion_text: str, guidance: str) -> str:
    """Rewrite an improvement prompt to use frontend field names the chat LLM understands."""
    frontend_id = _RUBRIC_TO_FRONTEND_ID.get(rubric_field, rubric_field)
    display_name = FIELD_LABELS.get(frontend_id, frontend_id)
    prompt = f"Please improve the '{display_name}' field ({frontend_id}) to meet this criterion: {criterion_text}"
    if guidance:
        prompt += f"\n\nGuidance: {guidance}"
    return prompt


def _postprocess_evaluation(result_dict: dict) -> dict:
    """Filter unsupported criteria and rewrite improvement prompts.

    - Removes criteria for rubric fields that have no frontend form input
    - Rewrites improvement prompts to use frontend field IDs and display names
    - Recalculates section/overall status after filtering
    """
    for section_key, section in result_dict.get("section_results", {}).items():
        cr = section.get("criteria_results", {})

        # Remove criteria for unsupported fields
        to_remove = [cid for cid, c in cr.items() if c["field"] in _UNSUPPORTED_RUBRIC_FIELDS]
        for cid in to_remove:
            del cr[cid]

        # Rewrite improvement prompts for remaining criteria
        for cid, c in cr.items():
            if c.get("improvement_prompt"):
                c["improvement_prompt"] = _rewrite_improvement_prompt(
                    c["field"], c["criterion"], c.get("guidance", "")
                )

        # Rebuild issues list from remaining criteria
        section["issues"] = [
            c["criterion"] for c in cr.values() if c["outcome"] == "dont_accept"
        ]

        # Recalculate section status after filtering
        has_required_failure = any(
            c["outcome"] == "dont_accept" and c["required"]
            for c in cr.values()
        )
        section["status"] = "needs_revision" if has_required_failure else "accept"

    # Filter improvement_suggestions
    suggestions = result_dict.get("improvement_suggestions", [])
    result_dict["improvement_suggestions"] = [
        s for s in suggestions if s["field"] not in _UNSUPPORTED_RUBRIC_FIELDS
    ]

    # Recalculate overall_status
    has_any_revision = any(
        s["status"] == "needs_revision"
        for s in result_dict.get("section_results", {}).values()
    )
    result_dict["overall_status"] = "needs_revision" if has_any_revision else "accepted"

    return result_dict


# --- Endpoints ---

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(
    data: str = Form(...),
    files: List[UploadFile] = File(default=[]),
):
    """
    Main chat endpoint. Returns an SSE stream with incremental reply text
    followed by a final ``done`` event containing the full structured response.

    SSE event types:
      - ``status``  -- progress messages (e.g. "Processing uploaded files...")
      - ``reply_chunk`` -- incremental reply text (``delta`` + ``snapshot``)
      - ``done``    -- final JSON payload (classification, reply, field_updates, conflicts)
      - ``error``   -- on failure
    """
    payload = json.loads(data)

    user_message = payload.get("user_message", "")
    form_state = payload.get("form_state", {})
    conversation_history = payload.get("conversation_history", [])

    # Read uploaded files into dicts before entering the sync generator
    file_dicts = []
    for upload in files:
        content = await upload.read()
        file_type = _detect_file_type(upload.filename or "file", upload.content_type)
        file_dicts.append({
            "data": base64.b64encode(content).decode("utf-8"),
            "type": file_type,
            "filename": upload.filename or "uploaded_file",
        })

    def _sse_generator():
        try:
            for event in process_user_input_stream(
                user_message=user_message,
                enriched_form_state=form_state,
                files=file_dicts if file_dicts else None,
                conversation_history=conversation_history,
            ):
                event_type = event["event"]
                event_data = json.dumps(event["data"], ensure_ascii=False)
                yield f"event: {event_type}\ndata: {event_data}\n\n"
        except Exception as exc:
            error_data = json.dumps({"detail": str(exc)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _create_llm_client() -> AzureOpenAI:
    """Create an Azure OpenAI client for LLM-based evaluation."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


@app.post("/api/evaluate")
async def evaluate(request: EvaluateRequest):
    """Full DREF evaluation against IFRC rubric."""
    plain_state = _extract_plain_values(request.form_state)
    rubric_state = _map_frontend_to_rubric(plain_state)
    evaluator = DrefEvaluator(llm_client=_create_llm_client())
    result = evaluator.evaluate(dref_id=0, form_state=rubric_state)
    return _postprocess_evaluation(evaluator.to_dict(result))


@app.post("/api/evaluate/section")
async def evaluate_section(request: EvaluateSectionRequest):
    """Section-level DREF evaluation."""
    plain_state = _extract_plain_values(request.form_state)
    rubric_state = _map_frontend_to_rubric(plain_state)
    evaluator = DrefEvaluator(llm_client=_create_llm_client())
    section_result = evaluator.evaluate_section(
        section_name=request.section,
        form_state=rubric_state,
    )

    # Build criteria dict, filtering out unsupported fields
    criteria_dict = {}
    for cid, cr in section_result.criteria_results.items():
        if cr.field in _UNSUPPORTED_RUBRIC_FIELDS:
            continue
        improvement_prompt = ""
        if cr.improvement_prompt:
            improvement_prompt = _rewrite_improvement_prompt(
                cr.field, cr.criterion, cr.guidance
            )
        criteria_dict[cid] = {
            "criterion_id": cr.criterion_id,
            "field": cr.field,
            "criterion": cr.criterion,
            "outcome": cr.outcome,
            "required": cr.required,
            "reasoning": cr.reasoning,
            "improvement_prompt": improvement_prompt,
            "guidance": cr.guidance,
        }

    # Recalculate section status after filtering
    has_required_failure = any(
        c["outcome"] == "dont_accept" and c["required"]
        for c in criteria_dict.values()
    )

    # Build improvement suggestions for failing criteria (excluding unsupported)
    suggestions = []
    for cid, c in criteria_dict.items():
        if c["outcome"] == "dont_accept":
            suggestions.append({
                "section": request.section,
                "field": c["field"],
                "criterion": c["criterion"],
                "priority": 1 if c["required"] else 2,
                "guidance": c["guidance"],
                "ready_prompt": c["improvement_prompt"],
                "auto_applicable": True,
            })

    return {
        "section_name": section_result.section_name,
        "section_display_name": section_result.section_display_name,
        "status": "needs_revision" if has_required_failure else "accept",
        "criteria_results": criteria_dict,
        "issues": [c["criterion"] for c in criteria_dict.values()
                   if c["outcome"] == "dont_accept"],
        "improvement_suggestions": suggestions,
    }


@app.get("/api/evaluate/rubric")
async def get_rubric():
    """Return the evaluation rubric."""
    rubric = RubricLoader()
    return rubric.rubric
