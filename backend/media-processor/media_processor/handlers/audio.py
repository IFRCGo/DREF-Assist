"""Audio file handler - transcription via Whisper."""
import base64
from pathlib import Path

from media_processor.models import FileInput, SourceResult
from media_processor.utils.transcription import transcribe_audio, TranscriptionError


class AudioHandler:
    """Handler for audio files (MP3, WAV, M4A, OGG)."""

    SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".webm"}
    MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

    def process(self, file_input: FileInput, source_index: int) -> SourceResult:
        """Process an audio file.

        Args:
            file_input: The file input containing base64 data
            source_index: Index for namespacing

        Returns:
            SourceResult with transcript or error
        """
        # Validate file extension
        ext = Path(file_input.filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return SourceResult(
                filename=file_input.filename,
                source_type="audio",
                error=f"Unsupported audio format '{ext}'. Supported: MP3, WAV, M4A, OGG",
                images={},
            )

        try:
            # Decode base64
            audio_bytes = base64.b64decode(file_input.data)

            # Check size limit
            if len(audio_bytes) > self.MAX_SIZE_BYTES:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="audio",
                    error=f"File exceeds size limit of 50MB",
                    images={},
                )

            # Transcribe
            transcript = transcribe_audio(audio_bytes, file_input.filename)

            return SourceResult(
                filename=file_input.filename,
                source_type="audio",
                text_content=transcript,
                images={},
                processing_notes="Audio transcribed via Whisper API",
            )

        except TranscriptionError as e:
            return SourceResult(
                filename=file_input.filename,
                source_type="audio",
                error=str(e),
                images={},
            )
        except Exception as e:
            return SourceResult(
                filename=file_input.filename,
                source_type="audio",
                error=f"Failed to process audio: {str(e)}",
                images={},
            )
