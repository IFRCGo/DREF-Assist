"""
Shared fixtures, markers, and configuration for the DREF Assist LLM test suite.

This conftest provides:
- Azure OpenAI client fixture (session-scoped, real API calls)
- API key validation (skips session if credentials missing)
- Custom pytest markers for blocker/tier1/security tests
- Path setup matching the backend module structure
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env from backend root
_backend = Path(__file__).parent.parent
load_dotenv(_backend / ".env")

# Add backend paths so imports resolve identically to how app.py does it
sys.path.insert(0, str(_backend))
sys.path.insert(0, str(_backend / "llm_handler"))
sys.path.insert(0, str(_backend / "conflict_resolver"))
sys.path.insert(0, str(_backend / "media-processor"))
sys.path.insert(0, str(_backend / "services"))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "blocker: critical safety test — failure is urgent")
    config.addinivalue_line("markers", "tier1: Tier 1 hard-coded assertion test")
    config.addinivalue_line("markers", "security: security-related test (injection, etc.)")


@pytest.fixture(scope="session")
def azure_client():
    """Create a real AzureOpenAI client for the test session.

    Fails immediately with a clear message if required environment
    variables are missing, rather than silently failing mid-run.
    """
    from openai import AzureOpenAI

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    if not api_key:
        pytest.fail(
            "AZURE_OPENAI_API_KEY environment variable is not set. "
            "LLM tests require a real Azure OpenAI API key. "
            "Set it in backend/.env or export it in your shell."
        )
    if not endpoint:
        pytest.fail(
            "AZURE_OPENAI_ENDPOINT environment variable is not set. "
            "Set it in backend/.env or export it in your shell."
        )

    return AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version or "2024-02-15-preview",
    )


@pytest.fixture
def call_handle_message(azure_client):
    """Fixture that returns a callable to invoke handle_message with the shared client.

    Usage:
        def test_something(call_handle_message):
            result = call_handle_message("Some input", form_state={})
    """
    from llm_handler.handler import handle_message

    def _call(user_message, form_state=None, conversation_history=None):
        return handle_message(
            user_message=user_message,
            current_form_state=form_state or {},
            conversation_history=conversation_history,
            client=azure_client,
        )

    return _call


@pytest.fixture
def call_process_user_input(azure_client):
    """Fixture that returns a callable to invoke process_user_input with the shared client.

    Used for conflict detection tests that need the full service layer.

    Usage:
        def test_conflict(call_process_user_input):
            result = call_process_user_input(
                "New message",
                enriched_form_state={...},
            )
    """
    from services.assistant import process_user_input

    def _call(user_message, enriched_form_state=None, conversation_history=None):
        return process_user_input(
            user_message=user_message,
            enriched_form_state=enriched_form_state or {},
            conversation_history=conversation_history,
            client=azure_client,
        )

    return _call
