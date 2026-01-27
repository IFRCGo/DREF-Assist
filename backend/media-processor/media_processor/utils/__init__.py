"""Utility modules."""
from media_processor.utils.perceptual_hash import (
    compute_hash,
    are_similar,
    deduplicate_frames,
)

__all__ = ["compute_hash", "are_similar", "deduplicate_frames"]
