"""
Main handler for processing user messages through GPT-4o.

This module provides the primary interface for the LLM handler, orchestrating
prompt construction, API calls, and response processing.
"""

import os
import time
from typing import Dict, Any, Generator, List, Optional, Tuple, Union

from openai import AzureOpenAI, RateLimitError, APITimeoutError
from dotenv import load_dotenv

from .prompt import build_system_prompt
from .parser import process_llm_response

load_dotenv()

# LLM timeout and retry configuration
LLM_TIMEOUT = 30  # seconds - prevents hanging on Azure OpenAI calls
LLM_MAX_RETRIES = 3  # maximum number of retry attempts
LLM_RETRY_BASE_DELAY = 1  # seconds - initial delay for exponential backoff
MAX_HISTORY_MESSAGES = 10  # send only the last 5 exchanges (10 messages) to the LLM

# Type alias for message content (text string or multimodal list from media-processor)
MessageContent = Union[str, List[Dict[str, Any]]]


def _create_client() -> AzureOpenAI:
    """Create an AzureOpenAI client from environment variables."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    if not api_key or not endpoint or not api_version:
        raise ValueError(
            f"Missing Azure OpenAI config: api_key={bool(api_key)}, "
            f"endpoint={bool(endpoint)}, api_version={bool(api_version)}"
        )

    return AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )


def _build_messages(
    user_message: MessageContent,
    current_form_state: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Build the messages array for the OpenAI API call."""
    system_prompt = build_system_prompt(current_form_state)
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history[-MAX_HISTORY_MESSAGES:])
    messages.append({"role": "user", "content": user_message})
    return messages


def _call_llm_with_retry(client: AzureOpenAI, deployment: str, messages: List[Dict[str, Any]]) -> str:
    """
    Call Azure OpenAI with exponential backoff retry logic.
    
    Retries on RateLimitError and APITimeoutError with exponential backoff.
    Max 3 attempts with delays: 1s, 2s, 4s.
    
    Args:
        client: AzureOpenAI client instance
        deployment: Model deployment name
        messages: Messages array for the API call
        
    Returns:
        Raw response content string
        
    Raises:
        Last exception if all retries fail
    """
    last_error = None
    
    for attempt in range(LLM_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=LLM_TIMEOUT,
            )
            return response.choices[0].message.content
        except (RateLimitError, APITimeoutError) as e:
            last_error = e
            if attempt < LLM_MAX_RETRIES - 1:
                delay = LLM_RETRY_BASE_DELAY * (2 ** attempt)
                print(f"LLM API error (attempt {attempt + 1}/{LLM_MAX_RETRIES}): {type(e).__name__}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"LLM API error after {LLM_MAX_RETRIES} attempts: {str(e)}")
    
    raise last_error


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
    try:
        if client is None:
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION")
            
            if not api_key or not endpoint or not api_version:
                raise ValueError(f"Missing Azure OpenAI config: api_key={bool(api_key)}, endpoint={bool(endpoint)}, api_version={bool(api_version)}")
            
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version,
            )

        system_prompt = build_system_prompt(current_form_state)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history[-MAX_HISTORY_MESSAGES:])

        messages.append({"role": "user", "content": user_message})

        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        print(f"Calling Azure OpenAI with deployment: {deployment}")
        
        raw_response = _call_llm_with_retry(client, deployment, messages)

        return process_llm_response(raw_response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in handle_message: {str(e)}")
        return {
            "classification": "ERROR",
            "reply": f"An error occurred while processing your message: {str(e)}",
            "field_updates": [],
        }


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
        client = _create_client()

    messages = _build_messages(user_message, current_form_state, conversation_history)

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    print(f"Calling Azure OpenAI (streaming) with deployment: {deployment}")

    stream = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
        stream=True,
        timeout=LLM_TIMEOUT,
    )

    accumulated = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            accumulated += delta
            yield delta, accumulated
