"""Video file handler - frame extraction, deduplication, and transcription."""
import base64
import io
import os
import subprocess
import tempfile
from pathlib import Path

import cv2
from PIL import Image

from media_processor.models import FileInput, SourceResult
from media_processor.utils.perceptual_hash import deduplicate_frames
from media_processor.utils.frame_sampler import calculate_sample_count, sample_frames
from media_processor.utils.transcription import transcribe_audio, TranscriptionError


class VideoHandler:
    """Handler for video files (MP4, MOV, AVI)."""

    SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi"}
    MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100MB

    def process(self, file_input: FileInput, source_index: int) -> SourceResult:
        """Process a video file.

        Pipeline:
        1. Extract frames at 1fps
        2. Deduplicate via perceptual hash (>90% similarity)
        3. Sample X frames where X = clamp(total * 0.10, min=5, max=20)
        4. Extract and transcribe audio

        Args:
            file_input: The file input containing base64 data
            source_index: Index for namespacing (VIDEO_N_FRAME_M)

        Returns:
            SourceResult with frames and transcript
        """
        # Validate file extension
        ext = Path(file_input.filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return SourceResult(
                filename=file_input.filename,
                source_type="video",
                error=f"Unsupported video format '{ext}'. Supported: MP4, MOV, AVI",
                images={},
            )

        try:
            # Decode base64
            video_bytes = base64.b64decode(file_input.data)

            # Check size limit
            if len(video_bytes) > self.MAX_SIZE_BYTES:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="video",
                    error=f"File exceeds size limit of 100MB",
                    images={},
                )

            # Process in temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                video_path = os.path.join(temp_dir, file_input.filename)
                audio_path = os.path.join(temp_dir, "audio.mp3")

                # Write video to temp file
                with open(video_path, "wb") as f:
                    f.write(video_bytes)

                # Extract frames
                frames = self._extract_frames_at_1fps(video_path)

                if not frames:
                    return SourceResult(
                        filename=file_input.filename,
                        source_type="video",
                        error="Failed to extract frames from video",
                        images={},
                    )

                # Deduplicate
                unique_frames = deduplicate_frames(frames, threshold=0.90)

                # Sample
                sample_count = calculate_sample_count(len(unique_frames))
                selected_frames = sample_frames(unique_frames, sample_count)

                # Convert frames to base64
                images = {}
                for i, frame in enumerate(selected_frames, start=1):
                    frame_key = f"VIDEO_{source_index}_FRAME_{i}"
                    buffer = io.BytesIO()
                    frame.save(buffer, format="JPEG", quality=85)
                    images[frame_key] = base64.b64encode(buffer.getvalue()).decode()

                # Extract and transcribe audio
                transcript = None
                transcription_warning = None

                try:
                    self._extract_audio(video_path, audio_path)
                    if os.path.exists(audio_path):
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                        transcript = transcribe_audio(audio_bytes, "audio.mp3")
                except TranscriptionError as e:
                    transcription_warning = f"Warning: Audio transcription failed - {str(e)}"
                except Exception as e:
                    transcription_warning = f"Warning: Could not extract audio - {str(e)}"

                notes = f"Selected {len(selected_frames)} frames from {len(frames)} extracted ({len(unique_frames)} after dedup)"
                if transcription_warning:
                    notes += f". {transcription_warning}"

                return SourceResult(
                    filename=file_input.filename,
                    source_type="video",
                    text_content=transcript,
                    images=images,
                    processing_notes=notes,
                )

        except Exception as e:
            return SourceResult(
                filename=file_input.filename,
                source_type="video",
                error=f"Failed to process video: {str(e)}",
                images={},
            )

    def _extract_frames_at_1fps(self, video_path: str) -> list[Image.Image]:
        """Extract frames at 1 frame per second."""
        frames = []
        cap = cv2.VideoCapture(video_path)

        try:
            if not cap.isOpened():
                return frames

            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0  # Default fallback

            frame_interval = int(fps)  # Extract every fps-th frame = 1 per second
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    frames.append(pil_image)

                frame_count += 1

        finally:
            cap.release()

        return frames

    def _extract_audio(self, video_path: str, audio_path: str) -> None:
        """Extract audio track from video using FFmpeg."""
        subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "libmp3lame",
                "-y",  # Overwrite
                audio_path,
            ],
            capture_output=True,
            check=False,  # Don't raise on error (video might have no audio)
        )
