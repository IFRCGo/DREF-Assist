"""
Main handler for processing user messages through GPT-4o.

This module provides the primary interface for the LLM handler, orchestrating
prompt construction, API calls, and response processing.
"""

import os
from typing import Dict, Any, Generator, List, Optional, Tuple, Union

from openai import AzureOpenAI, BadRequestError
from dotenv import load_dotenv

from .prompt import build_system_prompt
from .parser import process_llm_response

load_dotenv()

_CONTENT_FILTER_RESPONSE: Dict[str, Any] = {
    "classification": "OFF_TOPIC",
    "reply": (
        "I'm not able to help with that request. "
        "Please ask something related to the DREF application."
    ),
    "field_updates": [],
}

# Type alias for message content (text string or multimodal list from media-processor)
MessageContent = Union[str, List[Dict[str, Any]]]


def _build_messages(
    user_message: MessageContent,
    current_form_state: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Build the messages array for the OpenAI API call."""
    system_prompt = build_system_prompt(current_form_state)
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    return messages


def handle_message(
    user_message: MessageContent,
    current_form_state: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[AzureOpenAI] = None,
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
        client: Optional AzureOpenAI client instance. If not provided, creates one
            using Azure environment variables.

    Returns:
        Dictionary with:
        - classification: str ("NEW_INFORMATION", "MODIFICATION_REQUEST",
                               "QUESTION", "OFF_TOPIC", or "ERROR")
        - reply: str (message to display to the user)
        - field_updates: list of validated field update dicts
    """
    if client is None:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )

    messages = _build_messages(user_message, current_form_state, conversation_history)

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
    except BadRequestError:
        # Azure content management policy rejected the prompt
        return _CONTENT_FILTER_RESPONSE.copy()

    # Content filter may allow the request but redact the response
    raw_response = response.choices[0].message.content
    if raw_response is None:
        return _CONTENT_FILTER_RESPONSE.copy()

    return process_llm_response(raw_response)


def handle_message_stream(
    user_message: MessageContent,
    current_form_state: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[AzureOpenAI] = None,
) -> Generator[Tuple[str, str], None, None]:
    """
    Stream a user message response, yielding (delta, accumulated) tuples.

    Same as handle_message but uses stream=True. Yields raw token deltas
    as they arrive. The caller is responsible for parsing the final
    accumulated JSON via process_llm_response().

    Yields:
        Tuples of (delta_text, accumulated_text).
    """
    if client is None:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )

    messages = _build_messages(user_message, current_form_state, conversation_history)

    stream = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
        stream=True,
    )

    accumulated = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            accumulated += delta
            yield delta, accumulated
