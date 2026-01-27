import base64
import pytest
from unittest.mock import patch, Mock

from media_processor.handlers.audio import AudioHandler
from media_processor.models import FileInput, FileType
from media_processor.utils.transcription import TranscriptionError


class TestAudioHandler:
    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_process_valid_mp3(self, mock_transcribe):
        mock_transcribe.return_value = "Transcribed text from audio."
        handler = AudioHandler()
        data = base64.b64encode(b"fake mp3 data").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="test.mp3")

        result = handler.process(file_input, source_index=1)

        assert result.filename == "test.mp3"
        assert result.source_type == "audio"
        assert result.text_content == "Transcribed text from audio."
        assert result.images == {}
        assert result.error is None

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_process_valid_wav(self, mock_transcribe):
        mock_transcribe.return_value = "WAV transcript."
        handler = AudioHandler()
        data = base64.b64encode(b"fake wav data").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="test.wav")

        result = handler.process(file_input, source_index=1)

        assert result.error is None
        assert result.text_content == "WAV transcript."

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_process_valid_m4a(self, mock_transcribe):
        mock_transcribe.return_value = "M4A transcript."
        handler = AudioHandler()
        data = base64.b64encode(b"fake m4a data").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="recording.m4a")

        result = handler.process(file_input, source_index=1)

        assert result.error is None

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_process_valid_ogg(self, mock_transcribe):
        mock_transcribe.return_value = "OGG transcript."
        handler = AudioHandler()
        data = base64.b64encode(b"fake ogg data").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="audio.ogg")

        result = handler.process(file_input, source_index=1)

        assert result.error is None

    def test_reject_unsupported_format(self):
        handler = AudioHandler()
        data = base64.b64encode(b"fake data").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="audio.flac")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "Unsupported" in result.error
        assert "MP3, WAV, M4A, OGG" in result.error

    def test_reject_oversized_file(self):
        handler = AudioHandler()
        large_data = base64.b64encode(b"x" * (51 * 1024 * 1024)).decode()
        file_input = FileInput(data=large_data, type=FileType.AUDIO, filename="huge.mp3")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "50MB" in result.error

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_transcription_failure_returns_error(self, mock_transcribe):
        mock_transcribe.side_effect = TranscriptionError("Whisper API timeout")
        handler = AudioHandler()
        data = base64.b64encode(b"audio data").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="test.mp3")

        result = handler.process(file_input, source_index=1)

        assert result.error is not None
        assert "Whisper API timeout" in result.error

    @patch("media_processor.handlers.audio.transcribe_audio")
    def test_processing_notes_included(self, mock_transcribe):
        mock_transcribe.return_value = "Transcript"
        handler = AudioHandler()
        data = base64.b64encode(b"audio").decode()
        file_input = FileInput(data=data, type=FileType.AUDIO, filename="test.mp3")

        result = handler.process(file_input, source_index=1)

        assert result.processing_notes is not None
        assert "transcribed" in result.processing_notes.lower()
