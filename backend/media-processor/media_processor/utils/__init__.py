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
from media_processor.utils.transcription import (
    transcribe_audio,
    TranscriptionError,
)

__all__ = [
    "compute_hash",
    "are_similar",
    "deduplicate_frames",
    "calculate_sample_count",
    "sample_frames",
    "transcribe_audio",
    "TranscriptionError",
]
