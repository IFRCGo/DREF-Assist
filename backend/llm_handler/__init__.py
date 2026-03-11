"""
LLM Handler for DREF Assist.

This module provides the "brain" of the DREF Assist application, processing
user input (text + processed media) and current form state to produce a
conversational reply and structured field updates using GPT-4o.

Example usage:
    from llm_handler import handle_message

    result = handle_message(
        user_message="There was a flood in Bangladesh affecting 5000 people",
        current_form_state={"operation_overview.country": "Bangladesh"},
    )
    print(result["reply"])
    print(result["field_updates"])
"""

from .handler import handle_message, handle_message_stream

__all__ = ["handle_message", "handle_message_stream"]
