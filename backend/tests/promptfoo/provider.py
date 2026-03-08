"""
Custom Promptfoo provider wrapping the DREF Assist LLM handler.

This provider is called by Promptfoo for each Tier 2 test case.
It invokes handle_message() with real Azure OpenAI API calls and
returns the full JSON response for the judge to evaluate.

Usage in promptfooconfig.yaml:
    providers:
      - id: "python:provider.py"
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Setup paths identical to conftest.py
_backend = Path(__file__).parent.parent.parent
_project_root = _backend.parent
# Load .env from project root (where AZURE_OPENAI_* vars live)
load_dotenv(_project_root / ".env")
load_dotenv(_backend / ".env")  # fallback if backend has its own .env

sys.path.insert(0, str(_backend))
sys.path.insert(0, str(_backend / "llm_handler"))
sys.path.insert(0, str(_backend / "conflict_resolver"))
sys.path.insert(0, str(_backend / "media-processor"))

from openai import AzureOpenAI
from llm_handler.handler import handle_message


def _get_client() -> AzureOpenAI:
    """Create Azure OpenAI client from environment variables."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    if not api_key or not endpoint:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set. "
            "Check backend/.env or export them in your shell."
        )

    return AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version or "2024-02-15-preview",
    )


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Promptfoo custom provider entry point.

    Args:
        prompt: The rendered user message (from test_input variable)
        options: Provider config from promptfooconfig.yaml
        context: Contains 'vars' dict with test case variables

    Returns:
        dict with 'output' key containing the full system response as JSON string
    """
    client = _get_client()
    vars_ = context.get("vars", {})

    # Parse form state and conversation history from test case variables
    form_state_str = vars_.get("form_state_before", "{}")
    history_str = vars_.get("conversation_history", "[]")

    try:
        form_state = json.loads(form_state_str) if isinstance(form_state_str, str) else form_state_str
    except json.JSONDecodeError:
        form_state = {}

    try:
        conversation_history = json.loads(history_str) if isinstance(history_str, str) else history_str
    except json.JSONDecodeError:
        conversation_history = []

    # Call the real LLM handler
    result = handle_message(
        user_message=prompt,
        current_form_state=form_state,
        conversation_history=conversation_history,
        client=client,
    )

    # Return the full response as JSON for the judge to evaluate
    return {
        "output": json.dumps(result, indent=2, ensure_ascii=False),
    }
