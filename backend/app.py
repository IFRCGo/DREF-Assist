"""
DREF Assist FastAPI Application.

Stateless API that orchestrates media processing, LLM interaction,
conflict detection, and DREF evaluation.
"""

import json
import base64
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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

from services.assistant import process_user_input
from dref_evaluation.evaluator import DrefEvaluator, RubricLoader

app = FastAPI(title="DREF Assist API")

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
    Main chat endpoint. Accepts user message + form state + history as JSON
    in the 'data' form field, and optional file uploads.
    """
    payload = json.loads(data)

    user_message = payload.get("user_message", "")
    form_state = payload.get("form_state", {})
    conversation_history = payload.get("conversation_history", [])

    # Process uploaded files into the format expected by assistant
    file_dicts = []
    for upload in files:
        content = await upload.read()
        file_type = _detect_file_type(upload.filename or "file", upload.content_type)
        file_dicts.append({
            "data": base64.b64encode(content).decode("utf-8"),
            "type": file_type,
            "filename": upload.filename or "uploaded_file",
        })

    result = process_user_input(
        user_message=user_message,
        enriched_form_state=form_state,
        files=file_dicts if file_dicts else None,
        conversation_history=conversation_history,
    )

    return result


@app.post("/api/evaluate")
async def evaluate(request: EvaluateRequest):
    """Full DREF evaluation against IFRC rubric."""
    plain_state = _extract_plain_values(request.form_state)
    evaluator = DrefEvaluator()
    result = evaluator.evaluate(dref_id=0, form_state=plain_state)
    return evaluator.to_dict(result)


@app.post("/api/evaluate/section")
async def evaluate_section(request: EvaluateSectionRequest):
    """Section-level DREF evaluation."""
    plain_state = _extract_plain_values(request.form_state)
    evaluator = DrefEvaluator()
    section_result = evaluator.evaluate_section(
        section_name=request.section,
        form_state=plain_state,
    )
    return {
        "section_name": section_result.section_name,
        "section_display_name": section_result.section_display_name,
        "status": section_result.status,
        "criteria_results": {
            cid: {
                "criterion_id": cr.criterion_id,
                "field": cr.field,
                "criterion": cr.criterion,
                "outcome": cr.outcome,
                "required": cr.required,
                "reasoning": cr.reasoning,
                "guidance": cr.guidance,
            }
            for cid, cr in section_result.criteria_results.items()
        },
        "issues": section_result.issues,
    }


@app.get("/api/evaluate/rubric")
async def get_rubric():
    """Return the evaluation rubric."""
    rubric = RubricLoader()
    return rubric.rubric
