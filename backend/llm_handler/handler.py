"""
Main handler for processing user messages through GPT-4o.

This module provides the primary interface for the LLM handler, orchestrating
prompt construction, API calls, and response processing.
"""

from typing import Dict, Any, List, Optional, Union

from openai import OpenAI

from .prompt import build_system_prompt
from .parser import process_llm_response


# Type alias for message content (text string or multimodal list from media-processor)
MessageContent = Union[str, List[Dict[str, Any]]]


def handle_message(
    user_message: MessageContent,
    current_form_state: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[OpenAI] = None,
) -> Dict[str, Any]:
    """
    Process a user message and return reply + field updates.

    This is the main entry point for the LLM handler. It:
    1. Builds the system prompt with current form state
    2. Constructs the messages array with history
    3. Calls GPT-4o with JSON mode
    4. Validates and returns the structured response

    Args:
        user_message: The user's input. Can be:
            - A plain text string
            - A multimodal content list from media-processor's formatter
              (e.g., [{"type": "text", "text": "..."}, {"type": "image_url", ...}])
        current_form_state: Dictionary mapping field IDs to their current values.
        conversation_history: Optional list of previous message dicts with
            "role" and "content" keys.
        client: Optional OpenAI client instance. If not provided, creates one
            using OPENAI_API_KEY from environment.

    Returns:
        Dictionary with:
        - classification: str ("NEW_INFORMATION", "MODIFICATION_REQUEST",
                               "QUESTION", "OFF_TOPIC", or "ERROR")
        - reply: str (message to display to the user)
        - field_updates: list of validated field update dicts
    """
    if client is None:
        client = OpenAI()

    system_prompt = build_system_prompt(current_form_state)

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw_response = response.choices[0].message.content

    return process_llm_response(raw_response)
