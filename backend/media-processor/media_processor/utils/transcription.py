"""Audio transcription via OpenAI Whisper API."""
import io
from openai import OpenAI


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """Transcribe audio using OpenAI Whisper API.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename (used for format detection)

    Returns:
        Transcribed text

    Raises:
        TranscriptionError: If transcription fails
    """
    try:
        client = OpenAI()

        # Wrap bytes in a file-like object with name
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

        return response.text

    except Exception as e:
        raise TranscriptionError(f"Transcription failed: {str(e)}")
