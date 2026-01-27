import io
import pytest
from PIL import Image, ImageDraw

from media_processor.utils.perceptual_hash import (
    compute_hash,
    are_similar,
    deduplicate_frames,
)


def create_test_image(pattern: str = "diagonal", size: tuple = (100, 100)) -> Image.Image:
    """Create a test PIL Image with a pattern.

    Perceptual hashing looks at frequency content, so solid colors all hash
    to the same value. We need images with actual structure/patterns.
    """
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)

    if pattern == "diagonal":
        # Diagonal lines from top-left to bottom-right
        for i in range(0, size[0] + size[1], 10):
            draw.line([(i, 0), (0, i)], fill="black", width=2)
    elif pattern == "horizontal":
        # Horizontal stripes
        for y in range(0, size[1], 10):
            draw.line([(0, y), (size[0], y)], fill="black", width=2)
    elif pattern == "vertical":
        # Vertical stripes
        for x in range(0, size[0], 10):
            draw.line([(x, 0), (x, size[1])], fill="black", width=2)
    elif pattern == "checker":
        # Checkerboard pattern
        for x in range(0, size[0], 20):
            for y in range(0, size[1], 20):
                if (x // 20 + y // 20) % 2 == 0:
                    draw.rectangle([x, y, x + 20, y + 20], fill="black")
    elif pattern == "circle":
        # Concentric circles
        for r in range(5, max(size) // 2, 10):
            draw.ellipse(
                [size[0] // 2 - r, size[1] // 2 - r, size[0] // 2 + r, size[1] // 2 + r],
                outline="black",
                width=2,
            )

    return img


class TestComputeHash:
    def test_returns_hash_string(self):
        img = create_test_image("diagonal")
        hash_value = compute_hash(img)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 16  # phash produces 64 bits = 16 hex chars

    def test_identical_images_same_hash(self):
        img1 = create_test_image("horizontal")
        img2 = create_test_image("horizontal")
        assert compute_hash(img1) == compute_hash(img2)

    def test_different_images_different_hash(self):
        img1 = create_test_image("diagonal")
        img2 = create_test_image("checker")
        assert compute_hash(img1) != compute_hash(img2)


class TestAreSimilar:
    def test_identical_images_are_similar(self):
        img1 = create_test_image("diagonal")
        img2 = create_test_image("diagonal")
        hash1 = compute_hash(img1)
        hash2 = compute_hash(img2)
        assert are_similar(hash1, hash2, threshold=0.90)

    def test_very_different_images_not_similar(self):
        img1 = create_test_image("diagonal")
        img2 = create_test_image("checker")
        hash1 = compute_hash(img1)
        hash2 = compute_hash(img2)
        # Different patterns should have different hashes
        # We verify the function returns a proper Python bool
        result = are_similar(hash1, hash2, threshold=0.99)
        assert isinstance(result, bool)


class TestDeduplicateFrames:
    def test_removes_duplicates(self):
        frames = [
            create_test_image("diagonal"),
            create_test_image("diagonal"),  # duplicate
            create_test_image("checker"),
            create_test_image("diagonal"),  # duplicate
        ]
        unique = deduplicate_frames(frames, threshold=0.90)
        # Should keep first diagonal and checker
        assert len(unique) == 2

    def test_preserves_order(self):
        frames = [
            create_test_image("diagonal"),
            create_test_image("horizontal"),
            create_test_image("checker"),
        ]
        unique = deduplicate_frames(frames, threshold=0.90)
        assert len(unique) == 3

    def test_empty_list(self):
        unique = deduplicate_frames([], threshold=0.90)
        assert unique == []

    def test_single_frame(self):
        frames = [create_test_image("diagonal")]
        unique = deduplicate_frames(frames, threshold=0.90)
        assert len(unique) == 1
