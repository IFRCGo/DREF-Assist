import base64
import io
import pytest
from unittest.mock import patch, Mock
from PIL import Image

from media_processor.processor import MediaProcessor
from media_processor.models import FileInput, FileType, ProcessingInput


def create_test_image() -> str:
    img = Image.new("RGB", (10, 10), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


class TestMediaProcessor:
    def test_process_single_image(self):
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(
                data=create_test_image(),
                type=FileType.IMAGE,
                filename="photo.jpg",
            )
        ])

        result = processor.process(input_data)

        assert result.processing_summary.total_files == 1
        assert result.processing_summary.successful == 1
        assert result.processing_summary.failed == 0
        assert len(result.sources) == 1
        assert result.sources[0].source_type == "image"

    def test_process_multiple_files(self):
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="img1.jpg"),
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="img2.png"),
        ])

        result = processor.process(input_data)

        assert result.processing_summary.total_files == 2
        assert result.processing_summary.successful == 2
        assert len(result.sources) == 2

    def test_error_isolation(self):
        """One failing file shouldn't block others."""
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="good.jpg"),
            FileInput(data=base64.b64encode(b"not an image").decode(), type=FileType.IMAGE, filename="bad.jpg"),
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="also_good.jpg"),
        ])

        result = processor.process(input_data)

        assert result.processing_summary.total_files == 3
        assert result.processing_summary.successful == 2
        assert result.processing_summary.failed == 1

        # Verify error in failed file
        failed = [s for s in result.sources if s.error is not None]
        assert len(failed) == 1
        assert failed[0].filename == "bad.jpg"

    def test_empty_input(self):
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[])

        result = processor.process(input_data)

        assert result.processing_summary.total_files == 0
        assert result.processing_summary.successful == 0
        assert result.sources == []

    def test_source_indexing(self):
        """Verify sources are indexed correctly for namespacing."""
        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="img1.jpg"),
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="img2.jpg"),
        ])

        result = processor.process(input_data)

        # First image should have IMAGE_1, second should have IMAGE_2
        assert "IMAGE_1" in result.sources[0].images
        assert "IMAGE_2" in result.sources[1].images

    @patch("media_processor.handlers.audio.transcribe_audio")
    @patch("media_processor.handlers.pdf.fitz")
    def test_mixed_file_types(self, mock_fitz, mock_transcribe):
        mock_transcribe.return_value = "Audio transcript"

        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "PDF text content here"
        mock_page.get_text_blocks.return_value = [(0, 0, 100, 50, "PDF text", 0, 0)]
        mock_page.get_images.return_value = []
        mock_page.rect = Mock(height=800)
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc

        processor = MediaProcessor()
        input_data = ProcessingInput(files=[
            FileInput(data=create_test_image(), type=FileType.IMAGE, filename="photo.jpg"),
            FileInput(data=base64.b64encode(b"audio").decode(), type=FileType.AUDIO, filename="voice.mp3"),
            FileInput(data=base64.b64encode(b"pdf").decode(), type=FileType.PDF, filename="doc.pdf"),
        ])

        result = processor.process(input_data)

        assert result.processing_summary.total_files == 3
        source_types = {s.source_type for s in result.sources}
        assert source_types == {"image", "audio", "pdf"}
