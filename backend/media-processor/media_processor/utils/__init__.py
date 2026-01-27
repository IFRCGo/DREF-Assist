"""Utility modules."""
from media_processor.utils.perceptual_hash import (
    compute_hash,
    are_similar,
    deduplicate_frames,
)
from media_processor.utils.frame_sampler import (
    calculate_sample_count,
    sample_frames,
)

__all__ = [
    "compute_hash",
    "are_similar",
    "deduplicate_frames",
    "calculate_sample_count",
    "sample_frames",
]
