"""Bounded proportional frame sampling."""
from PIL import Image


def calculate_sample_count(
    total_frames: int,
    proportion: float = 0.10,
    min_frames: int = 5,
    max_frames: int = 20,
) -> int:
    """Calculate number of frames to sample.

    Formula: X = clamp(total * proportion, min, max)

    Args:
        total_frames: Total number of available frames
        proportion: Fraction of frames to select
        min_frames: Minimum frames to return
        max_frames: Maximum frames to return

    Returns:
        Number of frames to sample
    """
    if total_frames == 0:
        return 0

    if total_frames <= min_frames:
        return total_frames

    target = int(total_frames * proportion)
    return max(min_frames, min(target, max_frames))


def sample_frames(frames: list[Image.Image], count: int) -> list[Image.Image]:
    """Sample frames uniformly from a list.

    Args:
        frames: List of frames to sample from
        count: Number of frames to select

    Returns:
        Uniformly sampled subset of frames
    """
    total = len(frames)

    if total == 0:
        return []

    if count >= total:
        return frames

    if count == 1:
        return [frames[0]]

    # Uniform sampling: include first and last, distribute evenly between
    indices = []
    for i in range(count):
        # Map i in [0, count-1] to index in [0, total-1]
        index = round(i * (total - 1) / (count - 1))
        indices.append(index)

    return [frames[i] for i in indices]
