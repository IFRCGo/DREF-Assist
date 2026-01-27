import base64
import io
import os
import pytest
from unittest.mock import patch, Mock, MagicMock
from PIL import Image

from media_processor.handlers.video import VideoHandler
from media_processor.models import FileInput, FileType


def create_mock_video_capture(frame_count: int, fps: float = 30.0):
    """Create a mock cv2.VideoCapture."""
    mock_cap = Mock()
    mock_cap.get.side_effect = lambda prop: {
        5: fps,  # CAP_PROP_FPS
        7: frame_count,  # CAP_PROP_FRAME_COUNT
    }.get(prop, 0)

    frame_data = []
    for i in range(frame_count):
        # Create different colored frames
        import numpy as np
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[:, :] = [i * 10 % 256, 0, 0]  # Vary red channel
        frame_data.append(frame)

    call_count = [0]

    def read_side_effect():
        if call_count[0] < frame_count:
            frame = frame_data[call_count[0]]
            call_count[0] += 1
            return True, frame
        return False, None

    mock_cap.read.side_effect = read_side_effect
    mock_cap.release = Mock()
    mock_cap.isOpened.return_value = True

    return mock_cap


class TestVideoHandler:
    @patch("media_processor.handlers.video.transcribe_audio")
    @patch("media_processor.handlers.video.cv2")
    def test_process_extracts_frames_and_transcript(self, mock_cv2, mock_transcribe):
        # 300 frames at 30fps = 10 seconds = 10 frames at 1fps
        # After dedup, sample 5-20 based on formula
        mock_cap = create_mock_video_capture(frame_count=300, fps=30.0)
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.cvtColor = Mock(side_effect=lambda x, _: x)
        mock_transcribe.return_value = "Video transcript here."

        handler = VideoHandler()
        data = base64.b64encode(b"fake video data").decode()
        file_input = FileInput(data=data, type=FileType.VIDEO, filename="test.mp4")

        # Mock subprocess to create a dummy audio file
        def create_audio_file(*args, **kwargs):
            # Extract the audio path from ffmpeg args (last argument)
            if args and len(args[0]) > 0:
                audio_path = args[0][-1]  # Last arg is output path
                if audio_path.endswith(".mp3"):
                    with open(audio_path, "wb") as f:
                        f.write(b"audio data")
            return Mock(returncode=0)

        with patch("media_processor.handlers.video.subprocess") as mock_subprocess:
            mock_subprocess.run.side_effect = create_audio_file
            result = handler.process(file_input, source_index=1)

        assert result.filename == "test.mp4"
        assert result.source_type == "video"
        assert result.text_content == "Video transcript here."
        assert len(result.images) > 0
        # Check frame naming convention
        assert all(key.startswith("VIDEO_1_FRAME_") for key in result.images.keys())
        assert result.error is None

    @patch("media_processor.handlers.video.cv2")
    def test_reject_unsupported_format(self, mock_cv2):
        handler = VideoHandler()
        data = base64.b64encode(b"data").decode()
        file_input = FileInput(data=data, type=FileType.VIDEO, filename="video.mkv")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "Unsupported" in result.error
        assert "MP4, MOV, AVI" in result.error

    @patch("media_processor.handlers.video.cv2")
    def test_reject_oversized_file(self, mock_cv2):
        handler = VideoHandler()
        large_data = base64.b64encode(b"x" * (101 * 1024 * 1024)).decode()
        file_input = FileInput(data=large_data, type=FileType.VIDEO, filename="huge.mp4")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "100MB" in result.error

    @patch("media_processor.handlers.video.transcribe_audio")
    @patch("media_processor.handlers.video.cv2")
    def test_partial_result_on_transcription_failure(self, mock_cv2, mock_transcribe):
        mock_cap = create_mock_video_capture(frame_count=60, fps=30.0)
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.cvtColor = Mock(side_effect=lambda x, _: x)

        from media_processor.utils.transcription import TranscriptionError
        mock_transcribe.side_effect = TranscriptionError("Whisper timeout")

        handler = VideoHandler()
        data = base64.b64encode(b"video data").decode()
        file_input = FileInput(data=data, type=FileType.VIDEO, filename="test.mp4")

        # Mock subprocess to create a dummy audio file
        def create_audio_file(*args, **kwargs):
            if args and len(args[0]) > 0:
                audio_path = args[0][-1]
                if audio_path.endswith(".mp3"):
                    with open(audio_path, "wb") as f:
                        f.write(b"audio data")
            return Mock(returncode=0)

        with patch("media_processor.handlers.video.subprocess") as mock_subprocess:
            mock_subprocess.run.side_effect = create_audio_file
            result = handler.process(file_input, source_index=1)

        # Should still have frames even if transcription failed
        assert len(result.images) > 0
        assert result.error is None  # Not a hard error
        assert "warning" in result.processing_notes.lower()

    @patch("media_processor.handlers.video.cv2")
    def test_frame_count_bounds(self, mock_cv2):
        """Test the clamp(total * 0.10, min=5, max=20) formula."""
        # Test minimum: 30 unique frames * 0.10 = 3, clamped to 5
        handler = VideoHandler()

        # Verify calculate_sample_count is used correctly
        from media_processor.utils.frame_sampler import calculate_sample_count
        assert calculate_sample_count(30) == 5
        assert calculate_sample_count(100) == 10
        assert calculate_sample_count(300) == 20
