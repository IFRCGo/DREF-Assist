"""
System prompt construction for the DREF Assistant LLM.

This module builds the system prompt that instructs GPT-4o on how to process
user messages and extract form field updates for DREF applications.
"""

import json
from typing import Dict, Any

from .field_schema import VALID_FIELD_IDS, FIELD_TYPES, DROPDOWN_OPTIONS


ROLE_DEFINITION = """You are an assistant helping complete a DREF (Disaster Relief Emergency Fund) application for the IFRC. Your job is to extract relevant information from user messages and map it to specific form fields, while being helpful and conversational."""


BEHAVIOR_INSTRUCTIONS = """Instructions:

1. CLASSIFY the user message into one of four types:
   - NEW_INFORMATION: User provides facts, evidence, observations, or documents
   - MODIFICATION_REQUEST: User asks to change a specific field
   - QUESTION: User asks for clarification or help
   - OFF_TOPIC: Message unrelated to DREF application

2. Based on classification:

   NEW_INFORMATION:
   - Identify which fields the information maps to
   - Only update fields where you have clear, explicit information
   - Never guess or fabricate values
   - If information is ambiguous, ask for clarification instead of guessing

   MODIFICATION_REQUEST:
   - Update only the specific field(s) the user mentions
   - Confirm the change in your reply

   QUESTION:
   - Answer helpfully
   - Do not update any fields
   - Return empty field_updates array

   OFF_TOPIC:
   - Politely redirect to DREF-related assistance
   - Do not update any fields
   - Return empty field_updates array

3. NEVER fabricate information. If you cannot determine a value with confidence, do not include it in field_updates.

4. For dropdown fields, only use values from the allowed options.

5. For multi-select fields, return an array of strings.

6. For boolean fields, return true or false.

7. For dates, return ISO format: "YYYY-MM-DD"

CRITICAL - Do not hallucinate:

1. Never invent numbers. If the user says "many people" without a number, do not guess.

2. Never infer demographics. If user says "5000 affected", do not split into male/female unless explicitly stated.

3. Never assume dates. If user says "recently" or "last week", ask for the specific date.

4. Never fill contact information unless explicitly provided.

5. For dropdown fields, if the user's description doesn't clearly match an option, ask for clarification.

6. If unsure whether information maps to a field, err on the side of NOT updating and asking instead.

7. Do not copy information between fields (e.g., don't assume targeted population equals affected population).

Respond in this exact JSON format:
{
  "classification": "NEW_INFORMATION" | "MODIFICATION_REQUEST" | "QUESTION" | "OFF_TOPIC",
  "reply": "your message to the user",
  "field_updates": [
    { "field_id": "tab.field_name", "value": <value> }
  ]
}"""


def _build_field_schema_reference() -> str:
    """
    Builds the field schema reference section from field_schema definitions.

    Groups fields by their tab prefix and includes type information and dropdown options.
    Called once at module load time.
    """
    tabs: Dict[str, list] = {}
    for field_id in sorted(VALID_FIELD_IDS):
        tab, field_name = field_id.split(".", 1)
        if tab not in tabs:
            tabs[tab] = []
        tabs[tab].append((field_name, field_id))

    lines = ["Available fields you can update:"]

    for tab in sorted(tabs.keys()):
        lines.append(f"\n{tab}:")
        for field_name, field_id in tabs[tab]:
            field_type = FIELD_TYPES.get(field_id, "text")

            if field_type == "dropdown" and field_id in DROPDOWN_OPTIONS:
                options = ", ".join(f'"{opt}"' for opt in DROPDOWN_OPTIONS[field_id])
                lines.append(f"- {field_name} (dropdown: {options})")
            elif field_type == "dropdown":
                lines.append(f"- {field_name} (dropdown)")
            elif field_type == "date":
                lines.append(f"- {field_name} (date, ISO format YYYY-MM-DD)")
            elif field_type == "boolean":
                lines.append(f"- {field_name} (boolean)")
            elif field_type == "number":
                lines.append(f"- {field_name} (number)")
            else:
                lines.append(f"- {field_name} (text)")

    return "\n".join(lines)


# Pre-computed at module load - stays in sync with field_schema.py
FIELD_SCHEMA_REFERENCE = _build_field_schema_reference()


def build_system_prompt(current_form_state: Dict[str, Any]) -> str:
    """
    Constructs the complete system prompt with the current form state.

    The prompt has four parts:
    1. Role Definition - What the assistant is and does
    2. Current Form State - JSON of current field values
    3. Field Schema Reference - Available fields and their types (pre-computed)
    4. Behavior Instructions - Classification rules and anti-hallucination guidelines

    Args:
        current_form_state: Dictionary mapping field IDs to their current values.
                           Empty dict if form is blank.

    Returns:
        Complete system prompt string ready for the LLM.
    """
    form_state_json = json.dumps(current_form_state, indent=2, ensure_ascii=False)

    prompt_parts = [
        ROLE_DEFINITION,
        f"\nCurrent form state:\n{form_state_json}",
        f"\n{FIELD_SCHEMA_REFERENCE}",
        f"\n{BEHAVIOR_INSTRUCTIONS}",
    ]

    return "\n".join(prompt_parts)
