import pytest
from unittest.mock import Mock, patch, MagicMock
import io

from media_processor.utils.transcription import transcribe_audio, TranscriptionError


class TestTranscribeAudio:
    @patch("media_processor.utils.transcription.AzureOpenAI")
    def test_successful_transcription(self, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.text = "This is the transcribed text."
        mock_client.audio.transcriptions.create.return_value = mock_response

        audio_bytes = b"fake audio data"
        result = transcribe_audio(audio_bytes, filename="test.mp3")

        assert result == "This is the transcribed text."
        mock_client.audio.transcriptions.create.assert_called_once()

    @patch("media_processor.utils.transcription.AzureOpenAI")
    def test_empty_transcription(self, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.text = ""
        mock_client.audio.transcriptions.create.return_value = mock_response

        audio_bytes = b"silent audio"
        result = transcribe_audio(audio_bytes, filename="silent.mp3")

        assert result == ""

    @patch("media_processor.utils.transcription.AzureOpenAI")
    def test_api_error_raises_transcription_error(self, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

        audio_bytes = b"audio data"
        with pytest.raises(TranscriptionError) as exc_info:
            transcribe_audio(audio_bytes, filename="test.mp3")

        assert "API Error" in str(exc_info.value)

    @patch("media_processor.utils.transcription.AzureOpenAI")
    def test_uses_whisper_model(self, mock_openai_class):
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.text = "text"
        mock_client.audio.transcriptions.create.return_value = mock_response

        transcribe_audio(b"audio", filename="test.mp3")

        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["model"] == "whisper"
