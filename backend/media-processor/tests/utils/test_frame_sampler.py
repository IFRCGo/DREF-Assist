import pytest
from PIL import Image

from media_processor.utils.frame_sampler import sample_frames, calculate_sample_count


def create_test_frames(count: int) -> list[Image.Image]:
    """Create a list of test frames."""
    return [Image.new("RGB", (100, 100), color=f"#{i:02x}0000") for i in range(count)]


class TestCalculateSampleCount:
    def test_minimum_bound(self):
        # 30 frames * 0.10 = 3, but min is 5
        assert calculate_sample_count(30) == 5

    def test_maximum_bound(self):
        # 300 frames * 0.10 = 30, but max is 20
        assert calculate_sample_count(300) == 20

    def test_proportional_middle(self):
        # 100 frames * 0.10 = 10
        assert calculate_sample_count(100) == 10

    def test_exactly_at_minimum(self):
        # 50 frames * 0.10 = 5, exactly at min
        assert calculate_sample_count(50) == 5

    def test_exactly_at_maximum(self):
        # 200 frames * 0.10 = 20, exactly at max
        assert calculate_sample_count(200) == 20

    def test_fewer_frames_than_min(self):
        # 3 frames available, return all
        assert calculate_sample_count(3) == 3

    def test_zero_frames(self):
        assert calculate_sample_count(0) == 0


class TestSampleFrames:
    def test_uniform_sampling(self):
        frames = create_test_frames(100)
        sampled = sample_frames(frames, count=10)
        assert len(sampled) == 10
        # Should be uniformly distributed
        # First and last should be included
        assert sampled[0] is frames[0]
        assert sampled[-1] is frames[-1]

    def test_sample_count_exceeds_frames(self):
        frames = create_test_frames(5)
        sampled = sample_frames(frames, count=10)
        # Should return all available
        assert len(sampled) == 5

    def test_sample_all_frames(self):
        frames = create_test_frames(10)
        sampled = sample_frames(frames, count=10)
        assert len(sampled) == 10
        assert sampled == frames

    def test_empty_frames(self):
        sampled = sample_frames([], count=5)
        assert sampled == []

    def test_single_frame(self):
        frames = create_test_frames(1)
        sampled = sample_frames(frames, count=5)
        assert len(sampled) == 1

    def test_sample_two_from_many(self):
        frames = create_test_frames(100)
        sampled = sample_frames(frames, count=2)
        assert len(sampled) == 2
        assert sampled[0] is frames[0]
        assert sampled[-1] is frames[-1]
