"""Backend services - orchestration layer for domain modules."""

from services.assistant import process_user_input

__all__ = ["process_user_input"]
