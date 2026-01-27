"""Perceptual hashing for image deduplication."""
import imagehash
from PIL import Image


def compute_hash(image: Image.Image) -> str:
    """Compute perceptual hash for an image.

    Args:
        image: PIL Image to hash

    Returns:
        Hex string representation of the hash
    """
    return str(imagehash.phash(image))


def are_similar(hash1: str, hash2: str, threshold: float = 0.90) -> bool:
    """Check if two hashes indicate similar images.

    Args:
        hash1: First image hash
        hash2: Second image hash
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        True if images are similar (above threshold)
    """
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)

    # Hamming distance - number of different bits
    # Max distance for 64-bit hash is 64
    distance = h1 - h2
    similarity = 1.0 - (distance / 64.0)

    return bool(similarity >= threshold)


def deduplicate_frames(
    frames: list[Image.Image], threshold: float = 0.90
) -> list[Image.Image]:
    """Remove near-duplicate frames based on perceptual similarity.

    Args:
        frames: List of PIL Images
        threshold: Similarity threshold for considering duplicates

    Returns:
        List of unique frames (preserves order, keeps first occurrence)
    """
    if not frames:
        return []

    unique_frames = []
    unique_hashes = []

    for frame in frames:
        frame_hash = compute_hash(frame)

        # Check if similar to any existing unique frame
        is_duplicate = False
        for existing_hash in unique_hashes:
            if are_similar(frame_hash, existing_hash, threshold):
                is_duplicate = True
                break

        if not is_duplicate:
            unique_frames.append(frame)
            unique_hashes.append(frame_hash)

    return unique_frames
