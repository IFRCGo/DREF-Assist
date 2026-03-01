"""Audio transcription via Azure OpenAI Whisper API."""
import io
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """Transcribe audio using Azure OpenAI Whisper API.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename (used for format detection)

    Returns:
        Transcribed text

    Raises:
        TranscriptionError: If transcription fails
    """
    try:
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_AUDIO_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_AUDIO_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_AUDIO_API_VERSION"),
        )

        # Wrap bytes in a file-like object with name
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        response = client.audio.transcriptions.create(
            model=os.getenv("AZURE_OPENAI_AUDIO_DEPLOYMENT", "whisper"),
            file=audio_file,
        )

        return response.text

    except Exception as e:
        raise TranscriptionError(f"Transcription failed: {str(e)}")
