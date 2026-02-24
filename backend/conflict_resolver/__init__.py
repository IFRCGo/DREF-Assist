"""
Conflict Resolution Module for DREF Assist

Detects and manages conflicts when multiple documents provide
different values for the same form field.
"""

from .detector import ConflictDetector, Conflict, FieldValue
from .manager import ConflictManager, ConflictResolution
from .service import ConflictResolverService

__all__ = [
    "ConflictDetector",
    "Conflict",
    "FieldValue",
    "ConflictManager",
    "ConflictResolution",
    "ConflictResolverService",
]

__version__ = "1.0.0"